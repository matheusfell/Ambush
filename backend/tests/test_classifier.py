"""Testes unitários do classificador de resultados."""

from __future__ import annotations

import pytest
from app.checker.classifier import (
    CheckResult,
    ClassificationInput,
    LogSeverity,
    classify,
)


def _base(**overrides: object) -> ClassificationInput:
    data = {
        "status_code": 200,
        "response_time_ms": 100,
        "expected_status": [200],
        "expected_body_contains": None,
        "body_text": None,
        "slow_threshold_ms": 3000,
        "follow_redirects": True,
        "error_message": None,
    }
    data.update(overrides)
    return ClassificationInput(**data)  # type: ignore[arg-type]


def test_up_quando_status_aceito() -> None:
    outcome = classify(_base())
    assert outcome.result == CheckResult.UP
    assert outcome.severity == LogSeverity.INFO
    assert outcome.error_message is None


def test_degraded_quando_lento() -> None:
    outcome = classify(_base(response_time_ms=5000))
    assert outcome.result == CheckResult.DEGRADED
    assert outcome.severity == LogSeverity.WARN


def test_down_quando_body_nao_contem_esperado() -> None:
    outcome = classify(
        _base(
            expected_body_contains="OK",
            body_text="página de erro do proxy",
        )
    )
    assert outcome.result == CheckResult.DOWN
    assert outcome.severity == LogSeverity.ERROR
    assert outcome.error_message is not None
    assert "não contém" in outcome.error_message


def test_up_quando_body_contem_esperado() -> None:
    outcome = classify(
        _base(
            expected_body_contains="bem-vindo",
            body_text="<html>bem-vindo ao sistema</html>",
        )
    )
    assert outcome.result == CheckResult.UP


def test_down_redirect_sem_follow() -> None:
    outcome = classify(
        _base(
            status_code=302,
            expected_status=[200],
            follow_redirects=False,
        )
    )
    assert outcome.result == CheckResult.DOWN
    assert outcome.severity == LogSeverity.WARN


def test_up_redirect_na_lista_aceitos() -> None:
    outcome = classify(
        _base(
            status_code=302,
            expected_status=[200, 301, 302],
            follow_redirects=False,
        )
    )
    assert outcome.result == CheckResult.UP


@pytest.mark.parametrize("code", [401, 403, 404])
def test_down_4xx(code: int) -> None:
    outcome = classify(_base(status_code=code))
    assert outcome.result == CheckResult.DOWN
    assert outcome.severity == LogSeverity.ERROR


@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_down_5xx(code: int) -> None:
    outcome = classify(_base(status_code=code))
    assert outcome.result == CheckResult.DOWN
    assert outcome.severity == LogSeverity.ERROR


def test_down_timeout() -> None:
    outcome = classify(_base(status_code=None, error_message="Timeout após 10s"))
    assert outcome.result == CheckResult.DOWN
    assert outcome.severity == LogSeverity.ERROR


def test_down_status_fora_da_lista() -> None:
    outcome = classify(_base(status_code=201, expected_status=[200]))
    assert outcome.result == CheckResult.DOWN
