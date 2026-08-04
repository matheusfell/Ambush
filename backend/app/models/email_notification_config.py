"""Configuração de e-mail por monitor."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.monitor import Monitor


class EmailNotificationConfig(Base):
    """Destinatários, threshold e templates por monitor."""

    __tablename__ = "email_notification_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    emails: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: [],
    )
    failure_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    reminder_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    down_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="[FORA DO AR] {monitor_name}",
    )
    down_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "O monitor {monitor_name} está fora do ar.\n\n"
            "URL: {url}\nErro: {error}\nFalhas consecutivas: {failure_count}\n"
            "Dashboard: {dashboard_url}"
        ),
    )
    recovery_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="[RESTABELECIDO] {monitor_name}",
    )
    recovery_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "O monitor {monitor_name} voltou ao ar.\n\n"
            "URL: {url}\nDuração: {duration}\nDashboard: {dashboard_url}"
        ),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    monitor: Mapped[Monitor] = relationship("Monitor")
