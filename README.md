# PyWiggum — AI Agent Orchestrator with Dashboard

> "Me fail English? That's unpossible!" — Ralph Wiggum
>
> Chief Wiggum oversees Ralph. PyWiggum oversees your AI coding agents.

[![PyPI version](https://badge.fury.io/py/pywiggum.svg)](https://badge.fury.io/py/pywiggum)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What Is PyWiggum?

PyWiggum is a Python-based autonomous AI coding agent orchestrator with a built-in web dashboard. It runs a configurable loop that feeds tasks from a kanban to an LLM-powered coding agent, tracks velocity and progress, detects stalls, and gives humans real-time controls to steer the process — pause, resume, inject hints, and adjust iteration limits — all from a web UI.

**Key differentiators from existing Ralph implementations:**

1. **Local-model-first**: Native support for OpenAI-compatible APIs (vLLM, Ollama, llama.cpp) — not just Claude CLI
2. **Web dashboard**: Real-time kanban, velocity tracking, stall detection, baseline drift monitoring, ETA predictions
3. **Human-in-the-loop via web UI**: Pause/resume, hint injection, iteration control — no Telegram bot or CLI-only interaction
4. **Kanban-driven**: Uses a structured kanban.json (not PRD/user-stories), supports milestones with dependency ordering
5. **Model routing** (Layer 2, coming soon): Different models for different task types
6. **Escalation** (Layer 3, coming soon): Automatic escalation to frontier models when local model is stuck

## Installation

```bash
pip install pywiggum

# Or with uv (recommended)
uv pip install pywiggum
```

## Quick Start

```bash
# Initialize a new project with kanban
pywiggum init

# Edit wiggum.yaml and kanban.json to customize your project

# Start the autonomous loop
pywiggum run --max-iterations 50

# Start the dashboard (in another terminal)
pywiggum dash --port 3333

# Open http://localhost:3333 in your browser
```

## Usage

### Initialize Project

```bash
pywiggum init
```

This creates two files:
- `wiggum.yaml` - Configuration file
- `kanban.json` - Kanban board with example tasks

### Run the Agent Loop

```bash
# Basic usage
pywiggum run

# With options
pywiggum run --max-iterations 100 --agent claude_code --dash

# Available agents: opencode, claude_code, api
```

### Control the Runner

```bash
# Check status
pywiggum status

# Pause/resume
pywiggum pause
pywiggum resume

# Send a hint to the agent
pywiggum hint "The control IDs need zero-padding normalization"

# Add more iterations
pywiggum add-iterations 25
```

### Start the Dashboard

```bash
# Default (port 3333)
pywiggum dash

# Custom port/host
pywiggum dash --port 8080 --host 0.0.0.0
```

## Configuration

Edit `wiggum.yaml` to customize your project:

```yaml
# Project metadata
project:
  name: "My Awesome Project"
  kanban: "kanban.json"
  work_dir: "."

# Agent configuration
agent:
  backend: "opencode"  # opencode | claude_code | api
  model: "vllm/qwen3-coder-next"
  timeout: 600

# Runner settings
runner:
  max_iterations: 50
  sleep_between: 3
  commit_after_task: true
  commit_format: "{task_id}: {task_title}"

# Dashboard
dashboard:
  port: 3333
  host: "0.0.0.0"
  refresh_interval: 15

# Prompt customization
prompt:
  tech_stack: |
    SvelteKit 5, TypeScript, better-sqlite3, Tailwind CSS
    Use $state(), $derived(), $effect() (Svelte 5 runes)
  conventions: |
    All database code in src/lib/server/db.ts
    Types in src/lib/types.ts
  extra_context: ""
```

## Kanban Format

The `kanban.json` file defines your project structure:

```json
{
  "milestones": [
    {
      "id": "M1",
      "name": "Project Setup",
      "blocked_by": [],
      "tasks": [
        {
          "id": "M1.1",
          "title": "Initialize SvelteKit project",
          "description": "Run sv create to scaffold the project",
          "acceptance_criteria": [
            "package.json exists",
            "npm run dev works"
          ],
          "status": "todo"
        }
      ]
    },
    {
      "id": "M2",
      "name": "Core Implementation",
      "blocked_by": ["M1"],
      "tasks": [
        {
          "id": "M2.1",
          "title": "Create database schema",
          "description": "Set up SQLite database with initial tables",
          "acceptance_criteria": [
            "Database file created",
            "Tables exist"
          ],
          "status": "todo"
        }
      ]
    }
  ]
}
```

**Task status values**: `todo`, `done`, `failed`

## Agent Backends

### OpenCode (Local Models)

Use with vLLM, Ollama, or other OpenAI-compatible endpoints:

```yaml
agent:
  backend: "opencode"
  model: "vllm/qwen3-coder-next"
```

Requires: `opencode` CLI installed

### Claude Code

Use with Claude Code CLI:

```yaml
agent:
  backend: "claude_code"
```

Requires: `claude` CLI installed and authenticated

### API (Direct)

Make direct API calls to OpenAI-compatible endpoints:

```yaml
agent:
  backend: "api"
  model: "gpt-4"
  api_base_url: "http://localhost:8000/v1"
  api_key_env: "OPENAI_API_KEY"
```

Requires: Set environment variable specified in `api_key_env`

## Dashboard Features

The web dashboard provides:

- **Real-time status**: Running/paused/stopped with pulsing indicator
- **Progress tracking**: Visual progress bar and statistics
- **Velocity metrics**: Average task duration and recent velocity
- **ETA predictions**: Estimated completion time
- **Drift detection**: Alerts when behind schedule
- **Stall detection**: Warnings when tasks take too long
- **Kanban view**: Milestones and tasks with status
- **Git log**: Recent commits
- **Runner log**: Recent activity
- **Live controls**: Pause/resume, add iterations, send hints
- **Claude context blob**: Copyable status summary for Claude conversations

## How It Works

1. **Runner reads kanban.json** and finds the first `todo` task whose milestone is not blocked
2. **Builds a prompt** with project context, tech stack, conventions, and any human hints
3. **Invokes the agent backend** (OpenCode, Claude Code, or API)
4. **Agent completes the task** and updates kanban.json status to `done` or `failed`
5. **Optionally commits** the changes with a formatted message
6. **Records completion** in history for velocity tracking
7. **Repeats** until all tasks are done or max iterations reached

The dashboard runs independently and provides real-time visibility and control.

## Human-in-the-Loop Controls

PyWiggum uses file-based IPC for simple, debuggable control:

| File | Purpose |
|------|---------|
| `.wiggum-pause` | Exists = runner paused |
| `.wiggum-max` | Current max iteration count |
| `.wiggum-hint` | Text hint for next iteration |
| `.wiggum-hints-archive/` | Consumed hints with timestamps |

You can manually create/edit these files or use the CLI/dashboard.

## Examples

### Basic SvelteKit Project

```bash
pywiggum init
# Edit kanban.json to add your SvelteKit tasks
# Edit wiggum.yaml to set tech stack
pywiggum run --max-iterations 100 --dash
```

### Using Local Model with vLLM

```yaml
agent:
  backend: "opencode"
  model: "vllm/qwen3-coder-next"
```

```bash
# In one terminal: start vLLM server
vllm serve Qwen/Qwen2.5-Coder-32B-Instruct

# In another terminal: run PyWiggum
pywiggum run
```

### Using Claude Code

```yaml
agent:
  backend: "claude_code"
```

```bash
pywiggum run --agent claude_code
```

## Development

```bash
# Clone the repo
git clone https://github.com/pywiggum/pywiggum.git
cd pywiggum

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type check
mypy src/pywiggum
```

## Roadmap

### Layer 2: Model Routing

Config-driven model selection per task type:

```yaml
routing:
  code: "vllm/qwen3-coder-next"
  planning: "anthropic/claude-sonnet-4-5"
  test: "vllm/qwen3-coder-next"
```

### Layer 3: Escalation

Automatic escalation to frontier models when stuck:

```yaml
escalation:
  trigger_after: 3  # iterations without progress
  model: "anthropic/claude-sonnet-4-5"
  api_key_env: "ANTHROPIC_API_KEY"
```

### Layer 4: TBD

Multi-agent coordination? Parallel task execution? Self-improving prompts? You tell us!

## Design Principles

1. **Files as IPC**: No message queues, no WebSockets for control. Files are simple, debuggable, and work for single-user local setups.
2. **Single HTML dashboard**: No React, no build step, no node_modules. One HTML file with embedded CSS/JS.
3. **Config over code**: Everything customizable via wiggum.yaml. No need to edit Python to use it.
4. **Local-first**: Designed for local models on local hardware. Cloud APIs are optional escalation, not the default.
5. **One task per iteration**: Clean context per task. Memory persists via git history and kanban state, not model context.

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

## License

MIT License - see LICENSE file for details.

## Credits

Inspired by the Ralph pattern and all the Ralph implementations in the wild. PyWiggum brings the pattern to local models with a focus on observability and control.

---

"That's unpossible!" — Ralph Wiggum
