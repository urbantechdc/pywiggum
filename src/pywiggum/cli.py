"""Command-line interface for PyWiggum."""

import json
import subprocess
import sys
from pathlib import Path

import click

from pywiggum import __version__
from pywiggum.config import WiggumConfig
from pywiggum.controls import Controls
from pywiggum.kanban import KanbanManager
from pywiggum.runner import Runner


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """PyWiggum - AI Agent Orchestrator with Dashboard.

    "Me fail English? That's unpossible!" — Ralph Wiggum
    """
    pass


@main.command()
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(force: bool) -> None:
    """Initialize a new PyWiggum project with templates."""
    config_path = Path("wiggum.yaml")
    kanban_path = Path("kanban.json")

    # Check if files exist
    if config_path.exists() and not force:
        click.echo(f"Error: {config_path} already exists. Use --force to overwrite.")
        sys.exit(1)

    if kanban_path.exists() and not force:
        click.echo(f"Error: {kanban_path} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Create default config
    config = WiggumConfig()
    config.save(config_path)
    click.echo(f"Created {config_path}")

    # Create template kanban
    kanban = KanbanManager(kanban_path)
    board = kanban.create_template()
    kanban.save(board)
    click.echo(f"Created {kanban_path}")

    click.echo("\nProject initialized! Edit wiggum.yaml and kanban.json to customize.")
    click.echo("Run 'wiggum run' to start the autonomous loop.")


@main.command()
@click.option("--max-iterations", type=int, help="Override max iterations")
@click.option("--agent", help="Override agent backend")
@click.option("--model", help="Override model")
@click.option("--dash", is_flag=True, help="Also start dashboard in background")
def run(
    max_iterations: int | None, agent: str | None, model: str | None, dash: bool
) -> None:
    """Start the runner loop."""
    config_path = Path("wiggum.yaml")

    if not config_path.exists():
        click.echo("Error: wiggum.yaml not found. Run 'wiggum init' first.")
        sys.exit(1)

    # Load config
    config = WiggumConfig.load(config_path)

    # Apply overrides
    overrides = {}
    if max_iterations is not None:
        overrides["max_iterations"] = max_iterations
    if agent is not None:
        overrides["agent"] = agent
    if model is not None:
        overrides["model"] = model

    if overrides:
        config = config.merge_overrides(**overrides)

    # Start dashboard if requested
    if dash:
        click.echo("Starting dashboard in background...")
        subprocess.Popen(
            [sys.executable, "-m", "pywiggum.dashboard"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Create and run
    try:
        runner = Runner(config)
        runner.run()
    except KeyboardInterrupt:
        click.echo("\nRunner interrupted by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@main.command()
@click.option("--port", type=int, help="Override dashboard port")
@click.option("--host", help="Override dashboard host")
def dash(port: int | None, host: str | None) -> None:
    """Start the dashboard server."""
    config_path = Path("wiggum.yaml")

    if not config_path.exists():
        click.echo("Error: wiggum.yaml not found. Run 'wiggum init' first.")
        sys.exit(1)

    # Load config
    config = WiggumConfig.load(config_path)

    # Apply overrides
    overrides = {}
    if port is not None:
        overrides["port"] = port
    if host is not None:
        overrides["host"] = host

    if overrides:
        config = config.merge_overrides(**overrides)

    # Import and run dashboard
    from pywiggum.dashboard.server import start_server

    click.echo(f"Starting dashboard on {config.dashboard.host}:{config.dashboard.port}")
    start_server(config)


@main.command()
def status() -> None:
    """Print current status to terminal."""
    config_path = Path("wiggum.yaml")

    if not config_path.exists():
        click.echo("Error: wiggum.yaml not found. Run 'wiggum init' first.")
        sys.exit(1)

    config = WiggumConfig.load(config_path)
    controls = Controls(config.get_work_dir())
    kanban = KanbanManager(config.get_kanban_path())

    try:
        kanban.load()
    except FileNotFoundError:
        click.echo("Error: kanban.json not found")
        sys.exit(1)

    stats = kanban.get_stats()

    click.echo(f"Project: {config.project.name}")
    click.echo(f"Paused: {controls.is_paused()}")
    click.echo(f"Max iterations: {controls.get_max_iterations()}")
    click.echo(f"\nKanban status:")
    click.echo(f"  Total: {stats['total']}")
    click.echo(f"  Todo: {stats['todo']}")
    click.echo(f"  Done: {stats['done']}")
    click.echo(f"  Failed: {stats['failed']}")

    progress = (stats["done"] / stats["total"] * 100) if stats["total"] > 0 else 0
    click.echo(f"  Progress: {progress:.1f}%")


@main.command()
def pause() -> None:
    """Pause the runner."""
    config = WiggumConfig.load(Path("wiggum.yaml"))
    controls = Controls(config.get_work_dir())
    controls.pause()
    click.echo("Runner paused")


@main.command()
def resume() -> None:
    """Resume the runner."""
    config = WiggumConfig.load(Path("wiggum.yaml"))
    controls = Controls(config.get_work_dir())
    controls.resume()
    click.echo("Runner resumed")


@main.command()
@click.argument("text")
def hint(text: str) -> None:
    """Send hint to runner."""
    config = WiggumConfig.load(Path("wiggum.yaml"))
    controls = Controls(config.get_work_dir())
    controls.set_hint(text)
    click.echo("Hint sent to runner")


@main.command()
@click.argument("n", type=int)
def add_iterations(n: int) -> None:
    """Increase max iterations."""
    config = WiggumConfig.load(Path("wiggum.yaml"))
    controls = Controls(config.get_work_dir())
    new_max = controls.add_iterations(n)
    click.echo(f"Max iterations increased to {new_max}")


if __name__ == "__main__":
    main()
