"""Kanban board management for PyWiggum."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["todo", "done", "failed"]


class Task(BaseModel):
    """A single task in the kanban board."""

    id: str
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    status: TaskStatus = "todo"
    note: str | None = None  # For failure reasons or general notes
    type: str | None = None  # For future model routing


class Milestone(BaseModel):
    """A milestone containing multiple tasks."""

    id: str
    name: str
    blocked_by: list[str] = Field(default_factory=list)  # IDs of other milestones
    tasks: list[Task] = Field(default_factory=list)


class KanbanBoard(BaseModel):
    """The complete kanban board."""

    milestones: list[Milestone] = Field(default_factory=list)


class KanbanManager:
    """Manages kanban board operations."""

    def __init__(self, kanban_path: Path):
        """Initialize kanban manager.

        Args:
            kanban_path: Path to the kanban.json file
        """
        self.kanban_path = kanban_path
        self.board: KanbanBoard | None = None

    def load(self) -> KanbanBoard:
        """Load kanban board from file.

        Returns:
            The loaded kanban board

        Raises:
            FileNotFoundError: If kanban file doesn't exist
            ValueError: If kanban file is invalid
        """
        if not self.kanban_path.exists():
            raise FileNotFoundError(f"Kanban file not found: {self.kanban_path}")

        with open(self.kanban_path, "r") as f:
            data = json.load(f)

        try:
            self.board = KanbanBoard(**data)
            return self.board
        except Exception as e:
            raise ValueError(f"Invalid kanban file: {e}")

    def save(self, board: KanbanBoard | None = None) -> None:
        """Save kanban board to file.

        Args:
            board: Board to save. If None, uses self.board
        """
        if board is None:
            board = self.board

        if board is None:
            raise ValueError("No board to save")

        with open(self.kanban_path, "w") as f:
            json.dump(board.model_dump(), f, indent=2)

    def find_next_task(self) -> tuple[Milestone, Task] | None:
        """Find the next actionable task.

        Returns the first 'todo' task in the first unblocked milestone.

        Returns:
            Tuple of (milestone, task) or None if no tasks available
        """
        if self.board is None:
            self.load()

        assert self.board is not None

        # Build set of completed milestone IDs
        completed_milestone_ids = {
            m.id for m in self.board.milestones if self._is_milestone_done(m)
        }

        for milestone in self.board.milestones:
            # Check if milestone is blocked
            if any(blocker not in completed_milestone_ids for blocker in milestone.blocked_by):
                continue

            # Find first todo task in this milestone
            for task in milestone.tasks:
                if task.status == "todo":
                    return (milestone, task)

        return None

    def update_task_status(
        self, task_id: str, status: TaskStatus, note: str | None = None
    ) -> bool:
        """Update a task's status.

        Args:
            task_id: ID of the task to update
            status: New status
            note: Optional note (typically for failure reasons)

        Returns:
            True if task was found and updated, False otherwise
        """
        if self.board is None:
            self.load()

        assert self.board is not None

        for milestone in self.board.milestones:
            for task in milestone.tasks:
                if task.id == task_id:
                    task.status = status
                    if note is not None:
                        task.note = note
                    self.save()
                    return True

        return False

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: ID of the task

        Returns:
            The task or None if not found
        """
        if self.board is None:
            self.load()

        assert self.board is not None

        for milestone in self.board.milestones:
            for task in milestone.tasks:
                if task.id == task_id:
                    return task

        return None

    def get_stats(self) -> dict[str, int]:
        """Get kanban statistics.

        Returns:
            Dictionary with counts of todo, done, failed, and total tasks
        """
        if self.board is None:
            self.load()

        assert self.board is not None

        stats = {"todo": 0, "done": 0, "failed": 0, "total": 0}

        for milestone in self.board.milestones:
            for task in milestone.tasks:
                stats["total"] += 1
                if task.status == "todo":
                    stats["todo"] += 1
                elif task.status == "done":
                    stats["done"] += 1
                elif task.status == "failed":
                    stats["failed"] += 1

        return stats

    def get_milestone_stats(self, milestone_id: str) -> dict[str, int]:
        """Get statistics for a specific milestone.

        Args:
            milestone_id: ID of the milestone

        Returns:
            Dictionary with counts of todo, done, failed, and total tasks
        """
        if self.board is None:
            self.load()

        assert self.board is not None

        stats = {"todo": 0, "done": 0, "failed": 0, "total": 0}

        for milestone in self.board.milestones:
            if milestone.id == milestone_id:
                for task in milestone.tasks:
                    stats["total"] += 1
                    if task.status == "todo":
                        stats["todo"] += 1
                    elif task.status == "done":
                        stats["done"] += 1
                    elif task.status == "failed":
                        stats["failed"] += 1
                break

        return stats

    def _is_milestone_done(self, milestone: Milestone) -> bool:
        """Check if a milestone is complete.

        Args:
            milestone: The milestone to check

        Returns:
            True if all tasks are done, False otherwise
        """
        if not milestone.tasks:
            return True

        return all(task.status == "done" for task in milestone.tasks)

    def create_template(self) -> KanbanBoard:
        """Create a template kanban board.

        Returns:
            A template board with example milestones and tasks
        """
        board = KanbanBoard(
            milestones=[
                Milestone(
                    id="M1",
                    name="Project Setup",
                    blocked_by=[],
                    tasks=[
                        Task(
                            id="M1.1",
                            title="Initialize project structure",
                            description="Create basic project files and folders",
                            acceptance_criteria=[
                                "Project directory exists",
                                "Basic files created",
                            ],
                        ),
                        Task(
                            id="M1.2",
                            title="Set up development environment",
                            description="Install dependencies and configure tools",
                            acceptance_criteria=[
                                "Dependencies installed",
                                "Development server runs",
                            ],
                        ),
                    ],
                ),
                Milestone(
                    id="M2",
                    name="Core Implementation",
                    blocked_by=["M1"],
                    tasks=[
                        Task(
                            id="M2.1",
                            title="Implement core feature",
                            description="Build the main functionality",
                            acceptance_criteria=["Feature works as expected", "Tests pass"],
                        ),
                    ],
                ),
            ]
        )
        return board
