"""Tests for history tracking."""

import tempfile
from datetime import datetime
from pathlib import Path

from pywiggum.history import HistoryTracker, TaskCompletion


def test_record_completion():
    """Test recording task completions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = HistoryTracker(Path(tmpdir))

        completion = TaskCompletion(
            task_id="M1.1",
            task_title="Test task",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            duration_seconds=120.0,
            iterations=1,
            status="done",
        )

        tracker.record_completion(completion)
        assert len(tracker.completions) == 1


def test_velocity_calculation():
    """Test velocity calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = HistoryTracker(Path(tmpdir))

        # Add multiple completions
        for i in range(5):
            completion = TaskCompletion(
                task_id=f"M1.{i}",
                task_title=f"Task {i}",
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                duration_seconds=180.0,  # 3 minutes
                iterations=1,
                status="done",
            )
            tracker.record_completion(completion)

        avg_duration = tracker.get_average_duration()
        assert avg_duration == 3.0  # 3 minutes


def test_eta_prediction():
    """Test ETA prediction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = HistoryTracker(Path(tmpdir))

        # Add completions
        completion = TaskCompletion(
            task_id="M1.1",
            task_title="Test",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            duration_seconds=600.0,  # 10 minutes
            iterations=1,
            status="done",
        )
        tracker.record_completion(completion)

        eta = tracker.predict_eta(5)  # 5 tasks remaining
        assert eta is not None


def test_baseline_and_drift():
    """Test baseline and drift tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = HistoryTracker(Path(tmpdir))

        # Add completions
        completion = TaskCompletion(
            task_id="M1.1",
            task_title="Test",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            duration_seconds=300.0,
            iterations=1,
            status="done",
        )
        tracker.record_completion(completion)

        # Set baseline
        tracker.set_baseline(10)
        assert tracker.baseline_eta is not None

        # Check drift (should be minimal immediately)
        drift = tracker.get_drift(10)
        assert drift is not None


def test_stall_detection():
    """Test stall detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = HistoryTracker(Path(tmpdir))

        # Add completions with 5 minute average
        for i in range(3):
            completion = TaskCompletion(
                task_id=f"M1.{i}",
                task_title=f"Task {i}",
                started_at=datetime.now().isoformat(),
                completed_at=datetime.now().isoformat(),
                duration_seconds=300.0,
                iterations=1,
                status="done",
            )
            tracker.record_completion(completion)

        # Check if 10 minute task is stalled
        multiplier = tracker.detect_stall(600.0)
        assert multiplier == 2.0  # 2x average
