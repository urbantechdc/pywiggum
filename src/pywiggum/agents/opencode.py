"""OpenCode CLI agent backend."""

import shutil
import subprocess
from pathlib import Path

from pywiggum.agents.base import AgentResult, BaseAgent


class OpenCodeAgent(BaseAgent):
    """Agent backend using OpenCode CLI."""

    def __init__(self, model: str):
        """Initialize OpenCode agent.

        Args:
            model: Model identifier for OpenCode (e.g., "vllm/qwen3-coder-next")
        """
        self.model = model

    @property
    def name(self) -> str:
        """Get the agent backend name."""
        return "opencode"

    def check_available(self) -> bool:
        """Check if OpenCode CLI is available."""
        return shutil.which("opencode") is not None

    def run(self, prompt: str, work_dir: Path, timeout: int) -> AgentResult:
        """Execute a single iteration using OpenCode.

        Args:
            prompt: The prompt to execute
            work_dir: Working directory for the agent
            timeout: Timeout in seconds

        Returns:
            Agent execution result
        """
        cmd = ["opencode", "run", "-m", self.model, prompt]

        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
            )

            return AgentResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                success=result.returncode == 0,
            )

        except subprocess.TimeoutExpired:
            return AgentResult(
                exit_code=-1,
                stdout="",
                stderr=f"OpenCode timed out after {timeout} seconds",
                success=False,
            )
        except Exception as e:
            return AgentResult(
                exit_code=-1,
                stdout="",
                stderr=f"OpenCode execution failed: {e}",
                success=False,
            )
