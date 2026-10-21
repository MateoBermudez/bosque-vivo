from datetime import date

import pytest

from bosquevivo.audit import IndexCalculator, IndexConfig
from bosquevivo.audit.compare import compare_declared_observed
from bosquevivo.audit.inputs import AuditInputs, SeriesPoint


def monthly_series(start_year, end_year, *, level=0.8, drop_year=None, drop=0.3, valid=0.9):
    points = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            value = level - (drop if drop_year and year >= drop_year else 0.0)
            points.append(SeriesPoint(date(year, month, 1), value, valid, 4))
    return points


def make_inputs(**overrides):
    base = {
        "t0": date(2018, 1, 1),
        "declared_area_ha": 1000.0,
        "baseline_forest_ha": 950.0,
        "series": monthly_series(2015, 2024),
        "sensor": "s2",
        "loss_by_year": {},
    }
    base.update(overrides)
    return AuditInputs(**base)


def test_intact_forest_scores_high():
    outcome = IndexCalculator().calculate(make_inputs())
    assert outcome.category == "Alta"
    assert outcome.score is not None and outcome.score >= 95


def test_loss_after_t0_lowers_permanence():
    outcome = IndexCalculator().calculate(make_inputs(loss_by_year={2020: 475.0}))
    permanence = next(c for c in outcome.components if c.name == "permanencia")
    assert permanence.score == pytest.approx(50.0)


def test_loss_before_t0_is_ignored():
    outcome = IndexCalculator().calculate(make_inputs(loss_by_year={2010: 500.0}))
    permanence = next(c for c in outcome.components if c.name == "permanencia")
    assert permanence.score == 100.0


def test_abrupt_ndvi_drop_lowers_stability_and_trend_is_flat():
    series = monthly_series(2015, 2024, drop_year=2021)
    outcome = IndexCalculator().calculate(make_inputs(series=series))
    stability = next(c for c in outcome.components if c.name == "estabilidad")
    assert stability.score is not None and stability.score < 10
    assert stability.detail["fecha_caida"] is not None


def test_no_valid_data_is_insufficient():
    series = [SeriesPoint(date(2020, m, 1), None, 0.0, 0) for m in range(1, 13)]
    outcome = IndexCalculator().calculate(make_inputs(series=series))
    assert outcome.category == "Insuficiente"
    assert outcome.score is None


def test_low_valid_fraction_lowers_confidence():
    series = monthly_series(2015, 2024, valid=0.1)
    outcome = IndexCalculator().calculate(make_inputs(series=series))
    assert outcome.confidence.label in {"media", "baja"}


def test_missing_baseline_gives_insufficient():
    outcome = IndexCalculator().calculate(make_inputs(baseline_forest_ha=None))
    assert outcome.category == "Insuficiente"


def test_missing_t0_gives_insufficient():
    outcome = IndexCalculator().calculate(make_inputs(t0=None))
    assert outcome.category == "Insuficiente"


def test_sensitivity_range_brackets_score():
    outcome = IndexCalculator().calculate(make_inputs(loss_by_year={2020: 200.0}))
    assert outcome.score is not None
    assert outcome.sensitivity["minimo"] <= outcome.score <= outcome.sensitivity["maximo"]


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        IndexConfig(weight_permanence=0.9)


def test_comparison_marks_years_after_t0():
    rows = compare_declared_observed(make_inputs(loss_by_year={2019: 3.0}))
    by_year = {r.year: r for r in rows}
    assert not by_year[2016].after_t0
    assert by_year[2019].after_t0
    assert by_year[2019].loss_ha == 3.0


def test_nearly_all_pixels_masked_is_insufficient_even_with_full_coverage():
    series = monthly_series(2015, 2024, valid=0.02)
    outcome = IndexCalculator().calculate(make_inputs(series=series))
    assert outcome.category == "Insuficiente"
