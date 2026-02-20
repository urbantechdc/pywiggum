"""Base agent interface for PyWiggum backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentResult:
    """Result from an agent execution."""

    exit_code: int
    stdout: str
    stderr: str
    success: bool

    @property
    def output(self) -> str:
        """Combined stdout and stderr."""
        return f"{self.stdout}\n{self.stderr}".strip()


class BaseAgent(ABC):
    """Abstract base class for agent backends."""

    @abstractmethod
    def run(self, prompt: str, work_dir: Path, timeout: int) -> AgentResult:
        """Execute a single iteration.

        Args:
            prompt: The prompt to execute
            work_dir: Working directory for the agent
            timeout: Timeout in seconds

        Returns:
            Agent execution result
        """
        pass

    @abstractmethod
    def check_available(self) -> bool:
        """Check if the agent backend is installed and reachable.

        Returns:
            True if the backend is available
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent backend name.

        Returns:
            Backend name
        """
        pass
