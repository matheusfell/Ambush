"""Classificação de resultado de checagem: UP / DEGRADED / DOWN."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CheckResult(StrEnum):
    """Resultado final de uma checagem."""

    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


class LogSeverity(StrEnum):
    """Severidade sugerida para logging estruturado."""

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class ClassificationInput:
    """Dados brutos usados para classificar uma checagem."""

    status_code: int | None
    response_time_ms: int | None
    expected_status: list[int]
    expected_body_contains: str | None
    body_text: str | None
    slow_threshold_ms: int
    follow_redirects: bool
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class ClassificationOutcome:
    """Resultado da classificação com severidade e mensagem de erro."""

    result: CheckResult
    severity: LogSeverity
    error_message: str | None = None


def classify(data: ClassificationInput) -> ClassificationOutcome:
    """
    Classifica o resultado de uma checagem HTTP.

    Regras (padrões da especificação):
    - Erro de transporte (timeout, DNS, TLS, conexão) → DOWN / ERROR
    - Status na lista + body ok + lento → DEGRADED / WARN
    - Status na lista + body ok → UP / INFO
    - 200 (ou aceito) mas body não contém esperado → DOWN / ERROR
    - 3xx sem follow e fora da lista → DOWN / WARN
    - 4xx / 5xx → DOWN / ERROR
    """
    if data.error_message:
        return ClassificationOutcome(
            result=CheckResult.DOWN,
            severity=LogSeverity.ERROR,
            error_message=data.error_message,
        )

    if data.status_code is None:
        return ClassificationOutcome(
            result=CheckResult.DOWN,
            severity=LogSeverity.ERROR,
            error_message="Sem status HTTP na resposta",
        )

    status = data.status_code
    accepted = status in data.expected_status

    # Body esperado: se configurado, deve aparecer no corpo
    if accepted and data.expected_body_contains:
        body = data.body_text or ""
        if data.expected_body_contains not in body:
            return ClassificationOutcome(
                result=CheckResult.DOWN,
                severity=LogSeverity.ERROR,
                error_message=(
                    f"Corpo da resposta não contém o texto esperado: "
                    f"{data.expected_body_contains!r}"
                ),
            )

    if accepted:
        if (
            data.response_time_ms is not None
            and data.response_time_ms > data.slow_threshold_ms
        ):
            return ClassificationOutcome(
                result=CheckResult.DEGRADED,
                severity=LogSeverity.WARN,
                error_message=(
                    f"Tempo de resposta {data.response_time_ms}ms "
                    f"acima do limiar {data.slow_threshold_ms}ms"
                ),
            )
        return ClassificationOutcome(
            result=CheckResult.UP,
            severity=LogSeverity.INFO,
        )

    # 3xx sem follow e não aceito explicitamente
    if 300 <= status < 400 and not data.follow_redirects:
        return ClassificationOutcome(
            result=CheckResult.DOWN,
            severity=LogSeverity.WARN,
            error_message=f"Redirecionamento HTTP {status} não aceito",
        )

    if 400 <= status < 500:
        return ClassificationOutcome(
            result=CheckResult.DOWN,
            severity=LogSeverity.ERROR,
            error_message=f"Erro de cliente HTTP {status}",
        )

    if status >= 500:
        return ClassificationOutcome(
            result=CheckResult.DOWN,
            severity=LogSeverity.ERROR,
            error_message=f"Erro de servidor HTTP {status}",
        )

    return ClassificationOutcome(
        result=CheckResult.DOWN,
        severity=LogSeverity.ERROR,
        error_message=f"Status HTTP {status} fora da lista de aceitos {data.expected_status}",
    )
