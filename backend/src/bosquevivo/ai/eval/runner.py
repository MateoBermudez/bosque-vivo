import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.ai.agent import Agent, AgentRequest
from bosquevivo.ai.agent.tools import Role
from bosquevivo.ai.guardrails import find_accusatory_terms
from bosquevivo.db.models import AgentRun

CASES_DIR = Path(__file__).parent / "cases"
UNCERTAINTY = re.compile(
    r"(no puedo concluir|no hay datos|no tengo datos|datos suficientes|no encontr"
    r"|no hay informaci)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EvalCase:
    id: str
    role: Role
    question: str
    expected_tools: list[str]
    location: tuple[float, float] | None = None
    expects_uncertainty: bool = False
    must_be_neutral: bool = False
    must_not_contain: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    tools_called: list[str]
    answer: str
    tools_ok: bool
    fidelity_ok: bool
    neutral_ok: bool
    uncertainty_ok: bool
    leak_ok: bool
    length_ok: bool
    used_fallback: bool
    latency_ms: int

    @property
    def passed(self) -> bool:
        return all(
            (
                self.tools_ok,
                self.fidelity_ok,
                self.neutral_ok,
                self.uncertainty_ok,
                self.leak_ok,
                self.length_ok,
            )
        )


@dataclass
class EvalReport:
    results: list[CaseResult]

    def rate(self, attribute: str) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if getattr(r, attribute)) / len(self.results)

    def percentile(self, value: float) -> int:
        latencies = sorted(r.latency_ms for r in self.results)
        if not latencies:
            return 0
        index = max(0, math.ceil(value * len(latencies)) - 1)
        return latencies[index]

    def summary(self) -> dict[str, Any]:
        return {
            "casos": len(self.results),
            "aprobados": sum(1 for r in self.results if r.passed),
            "eleccion_de_herramientas": self.rate("tools_ok"),
            "fidelidad_numerica": self.rate("fidelity_ok"),
            "neutralidad": self.rate("neutral_ok"),
            "incertidumbre": self.rate("uncertainty_ok"),
            "sin_fugas": self.rate("leak_ok"),
            "longitud": self.rate("length_ok"),
            "uso_de_respaldo": self.rate("used_fallback"),
            "latencia_p50_ms": self.percentile(0.5),
            "latencia_p90_ms": self.percentile(0.9),
        }

    def to_json(self) -> str:
        return json.dumps(
            {"resumen": self.summary(), "casos": [asdict(r) for r in self.results]},
            ensure_ascii=False,
            indent=2,
        )


def load_cases(path: Path | None = None) -> list[EvalCase]:
    source = path or CASES_DIR / "cases_v1.json"
    items = json.loads(source.read_text(encoding="utf-8"))
    cases: list[EvalCase] = []
    for item in items:
        location = tuple(item["location"]) if item.get("location") else None
        cases.append(
            EvalCase(
                id=item["id"],
                role=item["role"],
                question=item["question"],
                expected_tools=item["expected_tools"],
                location=location,
                expects_uncertainty=item.get("expects_uncertainty", False),
                must_be_neutral=item.get("must_be_neutral", False),
                must_not_contain=item.get("must_not_contain", []),
            )
        )
    return cases


def is_subsequence(expected: list[str], actual: list[str]) -> bool:
    iterator = iter(actual)
    return all(tool in iterator for tool in expected)


class EvalRunner:
    def __init__(self, session: Session, agent: Agent) -> None:
        self.session = session
        self.agent = agent

    def run_case(self, case: EvalCase) -> CaseResult:
        answer = self.agent.answer(
            AgentRequest(
                text=case.question,
                role=case.role,
                location=case.location,
                user_ref=f"eval:{case.id}",
            )
        )
        run = self.session.scalars(select(AgentRun).where(AgentRun.id == answer.run_id)).one()
        text = answer.text
        lowered = text.lower()
        return CaseResult(
            case_id=case.id,
            tools_called=answer.tools_called,
            answer=text,
            tools_ok=is_subsequence(case.expected_tools, answer.tools_called),
            fidelity_ok=run.validator_passed is True or answer.used_fallback,
            neutral_ok=not find_accusatory_terms(text),
            uncertainty_ok=(not case.expects_uncertainty) or bool(UNCERTAINTY.search(text)),
            leak_ok=not any(t.lower() in lowered for t in case.must_not_contain),
            length_ok=case.role != "comunidad" or len(text) <= 300,
            used_fallback=answer.used_fallback,
            latency_ms=run.latency_ms or 0,
        )

    def run(self, cases: list[EvalCase]) -> EvalReport:
        return EvalReport([self.run_case(c) for c in cases])
