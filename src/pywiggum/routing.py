"""Agent routing and escalation system for PyWiggum.

The Springfield PD hierarchy:
- Ralph (Wiggum): Local models, does the grunt work
- Eddie: Better local model, steps in when Ralph struggles
- Lou: Much better (Claude), handles complex cases
- Chief Matt: Human in the loop, final authority
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentLevel(str, Enum):
    """Agent capability levels, Springfield PD hierarchy."""

    RALPH = "ralph"  # Local model, basic capability
    EDDIE = "eddie"  # Better local model
    LOU = "lou"  # Frontier model (Claude)
    MATT = "matt"  # Human in the loop


class RoutingRule(BaseModel):
    """Rule for routing tasks to specific agents."""

    task_type: str | None = None  # e.g., "code", "planning", "test"
    milestone_id: str | None = None  # e.g., "M1"
    task_id_pattern: str | None = None  # e.g., "M1.*"
    agent_level: AgentLevel = AgentLevel.RALPH
    model: str | None = None  # Override model for this rule


class EscalationConfig(BaseModel):
    """Configuration for automatic escalation."""

    enabled: bool = False
    trigger_after_iterations: int = 3  # Escalate after N failed iterations
    trigger_after_duration: int = 1800  # Escalate after N seconds (30 min default)
    escalation_chain: list[AgentLevel] = Field(
        default_factory=lambda: [
            AgentLevel.RALPH,
            AgentLevel.EDDIE,
            AgentLevel.LOU,
            AgentLevel.MATT,
        ]
    )


class RoutingConfig(BaseModel):
    """Complete routing configuration."""

    # Agent configurations by level
    agents: dict[AgentLevel, dict[str, Any]] = Field(
        default_factory=lambda: {
            AgentLevel.RALPH: {
                "backend": "opencode",
                "model": "vllm/qwen3-coder-next",
                "description": "Local model for basic tasks",
            },
            AgentLevel.EDDIE: {
                "backend": "opencode",
                "model": "vllm/qwen3-32b-instruct",
                "description": "Better local model for moderate complexity",
            },
            AgentLevel.LOU: {
                "backend": "claude_code",
                "model": "claude-sonnet-4-5",
                "description": "Frontier model for complex tasks",
            },
            AgentLevel.MATT: {
                "backend": "human",
                "description": "Human in the loop",
            },
        }
    )

    # Routing rules (first match wins)
    rules: list[RoutingRule] = Field(default_factory=list)

    # Default agent for tasks that don't match any rule
    default_agent: AgentLevel = AgentLevel.RALPH

    # Escalation configuration
    escalation: EscalationConfig = Field(default_factory=EscalationConfig)


class Router:
    """Routes tasks to appropriate agents based on rules and escalation."""

    def __init__(self, config: RoutingConfig):
        """Initialize router.

        Args:
            config: Routing configuration
        """
        self.config = config

    def route_task(
        self,
        task_id: str,
        task_type: str | None = None,
        milestone_id: str | None = None,
        current_level: AgentLevel | None = None,
    ) -> tuple[AgentLevel, dict[str, Any]]:
        """Determine which agent should handle a task.

        Args:
            task_id: Task identifier
            task_type: Optional task type
            milestone_id: Optional milestone identifier
            current_level: Current agent level (for escalation)

        Returns:
            Tuple of (agent_level, agent_config)
        """
        # Check routing rules
        for rule in self.config.rules:
            if self._matches_rule(rule, task_id, task_type, milestone_id):
                level = rule.agent_level
                agent_config = self.config.agents.get(level, {}).copy()
                if rule.model:
                    agent_config["model"] = rule.model
                return (level, agent_config)

        # Use default agent
        level = current_level or self.config.default_agent
        return (level, self.config.agents.get(level, {}))

    def escalate(self, current_level: AgentLevel) -> AgentLevel | None:
        """Get the next escalation level.

        Args:
            current_level: Current agent level

        Returns:
            Next agent level or None if no escalation available
        """
        if not self.config.escalation.enabled:
            return None

        chain = self.config.escalation.escalation_chain
        try:
            current_idx = chain.index(current_level)
            if current_idx + 1 < len(chain):
                return chain[current_idx + 1]
        except (ValueError, IndexError):
            pass

        return None

    def should_escalate(
        self, iterations_on_task: int, duration_seconds: float
    ) -> bool:
        """Determine if task should be escalated.

        Args:
            iterations_on_task: Number of iterations spent on current task
            duration_seconds: Time spent on current task

        Returns:
            True if task should be escalated
        """
        if not self.config.escalation.enabled:
            return False

        if iterations_on_task >= self.config.escalation.trigger_after_iterations:
            return True

        if duration_seconds >= self.config.escalation.trigger_after_duration:
            return True

        return False

    def _matches_rule(
        self,
        rule: RoutingRule,
        task_id: str,
        task_type: str | None,
        milestone_id: str | None,
    ) -> bool:
        """Check if a routing rule matches the task.

        Args:
            rule: Routing rule to check
            task_id: Task identifier
            task_type: Optional task type
            milestone_id: Optional milestone identifier

        Returns:
            True if rule matches
        """
        # Check task type
        if rule.task_type and rule.task_type != task_type:
            return False

        # Check milestone ID
        if rule.milestone_id and rule.milestone_id != milestone_id:
            return False

        # Check task ID pattern
        if rule.task_id_pattern:
            import re

            if not re.match(rule.task_id_pattern, task_id):
                return False

        return True

    def get_agent_description(self, level: AgentLevel) -> str:
        """Get human-readable description of an agent.

        Args:
            level: Agent level

        Returns:
            Description string
        """
        descriptions = {
            AgentLevel.RALPH: "👮 Ralph (Wiggum) - Local model, does the grunt work",
            AgentLevel.EDDIE: "👮‍♂️ Eddie - Better local model, steps in when Ralph struggles",
            AgentLevel.LOU: "👨‍✈️ Lou - Frontier model (Claude), handles complex cases",
            AgentLevel.MATT: "👨‍💼 Chief Matt - Human in the loop, final authority",
        }
        return descriptions.get(level, str(level))
