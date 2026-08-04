"""API de incidentes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.incident import IncidentRead
from app.services import incident_service

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_read(incident: object) -> IncidentRead:
    from app.models.incident import Incident

    assert isinstance(incident, Incident)
    data = IncidentRead.model_validate(incident)
    if incident.monitor is not None:
        data.monitor_name = incident.monitor.name
    return data


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    _user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    monitor_id: int | None = Query(default=None),
) -> list[IncidentRead]:
    rows = await incident_service.list_incidents(
        db, status=status_filter, monitor_id=monitor_id
    )
    return [_to_read(row) for row in rows]


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(
    incident_id: int,
    _user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> IncidentRead:
    incident = await incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente não encontrado",
        )
    return _to_read(incident)
