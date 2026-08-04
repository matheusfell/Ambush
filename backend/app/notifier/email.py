"""Envio de e-mail via aiosmtplib (STARTTLS / SSL implícito)."""

from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from app.core.crypto import CryptoError, decrypt
from app.core.logging import get_logger
from app.models.smtp_settings import SmtpSettings
from app.notifier.templates import EmailContent

logger = get_logger(__name__)


class SmtpNotConfiguredError(Exception):
    """SMTP incompleto (host/from ausentes)."""


class SmtpSendError(Exception):
    """Falha ao enviar e-mail (mensagem com o erro real do servidor)."""


def _password(settings: SmtpSettings) -> str | None:
    if not settings.password_encrypted:
        return None
    try:
        return decrypt(settings.password_encrypted)
    except CryptoError as exc:
        raise SmtpSendError(f"Falha ao descriptografar senha SMTP: {exc}") from exc


def _validate_configured(settings: SmtpSettings) -> None:
    if not settings.host or not settings.from_email:
        raise SmtpNotConfiguredError(
            "SMTP não configurado: informe host e from_email em /api/settings/smtp"
        )


def _build_message(
    settings: SmtpSettings,
    *,
    to_addrs: list[str],
    content: EmailContent,
) -> EmailMessage:
    msg = EmailMessage()
    from_name = settings.from_name or "AmbushSystem"
    msg["From"] = f"{from_name} <{settings.from_email}>"
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = content.subject
    msg.set_content("Abra este e-mail em um cliente que suporte HTML.")
    msg.add_alternative(content.html_body, subtype="html")
    return msg


async def send_email(
    settings: SmtpSettings,
    *,
    to_addrs: list[str],
    content: EmailContent,
) -> None:
    """Envia e-mail HTML. Propaga erro real do SMTP em SmtpSendError."""
    _validate_configured(settings)
    recipients = [e.strip() for e in to_addrs if e and e.strip()]
    if not recipients:
        raise SmtpSendError("Lista de destinatários vazia")

    message = _build_message(settings, to_addrs=recipients, content=content)
    password = _password(settings)

    # Porta 465 → TLS implícito; demais com use_tls → STARTTLS (ex.: 587 Office 365)
    use_implicit_tls = settings.port == 465
    start_tls = bool(settings.use_tls) and not use_implicit_tls

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.host,
            port=settings.port,
            username=settings.username or None,
            password=password,
            start_tls=start_tls,
            use_tls=use_implicit_tls,
        )
    except aiosmtplib.SMTPException as exc:
        logger.error("smtp_falhou", error=str(exc), host=settings.host, port=settings.port)
        raise SmtpSendError(str(exc)) from exc
    except OSError as exc:
        logger.error("smtp_conexao_falhou", error=str(exc), host=settings.host)
        raise SmtpSendError(f"Falha de conexão SMTP: {exc}") from exc

    logger.info(
        "email_enviado",
        subject=content.subject,
        recipients=recipients,
        host=settings.host,
    )


async def send_test_email(settings: SmtpSettings, to_addr: str) -> None:
    """E-mail de teste da tela de settings."""
    content = EmailContent(
        subject="[AmbushSystem] E-mail de teste",
        html_body=(
            "<p>Este é um e-mail de teste do <strong>AmbushSystem</strong>.</p>"
            "<p>Se você recebeu, a configuração SMTP está funcionando.</p>"
        ),
    )
    await send_email(settings, to_addrs=[to_addr], content=content)
