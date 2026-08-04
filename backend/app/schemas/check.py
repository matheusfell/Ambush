"""Schemas Pydantic de checagens."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckRead(BaseModel):
    """Registro de checagem retornado pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: int
    checked_at: datetime
    status_code: int | None
    response_time_ms: int | None
    result: str
    error_message: str | None
    attempt_count: int


class CheckListResponse(BaseModel):
    """Lista paginada de checagens."""

    items: list[CheckRead]
    total: int
    page: int
    page_size: int


class CheckQueryParams(BaseModel):
    """Filtros de listagem de checagens."""

    result: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
