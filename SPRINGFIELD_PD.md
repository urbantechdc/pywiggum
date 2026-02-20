# 🚔 Springfield PD: Agent Routing & Escalation

PyWiggum implements a hierarchical agent routing system inspired by Springfield's finest police department.

## The Hierarchy

```
👮 Ralph (Wiggum)  →  👮‍♂️ Eddie  →  👨‍✈️ Lou  →  👨‍💼 Chief Matt
   Local model      Better local   Claude     Human
   (Qwen 3)         (Qwen 32B)    (Sonnet)   (You!)
```

### Meet the Team

**👮 Ralph (Wiggum)** - *"Me fail task? That's unpossible!"*
- **Role**: Entry-level agent, handles basic tasks
- **Backend**: Local model (e.g., Qwen 3 Coder via vLLM/Ollama)
- **Best for**: Simple coding tasks, boilerplate, refactoring
- **When he struggles**: After 3 failed attempts or 30 minutes

**👮‍♂️ Eddie** - *"I got this one, Chief"*
- **Role**: Mid-level agent, more capable than Ralph
- **Backend**: Better local model (e.g., Qwen 32B Instruct)
- **Best for**: Moderate complexity tasks, debugging
- **When to call him**: Ralph is stuck, or task is known to be tricky

**👨‍✈️ Lou** - *"Let me handle the complex stuff"*
- **Role**: Senior officer, frontier model capabilities
- **Backend**: Claude Code (Sonnet 4.5)
- **Best for**: Complex architecture, planning, difficult debugging
- **When to call him**: Eddie is stuck, or task requires deep reasoning

**👨‍💼 Chief Matt (Human)** - *"Alright, I'll take it from here"*
- **Role**: Human in the loop, final authority
- **Backend**: You!
- **Best for**: Decisions, unclear requirements, critical tasks
- **When to call you**: All AI agents are stuck, or task explicitly requires human

## Configuration

Enable routing by adding a `routing` section to `wiggum.yaml`:

```yaml
routing:
  # Define your agents
  agents:
    ralph:
      backend: "opencode"
      model: "vllm/qwen3-coder-next"

    eddie:
      backend: "opencode"
      model: "vllm/qwen3-32b-instruct"

    lou:
      backend: "claude_code"
      model: "claude-sonnet-4-5"

    matt:
      backend: "human"

  # Routing rules (first match wins)
  rules:
    # Planning tasks → Lou (needs deep thinking)
    - task_type: "planning"
      agent_level: "lou"

    # Tests → Ralph (straightforward)
    - task_type: "test"
      agent_level: "ralph"

    # Milestone M3 → Start with Eddie
    - milestone_id: "M3"
      agent_level: "eddie"

    # Specific tricky task → Lou
    - task_id_pattern: "M2\\.2"
      agent_level: "lou"

  # Default for tasks that don't match
  default_agent: "ralph"

  # Escalation settings
  escalation:
    enabled: true
    trigger_after_iterations: 3      # Escalate after 3 failed attempts
    trigger_after_duration: 1800     # Escalate after 30 minutes
    escalation_chain:
      - "ralph"   # Start here
      - "eddie"   # First escalation
      - "lou"     # Second escalation
      - "matt"    # Final escalation (human)
```

## Routing Rules

### By Task Type

Tag tasks in your kanban with `"type"` field:

```json
{
  "id": "M2.1",
  "title": "Design database schema",
  "type": "planning",
  "description": "..."
}
```

Then route by type:

```yaml
rules:
  - task_type: "planning"
    agent_level: "lou"
```

### By Milestone

Route entire milestones to specific agents:

```yaml
rules:
  - milestone_id: "M3"
    agent_level: "eddie"
```

### By Task Pattern

Use regex to match task IDs:

```yaml
rules:
  - task_id_pattern: "M2\\..*"  # All M2 tasks
    agent_level: "eddie"

  - task_id_pattern: ".*\\.setup$"  # Tasks ending in .setup
    agent_level: "ralph"
```

### Rule Precedence

**First match wins!** Rules are evaluated in order. More specific rules should come first:

