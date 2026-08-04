"""API de grupos de notificação e regras globais."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser, CurrentUser
from app.database import get_db
from app.schemas.notification import (
    NotificationGroupCreate,
    NotificationGroupRead,
    NotificationGroupUpdate,
    NotificationRuleRead,
    NotificationRuleUpdate,
)
from app.services import notification_service

router = APIRouter(tags=["notifications"])


@router.get("/notification-groups", response_model=list[NotificationGroupRead])
async def list_groups(
    _user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[NotificationGroupRead]:
    rows = await notification_service.list_groups(db)
    return [NotificationGroupRead.model_validate(r) for r in rows]


@router.post(
    "/notification-groups",
    response_model=NotificationGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    payload: NotificationGroupCreate,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> NotificationGroupRead:
    group = await notification_service.create_group(db, payload)
    return NotificationGroupRead.model_validate(group)


@router.put("/notification-groups/{group_id}", response_model=NotificationGroupRead)
async def update_group(
    group_id: int,
    payload: NotificationGroupUpdate,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> NotificationGroupRead:
    group = await notification_service.get_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado")
    group = await notification_service.update_group(db, group, payload)
    return NotificationGroupRead.model_validate(group)


@router.delete("/notification-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    group = await notification_service.get_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo não encontrado")
    await notification_service.delete_group(db, group)


@router.get("/settings/notification-rules", response_model=NotificationRuleRead)
async def get_notification_rules(
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> NotificationRuleRead:
    rule = await notification_service.get_or_create_global_rule(db)
    return NotificationRuleRead.model_validate(rule)


@router.put("/settings/notification-rules", response_model=NotificationRuleRead)
async def update_notification_rules(
    payload: NotificationRuleUpdate,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> NotificationRuleRead:
    rule = await notification_service.update_global_rule(db, payload)
    return NotificationRuleRead.model_validate(rule)
