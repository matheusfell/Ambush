"""Schemas do dashboard."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MonitorHistoryItem(BaseModel):
    id: int
    result: str
    checked_at: datetime


class MonitorCard(BaseModel):
    id: int
    name: str
    url: str
    enabled: bool
    interval_seconds: int
    tags: list[str]
    current_result: str | None
    last_checked_at: datetime | None
    next_check_at: datetime | None
    last_response_time_ms: int | None
    uptime_24h_percent: float | None
    history: list[MonitorHistoryItem]


class DashboardSummary(BaseModel):
    up: int
    degraded: int
    down: int
    paused: int
    unknown: int
    monitors: list[MonitorCard]
