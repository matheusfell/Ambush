"""Aplicação FastAPI — AmbushSystem."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboard, health, incidents, monitors, notifications, settings
from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database import AsyncSessionLocal
from app.scheduler.scheduler import scheduler
from app.services import auth_service

setup_logging()
logger = get_logger(__name__)


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
