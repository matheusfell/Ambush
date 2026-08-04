"""Serviço de domínio para checagens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.checker.checker import CheckExecutionResult, execute_check
from app.core.logging import get_logger
from app.models.check import Check
from app.models.monitor import Monitor
from app.schemas.check import CheckListResponse, CheckRead

logger = get_logger(__name__)


async def persist_check_result(
    session: AsyncSession,
    monitor: Monitor,
    execution: CheckExecutionResult,
) -> Check:
    check = Check(
        monitor_id=monitor.id,
        status_code=execution.status_code,
        response_time_ms=execution.response_time_ms,
        result=execution.result.value,
        error_message=execution.error_message,
        attempt_count=execution.attempt_count,
    )
    session.add(check)
    await session.flush()
    await session.refresh(check)

    log_method = {
        "INFO": logger.info,
        "WARN": logger.warning,
        "ERROR": logger.error,
    }.get(execution.severity, logger.info)

    log_method(
        "checagem_concluida",
        monitor_id=monitor.id,
        monitor_name=monitor.name,
        result=execution.result.value,
        status_code=execution.status_code,
        response_time_ms=execution.response_time_ms,
        attempt_count=execution.attempt_count,
        error_message=execution.error_message,
    )

    # Fase 2: incidentes + notificações (erros de e-mail não derrubam a checagem)
    from app.services import incident_service

    await incident_service.process_check_result(session, monitor, check)
    return check


async def run_and_persist_check(session: AsyncSession, monitor: Monitor) -> Check:
    """Executa a checagem HTTP e persiste o resultado."""
    execution = await execute_check(monitor)
    return await persist_check_result(session, monitor, execution)


async def list_checks(
    session: AsyncSession,
    monitor_id: int,
    *,
    result: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CheckListResponse:
    filters = [Check.monitor_id == monitor_id]
    if result:
        filters.append(Check.result == result.upper())
    if date_from is not None:
        filters.append(Check.checked_at >= date_from)
    if date_to is not None:
        filters.append(Check.checked_at <= date_to)

    count_stmt = select(func.count()).select_from(Check).where(*filters)
    total = int((await session.execute(count_stmt)).scalar_one())

    offset = (page - 1) * page_size
    stmt = (
        select(Check)
        .where(*filters)
        .order_by(Check.checked_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    items = [CheckRead.model_validate(row) for row in rows]
    return CheckListResponse(items=items, total=total, page=page, page_size=page_size)
