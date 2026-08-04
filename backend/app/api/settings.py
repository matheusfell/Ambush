"""API de configuração SMTP."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser
from app.database import get_db
from app.notifier.email import SmtpNotConfiguredError, SmtpSendError
from app.schemas.smtp import SmtpSettingsRead, SmtpSettingsUpdate, SmtpTestRequest
from app.services import smtp_service

router = APIRouter(prefix="/settings/smtp", tags=["settings"])


def _to_read(row: object) -> SmtpSettingsRead:
    from app.models.smtp_settings import SmtpSettings

    assert isinstance(row, SmtpSettings)
    data = SmtpSettingsRead.model_validate(row)
    data.has_password = bool(row.password_encrypted)
    data.has_graph_client_secret = bool(row.graph_client_secret_encrypted)
    return data


@router.get("", response_model=SmtpSettingsRead)
async def get_smtp(
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsRead:
    row = await smtp_service.get_smtp(db)
    return _to_read(row)


@router.put("", response_model=SmtpSettingsRead)
async def update_smtp(
    payload: SmtpSettingsUpdate,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SmtpSettingsRead:
    row = await smtp_service.update_smtp(db, payload)
    return _to_read(row)


@router.post("/test")
async def test_smtp(
    payload: SmtpTestRequest,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        await smtp_service.test_smtp(db, str(payload.to_email))
    except SmtpNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SmtpSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return {"status": "ok", "detail": f"E-mail de teste enviado para {payload.to_email}"}
