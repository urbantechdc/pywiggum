"""Tests for configuration management."""

from pathlib import Path
import tempfile

from pywiggum.config import WiggumConfig


def test_default_config():
    """Test default configuration values."""
    config = WiggumConfig()

    assert config.project.name == "PyWiggum Project"
    assert config.project.kanban == "kanban.json"
    assert config.agent.backend == "opencode"
    assert config.runner.max_iterations == 50


def test_save_and_load():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "wiggum.yaml"

        # Create and save config
        config1 = WiggumConfig()
        config1.project.name = "Test Project"
        config1.save(config_path)

        # Load and verify
        config2 = WiggumConfig.load(config_path)
        assert config2.project.name == "Test Project"


def test_merge_overrides():
    """Test merging overrides."""
    config = WiggumConfig()
    new_config = config.merge_overrides(max_iterations=100, agent="claude_code")

    assert new_config.runner.max_iterations == 100
    assert new_config.agent.backend == "claude_code"
    # Original should be unchanged
    assert config.runner.max_iterations == 50
