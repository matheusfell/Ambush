"""Schemas de grupos e regras de notificação."""

from __future__ import annotations

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class NotificationGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    emails: list[EmailStr] = Field(..., min_length=1)


class NotificationGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    emails: list[EmailStr] | None = Field(default=None, min_length=1)


class NotificationGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    emails: list[str]
    created_at: datetime


class NotificationRuleUpdate(BaseModel):
    on_down: bool | None = None
    on_recovery: bool | None = None
    on_degraded: bool | None = None
    min_interval_minutes: int | None = Field(default=None, ge=1, le=24 * 60)
    reminder_minutes: int | None = Field(default=None, ge=1, le=24 * 60)
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None

    @field_validator("reminder_minutes")
    @classmethod
    def allow_clear_reminder(cls, value: int | None) -> int | None:
        return value


class NotificationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: int | None
    on_down: bool
    on_recovery: bool
    on_degraded: bool
    min_interval_minutes: int
    reminder_minutes: int | None
    quiet_hours_start: time | None
    quiet_hours_end: time | None
