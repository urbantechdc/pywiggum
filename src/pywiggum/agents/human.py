"""Human-in-the-loop agent backend (Chief Matt)."""

import sys
from pathlib import Path

from pywiggum.agents.base import AgentResult, BaseAgent


class HumanAgent(BaseAgent):
    """Agent backend that prompts a human for input (Chief Matt)."""

    @property
    def name(self) -> str:
        """Get the agent backend name."""
        return "human"

    def check_available(self) -> bool:
        """Check if human is available (always true if stdin exists)."""
        return sys.stdin.isatty()

    def run(self, prompt: str, work_dir: Path, timeout: int) -> AgentResult:
        """Execute a single iteration with human input.

        Args:
            prompt: The prompt to show to the human
            work_dir: Working directory for context
            timeout: Timeout in seconds (ignored for human)

        Returns:
            Agent execution result
        """
        print("\n" + "=" * 80)
        print("🚔 CHIEF MATT (HUMAN) - YOU'RE UP!")
        print("=" * 80)
        print("\nThe AI agents need your help. Here's the situation:\n")
        print(prompt)
        print("\n" + "=" * 80)
        print("Working directory:", work_dir)
        print("=" * 80)

        print("\nWhat would you like to do?")
        print("1. Complete the task yourself (type 'done' when finished)")
        print("2. Provide guidance to the AI (type 'hint: <your hint>')")
        print("3. Mark task as failed (type 'failed: <reason>')")
        print("4. Delegate back to AI (type 'delegate')")

        response = input("\nYour response: ").strip()

        if response.lower() == "done":
            print("\nGreat! Make sure you've:")
            print("- Completed the task")
            print("- Updated kanban.json (status to 'done')")
            print("- Committed your changes")
            input("\nPress Enter when ready to continue...")

            return AgentResult(
                exit_code=0,
                stdout="Human (Chief Matt) completed the task",
                stderr="",
                success=True,
            )

        elif response.lower().startswith("hint:"):
            hint = response[5:].strip()
            print(f"\nHint recorded: {hint}")
            print("Task will be delegated back to AI with your hint.")

            return AgentResult(
                exit_code=1,
                stdout="",
                stderr=f"Human provided hint: {hint}",
                success=False,
            )

        elif response.lower().startswith("failed:"):
            reason = response[7:].strip()
            print(f"\nTask marked as failed: {reason}")

            return AgentResult(
                exit_code=2,
                stdout="",
                stderr=f"Human marked task as failed: {reason}",
                success=False,
            )

        elif response.lower() == "delegate":
            print("\nDelegating back to AI...")

            return AgentResult(
                exit_code=1,
                stdout="",
                stderr="Human delegated task back to AI",
                success=False,
            )

        else:
            print("\nInvalid response. Task remains in progress.")

            return AgentResult(
                exit_code=1,
                stdout="",
                stderr=f"Human provided unclear response: {response}",
                success=False,
            )
