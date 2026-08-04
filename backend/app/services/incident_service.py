"""Abertura/fechamento de incidentes e disparo de notificações."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.checker.classifier import CheckResult
from app.config import get_settings
from app.core.logging import get_logger
from app.models.check import Check
from app.models.email_notification_config import EmailNotificationConfig
from app.models.incident import Incident
from app.models.monitor import Monitor
from app.models.notification_group import NotificationGroup
from app.models.notification_rule import NotificationRule
from app.models.smtp_settings import SmtpSettings
from app.notifier import policy
from app.notifier.email import SmtpNotConfiguredError, SmtpSendError, send_email
from app.notifier.templates import (
    EmailContent,
    build_custom_email,
    build_degraded_email,
    build_down_email,
    build_recovery_email,
    build_reminder_email,
)

logger = get_logger(__name__)


async def get_open_incident(session: AsyncSession, monitor_id: int) -> Incident | None:
    stmt = (
        select(Incident)
        .where(Incident.monitor_id == monitor_id, Incident.status == "open")
        .order_by(desc(Incident.started_at))
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_previous_check(
    session: AsyncSession,
    monitor_id: int,
    current_check_id: int,
) -> Check | None:
    stmt = (
        select(Check)
        .where(Check.monitor_id == monitor_id, Check.id != current_check_id)
        .order_by(desc(Check.checked_at))
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def resolve_rule(session: AsyncSession, monitor_id: int) -> NotificationRule:
    """Regra do monitor, senão regra global (monitor_id IS NULL)."""
    specific = (
        await session.execute(
            select(NotificationRule).where(NotificationRule.monitor_id == monitor_id)
        )
    ).scalar_one_or_none()
    if specific is not None:
        return specific

    global_rule = (
        await session.execute(
            select(NotificationRule).where(NotificationRule.monitor_id.is_(None))
        )
    ).scalar_one_or_none()
    if global_rule is None:
        rule = NotificationRule(
            monitor_id=None,
            on_down=True,
            on_recovery=True,
            on_degraded=False,
            min_interval_minutes=30,
        )
        session.add(rule)
        await session.flush()
        return rule
    return global_rule


async def _load_smtp(session: AsyncSession) -> SmtpSettings | None:
    return (await session.execute(select(SmtpSettings).limit(1))).scalar_one_or_none()


async def _recipients(session: AsyncSession, monitor: Monitor) -> list[str]:
    if monitor.notification_group_id is None:
        return []
    group = await session.get(NotificationGroup, monitor.notification_group_id)
    if group is None:
        return []
    return list(group.emails or [])


def _dashboard_url(monitor_id: int) -> str:
    base = get_settings().app_base_url.rstrip("/")
    return f"{base}/monitors/{monitor_id}"


def _error_text(check: Check) -> str:
    if check.error_message:
        return check.error_message
    if check.status_code is not None:
        return f"HTTP {check.status_code}"
    return "Falha desconhecida"


async def _load_email_config(
    session: AsyncSession,
    monitor_id: int,
) -> EmailNotificationConfig | None:
    stmt = select(EmailNotificationConfig).where(
        EmailNotificationConfig.monitor_id == monitor_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def _render_template(template: str, values: dict[str, object]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


def _changed_after_last_notification(
    config: EmailNotificationConfig | None,
    last_notified_at: datetime | None,
) -> bool:
    if config is None or not config.enabled:
        return False
    if last_notified_at is None:
        return True
    updated_at = (
        config.updated_at
        if config.updated_at.tzinfo
        else config.updated_at.replace(tzinfo=UTC)
    )
    last = (
        last_notified_at
        if last_notified_at.tzinfo
        else last_notified_at.replace(tzinfo=UTC)
    )
    return updated_at > last


def _custom_email_content(
    *,
    subject_template: str,
    body_template: str,
    values: dict[str, object],
    title: str,
    badge_color: str,
) -> EmailContent:
    subject = _render_template(subject_template, values)
    body = _render_template(body_template, values)
    return build_custom_email(
        subject=subject,
        body=body,
        title=title,
        badge_color=badge_color,
        dashboard_url=str(values.get("dashboard_url") or ""),
    )


async def _consecutive_down_info(
    session: AsyncSession,
    *,
    monitor_id: int,
    current_check_id: int,
    limit: int = 50,
) -> tuple[int, datetime | None]:
    stmt = (
        select(Check)
        .where(Check.monitor_id == monitor_id, Check.id <= current_check_id)
        .order_by(desc(Check.checked_at))
        .limit(limit)
    )
    checks = list((await session.execute(stmt)).scalars().all())
    count = 0
    first_down_at: datetime | None = None
    for row in checks:
        if row.result != CheckResult.DOWN.value:
            break
        count += 1
        first_down_at = row.checked_at
    return count, first_down_at


async def _try_notify(
    session: AsyncSession,
    *,
    monitor: Monitor,
    incident: Incident | None,
    content: EmailContent,
) -> bool:
    """Envia e-mail; retorna True se enviou. Erros SMTP não quebram o fluxo."""
    smtp = await _load_smtp(session)
    config = await _load_email_config(session, monitor.id)
    recipients = (
        list(config.emails or [])
        if config is not None and config.enabled and config.emails
        else await _recipients(session, monitor)
    )
    if smtp is None or not recipients:
        logger.warning(
            "notificacao_omitida",
            monitor_id=monitor.id,
            reason="smtp_ou_destinatarios_ausentes",
        )
        return False

    try:
        await send_email(smtp, to_addrs=recipients, content=content)
    except (SmtpNotConfiguredError, SmtpSendError) as exc:
        logger.error("falha_ao_notificar", monitor_id=monitor.id, error=str(exc))
        return False

    if incident is not None:
        incident.last_notified_at = datetime.now(UTC)
    return True


async def process_check_result(
    session: AsyncSession,
    monitor: Monitor,
    check: Check,
) -> Incident | None:
    """
    Processa o resultado da checagem: abre/fecha incidente e notifica.

    Chamado após persistir o Check (scheduler e check manual).
    """
    now = datetime.now(UTC)
    checked_at = (
        check.checked_at
        if check.checked_at.tzinfo
        else check.checked_at.replace(tzinfo=UTC)
    )
    rule = await resolve_rule(session, monitor.id)
    tz = get_settings().app_timezone
    previous = await get_previous_check(session, monitor.id, check.id)
    open_incident = await get_open_incident(session, monitor.id)
    result = check.result

    in_quiet = policy.is_in_quiet_hours(
        now,
        quiet_start=rule.quiet_hours_start,
        quiet_end=rule.quiet_hours_end,
        timezone_name=tz,
    )

    if result == CheckResult.DOWN.value:
        if open_incident is None:
            email_config = await _load_email_config(session, monitor.id)
            threshold = (
                email_config.failure_threshold
                if email_config is not None and email_config.enabled
                else 3
            )
            consecutive_down, first_down_at = await _consecutive_down_info(
                session,
                monitor_id=monitor.id,
                current_check_id=check.id,
            )

            if consecutive_down < threshold:
                logger.info(
                    "falha_abaixo_do_threshold",
                    monitor_id=monitor.id,
                    consecutive_down=consecutive_down,
                    threshold=threshold,
                )
                return None

            incident = Incident(
                monitor_id=monitor.id,
                started_at=first_down_at or checked_at,
                failure_count=consecutive_down,
                last_error=_error_text(check),
                status="open",
            )
            session.add(incident)
            await session.flush()
            await session.refresh(incident)
            logger.info("incidente_aberto", incident_id=incident.id, monitor_id=monitor.id)

            if rule.on_down and not in_quiet:
                duration = policy.format_duration(
                    max(0, int((now - incident.started_at).total_seconds()))
                )
                values = {
                    "monitor_name": monitor.name,
                    "url": monitor.url,
                    "started_at": policy.to_local_str(incident.started_at, tz),
                    "error": _error_text(check),
                    "duration": duration,
                    "duration_so_far": duration,
                    "dashboard_url": _dashboard_url(monitor.id),
                    "failure_count": incident.failure_count,
                    "status_code": check.status_code or "",
                }
                if email_config is not None and email_config.enabled:
                    content = _custom_email_content(
                        subject_template=email_config.down_subject,
                        body_template=email_config.down_body,
                        values=values,
                        title="FORA DO AR",
                        badge_color="#f87171",
                    )
                else:
                    content = build_down_email(
                        monitor_name=monitor.name,
                        url=monitor.url,
                        started_at_local=policy.to_local_str(incident.started_at, tz),
                        error=_error_text(check),
                        duration_so_far=duration,
                        dashboard_url=_dashboard_url(monitor.id),
                    )
                await _try_notify(
                    session, monitor=monitor, incident=incident, content=content
                )
            return incident

        open_incident.failure_count += 1
        open_incident.last_error = _error_text(check)
        await session.flush()

        email_config = await _load_email_config(session, monitor.id)
        reminder_minutes = (
            email_config.reminder_minutes
            if email_config is not None and email_config.enabled
            else rule.reminder_minutes
        )
        min_interval_minutes = (
            reminder_minutes
            if email_config is not None and email_config.enabled and reminder_minutes
            else rule.min_interval_minutes
        )
        should_notify_open_incident = policy.should_send_reminder(
            last_notified_at=open_incident.last_notified_at,
            now_utc=now,
            reminder_minutes=reminder_minutes,
            min_interval_minutes=min_interval_minutes,
        ) or _changed_after_last_notification(
            email_config,
            open_incident.last_notified_at,
        )
        if rule.on_down and not in_quiet and should_notify_open_incident:
            duration = policy.format_duration(
                max(0, int((now - open_incident.started_at).total_seconds()))
            )
            values = {
                "monitor_name": monitor.name,
                "url": monitor.url,
                "started_at": policy.to_local_str(open_incident.started_at, tz),
                "error": _error_text(check),
                "duration": duration,
                "duration_so_far": duration,
                "dashboard_url": _dashboard_url(monitor.id),
                "failure_count": open_incident.failure_count,
                "status_code": check.status_code or "",
            }
            if email_config is not None and email_config.enabled:
                content = _custom_email_content(
                    subject_template=email_config.down_subject,
                    body_template=email_config.down_body,
                    values=values,
                    title="AINDA FORA DO AR",
                    badge_color="#fb923c",
                )
            else:
                content = build_reminder_email(
                    monitor_name=monitor.name,
                    url=monitor.url,
                    started_at_local=policy.to_local_str(open_incident.started_at, tz),
                    error=_error_text(check),
                    duration_so_far=duration,
                    failure_count=open_incident.failure_count,
                    dashboard_url=_dashboard_url(monitor.id),
                )
            await _try_notify(
                session, monitor=monitor, incident=open_incident, content=content
            )
        return open_incident

    if result == CheckResult.UP.value:
        if open_incident is not None:
            open_incident.resolved_at = checked_at
            open_incident.duration_seconds = max(
                0,
                int((checked_at - open_incident.started_at).total_seconds()),
            )
            open_incident.status = "closed"
            await session.flush()
            logger.info(
                "incidente_fechado",
                incident_id=open_incident.id,
                monitor_id=monitor.id,
                duration_seconds=open_incident.duration_seconds,
            )

            if rule.on_recovery and not in_quiet:
                email_config = await _load_email_config(session, monitor.id)
                duration = policy.format_duration(open_incident.duration_seconds or 0)
                values = {
                    "monitor_name": monitor.name,
                    "url": monitor.url,
                    "started_at": policy.to_local_str(open_incident.started_at, tz),
                    "resolved_at": policy.to_local_str(checked_at, tz),
                    "duration": duration,
                    "dashboard_url": _dashboard_url(monitor.id),
                    "failure_count": open_incident.failure_count,
                    "status_code": check.status_code or "",
                    "error": _error_text(check),
                }
                if email_config is not None and email_config.enabled:
                    content = _custom_email_content(
                        subject_template=email_config.recovery_subject,
                        body_template=email_config.recovery_body,
                        values=values,
                        title="RESTABELECIDO",
                        badge_color="#4ade80",
                    )
                else:
                    content = build_recovery_email(
                        monitor_name=monitor.name,
                        url=monitor.url,
                        started_at_local=policy.to_local_str(open_incident.started_at, tz),
                        resolved_at_local=policy.to_local_str(checked_at, tz),
                        duration=duration,
                        dashboard_url=_dashboard_url(monitor.id),
                    )
                await _try_notify(
                    session, monitor=monitor, incident=open_incident, content=content
                )
            return open_incident
        return None

    if result == CheckResult.DEGRADED.value:
        prev_was_degraded = (
            previous is not None and previous.result == CheckResult.DEGRADED.value
        )
        # Notifica só na transição para DEGRADED (evita flood sem incidente)
        if rule.on_degraded and not in_quiet and not prev_was_degraded:
            content = build_degraded_email(
                monitor_name=monitor.name,
                url=monitor.url,
                checked_at_local=policy.to_local_str(checked_at, tz),
                detail=_error_text(check),
                dashboard_url=_dashboard_url(monitor.id),
            )
            await _try_notify(session, monitor=monitor, incident=None, content=content)
        return open_incident

    return open_incident


async def list_incidents(
    session: AsyncSession,
    *,
    status: str | None = None,
    monitor_id: int | None = None,
) -> list[Incident]:
    filters = []
    if status:
        filters.append(Incident.status == status.lower())
    if monitor_id is not None:
        filters.append(Incident.monitor_id == monitor_id)
    stmt = (
        select(Incident)
        .options(selectinload(Incident.monitor))
        .where(*filters)
        .order_by(desc(Incident.started_at))
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_incident(session: AsyncSession, incident_id: int) -> Incident | None:
    stmt = (
        select(Incident)
        .options(selectinload(Incident.monitor))
        .where(Incident.id == incident_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()
