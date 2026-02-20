# Contributing to PyWiggum

Thank you for your interest in contributing to PyWiggum!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/pywiggum/pywiggum.git
cd pywiggum
```

2. Install with dev dependencies:
```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

4. Run linter:
```bash
ruff check .
```

5. Run type checker:
```bash
mypy src/pywiggum
```

## Project Structure

```
pywiggum/
├── src/pywiggum/          # Main package
│   ├── agents/            # Agent backends
│   ├── dashboard/         # Web dashboard
│   ├── cli.py            # CLI commands
│   ├── config.py         # Configuration
│   ├── controls.py       # File-based IPC
│   ├── history.py        # Velocity tracking
│   ├── kanban.py         # Kanban management
│   ├── prompt.py         # Prompt building
│   └── runner.py         # Main loop
├── tests/                # Test suite
├── examples/             # Example configs
└── pyproject.toml        # Package config
```

## Coding Standards

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all public APIs
- Keep functions focused and testable
- Add tests for new features

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and linters
6. Submit a pull request

## Adding New Agent Backends

To add a new agent backend:

1. Create a new file in `src/pywiggum/agents/`
2. Extend `BaseAgent` class
3. Implement required methods:
   - `run()`: Execute a prompt
   - `check_available()`: Check if backend is installed
   - `name` property: Return backend name
4. Update documentation

Example:
```python
from pywiggum.agents.base import BaseAgent, AgentResult

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "myagent"

    def check_available(self) -> bool:
        # Check if agent is available
        return True

    def run(self, prompt: str, work_dir: Path, timeout: int) -> AgentResult:
        # Execute prompt
        return AgentResult(
            exit_code=0,
            stdout="output",
            stderr="",
            success=True
        )
```

## Questions?

Open an issue on GitHub or start a discussion!
