"""Schemas do dashboard."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MonitorCard(BaseModel):
    id: int
    name: str
    url: str
    enabled: bool
    tags: list[str]
    current_result: str | None
    last_checked_at: datetime | None
    last_response_time_ms: int | None
    uptime_24h_percent: float | None
    history: list[str]  # últimos N resultados: UP|DEGRADED|DOWN


class DashboardSummary(BaseModel):
    up: int
    degraded: int
    down: int
    paused: int
    unknown: int
    monitors: list[MonitorCard]
