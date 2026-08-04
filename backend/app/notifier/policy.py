"""Regras de quiet hours e anti-flood (funções puras — fáceis de testar)."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo


def is_in_quiet_hours(
    now_utc: datetime,
    *,
    quiet_start: time | None,
    quiet_end: time | None,
    timezone_name: str,
) -> bool:
    """
    Retorna True se o horário local atual está na janela de silêncio.

    Suporta janela que cruza meia-noite (ex.: 22:00–06:00).
    Sem start/end configurados → nunca em quiet hours.
    """
    if quiet_start is None or quiet_end is None:
        return False

    local_now = now_utc.astimezone(ZoneInfo(timezone_name)).time()

    if quiet_start <= quiet_end:
        # Ex.: 08:00–18:00
        return quiet_start <= local_now < quiet_end

    # Cruza meia-noite: 22:00–06:00 → silêncio se >= 22 ou < 06
    return local_now >= quiet_start or local_now < quiet_end


def can_send_notification(
    *,
    last_notified_at: datetime | None,
    now_utc: datetime,
    min_interval_minutes: int,
) -> bool:
    """Anti-flood: True se nunca notificou ou já passou o intervalo mínimo."""
    if last_notified_at is None:
        return True
    last = last_notified_at if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=UTC)
    elapsed = now_utc - last
    return elapsed >= timedelta(minutes=min_interval_minutes)


def should_send_reminder(
    *,
    last_notified_at: datetime | None,
    now_utc: datetime,
    reminder_minutes: int | None,
    min_interval_minutes: int,
) -> bool:
    """Lembrete enquanto incidente aberto: respeita reminder e anti-flood."""
    if reminder_minutes is None or reminder_minutes <= 0:
        return False
    if last_notified_at is None:
        return True
    last = last_notified_at if last_notified_at.tzinfo else last_notified_at.replace(tzinfo=UTC)
    # Usa o maior entre reminder e min_interval para não floodar
    wait = max(reminder_minutes, min_interval_minutes)
    return (now_utc - last) >= timedelta(minutes=wait)


def format_duration(seconds: int) -> str:
    """Formata duração em português curto (ex.: '14 minutos')."""
    if seconds < 60:
        return f"{seconds} segundo{'s' if seconds != 1 else ''}"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minuto{'s' if minutes != 1 else ''}"
    hours = minutes // 60
    rem = minutes % 60
    if rem == 0:
        return f"{hours} hora{'s' if hours != 1 else ''}"
    return f"{hours}h {rem}min"


def to_local_str(dt: datetime, timezone_name: str) -> str:
    """Datetime UTC → string local America/Sao_Paulo."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    local = dt.astimezone(ZoneInfo(timezone_name))
    return local.strftime("%d/%m/%Y %H:%M:%S %Z")
