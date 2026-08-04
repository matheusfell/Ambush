"""Schemas Pydantic de monitores (entrada e saída separados dos models)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

HttpMethod = Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]


class MonitorCreate(BaseModel):
    """Payload para criar um monitor."""

    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    method: HttpMethod = "GET"
    interval_seconds: int = Field(default=300, ge=30)
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    expected_status: list[int] = Field(default_factory=lambda: [200])
    expected_body_contains: str | None = None
    headers: dict[str, Any] | None = None
    body: str | None = None
    basic_auth_user: str | None = None
    basic_auth_pass: str | None = None
    skip_tls_verify: bool = False
    follow_redirects: bool = True
    retries: int = Field(default=2, ge=0, le=10)
    slow_threshold_ms: int = Field(default=3000, ge=1)
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    notification_group_id: int | None = None

    @field_validator("expected_status")
    @classmethod
    def validate_expected_status(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("expected_status não pode ser vazio")
        for code in value:
            if code < 100 or code > 599:
                raise ValueError(f"Status HTTP inválido: {code}")
        return value

    @field_validator("method")
    @classmethod
    def uppercase_method(cls, value: str) -> str:
        return value.upper()


class MonitorUpdate(BaseModel):
    """Payload parcial/total para atualizar um monitor."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    method: HttpMethod | None = None
    interval_seconds: int | None = Field(default=None, ge=30)
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    expected_status: list[int] | None = None
    expected_body_contains: str | None = None
    headers: dict[str, Any] | None = None
    body: str | None = None
    basic_auth_user: str | None = None
    basic_auth_pass: str | None = None
    skip_tls_verify: bool | None = None
    follow_redirects: bool | None = None
    retries: int | None = Field(default=None, ge=0, le=10)
    slow_threshold_ms: int | None = Field(default=None, ge=1)
    enabled: bool | None = None
    tags: list[str] | None = None
    notification_group_id: int | None = None

    @field_validator("expected_status")
    @classmethod
    def validate_expected_status(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        if not value:
            raise ValueError("expected_status não pode ser vazio")
        for code in value:
            if code < 100 or code > 599:
                raise ValueError(f"Status HTTP inválido: {code}")
        return value

    @field_validator("method")
    @classmethod
    def uppercase_method(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class MonitorRead(BaseModel):
    """Representação pública de um monitor (sem senha em claro)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    method: str
    interval_seconds: int
    timeout_seconds: int
    expected_status: list[int]
    expected_body_contains: str | None
    headers: dict[str, Any] | None
    body: str | None
    basic_auth_user: str | None
    has_basic_auth_pass: bool = False
    skip_tls_verify: bool
    follow_redirects: bool
    retries: int
    slow_threshold_ms: int
    enabled: bool
    tags: list[str]
    notification_group_id: int | None = None
    created_at: datetime
    updated_at: datetime
    # Preenchido opcionalmente na listagem
    last_result: str | None = None
    last_checked_at: datetime | None = None
    last_response_time_ms: int | None = None
