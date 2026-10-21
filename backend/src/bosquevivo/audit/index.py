from dataclasses import dataclass, field
from typing import Any

from bosquevivo.audit.components import ComponentResult, permanence, stability, trend
from bosquevivo.audit.confidence import Confidence, assess_confidence
from bosquevivo.audit.config import IndexConfig, default_config
from bosquevivo.audit.inputs import AuditInputs

INSUFFICIENT = "Insuficiente"


@dataclass(frozen=True)
class IndexOutcome:
    score: float | None
    category: str
    components: list[ComponentResult]
    confidence: Confidence
    sensitivity: dict[str, float] = field(default_factory=dict)
    index_version: str = "v0"

    def components_payload(self) -> dict[str, Any]:
        return {
            c.name: {"puntaje": None if c.score is None else round(c.score, 1), **c.detail}
            for c in self.components
        }


def categorize(score: float, config: IndexConfig) -> str:
    if score >= config.category_high:
        return "Alta"
    if score >= config.category_medium:
        return "Media"
    return "Baja"


def weighted_score(components: list[ComponentResult], weights: dict[str, float]) -> float | None:
    available = [(c.score, weights[c.name]) for c in components if c.score is not None]
    if not available:
        return None
    total_weight = sum(w for _, w in available)
    return sum(s * w for s, w in available) / total_weight


class IndexCalculator:
    def __init__(self, config: IndexConfig | None = None) -> None:
        self.config = config or default_config()

    def _weights(self, config: IndexConfig) -> dict[str, float]:
        return {
            "permanencia": config.weight_permanence,
            "tendencia": config.weight_trend,
            "estabilidad": config.weight_stability,
        }

    def calculate(self, inputs: AuditInputs) -> IndexOutcome:
        config = self.config
        components = [permanence(inputs), trend(inputs, config), stability(inputs, config)]
        confidence = assess_confidence(inputs, config)
        missing_core = components[0].score is None or all(c.score is None for c in components[1:])
        score = weighted_score(components, self._weights(config))
        if score is None or confidence.value < config.min_confidence or missing_core:
            return IndexOutcome(None, INSUFFICIENT, components, confidence, {}, config.version)
        return IndexOutcome(
            round(score, 1),
            categorize(score, config),
            components,
            confidence,
            self.sensitivity(components),
            config.version,
        )

    def sensitivity(self, components: list[ComponentResult]) -> dict[str, float]:
        delta = self.config.sensitivity_delta
        scores: list[float] = []
        base = self._weights(self.config)
        for name in base:
            for sign in (-1, 1):
                shifted = dict(base)
                shifted[name] = max(0.0, shifted[name] + sign * delta)
                total = sum(shifted.values())
                shifted = {k: v / total for k, v in shifted.items()}
                value = weighted_score(components, shifted)
                if value is not None:
                    scores.append(value)
        if not scores:
            return {}
        return {"minimo": round(min(scores), 1), "maximo": round(max(scores), 1)}

    def with_config(self, **changes: Any) -> "IndexCalculator":
        return IndexCalculator(replace_config(self.config, **changes))


def replace_config(config: IndexConfig, **changes: Any) -> IndexConfig:
    return config.model_copy(update=changes)
