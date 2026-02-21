"""File-based IPC controls for PyWiggum runner."""

import json
import os
import time
from datetime import datetime
from pathlib import Path


class Controls:
    """File-based controls for runner orchestration."""

    def __init__(self, work_dir: Path):
        """Initialize controls.

        Args:
            work_dir: Working directory for control files
        """
        self.work_dir = work_dir
        self.pause_file = work_dir / ".wiggum-pause"
        self.max_file = work_dir / ".wiggum-max"
        self.hint_file = work_dir / ".wiggum-hint"
        self.hints_archive_dir = work_dir / ".wiggum-hints-archive"
        self.state_file = work_dir / ".wiggum-state.json"

        # Ensure hints archive directory exists
        self.hints_archive_dir.mkdir(exist_ok=True)

    def is_paused(self) -> bool:
        """Check if runner is paused.

        Returns:
            True if pause file exists
        """
        return self.pause_file.exists()

    def pause(self) -> None:
        """Pause the runner by creating pause file."""
        self.pause_file.touch()

    def resume(self) -> None:
        """Resume the runner by removing pause file."""
        if self.pause_file.exists():
            self.pause_file.unlink()

    def get_max_iterations(self) -> int | None:
        """Get max iterations from control file.

        Returns:
            Max iterations if file exists and is valid, None otherwise
        """
        if not self.max_file.exists():
            return None

        try:
            content = self.max_file.read_text().strip()
            return int(content)
        except (ValueError, OSError):
            return None

    def set_max_iterations(self, max_iterations: int) -> None:
        """Set max iterations in control file.

        Args:
            max_iterations: New max iterations value
        """
        self.max_file.write_text(str(max_iterations))

    def add_iterations(self, additional: int) -> int:
        """Add iterations to the current max.

        Args:
            additional: Number of iterations to add

        Returns:
            New max iterations value
        """
        current = self.get_max_iterations()
        if current is None:
            current = 0

        new_max = current + additional
        self.set_max_iterations(new_max)
        return new_max

    def get_hint(self) -> str | None:
        """Get the current hint if one exists.

        Returns:
            Hint text or None if no hint file exists
        """
        if not self.hint_file.exists():
            return None

        try:
            return self.hint_file.read_text().strip()
        except OSError:
            return None

    def set_hint(self, hint: str) -> None:
        """Set a hint for the next iteration.

        Args:
            hint: Hint text
        """
        self.hint_file.write_text(hint)

    def consume_hint(self) -> str | None:
        """Consume the hint file (read and archive it).

        Returns:
            Hint text or None if no hint exists
        """
        hint = self.get_hint()
        if hint is None:
            return None

        # Archive the hint
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = self.hints_archive_dir / f"hint-{timestamp}.txt"
        archive_path.write_text(hint)

        # Remove the hint file
        self.hint_file.unlink()

        return hint

    def wait_while_paused(self, check_interval: int = 2) -> None:
        """Wait in a loop while paused.

        Args:
            check_interval: Seconds between pause checks
        """
        while self.is_paused():
            time.sleep(check_interval)

    def write_state(self, iteration: int, task_id: str | None = None) -> None:
        """Write runner state (PID, iteration, heartbeat).

        Args:
            iteration: Current iteration number
            task_id: Current task ID if active
        """
        state = {
            "pid": os.getpid(),
            "iteration": iteration,
            "task_id": task_id,
            "updated_at": datetime.now().isoformat(),
        }
        self.state_file.write_text(json.dumps(state))

    def clear_state(self) -> None:
        """Remove state file on clean shutdown."""
        if self.state_file.exists():
            self.state_file.unlink()

    def read_state(self) -> dict | None:
        """Read runner state file.

        Returns:
            State dict or None if file doesn't exist
        """
        if not self.state_file.exists():
            return None
        try:
            return json.loads(self.state_file.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def is_runner_alive(self) -> bool:
        """Check if the runner process is still alive.

        Returns:
            True if runner PID exists and process is running
        """
        state = self.read_state()
        if state is None:
            return False
        pid = state.get("pid")
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False
