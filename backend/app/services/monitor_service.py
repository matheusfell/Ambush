"""Serviço de domínio para monitores."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt
from app.models.check import Check
from app.models.monitor import Monitor
from app.schemas.monitor import MonitorCreate, MonitorRead, MonitorUpdate


def _to_read(monitor: Monitor, last_check: Check | None = None) -> MonitorRead:
    data = MonitorRead.model_validate(monitor)
    data.has_basic_auth_pass = bool(monitor.basic_auth_pass_encrypted)
    if last_check is not None:
        data.last_result = last_check.result
        data.last_checked_at = last_check.checked_at
        data.last_response_time_ms = last_check.response_time_ms
    return data


async def create_monitor(session: AsyncSession, payload: MonitorCreate) -> Monitor:
    encrypted: str | None = None
    if payload.basic_auth_pass:
        encrypted = encrypt(payload.basic_auth_pass)

    monitor = Monitor(
        name=payload.name,
        url=str(payload.url),
        method=payload.method,
        interval_seconds=payload.interval_seconds,
        timeout_seconds=payload.timeout_seconds,
        expected_status=list(payload.expected_status),
        expected_body_contains=payload.expected_body_contains,
        headers=payload.headers,
        body=payload.body,
        basic_auth_user=payload.basic_auth_user,
        basic_auth_pass_encrypted=encrypted,
        skip_tls_verify=payload.skip_tls_verify,
        follow_redirects=payload.follow_redirects,
        retries=payload.retries,
        slow_threshold_ms=payload.slow_threshold_ms,
        enabled=payload.enabled,
        tags=list(payload.tags),
        notification_group_id=payload.notification_group_id,
    )
    session.add(monitor)
    await session.flush()
    await session.refresh(monitor)
    return monitor


async def get_monitor(session: AsyncSession, monitor_id: int) -> Monitor | None:
    return await session.get(Monitor, monitor_id)


async def list_monitors(session: AsyncSession) -> list[MonitorRead]:
    stmt: Select[tuple[Monitor]] = select(Monitor).order_by(Monitor.id)
    result = await session.execute(stmt)
    monitors = list(result.scalars().all())

    reads: list[MonitorRead] = []
    for monitor in monitors:
        last_stmt = (
            select(Check)
            .where(Check.monitor_id == monitor.id)
            .order_by(desc(Check.checked_at))
            .limit(1)
        )
        last_result = await session.execute(last_stmt)
        last_check = last_result.scalar_one_or_none()
        reads.append(_to_read(monitor, last_check))
    return reads


async def update_monitor(
    session: AsyncSession,
    monitor: Monitor,
    payload: MonitorUpdate,
) -> Monitor:
    data: dict[str, Any] = payload.model_dump(exclude_unset=True)

    if "basic_auth_pass" in data:
        password = data.pop("basic_auth_pass")
        if password is None or password == "":
            monitor.basic_auth_pass_encrypted = None
        else:
            monitor.basic_auth_pass_encrypted = encrypt(password)

    if "url" in data and data["url"] is not None:
        data["url"] = str(data["url"])

    for key, value in data.items():
        setattr(monitor, key, value)

    monitor.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(monitor)
    return monitor


async def delete_monitor(session: AsyncSession, monitor: Monitor) -> None:
    await session.delete(monitor)
    await session.flush()


async def toggle_monitor(session: AsyncSession, monitor: Monitor) -> Monitor:
    monitor.enabled = not monitor.enabled
    monitor.updated_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(monitor)
    return monitor


async def list_enabled_monitors(session: AsyncSession) -> list[Monitor]:
    stmt = select(Monitor).where(Monitor.enabled.is_(True)).order_by(Monitor.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


def monitor_to_read(monitor: Monitor, last_check: Check | None = None) -> MonitorRead:
    return _to_read(monitor, last_check)
