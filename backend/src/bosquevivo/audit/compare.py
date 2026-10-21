from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from bosquevivo.audit.inputs import AuditInputs


@dataclass(frozen=True)
class ComparisonRow:
    year: int
    after_t0: bool
    ndvi_mean: float | None
    loss_ha: float
    declared_note: str


def compare_declared_observed(inputs: AuditInputs) -> list[ComparisonRow]:
    by_year: dict[int, list[float]] = defaultdict(list)
    for point in inputs.series:
        if point.ndvi_mean is not None:
            by_year[point.period.year].append(point.ndvi_mean)
    years = sorted(set(by_year) | set(inputs.loss_by_year))
    rows: list[ComparisonRow] = []
    for year in years:
        values = by_year.get(year, [])
        t0 = inputs.t0
        after = t0 is not None and date(year, 12, 31) >= t0
        rows.append(
            ComparisonRow(
                year=year,
                after_t0=after,
                ndvi_mean=round(sum(values) / len(values), 4) if values else None,
                loss_ha=round(inputs.loss_by_year.get(year, 0.0), 2),
                declared_note="acreditado" if after else "previo a la acreditación",
            )
        )
    return rows
