"""Testes do checker com httpx mockado via respx."""

from __future__ import annotations

import httpx
import pytest
import respx
from app.checker.checker import execute_check
from app.checker.classifier import CheckResult
from app.models.monitor import Monitor


def _monitor(**overrides: object) -> Monitor:
    defaults: dict[str, object] = {
        "id": 1,
        "name": "Teste",
        "url": "https://exemplo.test/health",
        "method": "GET",
        "interval_seconds": 300,
        "timeout_seconds": 5,
        "expected_status": [200],
        "expected_body_contains": None,
        "headers": None,
        "body": None,
        "basic_auth_user": None,
        "basic_auth_pass_encrypted": None,
        "skip_tls_verify": False,
        "follow_redirects": True,
        "retries": 2,
        "slow_threshold_ms": 3000,
        "enabled": True,
        "tags": [],
    }
    defaults.update(overrides)
    return Monitor(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
@respx.mock
async def test_execute_check_up() -> None:
    respx.get("https://exemplo.test/health").mock(
        return_value=httpx.Response(200, text="ok")
    )
    result = await execute_check(_monitor())
    assert result.result == CheckResult.UP
    assert result.status_code == 200
    assert result.attempt_count == 1
    assert result.response_time_ms is not None


@pytest.mark.asyncio
@respx.mock
async def test_retries_ate_sucesso() -> None:
    route = respx.get("https://exemplo.test/health")
    route.side_effect = [
        httpx.Response(500, text="erro"),
        httpx.Response(200, text="ok"),
    ]
    result = await execute_check(_monitor(retries=2))
    assert result.result == CheckResult.UP
    assert result.attempt_count == 2
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_retries_esgotados_permanece_down() -> None:
    respx.get("https://exemplo.test/health").mock(
        return_value=httpx.Response(503, text="indisponível")
    )
    result = await execute_check(_monitor(retries=1))
    assert result.result == CheckResult.DOWN
    assert result.attempt_count == 2
    assert result.status_code == 503


@pytest.mark.asyncio
@respx.mock
async def test_timeout_vira_down() -> None:
    respx.get("https://exemplo.test/health").mock(
        side_effect=httpx.TimeoutException("timeout")
    )
    result = await execute_check(_monitor(retries=0))
    assert result.result == CheckResult.DOWN
    assert result.status_code is None
    assert result.error_message is not None
    assert "Timeout" in result.error_message


@pytest.mark.asyncio
@respx.mock
async def test_body_contains() -> None:
    respx.get("https://exemplo.test/health").mock(
        return_value=httpx.Response(200, text="<html>erro interno</html>")
    )
    result = await execute_check(
        _monitor(expected_body_contains="dashboard", retries=0)
    )
    assert result.result == CheckResult.DOWN
    assert result.error_message is not None
