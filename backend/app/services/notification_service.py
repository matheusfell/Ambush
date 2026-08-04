"""CRUD de grupos de notificação e regras."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_group import NotificationGroup
from app.models.notification_rule import NotificationRule
from app.schemas.notification import (
    NotificationGroupCreate,
    NotificationGroupUpdate,
    NotificationRuleUpdate,
)


async def list_groups(session: AsyncSession) -> list[NotificationGroup]:
    stmt = select(NotificationGroup).order_by(NotificationGroup.id)
    return list((await session.execute(stmt)).scalars().all())


async def get_group(session: AsyncSession, group_id: int) -> NotificationGroup | None:
    return await session.get(NotificationGroup, group_id)


async def create_group(
    session: AsyncSession,
    payload: NotificationGroupCreate,
) -> NotificationGroup:
    group = NotificationGroup(name=payload.name, emails=list(payload.emails))
    session.add(group)
    await session.flush()
    await session.refresh(group)
    return group


async def update_group(
    session: AsyncSession,
    group: NotificationGroup,
    payload: NotificationGroupUpdate,
) -> NotificationGroup:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(group, key, value)
    await session.flush()
    await session.refresh(group)
    return group


async def delete_group(session: AsyncSession, group: NotificationGroup) -> None:
    await session.delete(group)
    await session.flush()


async def get_or_create_global_rule(session: AsyncSession) -> NotificationRule:
    rule = (
        await session.execute(
            select(NotificationRule).where(NotificationRule.monitor_id.is_(None))
        )
    ).scalar_one_or_none()
    if rule is None:
        rule = NotificationRule(
            monitor_id=None,
            on_down=True,
            on_recovery=True,
            on_degraded=False,
            min_interval_minutes=30,
        )
        session.add(rule)
        await session.flush()
        await session.refresh(rule)
    return rule


async def update_global_rule(
    session: AsyncSession,
    payload: NotificationRuleUpdate,
) -> NotificationRule:
    rule = await get_or_create_global_rule(session)
    data: dict[str, Any] = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(rule, key, value)
    await session.flush()
    await session.refresh(rule)
    return rule
