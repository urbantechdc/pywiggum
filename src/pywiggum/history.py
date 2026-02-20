"""Task completion history and velocity tracking."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class TaskCompletion:
    """Record of a completed task."""

    task_id: str
    task_title: str
    started_at: str  # ISO format timestamp
    completed_at: str  # ISO format timestamp
    duration_seconds: float
    iterations: int
    status: str  # done or failed


class HistoryTracker:
    """Tracks task completion history and calculates velocity metrics."""

    def __init__(self, work_dir: Path):
        """Initialize history tracker.

        Args:
            work_dir: Working directory for history file
        """
        self.work_dir = work_dir
        self.history_file = work_dir / ".wiggum-history.json"
        self.completions: list[TaskCompletion] = []
        self.baseline_eta: datetime | None = None
        self.baseline_remaining: int = 0

    def load(self) -> None:
        """Load history from file."""
        if not self.history_file.exists():
            self.completions = []
            return

        try:
            with open(self.history_file, "r") as f:
                data = json.load(f)

            self.completions = [
                TaskCompletion(**item) for item in data.get("completions", [])
            ]

            # Load baseline if present
            baseline = data.get("baseline")
            if baseline:
                self.baseline_eta = (
                    datetime.fromisoformat(baseline["eta"]) if baseline.get("eta") else None
                )
                self.baseline_remaining = baseline.get("remaining", 0)

        except (json.JSONDecodeError, KeyError, ValueError):
            self.completions = []

    def save(self) -> None:
        """Save history to file."""
        data = {
            "completions": [
                {
                    "task_id": c.task_id,
                    "task_title": c.task_title,
                    "started_at": c.started_at,
                    "completed_at": c.completed_at,
                    "duration_seconds": c.duration_seconds,
                    "iterations": c.iterations,
                    "status": c.status,
                }
                for c in self.completions
            ],
            "baseline": {
                "eta": self.baseline_eta.isoformat() if self.baseline_eta else None,
                "remaining": self.baseline_remaining,
            }
            if self.baseline_eta
            else None,
        }

        with open(self.history_file, "w") as f:
            json.dump(data, f, indent=2)

    def record_completion(self, completion: TaskCompletion) -> None:
        """Record a task completion.

        Args:
            completion: The completion record
        """
        self.completions.append(completion)
        self.save()

    def get_average_duration(self) -> float:
        """Get average task duration in minutes.

        Returns:
            Average duration in minutes, or 0 if no completions
        """
        if not self.completions:
            return 0.0

        successful = [c for c in self.completions if c.status == "done"]
        if not successful:
            return 0.0

        total_seconds = sum(c.duration_seconds for c in successful)
        return total_seconds / len(successful) / 60.0

    def get_recent_velocity(self, n: int = 3) -> float:
        """Get recent velocity (rolling average).

        Args:
            n: Number of recent tasks to include

        Returns:
            Average duration in minutes for last n tasks, or 0 if insufficient data
        """
        successful = [c for c in self.completions if c.status == "done"]
        if not successful:
            return 0.0

        recent = successful[-n:]
        if not recent:
            return 0.0

        total_seconds = sum(c.duration_seconds for c in recent)
        return total_seconds / len(recent) / 60.0

    def predict_eta(self, remaining_tasks: int) -> datetime | None:
        """Predict ETA for completing remaining tasks.

        Args:
            remaining_tasks: Number of tasks remaining

        Returns:
            Predicted completion datetime, or None if insufficient data
        """
        if remaining_tasks == 0:
            return datetime.now()

        avg_duration = self.get_average_duration()
        if avg_duration == 0:
            return None

        estimated_minutes = avg_duration * remaining_tasks
        return datetime.now() + timedelta(minutes=estimated_minutes)

    def set_baseline(self, remaining_tasks: int) -> None:
        """Set the baseline ETA for drift tracking.

        Args:
            remaining_tasks: Number of tasks remaining when baseline is set
        """
        eta = self.predict_eta(remaining_tasks)
        if eta:
            self.baseline_eta = eta
            self.baseline_remaining = remaining_tasks
            self.save()

    def get_drift(self, remaining_tasks: int) -> timedelta | None:
        """Calculate drift from baseline ETA.

        Args:
            remaining_tasks: Current number of tasks remaining

        Returns:
            Time delta (positive = behind schedule, negative = ahead), or None if no baseline
        """
        if not self.baseline_eta:
            return None

        current_eta = self.predict_eta(remaining_tasks)
        if not current_eta:
            return None

        return current_eta - self.baseline_eta

    def detect_stall(self, current_task_duration: float) -> float:
        """Detect if current task is stalled.

        Args:
            current_task_duration: Duration of current task in seconds

        Returns:
            Multiplier of average (e.g., 2.5 means current task is 2.5x average)
        """
        avg_seconds = self.get_average_duration() * 60.0
        if avg_seconds == 0:
            return 0.0

        return current_task_duration / avg_seconds

    def get_stats(self) -> dict[str, float | int]:
        """Get summary statistics.

        Returns:
            Dictionary of statistics
        """
        successful = [c for c in self.completions if c.status == "done"]
        failed = [c for c in self.completions if c.status == "failed"]

        return {
            "total_completions": len(self.completions),
            "successful": len(successful),
            "failed": len(failed),
            "avg_duration_minutes": self.get_average_duration(),
            "recent_velocity_minutes": self.get_recent_velocity(),
        }
