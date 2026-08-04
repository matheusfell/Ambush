"""Regras de notificação (global ou por monitor)."""

from __future__ import annotations

from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationRule(Base):
    """
    Controla quais eventos disparam e-mail e o anti-flood.

    ``monitor_id`` nulo = regra global (fallback).
    Regra específica do monitor tem precedência.
    """

    __tablename__ = "notification_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )
    on_down: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    on_recovery: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    on_degraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    reminder_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    def __repr__(self) -> str:
        return f"<NotificationRule id={self.id} monitor_id={self.monitor_id}>"
