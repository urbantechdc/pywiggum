"""Tests for routing and escalation."""

from pywiggum.routing import AgentLevel, EscalationConfig, Router, RoutingConfig, RoutingRule


def test_default_routing():
    """Test default routing configuration."""
    config = RoutingConfig()
    router = Router(config)

    # Should route to default (ralph)
    level, agent_config = router.route_task("M1.1")
    assert level == AgentLevel.RALPH
    assert agent_config["backend"] == "opencode"


def test_routing_by_task_type():
    """Test routing by task type."""
    config = RoutingConfig(
        rules=[
            RoutingRule(task_type="planning", agent_level=AgentLevel.LOU),
            RoutingRule(task_type="test", agent_level=AgentLevel.RALPH),
        ]
    )
    router = Router(config)

    # Planning tasks go to Lou
    level, _ = router.route_task("M1.1", task_type="planning")
    assert level == AgentLevel.LOU

    # Test tasks go to Ralph
    level, _ = router.route_task("M1.2", task_type="test")
    assert level == AgentLevel.RALPH

    # Other tasks use default
    level, _ = router.route_task("M1.3", task_type="code")
    assert level == AgentLevel.RALPH


def test_routing_by_milestone():
    """Test routing by milestone ID."""
    config = RoutingConfig(
        rules=[RoutingRule(milestone_id="M3", agent_level=AgentLevel.EDDIE)]
    )
    router = Router(config)

    # M3 tasks go to Eddie
    level, _ = router.route_task("M3.1", milestone_id="M3")
    assert level == AgentLevel.EDDIE

    # Other milestones use default
    level, _ = router.route_task("M1.1", milestone_id="M1")
    assert level == AgentLevel.RALPH


def test_routing_by_task_pattern():
    """Test routing by task ID pattern."""
    config = RoutingConfig(
        rules=[RoutingRule(task_id_pattern=r"M2\..*", agent_level=AgentLevel.EDDIE)]
    )
    router = Router(config)

    # M2.* tasks go to Eddie
    level, _ = router.route_task("M2.1")
    assert level == AgentLevel.EDDIE

    level, _ = router.route_task("M2.999")
    assert level == AgentLevel.EDDIE

    # Other tasks use default
    level, _ = router.route_task("M1.1")
    assert level == AgentLevel.RALPH


def test_escalation_disabled():
    """Test that escalation doesn't happen when disabled."""
    config = RoutingConfig(
        escalation=EscalationConfig(enabled=False, trigger_after_iterations=1)
    )
    router = Router(config)

    # Should not escalate even though conditions are met
    assert not router.should_escalate(iterations_on_task=5, duration_seconds=3600)


def test_escalation_by_iterations():
    """Test escalation triggered by iteration count."""
    config = RoutingConfig(
        escalation=EscalationConfig(enabled=True, trigger_after_iterations=3)
    )
    router = Router(config)

    # Should not escalate yet
    assert not router.should_escalate(iterations_on_task=2, duration_seconds=0)

    # Should escalate after 3 iterations
    assert router.should_escalate(iterations_on_task=3, duration_seconds=0)


def test_escalation_by_duration():
    """Test escalation triggered by duration."""
    config = RoutingConfig(
        escalation=EscalationConfig(
            enabled=True, trigger_after_iterations=999, trigger_after_duration=1800
        )
    )
    router = Router(config)

    # Should not escalate yet
    assert not router.should_escalate(iterations_on_task=1, duration_seconds=1000)

    # Should escalate after 1800 seconds (30 minutes)
    assert router.should_escalate(iterations_on_task=1, duration_seconds=1800)


def test_escalation_chain():
    """Test escalation through the chain."""
    config = RoutingConfig(
        escalation=EscalationConfig(
            enabled=True,
            escalation_chain=[
                AgentLevel.RALPH,
                AgentLevel.EDDIE,
                AgentLevel.LOU,
                AgentLevel.MATT,
            ],
        )
    )
    router = Router(config)

    # Ralph → Eddie
    next_level = router.escalate(AgentLevel.RALPH)
    assert next_level == AgentLevel.EDDIE

    # Eddie → Lou
    next_level = router.escalate(AgentLevel.EDDIE)
    assert next_level == AgentLevel.LOU

    # Lou → Matt
    next_level = router.escalate(AgentLevel.LOU)
    assert next_level == AgentLevel.MATT

    # Matt → None (end of chain)
    next_level = router.escalate(AgentLevel.MATT)
    assert next_level is None


def test_agent_descriptions():
    """Test getting agent descriptions."""
    config = RoutingConfig()
    router = Router(config)

    desc = router.get_agent_description(AgentLevel.RALPH)
    assert "Ralph" in desc
    assert "Wiggum" in desc

    desc = router.get_agent_description(AgentLevel.EDDIE)
    assert "Eddie" in desc

    desc = router.get_agent_description(AgentLevel.LOU)
    assert "Lou" in desc

    desc = router.get_agent_description(AgentLevel.MATT)
    assert "Matt" in desc
