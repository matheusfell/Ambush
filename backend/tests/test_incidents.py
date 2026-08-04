"""Testes de abertura/fechamento de incidente (Postgres de desenvolvimento)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from app.database import AsyncSessionLocal
from app.models.check import Check
from app.models.incident import Incident
from app.models.monitor import Monitor
from app.services import incident_service
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def session() -> AsyncSession:
    async with AsyncSessionLocal() as sess:
        yield sess
        await sess.rollback()


async def _make_monitor(session: AsyncSession) -> Monitor:
    monitor = Monitor(
        name="Teste Incidente Fase2",
        url="https://exemplo.test/incidente",
        method="GET",
        interval_seconds=300,
        timeout_seconds=10,
        expected_status=[200],
        retries=0,
        slow_threshold_ms=3000,
        enabled=False,  # não agenda job
        tags=["teste"],
    )
    session.add(monitor)
    await session.flush()
    await session.refresh(monitor)
    return monitor


async def _add_check(session: AsyncSession, monitor_id: int, result: str) -> Check:
    check = Check(
        monitor_id=monitor_id,
        checked_at=datetime.now(UTC),
        status_code=500 if result == "DOWN" else 200,
        response_time_ms=100,
        result=result,
        error_message="erro simulado" if result == "DOWN" else None,
        attempt_count=1,
    )
    session.add(check)
    await session.flush()
    await session.refresh(check)
    return check


async def _cleanup(session: AsyncSession, monitor_id: int) -> None:
    await session.execute(delete(Incident).where(Incident.monitor_id == monitor_id))
    await session.execute(delete(Check).where(Check.monitor_id == monitor_id))
    await session.execute(delete(Monitor).where(Monitor.id == monitor_id))
    await session.commit()


@pytest.mark.asyncio
async def test_abre_acumula_e_fecha_incidente(session: AsyncSession) -> None:
    monitor = await _make_monitor(session)
    await session.commit()

    try:
        with patch(
            "app.services.incident_service._try_notify",
            new_callable=AsyncMock,
            return_value=False,
        ) as notify:
            # Ainda não abre: regra padrão exige 3 DOWN consecutivos.
            first = await incident_service.process_check_result(
                session, monitor, await _add_check(session, monitor.id, "DOWN")
            )
            await session.commit()
            assert first is None

            second = await incident_service.process_check_result(
                session, monitor, await _add_check(session, monitor.id, "DOWN")
            )
            await session.commit()
            assert second is None
            notify.assert_not_awaited()

            # Abre na terceira falha consecutiva.
            open_inc = await incident_service.process_check_result(
                session, monitor, await _add_check(session, monitor.id, "DOWN")
            )
            await session.commit()
            assert open_inc is not None
            assert open_inc.status == "open"
            assert open_inc.failure_count == 3

            # Acumula
            same = await incident_service.process_check_result(
                session, monitor, await _add_check(session, monitor.id, "DOWN")
            )
            await session.commit()
            assert same is not None
            assert same.id == open_inc.id
            assert same.failure_count == 4

            # Fecha
            closed = await incident_service.process_check_result(
                session, monitor, await _add_check(session, monitor.id, "UP")
            )
            await session.commit()
            assert closed is not None
            assert closed.status == "closed"
            assert closed.resolved_at is not None
            assert closed.duration_seconds is not None

            still_open = (
                await session.execute(
                    select(Incident).where(
                        Incident.monitor_id == monitor.id,
                        Incident.status == "open",
                    )
                )
            ).scalars().all()
            assert still_open == []
    finally:
        await _cleanup(session, monitor.id)
