"""Configuração via variáveis de ambiente (pydantic-settings)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    """Configuração da aplicação carregada do ambiente / `.env`."""

    model_config = SettingsConfigDict(
        env_file=(
            _PROJECT_ROOT / ".env",
            _BACKEND_DIR / ".env",
            Path(".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://ambush:ambush@localhost:5432/ambush",
        description="URL async do PostgreSQL (postgresql+asyncpg://...)",
    )
    encryption_key: str = Field(
        default="",
        description="Chave Fernet (base64) para criptografar senhas sensíveis",
    )
    check_concurrency: int = Field(default=20, ge=1, le=200)
    log_level: str = Field(default="INFO")
    app_timezone: str = Field(default="America/Sao_Paulo")
    # Base URL do dashboard (links nos e-mails). Fase 3 terá o frontend.
    app_base_url: str = Field(default="http://localhost:5173")
    jwt_secret: str = Field(
        default="change-me-in-production-use-long-random-string",
        description="Segredo HMAC para assinar JWT",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60 * 12, ge=5)
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Origens CORS separadas por vírgula",
    )
    admin_username: str = Field(default="admin")
    admin_password: str = Field(
        default="admin123",
        description="Senha do admin seed (apenas se não houver usuários)",
    )
    o365_tenant_id: str = Field(default="")
    o365_client_id: str = Field(default="")
    o365_client_secret: str = Field(default="")
    email_from_addr: str = Field(default="")
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = Field(default="")
    smtp_pass: str = Field(default="")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()


@lru_cache
def get_settings() -> Settings:
    """Retorna settings em cache (singleton por processo)."""
    return Settings()