```yaml
rules:
  # Specific task
  - task_id_pattern: "M2\\.2"
    agent_level: "lou"

  # General milestone (will not match M2.2 because rule above matched first)
  - milestone_id: "M2"
    agent_level: "eddie"
```

## Escalation

When an agent gets stuck on a task, PyWiggum automatically escalates up the chain.

### Escalation Triggers

**By Iterations**: Agent fails to complete task after N attempts
```yaml
escalation:
  trigger_after_iterations: 3  # Escalate after 3 attempts
```

**By Duration**: Task takes too long
```yaml
escalation:
  trigger_after_duration: 1800  # Escalate after 30 minutes
```

### Escalation Chain

Define your escalation path:

```yaml
escalation:
  escalation_chain:
    - "ralph"   # 👮 Start here
    - "eddie"   # 👮‍♂️ Escalate if Ralph fails
    - "lou"     # 👨‍✈️ Escalate if Eddie fails
    - "matt"    # 👨‍💼 Finally ask human
```

**Custom chains** are supported:
```yaml
escalation_chain:
  - "ralph"   # Try local model first
  - "lou"     # Skip Eddie, go straight to Claude
  - "matt"    # Then human
```

## Human-in-the-Loop (Chief Matt)

When a task escalates to `matt`, PyWiggum pauses and prompts you:

```
🚔 CHIEF MATT (HUMAN) - YOU'RE UP!
The AI agents need your help. Here's the situation:

[Task description and context]

What would you like to do?
1. Complete the task yourself (type 'done' when finished)
2. Provide guidance to the AI (type 'hint: <your hint>')
3. Mark task as failed (type 'failed: <reason>')
4. Delegate back to AI (type 'delegate')

Your response: _
```

**Options:**

- `done` - You completed the task manually
- `hint: Fix the SQL syntax in line 42` - Give AI a hint and retry
- `failed: Requires external API we don't have` - Mark as failed
- `delegate` - Send back to AI without changes

## Example Scenarios

### Scenario 1: Simple Task

```
Task M1.1: "Create README"
→ Ralph handles it ✅ Done in 2 minutes
```

### Scenario 2: Moderate Complexity

```
Task M2.3: "Implement complex validation"
→ Ralph tries → Fails after 2 attempts
→ Escalates to Eddie
→ Eddie completes it ✅ Done in 15 minutes
```

### Scenario 3: Very Complex

```
Task M3.1: "Design microservices architecture"
→ Routed directly to Lou (planning task)
→ Lou completes it ✅ Done in 20 minutes
```

### Scenario 4: Stuck and Need Human

```
Task M2.5: "Integrate payment gateway"
→ Ralph tries → Fails (3 attempts)
→ Eddie tries → Fails (30 minutes)
→ Lou tries → Fails (unclear API docs)
→ Escalates to Matt (you)
→ You: "hint: Use the test API key from Slack"
→ Lou retries ✅ Done!
```

## Benefits

1. **Cost-effective**: Use cheap local models for simple tasks
2. **Quality when needed**: Escalate to Claude for complex work
3. **Human oversight**: You're always the final authority
4. **Automatic**: No manual intervention until necessary
5. **Transparent**: Dashboard shows current agent level

## Dashboard Integration

The dashboard shows:
- Current agent handling the task
- Number of attempts on current task
- Agent level (Ralph/Eddie/Lou/Matt)
- Escalation warnings when approaching thresholds

## Best Practices

1. **Start conservative**: Let Ralph handle most tasks, escalate when needed
2. **Tag task types**: Use `"type": "planning"` etc. for smart routing
3. **Monitor thresholds**: Adjust escalation triggers based on your models
4. **Human check-ins**: Set reasonable iteration limits so you're not waiting forever
5. **Learn patterns**: If Ralph always fails a certain type, route it higher

---

**"Me fail English? That's unpossible!"** — Ralph Wiggum

But with Springfield PD routing, when Ralph fails, Eddie's got your back. And when Eddie fails, Lou steps in. And when Lou needs help... well, that's what Chief Matt is for. 🚔
