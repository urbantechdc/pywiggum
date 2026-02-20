"""Configuration management for PyWiggum."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project metadata configuration."""

    name: str = "PyWiggum Project"
    kanban: str = "kanban.json"
    work_dir: str = "."


class AgentConfig(BaseModel):
    """Agent backend configuration."""

    backend: str = "opencode"  # opencode | claude_code | api
    model: str = "vllm/qwen3-coder-next"
    timeout: int = 600  # seconds per iteration
    api_base_url: str | None = None  # for API backend
    api_key_env: str | None = None  # environment variable name for API key


class RunnerConfig(BaseModel):
    """Runner loop configuration."""

    max_iterations: int = 50
    sleep_between: int = 3  # seconds between iterations
    commit_after_task: bool = True
    commit_format: str = "{task_id}: {task_title}"


class DashboardConfig(BaseModel):
    """Dashboard server configuration."""

    port: int = 3333
    host: str = "0.0.0.0"
    refresh_interval: int = 15  # seconds


class PromptConfig(BaseModel):
    """Prompt customization configuration."""

    tech_stack: str = ""
    conventions: str = ""
    extra_context: str = ""


class WiggumConfig(BaseModel):
    """Root configuration model."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    runner: RunnerConfig = Field(default_factory=RunnerConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    prompt: PromptConfig = Field(default_factory=PromptConfig)

    @classmethod
    def load(cls, config_path: Path) -> "WiggumConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        if data is None:
            return cls()

        return cls(**data)

    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        data = self.model_dump()
        with open(config_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def get_work_dir(self) -> Path:
        """Get the project working directory as an absolute path."""
        return Path(self.project.work_dir).resolve()

    def get_kanban_path(self) -> Path:
        """Get the kanban file path as an absolute path."""
        work_dir = self.get_work_dir()
        return (work_dir / self.project.kanban).resolve()

    def merge_overrides(self, **overrides: Any) -> "WiggumConfig":
        """Create a new config with overrides applied."""
        data = self.model_dump()

        # Support nested overrides like max_iterations, agent, model, etc.
        if "max_iterations" in overrides:
            data["runner"]["max_iterations"] = overrides["max_iterations"]
        if "agent" in overrides:
            data["agent"]["backend"] = overrides["agent"]
        if "model" in overrides:
            data["agent"]["model"] = overrides["model"]
        if "port" in overrides:
            data["dashboard"]["port"] = overrides["port"]
        if "host" in overrides:
            data["dashboard"]["host"] = overrides["host"]

        return WiggumConfig(**data)
