# Changelog

All notable changes to PyWiggum will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-20

### Added
- Initial release of PyWiggum
- Core orchestration loop with kanban-driven task execution
- Support for three agent backends:
  - OpenCode CLI (local models via vLLM/Ollama)
  - Claude Code CLI
  - Direct API (OpenAI-compatible endpoints)
- Web dashboard with:
  - Real-time status and progress tracking
  - Velocity metrics and ETA predictions
  - Drift detection and stall alerts
  - Live controls (pause/resume/hints/iterations)
  - Kanban visualization
  - Git log integration
- File-based IPC for simple control
- History tracking with velocity calculation
- CLI commands:
  - `pywiggum init` - Initialize project
  - `pywiggum run` - Start runner
  - `pywiggum dash` - Start dashboard
  - `pywiggum status` - Check status
  - `pywiggum pause/resume` - Control runner
  - `pywiggum hint` - Send hints
  - `pywiggum add-iterations` - Extend run
- Comprehensive test suite
- Example configurations

### Documentation
- Complete README with usage examples
- Architecture documentation
- Contributing guidelines
- Type hints throughout codebase

[0.1.0]: https://github.com/pywiggum/pywiggum/releases/tag/v0.1.0
