"""Tests for control file management."""

import tempfile
from pathlib import Path

from pywiggum.controls import Controls


def test_pause_resume():
    """Test pause and resume functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        controls = Controls(Path(tmpdir))

        assert not controls.is_paused()

        controls.pause()
        assert controls.is_paused()

        controls.resume()
        assert not controls.is_paused()


def test_max_iterations():
    """Test max iterations control."""
    with tempfile.TemporaryDirectory() as tmpdir:
        controls = Controls(Path(tmpdir))

        assert controls.get_max_iterations() is None

        controls.set_max_iterations(50)
        assert controls.get_max_iterations() == 50

        new_max = controls.add_iterations(25)
        assert new_max == 75
        assert controls.get_max_iterations() == 75


def test_hints():
    """Test hint management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        controls = Controls(Path(tmpdir))

        assert controls.get_hint() is None

        controls.set_hint("Test hint")
        assert controls.get_hint() == "Test hint"

        hint = controls.consume_hint()
        assert hint == "Test hint"
        assert controls.get_hint() is None

        # Check that hint was archived
        archive_dir = Path(tmpdir) / ".wiggum-hints-archive"
        assert archive_dir.exists()
        archived_files = list(archive_dir.glob("hint-*.txt"))
        assert len(archived_files) == 1
