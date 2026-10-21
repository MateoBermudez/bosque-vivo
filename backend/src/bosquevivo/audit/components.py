from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes

from bosquevivo.audit.config import IndexConfig
from bosquevivo.audit.inputs import AuditInputs, SeriesPoint


@dataclass(frozen=True)
class ComponentResult:
    name: str
    score: float | None
    detail: dict[str, Any]


LOW_DATA = "pocos meses con datos posteriores a T0"


def _clip(value: float) -> float:
    return float(max(0.0, min(100.0, value)))


def _years(points: list[SeriesPoint]) -> np.ndarray:
    base = points[0].period
    return np.array([(p.period - base).days / 365.25 for p in points])


def _value(point: SeriesPoint) -> float:
    return 0.0 if point.ndvi_mean is None else float(point.ndvi_mean)


def valid_points(points: list[SeriesPoint]) -> list[SeriesPoint]:
    return [p for p in points if p.ndvi_mean is not None]


def split_at(points: list[SeriesPoint], t0: date) -> tuple[list[SeriesPoint], list[SeriesPoint]]:
    pre = [p for p in points if p.period < t0]
    post = [p for p in points if p.period >= t0]
    return pre, post


def permanence(inputs: AuditInputs) -> ComponentResult:
    if inputs.t0 is None or not inputs.baseline_forest_ha or inputs.baseline_forest_ha <= 0:
        return ComponentResult("permanencia", None, {"motivo": "sin línea base de bosque"})
    lost = sum(ha for year, ha in inputs.loss_by_year.items() if year >= inputs.t0.year)
    remaining = max(0.0, 1.0 - lost / inputs.baseline_forest_ha)
    return ComponentResult(
        "permanencia",
        _clip(remaining * 100.0),
        {
            "ha_perdidas_desde_t0": round(lost, 2),
            "ha_bosque_inicial": round(inputs.baseline_forest_ha, 2),
            "porcentaje_en_pie": round(remaining * 100.0, 1),
        },
    )


def trend(inputs: AuditInputs, config: IndexConfig) -> ComponentResult:
    if inputs.t0 is None:
        return ComponentResult("tendencia", None, {"motivo": "sin fecha T0"})
    _, post = split_at(valid_points(inputs.series), inputs.t0)
    if len(post) < config.min_valid_months_post:
        return ComponentResult(
            "tendencia", None, {"motivo": "pocos meses con datos posteriores a T0"}
        )
    x = _years(post)
    y = np.array([_value(p) for p in post], dtype=float)
    slope = float(np.asarray(theilslopes(y, x)[0]))
    test = mk.original_test(y, alpha=config.significance_level)
    if slope >= 0:
        score = 100.0
    else:
        raw = 100.0 * (1.0 - slope / config.trend_zero_slope_per_year)
        score = _clip(raw)
        if not test.h:
            score = _clip(100.0 - (100.0 - score) * 0.5)
    return ComponentResult(
        "tendencia",
        score,
        {
            "pendiente_ndvi_por_anio": round(slope, 4),
            "tendencia_significativa": int(bool(test.h)),
            "p_valor": round(float(test.p), 4),
            "meses_usados": len(post),
        },
    )


def seasonal_anomalies(points: list[SeriesPoint]) -> list[tuple[date, float]]:
    by_month: dict[int, list[float]] = {}
    for p in points:
        by_month.setdefault(p.period.month, []).append(_value(p))
    medians = {month: float(np.median(values)) for month, values in by_month.items()}
    return [(p.period, _value(p) - medians[p.period.month]) for p in points]


def largest_drop(anomalies: list[tuple[date, float]], window: int = 3) -> tuple[float, date | None]:
    if len(anomalies) < window * 2:
        return 0.0, None
    values = np.array([a for _, a in anomalies])
    best, when = 0.0, None
    for i in range(window, len(values) - window + 1):
        before = float(np.mean(values[i - window : i]))
        after = float(np.mean(values[i : i + window]))
        drop = before - after
        if drop > best:
            best, when = drop, anomalies[i][0]
    return best, when


def stability(inputs: AuditInputs, config: IndexConfig) -> ComponentResult:
    if inputs.t0 is None:
        return ComponentResult("estabilidad", None, {"motivo": "sin fecha T0"})
    valid = valid_points(inputs.series)
    _, post = split_at(valid, inputs.t0)
    if len(post) < config.min_valid_months_post:
        return ComponentResult(
            "estabilidad", None, {"motivo": "pocos meses con datos posteriores a T0"}
        )
    drop, when = largest_drop(seasonal_anomalies(valid))
    span = config.stability_zero_drop - config.stability_full_drop
    score = (
        _clip(100.0 * (1.0 - (drop - config.stability_full_drop) / span))
        if drop > config.stability_full_drop
        else 100.0
    )
    return ComponentResult(
        "estabilidad",
        score,
        {
            "caida_maxima_ndvi": round(drop, 4),
            "fecha_caida": when.isoformat() if when else None,
        },
    )
