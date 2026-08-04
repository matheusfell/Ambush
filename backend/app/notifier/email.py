"""Envio de e-mail via Microsoft Graph (preferencial) ou SMTP."""

from __future__ import annotations

from email.message import EmailMessage
from typing import Any
from urllib.parse import quote

import aiosmtplib
import httpx

from app.core.crypto import CryptoError, decrypt
from app.core.logging import get_logger
from app.models.smtp_settings import SmtpSettings
from app.notifier.templates import EmailContent, build_custom_email

logger = get_logger(__name__)


class SmtpNotConfiguredError(Exception):
    """Configuração de envio incompleta."""


class SmtpSendError(Exception):
    """Falha ao enviar e-mail (mensagem com o erro real do servidor)."""


def _decrypt_secret(value: str | None, label: str) -> str | None:
    if not value:
        return None
    try:
        return decrypt(value)
    except CryptoError as exc:
        raise SmtpSendError(f"Falha ao descriptografar {label}: {exc}") from exc


def _password(settings: SmtpSettings) -> str | None:
    return _decrypt_secret(settings.password_encrypted, "senha SMTP")


def _graph_client_secret(settings: SmtpSettings) -> str | None:
    return _decrypt_secret(settings.graph_client_secret_encrypted, "client secret O365")


def _validate_smtp_configured(settings: SmtpSettings) -> None:
    if not settings.host or not settings.from_email:
        raise SmtpNotConfiguredError(
            "SMTP não configurado: informe host e remetente em /api/settings/smtp"
        )


def _validate_graph_configured(settings: SmtpSettings) -> None:
    if not (
        settings.graph_tenant_id
        and settings.graph_client_id
        and settings.graph_client_secret_encrypted
        and settings.from_email
    ):
        raise SmtpNotConfiguredError(
            "Microsoft Graph não configurado: informe Tenant ID, Client ID, "
            "Client Secret e remetente"
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


def _recipients(to_addrs: list[str]) -> list[str]:
    recipients = [email.strip() for email in to_addrs if email and email.strip()]
    if not recipients:
        raise SmtpSendError("Lista de destinatários vazia")
    return recipients


async def _send_smtp_email(
    settings: SmtpSettings,
    *,
    recipients: list[str],
    content: EmailContent,
) -> None:
    _validate_smtp_configured(settings)
    message = _build_message(settings, to_addrs=recipients, content=content)
    password = _password(settings)

    # Porta 465 usa TLS implícito; porta 587 usa STARTTLS quando habilitado.
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


async def _graph_access_token(settings: SmtpSettings) -> str:
    _validate_graph_configured(settings)
    client_secret = _graph_client_secret(settings)
    if not client_secret:
        raise SmtpNotConfiguredError("Client Secret O365 ausente")

    token_url = (
        f"https://login.microsoftonline.com/{settings.graph_tenant_id}"
        "/oauth2/v2.0/token"
    )
    data = {
        "client_id": settings.graph_client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "graph_token_falhou",
            status=exc.response.status_code,
            response=exc.response.text,
        )
        raise SmtpSendError(
            f"Falha ao obter token Microsoft Graph: HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("graph_token_conexao_falhou", error=str(exc))
        raise SmtpSendError(f"Falha de conexão Microsoft Graph: {exc}") from exc

    payload: dict[str, Any] = response.json()
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise SmtpSendError("Resposta do Microsoft Graph sem access_token")
    return access_token


async def _send_graph_email(
    settings: SmtpSettings,
    *,
    recipients: list[str],
    content: EmailContent,
) -> None:
    access_token = await _graph_access_token(settings)
    from_addr = quote(settings.from_email, safe="")
    send_url = f"https://graph.microsoft.com/v1.0/users/{from_addr}/sendMail"
    payload = {
        "message": {
            "subject": content.subject,
            "body": {"contentType": "HTML", "content": content.html_body},
            "toRecipients": [
                {"emailAddress": {"address": recipient}} for recipient in recipients
            ],
        },
        "saveToSentItems": False,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(send_url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "graph_send_falhou",
            status=exc.response.status_code,
            response=exc.response.text,
        )
        raise SmtpSendError(
            f"Falha ao enviar via Microsoft Graph: HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("graph_send_conexao_falhou", error=str(exc))
        raise SmtpSendError(f"Falha de conexão Microsoft Graph: {exc}") from exc


async def send_email(
    settings: SmtpSettings,
    *,
    to_addrs: list[str],
    content: EmailContent,
) -> None:
    """Envia e-mail HTML pelo método configurado."""
    recipients = _recipients(to_addrs)
    if settings.delivery_method == "graph":
        await _send_graph_email(settings, recipients=recipients, content=content)
        method = "graph"
    else:
        await _send_smtp_email(settings, recipients=recipients, content=content)
        method = "smtp"

    logger.info(
        "email_enviado",
        method=method,
        subject=content.subject,
        recipients=recipients,
        from_email=settings.from_email,
    )


async def send_test_email(settings: SmtpSettings, to_addr: str) -> None:
    """E-mail de teste da tela de settings."""
    content = build_custom_email(
        subject="[Ambush] E-mail de teste",
        title="TESTE",
        badge_color="#38bdf8",
        body=(
            "Este é um e-mail de teste do Ambush.\n\n"
            "Se você recebeu, a configuração de envio está funcionando."
        ),
    )
    await send_email(settings, to_addrs=[to_addr], content=content)
