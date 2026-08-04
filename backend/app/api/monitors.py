"""CRUD de monitores + checagem manual + toggle."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import AdminUser, CurrentUser
from app.database import get_db
from app.scheduler.scheduler import scheduler
from app.schemas.check import CheckListResponse, CheckRead
from app.schemas.monitor import MonitorCreate, MonitorRead, MonitorUpdate
from app.services import check_service, monitor_service

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.get("", response_model=list[MonitorRead])
async def list_monitors(
    _user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[MonitorRead]:
    return await monitor_service.list_monitors(db)


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    payload: MonitorCreate,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MonitorRead:
    monitor = await monitor_service.create_monitor(db, payload)
    await db.commit()
    await db.refresh(monitor)
    scheduler.sync_monitor(monitor)
    return monitor_service.monitor_to_read(monitor)


@router.get("/{monitor_id}", response_model=MonitorRead)
async def get_monitor(
    monitor_id: int,
    _user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> MonitorRead:
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor não encontrado")
    return monitor_service.monitor_to_read(monitor)


@router.put("/{monitor_id}", response_model=MonitorRead)
async def update_monitor(
    monitor_id: int,
    payload: MonitorUpdate,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MonitorRead:
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor não encontrado")
    monitor = await monitor_service.update_monitor(db, monitor, payload)
    await db.commit()
    await db.refresh(monitor)
    scheduler.sync_monitor(monitor)
    return monitor_service.monitor_to_read(monitor)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: int,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor não encontrado")
    scheduler.remove_monitor(monitor_id)
    await monitor_service.delete_monitor(db, monitor)
    await db.commit()


@router.patch("/{monitor_id}/toggle", response_model=MonitorRead)
async def toggle_monitor(
    monitor_id: int,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MonitorRead:
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor não encontrado")
    monitor = await monitor_service.toggle_monitor(db, monitor)
    await db.commit()
    await db.refresh(monitor)
    scheduler.sync_monitor(monitor)
    return monitor_service.monitor_to_read(monitor)


@router.post("/{monitor_id}/check", response_model=CheckRead)
async def check_now(
    monitor_id: int,
    _admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> CheckRead:
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor não encontrado")
    check = await check_service.run_and_persist_check(db, monitor)
    return CheckRead.model_validate(check)


@router.get("/{monitor_id}/checks", response_model=CheckListResponse)
async def list_monitor_checks(
    monitor_id: int,
    _user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    result: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> CheckListResponse:
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor não encontrado")
    return await check_service.list_checks(
        db,
        monitor_id,
        result=result,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
