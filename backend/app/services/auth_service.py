"""Serviço de autenticação e usuários."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate

logger = get_logger(__name__)


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def authenticate(
    session: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    user = await get_user_by_username(session, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def issue_token(user: User) -> str:
    return create_access_token(subject=user.username, role=user.role, user_id=user.id)


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    existing = await get_user_by_username(session, payload.username)
    if existing is not None:
        raise ValueError("Username já existe")
    if payload.role not in {"admin", "viewer"}:
        raise ValueError("Role inválida")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def list_users(session: AsyncSession) -> list[User]:
    stmt = select(User).order_by(User.id)
    return list((await session.execute(stmt)).scalars().all())


async def ensure_admin_seed(session: AsyncSession) -> None:
    """Cria admin inicial se a tabela users estiver vazia."""
    count = int((await session.execute(select(func.count()).select_from(User))).scalar_one())
    if count > 0:
        return
    settings = get_settings()
    user = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        role="admin",
    )
    session.add(user)
    await session.commit()
    logger.info("admin_seed_criado", username=settings.admin_username)
