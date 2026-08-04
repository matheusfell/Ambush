"""Hash de senha (bcrypt) e JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(*, subject: str, role: str, user_id: int) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "uid": user_id,
        "exp": expire,
    }
    encoded: str = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if not isinstance(payload, dict):
            raise ValueError("Token inválido ou expirado")
        return dict(payload)
    except JWTError as exc:
        raise ValueError("Token inválido ou expirado") from exc
