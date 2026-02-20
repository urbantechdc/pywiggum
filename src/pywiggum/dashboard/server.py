"""FastAPI dashboard server."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from pywiggum.config import WiggumConfig
from pywiggum.dashboard.api import create_api_routes

app = FastAPI(title="PyWiggum Dashboard")


def create_app(config: WiggumConfig) -> FastAPI:
    """Create and configure the FastAPI app.

    Args:
        config: PyWiggum configuration

    Returns:
        Configured FastAPI app
    """
    # Add API routes
    api_router = create_api_routes(config)
    app.include_router(api_router, prefix="/api")

    # Serve static files
    from pathlib import Path

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Root route - serve dashboard HTML
    @app.get("/", response_class=HTMLResponse)
    async def root() -> FileResponse:
        """Serve the dashboard HTML."""
        html_path = static_dir / "index.html"
        if html_path.exists():
            return FileResponse(html_path)
        return HTMLResponse("<h1>PyWiggum Dashboard</h1><p>index.html not found</p>")

    return app


def start_server(config: WiggumConfig) -> None:
    """Start the dashboard server.

    Args:
        config: PyWiggum configuration
    """
    configured_app = create_app(config)
    uvicorn.run(
        configured_app,
        host=config.dashboard.host,
        port=config.dashboard.port,
        log_level="info",
    )


if __name__ == "__main__":
    from pathlib import Path

    config = WiggumConfig.load(Path("wiggum.yaml"))
    start_server(config)
