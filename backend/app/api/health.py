"""Healthcheck do próprio AmbushSystem."""

from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Quem monitora o monitor — verifica conectividade com o banco."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — health deve reportar qualquer falha
        return {"status": "degraded", "detail": str(exc)}
