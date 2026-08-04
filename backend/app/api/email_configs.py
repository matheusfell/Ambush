"""API de configuração de e-mail por monitor."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser
from app.database import get_db
from app.schemas.email_config import EmailNotificationConfigRead, EmailNotificationConfigUpsert
from app.services import email_config_service

router = APIRouter(prefix="/settings/email-configs", tags=["settings"])


@router.get("", response_model=list[EmailNotificationConfigRead])
async def list_email_configs(
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> list[EmailNotificationConfigRead]:
    rows = await email_config_service.list_configs(db)
    return [EmailNotificationConfigRead.model_validate(row) for row in rows]


@router.get("/{monitor_id}", response_model=EmailNotificationConfigRead | None)
async def get_email_config(
    monitor_id: int,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> EmailNotificationConfigRead | None:
    row = await email_config_service.get_config(db, monitor_id)
    if row is None:
        return None
    return EmailNotificationConfigRead.model_validate(row)


@router.put("/{monitor_id}", response_model=EmailNotificationConfigRead)
async def upsert_email_config(
    monitor_id: int,
    payload: EmailNotificationConfigUpsert,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> EmailNotificationConfigRead:
    payload = payload.model_copy(update={"monitor_id": monitor_id})
    try:
        row = await email_config_service.upsert_config(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EmailNotificationConfigRead.model_validate(row)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_config(
    monitor_id: int,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    await email_config_service.delete_config(db, monitor_id)
