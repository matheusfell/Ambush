"""Model SQLAlchemy do monitor (alvo de checagem)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.check import Check
    from app.models.incident import Incident
    from app.models.notification_group import NotificationGroup


class Monitor(Base):
    """Sistema a ser verificado periodicamente."""

    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="GET")
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    expected_status: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=lambda: [200],
    )
    expected_body_contains: Mapped[str | None] = mapped_column(Text, nullable=True)
    headers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    basic_auth_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    basic_auth_pass_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    skip_tls_verify: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    follow_redirects: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    slow_threshold_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=3000)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: [],
    )
    notification_group_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("notification_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    checks: Mapped[list[Check]] = relationship(
        "Check",
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    incidents: Mapped[list[Incident]] = relationship(
        "Incident",
        back_populates="monitor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notification_group: Mapped[NotificationGroup | None] = relationship(
        "NotificationGroup",
        back_populates="monitors",
    )

    def __repr__(self) -> str:
        return f"<Monitor id={self.id} name={self.name!r} enabled={self.enabled}>"
