"""Schemas de configuração de envio de e-mail."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

DeliveryMethod = Literal["graph", "smtp"]


class SmtpSettingsUpdate(BaseModel):
    delivery_method: DeliveryMethod | None = None

    graph_tenant_id: str | None = Field(default=None, max_length=255)
    graph_client_id: str | None = Field(default=None, max_length=255)
    graph_client_secret: str | None = None

    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    from_email: EmailStr | None = None
    from_name: str | None = Field(default=None, max_length=255)
    use_tls: bool | None = None


class SmtpSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    delivery_method: str
    graph_tenant_id: str | None
    graph_client_id: str | None
    has_graph_client_secret: bool = False
    host: str
    port: int
    username: str | None
    has_password: bool = False
    from_email: str
    from_name: str
    use_tls: bool
    updated_at: datetime


class SmtpTestRequest(BaseModel):
    to_email: EmailStr
