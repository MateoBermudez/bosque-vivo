from dataclasses import dataclass

from bosquevivo.audit.components import split_at, valid_points
from bosquevivo.audit.config import IndexConfig
from bosquevivo.audit.inputs import AuditInputs


@dataclass(frozen=True)
class Confidence:
    value: float
    label: str
    coverage: float
    valid_fraction: float
    scenes_per_month: float


def expected_months(inputs: AuditInputs) -> int:
    if not inputs.series:
        return 0
    first = min(p.period for p in inputs.series)
    last = max(p.period for p in inputs.series)
    return (last.year - first.year) * 12 + (last.month - first.month) + 1


def assess_confidence(inputs: AuditInputs, config: IndexConfig) -> Confidence:
    total = expected_months(inputs)
    valid = valid_points(inputs.series)
    if total == 0 or not valid:
        return Confidence(0.0, "baja", 0.0, 0.0, 0.0)
    if inputs.t0 is not None:
        _, post = split_at(valid, inputs.t0)
        window = [p for p in inputs.series if p.period >= inputs.t0]
        months = len(window) or total
        coverage = min(1.0, len(post) / months)
    else:
        coverage = min(1.0, len(valid) / total)
    valid_fraction = sum(p.valid_fraction for p in valid) / len(valid)
    scenes = sum(p.scene_count for p in valid) / len(valid)
    value = 0.4 * coverage + 0.4 * valid_fraction + 0.2 * min(1.0, scenes / 3.0)
    label = (
        "alta"
        if value >= config.confidence_high
        else "media"
        if value >= config.confidence_medium
        else "baja"
    )
    return Confidence(
        round(value, 3), label, round(coverage, 3), round(valid_fraction, 3), round(scenes, 2)
    )
