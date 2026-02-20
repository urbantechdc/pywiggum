"""
PyWiggum - AI Agent Orchestrator with Dashboard

"Me fail English? That's unpossible!" — Ralph Wiggum
Chief Wiggum oversees Ralph. PyWiggum oversees your AI coding agents.
"""

__version__ = "0.1.0"

from pywiggum.config import WiggumConfig
from pywiggum.kanban import KanbanManager, Milestone, Task
from pywiggum.runner import Runner

__all__ = [
    "__version__",
    "WiggumConfig",
    "KanbanManager",
    "Milestone",
    "Task",
    "Runner",
]
