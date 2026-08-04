"""Aplicação FastAPI — AmbushSystem."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import (
    auth,
    dashboard,
    email_configs,
    health,
    incidents,
    monitors,
    notifications,
    settings,
)
from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database import AsyncSessionLocal
from app.scheduler.scheduler import scheduler
from app.services import auth_service

setup_logging()
logger = get_logger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"
_FRONTEND_ASSETS = _FRONTEND_DIST / "assets"
_FRONTEND_INDEX = _FRONTEND_DIST / "index.html"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Sobe seed de admin + agendador; encerra Tasks no shutdown."""
    logger.info("aplicacao_iniciando")
    async with AsyncSessionLocal() as session:
        await auth_service.ensure_admin_seed(session)
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()
        logger.info("aplicacao_encerrada")


app = FastAPI(
    title="AmbushSystem",
    description="Monitoramento interno de disponibilidade de sistemas",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(monitors.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(email_configs.router, prefix="/api")

if _FRONTEND_ASSETS.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_FRONTEND_ASSETS),
        name="frontend-assets",
    )


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def serve_frontend(full_path: str) -> FileResponse | HTMLResponse:
    """Serve o build React e faz fallback para o React Router."""
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if not _FRONTEND_INDEX.exists():
        return HTMLResponse(
            (
                "<h1>Frontend não buildado</h1>"
                "<p>Rode <code>npm run build</code> em <code>frontend</code> "
                "e reinicie o backend.</p>"
            ),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    requested_path = (_FRONTEND_DIST / full_path).resolve()
    dist_root = _FRONTEND_DIST.resolve()
    try:
        requested_path.relative_to(dist_root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc

    if requested_path.is_file():
        return FileResponse(requested_path)
    return FileResponse(_FRONTEND_INDEX)
