"""Schemas de configuração de e-mail por monitor."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailNotificationConfigUpsert(BaseModel):
    monitor_id: int
    enabled: bool = True
    emails: list[EmailStr] = Field(default_factory=list)
    failure_threshold: int = Field(default=3, ge=1, le=20)
    reminder_minutes: int = Field(default=30, ge=0, le=1440)
    down_subject: str = Field(default="[FORA DO AR] {monitor_name}", min_length=1, max_length=255)
    down_body: str = Field(
        default=(
            "O monitor {monitor_name} está fora do ar.\n\n"
            "URL: {url}\nErro: {error}\nFalhas consecutivas: {failure_count}\n"
            "Dashboard: {dashboard_url}"
        ),
        min_length=1,
    )
    recovery_subject: str = Field(
        default="[RESTABELECIDO] {monitor_name}",
        min_length=1,
        max_length=255,
    )
    recovery_body: str = Field(
        default=(
            "O monitor {monitor_name} voltou ao ar.\n\n"
            "URL: {url}\nDuração: {duration}\nDashboard: {dashboard_url}"
        ),
        min_length=1,
    )


class EmailNotificationConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: int
    enabled: bool
    emails: list[str]
    failure_threshold: int
    reminder_minutes: int
    down_subject: str
    down_body: str
    recovery_subject: str
    recovery_body: str
    updated_at: datetime
