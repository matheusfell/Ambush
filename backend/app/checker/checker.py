"""Cliente HTTP assíncrono para execução de checagens."""

from __future__ import annotations

import asyncio
import ssl
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.checker.classifier import (
    CheckResult,
    ClassificationInput,
    ClassificationOutcome,
    classify,
)
from app.core.crypto import CryptoError, decrypt
from app.core.logging import get_logger
from app.models.monitor import Monitor

logger = get_logger(__name__)

# Pausa entre tentativas para não martelar a rede em falha transitória
_RETRY_BACKOFF_SECONDS = 0.5
_BODY_EXCERPT_LIMIT = 4000


@dataclass(frozen=True, slots=True)
class CheckExecutionResult:
    """Resultado consolidado após retries (pronto para persistir)."""

    status_code: int | None
    response_time_ms: int | None
    result: CheckResult
    error_message: str | None
    response_body_excerpt: str | None
    attempt_count: int
    severity: str


@dataclass(frozen=True, slots=True)
class _AttemptDetail:
    status_code: int | None
    response_time_ms: int | None
    outcome: ClassificationOutcome
    response_body_excerpt: str | None = None


def _build_ssl_context(skip_tls_verify: bool) -> ssl.SSLContext:
    """
    Monta o contexto SSL.

    Usa o trust store do sistema (no Windows: certificados da máquina/empresa),
    em vez do bundle isolado do certifi — necessário para CAs corporativas.
    """
    ctx = ssl.create_default_context()
    if skip_tls_verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _auth(monitor: Monitor) -> httpx.BasicAuth | None:
    if not monitor.basic_auth_user:
        return None
    password = ""
    if monitor.basic_auth_pass_encrypted:
        password = decrypt(monitor.basic_auth_pass_encrypted)
    return httpx.BasicAuth(monitor.basic_auth_user, password)


def _headers(monitor: Monitor) -> dict[str, str]:
    raw: dict[str, Any] | None = monitor.headers
    if not raw:
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def _classify_error(
    monitor: Monitor,
    *,
    elapsed_ms: int,
    error_message: str,
) -> _AttemptDetail:
    outcome = classify(
        ClassificationInput(
            status_code=None,
            response_time_ms=elapsed_ms,
            expected_status=list(monitor.expected_status or [200]),
            expected_body_contains=monitor.expected_body_contains,
            body_text=None,
            slow_threshold_ms=monitor.slow_threshold_ms,
            follow_redirects=monitor.follow_redirects,
            error_message=error_message,
        )
    )
    return _AttemptDetail(None, elapsed_ms, outcome)


def _body_excerpt(response: httpx.Response) -> str | None:
    if not response.content:
        return None
    body = response.text
    if len(body) <= _BODY_EXCERPT_LIMIT:
        return body
    return body[:_BODY_EXCERPT_LIMIT] + "\n\n[resposta truncada]"


async def _single_attempt(monitor: Monitor) -> _AttemptDetail:
    """Executa uma única requisição HTTP e classifica o resultado com métricas."""
    timeout = httpx.Timeout(float(monitor.timeout_seconds))
    verify = _build_ssl_context(monitor.skip_tls_verify)
    method = monitor.method.upper()
    headers = _headers(monitor)
    auth = _auth(monitor)
    content = monitor.body if method in {"POST", "PUT", "PATCH"} else None

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            verify=verify,
            follow_redirects=monitor.follow_redirects,
            auth=auth,
        ) as client:
            response = await client.request(
                method=method,
                url=monitor.url,
                headers=headers,
                content=content,
            )
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        body_text = _body_excerpt(response)

        outcome = classify(
            ClassificationInput(
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                expected_status=list(monitor.expected_status or [200]),
                expected_body_contains=monitor.expected_body_contains,
                body_text=body_text,
                slow_threshold_ms=monitor.slow_threshold_ms,
                follow_redirects=monitor.follow_redirects,
            )
        )
        return _AttemptDetail(
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            outcome=outcome,
            response_body_excerpt=body_text,
        )
    except httpx.TimeoutException:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return _classify_error(
            monitor,
            elapsed_ms=elapsed_ms,
            error_message=f"Timeout após {monitor.timeout_seconds}s",
        )
    except httpx.ConnectError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return _classify_error(
            monitor,
            elapsed_ms=elapsed_ms,
            error_message=f"Falha de conexão: {exc}",
        )
    except ssl.SSLError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return _classify_error(
            monitor,
            elapsed_ms=elapsed_ms,
            error_message=f"Erro de TLS: {exc}",
        )
    except httpx.HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return _classify_error(
            monitor,
            elapsed_ms=elapsed_ms,
            error_message=f"Erro HTTP: {exc}",
        )


async def execute_check(monitor: Monitor) -> CheckExecutionResult:
    """
    Executa a checagem com retries.

    Em um único tick: até ``retries + 1`` tentativas. Para no primeiro
    UP/DEGRADED. Persiste-se um único registro com ``attempt_count``.
    """
    max_attempts = max(1, monitor.retries + 1)
    last: _AttemptDetail | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            detail = await _single_attempt(monitor)
        except CryptoError as exc:
            logger.error(
                "falha_ao_descriptografar_basic_auth",
                monitor_id=monitor.id,
                error=str(exc),
            )
            return CheckExecutionResult(
                status_code=None,
                response_time_ms=None,
                result=CheckResult.DOWN,
                error_message=str(exc),
                response_body_excerpt=None,
                attempt_count=attempt,
                severity="ERROR",
            )

        last = detail
        if detail.outcome.result in {CheckResult.UP, CheckResult.DEGRADED}:
            return CheckExecutionResult(
                status_code=detail.status_code,
                response_time_ms=detail.response_time_ms,
                result=detail.outcome.result,
                error_message=detail.outcome.error_message,
                response_body_excerpt=detail.response_body_excerpt,
                attempt_count=attempt,
                severity=detail.outcome.severity.value,
            )

        if attempt < max_attempts:
            await asyncio.sleep(_RETRY_BACKOFF_SECONDS)

    assert last is not None
    return CheckExecutionResult(
        status_code=last.status_code,
        response_time_ms=last.response_time_ms,
        result=last.outcome.result,
        error_message=last.outcome.error_message,
        response_body_excerpt=last.response_body_excerpt,
        attempt_count=max_attempts,
        severity=last.outcome.severity.value,
    )
