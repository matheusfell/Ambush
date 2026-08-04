"""Agendador asyncio: uma Task por monitor ativo, com hot-reload."""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from app.config import get_settings
from app.core.logging import get_logger
from app.database import AsyncSessionLocal
from app.services import check_service, monitor_service

if TYPE_CHECKING:
    from app.models.monitor import Monitor

logger = get_logger(__name__)


class MonitorScheduler:
    """
    Mantém um ``asyncio.Task`` por monitor habilitado.

    - Jitter no start para não disparar tudo no mesmo segundo.
    - ``asyncio.Semaphore`` limita checagens simultâneas (I/O bound).
    - CRUD chama ``sync_monitor`` / ``remove_monitor`` sem reiniciar o processo.
    """

    def __init__(self) -> None:
        self._tasks: dict[int, asyncio.Task[None]] = {}
        self._semaphore: asyncio.Semaphore | None = None
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    async def start(self) -> None:
        if self._started:
            return
        concurrency = get_settings().check_concurrency
        self._semaphore = asyncio.Semaphore(concurrency)
        self._started = True

        async with AsyncSessionLocal() as session:
            monitors = await monitor_service.list_enabled_monitors(session)

        logger.info(
            "agendador_iniciado",
            monitors=len(monitors),
            concurrency=concurrency,
        )
        for monitor in monitors:
            self._spawn(monitor, with_jitter=True)

    async def stop(self) -> None:
        self._started = False
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("agendador_parado")

    def sync_monitor(self, monitor: Monitor) -> None:
        """Reprograma (ou remove) o job conforme o estado atual do monitor."""
        if not self._started:
            return
        self.remove_monitor(monitor.id)
        if monitor.enabled:
            self._spawn(monitor, with_jitter=False)

    def remove_monitor(self, monitor_id: int) -> None:
        task = self._tasks.pop(monitor_id, None)
        if task is not None and not task.done():
            task.cancel()
            logger.info("job_removido", monitor_id=monitor_id)

    def _spawn(self, monitor: Monitor, *, with_jitter: bool) -> None:
        if with_jitter:
            jitter = random.uniform(0, min(30.0, float(monitor.interval_seconds)))
        else:
            jitter = 0.0
        task = asyncio.create_task(
            self._monitor_loop(monitor.id, monitor.interval_seconds, jitter),
            name=f"monitor-{monitor.id}",
        )
        self._tasks[monitor.id] = task
        logger.info(
            "job_agendado",
            monitor_id=monitor.id,
            interval_seconds=monitor.interval_seconds,
            jitter_seconds=round(jitter, 2),
        )

    async def _monitor_loop(
        self,
        monitor_id: int,
        interval_seconds: int,
        jitter: float,
    ) -> None:
        if jitter > 0:
            try:
                await asyncio.sleep(jitter)
            except asyncio.CancelledError:
                raise

        while True:
            try:
                await self._run_one(monitor_id)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — isolamento do loop do job
                # Isolamento deliberado: uma falha inesperada não pode matar o job.
                # Tipos específicos já são tratados dentro do checker; isto é a rede de segurança.
                logger.exception(
                    "erro_nao_tratado_no_job",
                    monitor_id=monitor_id,
                    error=str(exc),
                )

            try:
                # Intervalo pode ter mudado: relemos do registry local via DB a cada ciclo
                interval = await self._current_interval(monitor_id)
                if interval is None:
                    # Monitor pausado/excluído — encerra o loop
                    return
                await asyncio.sleep(float(interval))
            except asyncio.CancelledError:
                raise

    async def _current_interval(self, monitor_id: int) -> int | None:
        async with AsyncSessionLocal() as session:
            monitor = await monitor_service.get_monitor(session, monitor_id)
            if monitor is None or not monitor.enabled:
                return None
            # Atualiza intervalo vivo se o job ainda for o mesmo
            return monitor.interval_seconds

    async def _run_one(self, monitor_id: int) -> None:
        assert self._semaphore is not None
        async with self._semaphore, AsyncSessionLocal() as session:
            monitor = await monitor_service.get_monitor(session, monitor_id)
            if monitor is None or not monitor.enabled:
                return
            try:
                await check_service.run_and_persist_check(session, monitor)
                await session.commit()
            except Exception as exc:  # noqa: BLE001 — logar e seguir
                await session.rollback()
                logger.exception(
                    "falha_na_checagem_agendada",
                    monitor_id=monitor_id,
                    error=str(exc),
                )

    async def run_now(self, monitor_id: int) -> None:
        """Dispara checagem imediata respeitando o semáforo global."""
        await self._run_one(monitor_id)


# Instância única do processo (1 worker Uvicorn)
scheduler = MonitorScheduler()
