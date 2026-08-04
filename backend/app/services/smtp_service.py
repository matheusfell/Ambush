"""Serviço de configuração de envio de e-mail."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.crypto import encrypt
from app.models.smtp_settings import SmtpSettings
from app.notifier.email import send_test_email
from app.schemas.smtp import SmtpSettingsUpdate


async def get_smtp(session: AsyncSession) -> SmtpSettings:
    row = (await session.execute(select(SmtpSettings).limit(1))).scalar_one_or_none()
    if row is None:
        settings = get_settings()
        row = SmtpSettings(
            delivery_method="graph" if settings.o365_tenant_id else "smtp",
            graph_tenant_id=settings.o365_tenant_id or None,
            graph_client_id=settings.o365_client_id or None,
            graph_client_secret_encrypted=(
                encrypt(settings.o365_client_secret)
                if settings.o365_client_secret
                else None
            ),
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password_encrypted=encrypt(settings.smtp_pass) if settings.smtp_pass else None,
            from_email=settings.email_from_addr or settings.smtp_user,
            from_name="AmbushSystem",
            use_tls=True,
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
    return row


async def update_smtp(
    session: AsyncSession,
    payload: SmtpSettingsUpdate,
) -> SmtpSettings:
    row = await get_smtp(session)
    data: dict[str, Any] = payload.model_dump(exclude_unset=True)

    if "password" in data:
        password = data.pop("password")
        if password:
            row.password_encrypted = encrypt(password)

    if "graph_client_secret" in data:
        client_secret = data.pop("graph_client_secret")
        if client_secret:
            row.graph_client_secret_encrypted = encrypt(client_secret)

    for key, value in data.items():
        setattr(row, key, value)

    row.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(row)
    return row


async def test_smtp(session: AsyncSession, to_email: str) -> None:
    row = await get_smtp(session)
    await send_test_email(row, to_email)
