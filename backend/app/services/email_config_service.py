"""Serviço de configuração de e-mail por monitor."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_notification_config import EmailNotificationConfig
from app.models.monitor import Monitor
from app.schemas.email_config import EmailNotificationConfigUpsert


async def list_configs(session: AsyncSession) -> list[EmailNotificationConfig]:
    stmt = select(EmailNotificationConfig).order_by(EmailNotificationConfig.monitor_id)
    return list((await session.execute(stmt)).scalars().all())


async def get_config(
    session: AsyncSession,
    monitor_id: int,
) -> EmailNotificationConfig | None:
    stmt = select(EmailNotificationConfig).where(EmailNotificationConfig.monitor_id == monitor_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def upsert_config(
    session: AsyncSession,
    payload: EmailNotificationConfigUpsert,
) -> EmailNotificationConfig:
    monitor = await session.get(Monitor, payload.monitor_id)
    if monitor is None:
        raise ValueError("Monitor não encontrado")

    row = await get_config(session, payload.monitor_id)
    if row is None:
        row = EmailNotificationConfig(monitor_id=payload.monitor_id)
        session.add(row)

    row.enabled = payload.enabled
    row.emails = [str(email) for email in payload.emails]
    row.failure_threshold = payload.failure_threshold
    row.reminder_minutes = payload.reminder_minutes
    row.down_subject = payload.down_subject
    row.down_body = payload.down_body
    row.recovery_subject = payload.recovery_subject
    row.recovery_body = payload.recovery_body
    row.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(row)
    return row


async def delete_config(session: AsyncSession, monitor_id: int) -> None:
    row = await get_config(session, monitor_id)
    if row is None:
        return
    await session.delete(row)
    await session.flush()
