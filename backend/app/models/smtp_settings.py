"""Configuração de envio de e-mail persistida (secrets criptografados)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SmtpSettings(Base):
    """Única linha de configuração de envio (Graph recomendado, SMTP legado)."""

    __tablename__ = "smtp_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_method: Mapped[str] = mapped_column(String(20), nullable=False, default="graph")

    graph_tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graph_client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graph_client_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    host: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    from_name: Mapped[str] = mapped_column(String(255), nullable=False, default="AmbushSystem")
    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<EmailSettings method={self.delivery_method!r} from={self.from_email!r}>"
