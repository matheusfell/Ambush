"""Grupo de destinatários de notificação."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.monitor import Monitor


class NotificationGroup(Base):
    """Lista nomeada de e-mails para alertas."""

    __tablename__ = "notification_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    emails: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: [],
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    monitors: Mapped[list[Monitor]] = relationship(
        "Monitor",
        back_populates="notification_group",
    )

    def __repr__(self) -> str:
        return f"<NotificationGroup id={self.id} name={self.name!r}>"
