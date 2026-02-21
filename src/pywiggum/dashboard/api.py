"""REST API endpoints for dashboard."""

import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pywiggum.config import WiggumConfig
from pywiggum.controls import Controls
from pywiggum.history import HistoryTracker
from pywiggum.kanban import KanbanManager


class ControlRequest(BaseModel):
    """Request for control actions."""

    action: str  # pause, resume, add-iterations, hint
    value: str | None = None  # For add-iterations (number) or hint (text)


def create_api_routes(config: WiggumConfig) -> APIRouter:
    """Create API routes for dashboard.

    Args:
        config: PyWiggum configuration

    Returns:
        FastAPI router with all endpoints
    """
    router = APIRouter()

    work_dir = config.get_work_dir()
    kanban_path = config.get_kanban_path()

    @router.get("/status")
    async def get_status() -> dict:
        """Get full status of the PyWiggum system."""
        controls = Controls(work_dir)
        kanban = KanbanManager(kanban_path)
        history = HistoryTracker(work_dir)

        # Load data
        try:
            kanban.load()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Kanban file not found")

        history.load()

        # Get basic stats
        kanban_stats = kanban.get_stats()
        history_stats = history.get_stats()

        # Build status
        status = {
            "project_name": config.project.name,
            "timestamp": datetime.now().isoformat(),
            "paused": controls.is_paused(),
            "max_iterations": controls.get_max_iterations(),
            "kanban": {
                "total": kanban_stats["total"],
                "todo": kanban_stats["todo"],
                "done": kanban_stats["done"],
                "failed": kanban_stats["failed"],
                "progress_percent": (
                    (kanban_stats["done"] / kanban_stats["total"] * 100)
                    if kanban_stats["total"] > 0
                    else 0
                ),
            },
            "velocity": {
                "avg_minutes": history_stats["avg_duration_minutes"],
                "recent_minutes": history_stats["recent_velocity_minutes"],
            },
            "milestones": [],
        }

        # Add milestone details
        if kanban.board:
            for milestone in kanban.board.milestones:
                milestone_stats = kanban.get_milestone_stats(milestone.id)
                status["milestones"].append(
                    {
                        "id": milestone.id,
                        "name": milestone.name,
                        "blocked_by": milestone.blocked_by,
                        "total": milestone_stats["total"],
                        "done": milestone_stats["done"],
                        "todo": milestone_stats["todo"],
                        "failed": milestone_stats["failed"],
                        "tasks": [
                            {
                                "id": task.id,
                                "title": task.title,
                                "status": task.status,
                                "note": task.note,
                            }
                            for task in milestone.tasks
                        ],
                    }
                )

        # Add predictions
        eta = history.predict_eta(kanban_stats["todo"])
        if eta:
            status["predicted_eta"] = eta.isoformat()

        # Add drift
        drift = history.get_drift(kanban_stats["todo"])
        if drift:
            status["drift_minutes"] = drift.total_seconds() / 60.0

        # Add baseline
        if history.baseline_eta:
            status["baseline_eta"] = history.baseline_eta.isoformat()

        # Check runner process
        runner_state = controls.read_state()
        runner_alive = controls.is_runner_alive()
        status["runner_alive"] = runner_alive
        status["runner_crashed"] = not runner_alive and runner_state is not None
        if runner_state:
            status["iterations_used"] = runner_state.get("iteration", 0)
        else:
            # No state file — estimate from history
            status["iterations_used"] = sum(
                c.iterations for c in history.completions
            )

        # Get git log
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-12"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                status["git_log"] = result.stdout.strip().split("\n")
        except Exception:
            status["git_log"] = []

        # Get runner log
        log_file = work_dir / "wiggum.log"
        if log_file.exists():
            try:
                lines = log_file.read_text().strip().split("\n")
                status["runner_log"] = lines[-5:]  # Last 5 lines
            except Exception:
                status["runner_log"] = []
        else:
            status["runner_log"] = []

        return status

    @router.get("/claude-blob")
    async def get_claude_blob() -> dict:
        """Get compact status string for pasting into Claude conversations."""
        controls = Controls(work_dir)
        kanban = KanbanManager(kanban_path)
        history = HistoryTracker(work_dir)

        try:
            kanban.load()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Kanban file not found")

        history.load()

        stats = kanban.get_stats()
        history_stats = history.get_stats()

        runner_alive = controls.is_runner_alive()
        runner_state = controls.read_state()

        # Determine runner status label
        if controls.is_paused():
            status_label = "Paused"
        elif runner_alive:
            status_label = "Running"
        else:
            status_label = "Crashed" if runner_state else "Stopped"

        # Iteration info
        if runner_state:
            iterations_used = runner_state.get("iteration", 0)
        else:
            iterations_used = sum(c.iterations for c in history.completions)
        max_iter = controls.get_max_iterations()

        blob_parts = [
            f"# {config.project.name} - PyWiggum Status",
            f"Status: {status_label}",
            f"Iterations: {iterations_used}/{max_iter or '?'}",
            f"Progress: {stats['done']}/{stats['total']} tasks ({stats['done']/stats['total']*100:.1f}%)",
            f"Avg velocity: {history_stats['avg_duration_minutes']:.1f} min/task",
        ]

        eta = history.predict_eta(stats["todo"])
        if eta:
            blob_parts.append(f"ETA: {eta.strftime('%Y-%m-%d %H:%M')}")

        # If crashed, include tail of runner log
        if not runner_alive and runner_state:
            log_file = work_dir / "wiggum.log"
            if log_file.exists():
                try:
                    lines = log_file.read_text().strip().split("\n")
                    tail = lines[-10:]
                    blob_parts.append("")
                    blob_parts.append("## Crash Log (last 10 lines)")
                    blob_parts.extend(tail)
                except Exception:
                    pass

        blob = "\n".join(blob_parts)

        return {"blob": blob}

    @router.post("/control")
    async def control_action(request: ControlRequest) -> dict:
        """Execute a control action."""
        controls = Controls(work_dir)

        if request.action == "pause":
            controls.pause()
            return {"status": "paused"}

        elif request.action == "resume":
            controls.resume()
            return {"status": "resumed"}

        elif request.action == "add-iterations":
            if not request.value:
                raise HTTPException(status_code=400, detail="value required for add-iterations")
            try:
                n = int(request.value)
                new_max = controls.add_iterations(n)
                return {"status": "updated", "new_max": new_max}
            except ValueError:
                raise HTTPException(status_code=400, detail="value must be an integer")

        elif request.action == "hint":
            if not request.value:
                raise HTTPException(status_code=400, detail="value required for hint")
            controls.set_hint(request.value)
            return {"status": "hint_set"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    return router
