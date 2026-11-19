"""Evaluación del agente contra un despliegue: cada caso se ejecuta en el servidor, con su
modelo y su base, y aquí solo se arma el informe. La clave del modelo no sale del servidor."""

import time
from collections.abc import Callable

import httpx

from bosquevivo.ai.eval.runner import CaseResult, EvalCase, EvalReport

CASE_TIMEOUT_SECONDS = 120.0


def run_remote(
    base_url: str,
    admin_token: str,
    cases: list[EvalCase],
    *,
    client: httpx.Client | None = None,
    progress: Callable[[CaseResult], None] | None = None,
    pause_seconds: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> EvalReport:
    """`pause_seconds` separa los casos para respetar el límite de peticiones por minuto."""
    http = client or httpx.Client(timeout=CASE_TIMEOUT_SECONDS)
    results: list[CaseResult] = []
    for index, case in enumerate(cases):
        if index and pause_seconds:
            sleep(pause_seconds)
        response = http.post(
            f"{base_url.rstrip('/')}/api/v1/admin/eval/{case.id}",
            headers={"X-Admin-Token": admin_token},
        )
        response.raise_for_status()
        result = CaseResult(**response.json())
        results.append(result)
        if progress:
            progress(result)
    return EvalReport(results)
