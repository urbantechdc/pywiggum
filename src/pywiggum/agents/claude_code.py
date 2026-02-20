"""Claude Code CLI agent backend."""

import shutil
import subprocess
from pathlib import Path

from pywiggum.agents.base import AgentResult, BaseAgent


class ClaudeCodeAgent(BaseAgent):
    """Agent backend using Claude Code CLI."""

    @property
    def name(self) -> str:
        """Get the agent backend name."""
        return "claude_code"

    def check_available(self) -> bool:
        """Check if Claude Code CLI is available."""
        return shutil.which("claude") is not None

    def run(self, prompt: str, work_dir: Path, timeout: int) -> AgentResult:
        """Execute a single iteration using Claude Code.

        Args:
            prompt: The prompt to execute
            work_dir: Working directory for the agent
            timeout: Timeout in seconds

        Returns:
            Agent execution result
        """
        cmd = ["claude", "-p", prompt]

        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
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
                stderr=f"Claude Code timed out after {timeout} seconds",
                success=False,
            )
        except Exception as e:
            return AgentResult(
                exit_code=-1,
                stdout="",
                stderr=f"Claude Code execution failed: {e}",
                success=False,
            )
