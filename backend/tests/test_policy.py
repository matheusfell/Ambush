"""Testes de quiet hours, anti-flood e lembrete."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from app.notifier.policy import (
    can_send_notification,
    format_duration,
    is_in_quiet_hours,
    should_send_reminder,
)


def test_quiet_hours_janela_simples() -> None:
    # 10:00 SP está dentro de 08:00–18:00
    now = datetime(2026, 8, 4, 13, 0, tzinfo=UTC)  # 10:00 SP (UTC-3)
    assert is_in_quiet_hours(
        now,
        quiet_start=time(8, 0),
        quiet_end=time(18, 0),
        timezone_name="America/Sao_Paulo",
    )


def test_quiet_hours_fora_da_janela() -> None:
    now = datetime(2026, 8, 4, 3, 0, tzinfo=UTC)  # 00:00 SP
    assert not is_in_quiet_hours(
        now,
        quiet_start=time(8, 0),
        quiet_end=time(18, 0),
        timezone_name="America/Sao_Paulo",
    )


def test_quiet_hours_cruza_meia_noite() -> None:
    # 23:00 SP → dentro de 22:00–06:00
    now = datetime(2026, 8, 5, 2, 0, tzinfo=UTC)  # 23:00 SP
    assert is_in_quiet_hours(
        now,
        quiet_start=time(22, 0),
        quiet_end=time(6, 0),
        timezone_name="America/Sao_Paulo",
    )
    # 12:00 SP → fora
    noon = datetime(2026, 8, 4, 15, 0, tzinfo=UTC)
    assert not is_in_quiet_hours(
        noon,
        quiet_start=time(22, 0),
        quiet_end=time(6, 0),
        timezone_name="America/Sao_Paulo",
    )


def test_quiet_hours_desligado() -> None:
    now = datetime(2026, 8, 4, 13, 0, tzinfo=UTC)
    assert not is_in_quiet_hours(
        now, quiet_start=None, quiet_end=None, timezone_name="America/Sao_Paulo"
    )


def test_anti_flood_primeira_vez() -> None:
    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    assert can_send_notification(
        last_notified_at=None, now_utc=now, min_interval_minutes=30
    )


def test_anti_flood_bloqueia_dentro_do_intervalo() -> None:
    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=10)
    assert not can_send_notification(
        last_notified_at=last, now_utc=now, min_interval_minutes=30
    )


def test_anti_flood_libera_apos_intervalo() -> None:
    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=31)
    assert can_send_notification(
        last_notified_at=last, now_utc=now, min_interval_minutes=30
    )


def test_reminder_desligado() -> None:
    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    assert not should_send_reminder(
        last_notified_at=now - timedelta(hours=2),
        now_utc=now,
        reminder_minutes=None,
        min_interval_minutes=30,
    )


def test_reminder_apos_espera() -> None:
    now = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    last = now - timedelta(minutes=60)
    assert should_send_reminder(
        last_notified_at=last,
        now_utc=now,
        reminder_minutes=45,
        min_interval_minutes=30,
    )


def test_format_duration() -> None:
    assert format_duration(45) == "45 segundos"
    assert format_duration(14 * 60) == "14 minutos"
    assert format_duration(2 * 3600) == "2 horas"
