"""Prompt builder for PyWiggum agents."""

from pathlib import Path

from pywiggum.config import WiggumConfig
from pywiggum.kanban import Task


class PromptBuilder:
    """Builds prompts for agent execution."""

    def __init__(self, config: WiggumConfig):
        """Initialize prompt builder.

        Args:
            config: PyWiggum configuration
        """
        self.config = config

    def build_task_prompt(self, task: Task, hint: str | None = None) -> str:
        """Build a prompt for executing a task.

        Args:
            task: The task to execute
            hint: Optional hint from human operator

        Returns:
            Complete prompt string
        """
        project_name = self.config.project.name
        kanban_path = Path(self.config.project.kanban).name
        tech_stack = self.config.prompt.tech_stack
        conventions = self.config.prompt.conventions
        extra_context = self.config.prompt.extra_context
        commit_format = self.config.runner.commit_format

        # Build the base prompt
        prompt_parts = [
            f"You are an autonomous coding agent working on {project_name}.",
            "",
            "## INSTRUCTIONS",
            f"1. Read {kanban_path} in the project root.",
            "2. Find the first task with status 'todo' whose milestone is not blocked.",
            "3. Implement the task. Write code, create files, install packages as needed.",
            "4. Verify your work against the acceptance criteria.",
            f"5. CRITICAL: Update {kanban_path}: set the task's status to 'done' (or 'failed' with a note). "
            f"This step is MANDATORY — if you skip it, the task will be re-run. "
            f"Edit the JSON file directly to change \"status\": \"todo\" to \"status\": \"done\".",
        ]

        # Add git commit instruction if enabled
        if self.config.runner.commit_after_task:
            commit_msg = commit_format.format(task_id=task.id, task_title=task.title)
            prompt_parts.append(f"6. Git commit with message: '{commit_msg}'")
            prompt_parts.append("7. EXIT. One task per iteration.")
        else:
            prompt_parts.append("6. EXIT. One task per iteration.")

        # Add tech stack if provided
        if tech_stack.strip():
            prompt_parts.extend(
                [
                    "",
                    "## TECH STACK",
                    tech_stack.strip(),
                ]
            )

        # Add conventions if provided
        if conventions.strip():
            prompt_parts.extend(
                [
                    "",
                    "## CONVENTIONS",
                    conventions.strip(),
                ]
            )

        # Add extra context if provided
        if extra_context.strip():
            prompt_parts.extend(
                [
                    "",
                    extra_context.strip(),
                ]
            )

        # Add hint if provided
        if hint and hint.strip():
            prompt_parts.extend(
                [
                    "",
                    "## HUMAN HINT (read this carefully, it's from the project lead)",
                    hint.strip(),
                ]
            )

        return "\n".join(prompt_parts)
