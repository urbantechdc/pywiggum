"""Direct API agent backend for OpenAI-compatible endpoints."""

import json
import os
from pathlib import Path

from pywiggum.agents.base import AgentResult, BaseAgent


class APIAgent(BaseAgent):
    """Agent backend using direct API calls to OpenAI-compatible endpoints."""

    def __init__(
        self, model: str, api_base_url: str | None = None, api_key_env: str | None = None
    ):
        """Initialize API agent.

        Args:
            model: Model identifier
            api_base_url: Base URL for API endpoint (e.g., http://localhost:8000/v1)
            api_key_env: Environment variable name for API key
        """
        self.model = model
        self.api_base_url = api_base_url or "http://localhost:8000/v1"
        self.api_key_env = api_key_env or "OPENAI_API_KEY"

    @property
    def name(self) -> str:
        """Get the agent backend name."""
        return "api"

    def check_available(self) -> bool:
        """Check if API endpoint is available."""
        try:
            import requests

            # Try to reach the endpoint
            response = requests.get(f"{self.api_base_url}/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def run(self, prompt: str, work_dir: Path, timeout: int) -> AgentResult:
        """Execute a single iteration using API.

        Args:
            prompt: The prompt to execute
            work_dir: Working directory for context
            timeout: Timeout in seconds

        Returns:
            Agent execution result
        """
        try:
            import requests
        except ImportError:
            return AgentResult(
                exit_code=-1,
                stdout="",
                stderr="requests library not installed. Install with: pip install requests",
                success=False,
            )

        # Get API key from environment
        api_key = os.environ.get(self.api_key_env, "")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            if response.status_code != 200:
                return AgentResult(
                    exit_code=response.status_code,
                    stdout="",
                    stderr=f"API request failed: {response.status_code} - {response.text}",
                    success=False,
                )

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return AgentResult(
                exit_code=0,
                stdout=content,
                stderr="",
                success=True,
            )

        except requests.exceptions.Timeout:
            return AgentResult(
                exit_code=-1,
                stdout="",
                stderr=f"API request timed out after {timeout} seconds",
                success=False,
            )
        except Exception as e:
            return AgentResult(
                exit_code=-1,
                stdout="",
                stderr=f"API request failed: {e}",
                success=False,
            )
