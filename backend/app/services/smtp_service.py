"""Serviço de configuração SMTP."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt
from app.models.smtp_settings import SmtpSettings
from app.notifier.email import send_test_email
from app.schemas.smtp import SmtpSettingsUpdate


async def get_smtp(session: AsyncSession) -> SmtpSettings:
    row = (await session.execute(select(SmtpSettings).limit(1))).scalar_one_or_none()
    if row is None:
        row = SmtpSettings(
            host="",
            port=587,
            from_email="",
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
        if password is None or password == "":
            row.password_encrypted = None
        else:
            row.password_encrypted = encrypt(password)

    for key, value in data.items():
        setattr(row, key, value)

    row.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(row)
    return row


async def test_smtp(session: AsyncSession, to_email: str) -> None:
    row = await get_smtp(session)
    await send_test_email(row, to_email)
