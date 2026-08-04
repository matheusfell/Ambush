"""Schemas de incidentes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: int
    monitor_name: str | None = None
    started_at: datetime
    resolved_at: datetime | None
    duration_seconds: int | None
    failure_count: int
    last_error: str | None
    last_notified_at: datetime | None
    status: str
