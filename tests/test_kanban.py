"""Tests for kanban management."""

import json
import tempfile
from pathlib import Path

from pywiggum.kanban import KanbanManager, Milestone, Task


def test_create_template():
    """Test creating a template kanban board."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kanban_path = Path(tmpdir) / "kanban.json"
        manager = KanbanManager(kanban_path)

        board = manager.create_template()
        manager.save(board)

        assert kanban_path.exists()

        # Verify structure
        with open(kanban_path, "r") as f:
            data = json.load(f)

        assert "milestones" in data
        assert len(data["milestones"]) > 0


def test_find_next_task():
    """Test finding the next actionable task."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kanban_path = Path(tmpdir) / "kanban.json"
        manager = KanbanManager(kanban_path)

        # Create test board
        board = manager.create_template()
        manager.save(board)
        manager.load()

        # Find next task
        result = manager.find_next_task()
        assert result is not None

        milestone, task = result
        assert task.status == "todo"


def test_update_task_status():
    """Test updating task status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kanban_path = Path(tmpdir) / "kanban.json"
        manager = KanbanManager(kanban_path)

        board = manager.create_template()
        manager.save(board)
        manager.load()

        # Get first task
        result = manager.find_next_task()
        assert result is not None
        _, task = result

        # Update status
        success = manager.update_task_status(task.id, "done")
        assert success

        # Verify update
        updated_task = manager.get_task(task.id)
        assert updated_task is not None
        assert updated_task.status == "done"


def test_get_stats():
    """Test getting kanban statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kanban_path = Path(tmpdir) / "kanban.json"
        manager = KanbanManager(kanban_path)

        board = manager.create_template()
        manager.save(board)
        manager.load()

        stats = manager.get_stats()
        assert "total" in stats
        assert "todo" in stats
        assert "done" in stats
        assert "failed" in stats
        assert stats["total"] > 0


def test_milestone_blocking():
    """Test milestone dependency blocking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kanban_path = Path(tmpdir) / "kanban.json"
        manager = KanbanManager(kanban_path)

        # Create board with dependencies
        board = manager.create_template()
        manager.save(board)
        manager.load()

        # Find next task (should be from M1, not M2)
        result = manager.find_next_task()
        assert result is not None
        milestone, task = result
        assert milestone.id == "M1"

        # Complete all M1 tasks
        for task in milestone.tasks:
            manager.update_task_status(task.id, "done")

        # Now next task should be from M2
        manager.load()
        result = manager.find_next_task()
        assert result is not None
        milestone, task = result
        assert milestone.id == "M2"
