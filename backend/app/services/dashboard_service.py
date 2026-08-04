"""Agregações para o dashboard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check import Check
from app.models.monitor import Monitor
from app.schemas.dashboard import DashboardSummary, MonitorCard, MonitorHistoryItem

HISTORY_LIMIT = 60


async def get_dashboard_summary(session: AsyncSession) -> DashboardSummary:
    monitors = list(
        (await session.execute(select(Monitor).order_by(Monitor.name))).scalars().all()
    )
    since = datetime.now(UTC) - timedelta(hours=24)

    cards: list[MonitorCard] = []
    up = degraded = down = paused = unknown = 0

    for monitor in monitors:
        last_stmt = (
            select(Check)
            .where(Check.monitor_id == monitor.id)
            .order_by(desc(Check.checked_at))
            .limit(1)
        )
        last = (await session.execute(last_stmt)).scalar_one_or_none()

        hist_stmt = (
            select(Check)
            .where(Check.monitor_id == monitor.id)
            .order_by(desc(Check.checked_at))
            .limit(HISTORY_LIMIT)
        )
        history_rows = list((await session.execute(hist_stmt)).scalars().all())
        # Ordem cronológica na barra (mais antigo → mais recente)
        history = [
            MonitorHistoryItem(
                id=row.id,
                result=row.result,
                checked_at=row.checked_at,
            )
            for row in reversed(history_rows)
        ]

        # Uptime 24h: % de checagens UP ou DEGRADED
        stats_stmt = (
            select(Check.result, func.count())
            .where(Check.monitor_id == monitor.id, Check.checked_at >= since)
            .group_by(Check.result)
        )
        counts: dict[str, int] = {
            str(row[0]): int(row[1])
            for row in (await session.execute(stats_stmt)).all()
        }
        total_24h = sum(counts.values())
        ok_24h = counts.get("UP", 0) + counts.get("DEGRADED", 0)
        uptime: float | None = (
            round(100.0 * ok_24h / total_24h, 2) if total_24h > 0 else None
        )

        current = last.result if last else None
        next_check_at: datetime | None = None
        if monitor.enabled:
            if last is None:
                next_check_at = datetime.now(UTC)
            else:
                scheduled_at = last.checked_at + timedelta(
                    seconds=monitor.interval_seconds
                )
                next_check_at = max(scheduled_at, datetime.now(UTC))

        if not monitor.enabled:
            paused += 1
        elif current == "UP":
            up += 1
        elif current == "DEGRADED":
            degraded += 1
        elif current == "DOWN":
            down += 1
        else:
            unknown += 1

        cards.append(
            MonitorCard(
                id=monitor.id,
                name=monitor.name,
                url=monitor.url,
                enabled=monitor.enabled,
                interval_seconds=monitor.interval_seconds,
                tags=list(monitor.tags or []),
                current_result=current,
                last_checked_at=last.checked_at if last else None,
                next_check_at=next_check_at,
                last_response_time_ms=last.response_time_ms if last else None,
                uptime_24h_percent=uptime,
                history=history,
            )
        )

    return DashboardSummary(
        up=up,
        degraded=degraded,
        down=down,
        paused=paused,
        unknown=unknown,
        monitors=cards,
    )
