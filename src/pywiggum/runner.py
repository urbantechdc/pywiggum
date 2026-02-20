"""Main orchestration loop for PyWiggum."""

import logging
import time
from datetime import datetime
from pathlib import Path

from pywiggum.agents.base import BaseAgent
from pywiggum.agents.opencode import OpenCodeAgent
from pywiggum.config import WiggumConfig
from pywiggum.controls import Controls
from pywiggum.history import HistoryTracker, TaskCompletion
from pywiggum.kanban import KanbanManager
from pywiggum.prompt import PromptBuilder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class Runner:
    """Main orchestration loop for PyWiggum."""

    def __init__(self, config: WiggumConfig, log_file: Path | None = None):
        """Initialize runner.

        Args:
            config: PyWiggum configuration
            log_file: Optional path to log file (defaults to work_dir/wiggum.log)
        """
        self.config = config
        self.work_dir = config.get_work_dir()

        # Set up file logging
        if log_file is None:
            log_file = self.work_dir / "wiggum.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(file_handler)

        # Initialize components
        self.kanban = KanbanManager(config.get_kanban_path())
        self.controls = Controls(self.work_dir)
        self.history = HistoryTracker(self.work_dir)
        self.prompt_builder = PromptBuilder(config)

        # Initialize agent
        self.agent = self._create_agent()

        # Runtime state
        self.current_iteration = 0
        self.current_task_id: str | None = None
        self.current_task_start: datetime | None = None

    def _create_agent(self) -> BaseAgent:
        """Create the agent backend based on configuration.

        Returns:
            Agent instance

        Raises:
            ValueError: If agent backend is not supported or not available
        """
        backend = self.config.agent.backend

        if backend == "opencode":
            agent = OpenCodeAgent(self.config.agent.model)
        elif backend == "claude_code":
            # Import here to avoid circular dependency
            from pywiggum.agents.claude_code import ClaudeCodeAgent

            agent = ClaudeCodeAgent()
        elif backend == "api":
            # Import here to avoid circular dependency
            from pywiggum.agents.api import APIAgent

            agent = APIAgent(
                model=self.config.agent.model,
                api_base_url=self.config.agent.api_base_url,
                api_key_env=self.config.agent.api_key_env,
            )
        else:
            raise ValueError(f"Unsupported agent backend: {backend}")

        if not agent.check_available():
            raise ValueError(f"Agent backend '{backend}' is not available")

        return agent

    def run(self) -> None:
        """Run the main orchestration loop."""
        logger.info(f"Starting PyWiggum runner for {self.config.project.name}")
        logger.info(f"Agent: {self.agent.name} / Model: {self.config.agent.model}")

        # Load history and kanban
        self.history.load()
        self.kanban.load()

        # Initialize max iterations control
        max_iterations = self.controls.get_max_iterations()
        if max_iterations is None:
            max_iterations = self.config.runner.max_iterations
            self.controls.set_max_iterations(max_iterations)

        # Set baseline if first run
        stats = self.kanban.get_stats()
        if not self.history.baseline_eta and stats["todo"] > 0:
            self.history.set_baseline(stats["todo"])
            logger.info(f"Set baseline ETA for {stats['todo']} remaining tasks")

        # Main loop
        while self.current_iteration < max_iterations:
            self.current_iteration += 1

            # Check for max iterations update
            new_max = self.controls.get_max_iterations()
            if new_max is not None and new_max != max_iterations:
                max_iterations = new_max
                logger.info(f"Max iterations updated to {max_iterations}")

            # Check for pause
            if self.controls.is_paused():
                logger.info("Runner paused, waiting for resume...")
                self.controls.wait_while_paused()
                logger.info("Runner resumed")

            # Find next task
            next_task = self.kanban.find_next_task()
            if next_task is None:
                logger.info("No more tasks available, exiting")
                break

            milestone, task = next_task
            logger.info(
                f"Iteration {self.current_iteration}/{max_iterations}: "
                f"Starting task {task.id} - {task.title}"
            )

            # Track task start
            self.current_task_id = task.id
            self.current_task_start = datetime.now()

            # Check for hint
            hint = self.controls.consume_hint()
            if hint:
                logger.info(f"Received hint: {hint[:100]}...")

            # Build prompt
            prompt = self.prompt_builder.build_task_prompt(task, hint)

            # Execute agent
            result = self.agent.run(
                prompt=prompt,
                work_dir=self.work_dir,
                timeout=self.config.agent.timeout,
            )

            # Log result
            if result.success:
                logger.info(f"Agent completed (exit code {result.exit_code})")
            else:
                logger.warning(f"Agent failed (exit code {result.exit_code})")
                if result.stderr:
                    logger.warning(f"Error: {result.stderr[:200]}")

            # Reload kanban to check if task was updated
            self.kanban.load()
            updated_task = self.kanban.get_task(task.id)

            if updated_task and updated_task.status != "todo":
                # Task was completed
                duration = (datetime.now() - self.current_task_start).total_seconds()

                completion = TaskCompletion(
                    task_id=task.id,
                    task_title=task.title,
                    started_at=self.current_task_start.isoformat(),
                    completed_at=datetime.now().isoformat(),
                    duration_seconds=duration,
                    iterations=1,
                    status=updated_task.status,
                )

                self.history.record_completion(completion)
                logger.info(
                    f"Task {task.id} completed with status '{updated_task.status}' "
                    f"in {duration / 60:.1f} minutes"
                )

                # Reset task tracking
                self.current_task_id = None
                self.current_task_start = None
            else:
                logger.warning(f"Task {task.id} was not updated by agent")

            # Sleep between iterations
            time.sleep(self.config.runner.sleep_between)

        logger.info(f"Runner completed after {self.current_iteration} iterations")

    def get_status(self) -> dict:
        """Get current runner status.

        Returns:
            Status dictionary
        """
        stats = self.kanban.get_stats()
        history_stats = self.history.get_stats()

        status = {
            "running": self.current_task_id is not None,
            "paused": self.controls.is_paused(),
            "iteration": self.current_iteration,
            "max_iterations": self.controls.get_max_iterations(),
            "current_task": self.current_task_id,
            "kanban_stats": stats,
            "history_stats": history_stats,
        }

        # Add current task duration if active
        if self.current_task_start:
            duration = (datetime.now() - self.current_task_start).total_seconds()
            status["current_task_duration_seconds"] = duration

            # Check for stall
            stall_multiplier = self.history.detect_stall(duration)
            if stall_multiplier > 0:
                status["stall_multiplier"] = stall_multiplier

        # Add ETA prediction
        eta = self.history.predict_eta(stats["todo"])
        if eta:
            status["predicted_eta"] = eta.isoformat()

        # Add drift
        drift = self.history.get_drift(stats["todo"])
        if drift:
            status["drift_minutes"] = drift.total_seconds() / 60.0

        return status
