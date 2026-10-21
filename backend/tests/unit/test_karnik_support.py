from datetime import date

import pytest
from shapely.geometry import MultiPolygon, Point, box

from bosquevivo.audit.compare import compare_declared_observed
from bosquevivo.audit.index import INSUFFICIENT, IndexCalculator
from bosquevivo.audit.inputs import AuditInputs, SeriesPoint
from bosquevivo.audit.narrative import build_narrative
from bosquevivo.audit.service import analysis_window_start
from bosquevivo.registry.geometry import (
    MAX_ANALYSIS_VERTICES,
    keep_largest_parts,
    simplify_for_analysis,
    vertex_count,
)
from bosquevivo.registry.importer import resolve_columns
from bosquevivo.registry.karnik import parse_us_date


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("11/13/2013", date(2013, 11, 13)),
        ("01/01/2018", date(2018, 1, 1)),
        ("2016-05-02", date(2016, 5, 2)),
        ("", None),
        ("nan", None),
        (None, None),
        ("13/45/2013", None),
    ],
)
def test_parse_us_date(text, expected):
    assert parse_us_date(text) == expected


def test_la_ventana_de_series_empieza_antes_de_t0_sin_bajar_de_2000():
    assert analysis_window_start(None) == date(2000, 1, 1)
    assert analysis_window_start(date(2013, 11, 13)) == date(2010, 1, 1)
    assert analysis_window_start(date(2002, 5, 1)) == date(2000, 1, 1)
    assert analysis_window_start(date(2020, 1, 1)) == date(2017, 1, 1)


def test_no_toca_los_poligonos_pequenos():
    square = box(-75.0, 5.0, -74.9, 5.1)
    result = simplify_for_analysis(square)

    assert not result.simplified
    assert result.geometry.equals(square)
    assert result.area_change_pct == 0.0


def test_reduce_los_poligonos_gigantes_y_conserva_el_area():
    circle = Point(-75.0, 5.0).buffer(0.1, quad_segs=10_000)  # ~40.000 vértices
    result = simplify_for_analysis(circle)

    assert result.original_vertices > MAX_ANALYSIS_VERTICES
    assert vertex_count(result.geometry) <= MAX_ANALYSIS_VERTICES
    assert result.simplified and result.tolerance >= 0.0001
    assert result.area_change_pct < 0.5
    assert result.geometry.is_valid


def test_el_importador_generico_reconoce_columnas_con_espacios():
    resolved = resolve_columns(
        ["Project Name", "ProjectID", "Registry Name", "Project Start Date", "Country"]
    )

    assert resolved["name"] == "Project Name"
    assert resolved["registry_id"] == "ProjectID"
    assert resolved["source_registry"] == "Registry Name"
    assert resolved["start_year"] == "Project Start Date"
    assert resolved["country"] == "Country"


def _series(months=40):
    return [SeriesPoint(date(2016 + i // 12, i % 12 + 1, 1), 0.6, 0.9, 3) for i in range(months)]


def test_sin_bosque_de_referencia_el_texto_no_culpa_a_las_nubes():
    inputs = AuditInputs(
        t0=date(2015, 1, 1),
        declared_area_ha=500.0,
        baseline_forest_ha=0.0,  # reforestación: no había bosque en 2000
        series=_series(),
        sensor="landsat",
    )
    outcome = IndexCalculator().calculate(inputs)
    text = build_narrative(outcome, "Proyecto ARR")

    assert outcome.category == INSUFFICIENT
    assert "bosque de referencia" in text
    assert "nubosidad" not in text
    assert "reforestación" in text


def test_con_pocas_imagenes_el_texto_si_menciona_las_nubes():
    inputs = AuditInputs(
        t0=date(2015, 1, 1),
        declared_area_ha=500.0,
        baseline_forest_ha=400.0,
        series=[],
        sensor="landsat",
        loss_by_year={},
    )
    text = build_narrative(IndexCalculator().calculate(inputs), "Proyecto AD")

    assert "nubosidad" in text


def test_la_comparacion_marca_los_anos_desde_t0():
    inputs = AuditInputs(
        t0=date(2013, 11, 13),
        declared_area_ha=100.0,
        baseline_forest_ha=90.0,
        series=_series(),
        loss_by_year={2012: 3.0, 2013: 1.0, 2014: 5.0},
    )
    rows = {r.year: r for r in compare_declared_observed(inputs)}

    assert not rows[2012].after_t0 and rows[2014].after_t0
    assert rows[2013].after_t0  # el 31-dic-2013 ya es posterior a T0


def test_conserva_solo_las_partes_mas_grandes():
    parcels = [box(i, 0, i + 0.1 * (i + 1), 0.1 * (i + 1)) for i in range(6)]  # áreas crecientes
    multi = MultiPolygon(parcels)

    kept = keep_largest_parts(multi, 2)

    assert len(kept.geoms) == 2
    assert {round(p.area, 3) for p in kept.geoms} == {
        round(parcels[5].area, 3),
        round(parcels[4].area, 3),
    }
    assert keep_largest_parts(multi, 10) is multi  # no hace nada si ya cabe
    assert keep_largest_parts(parcels[0], 1) is parcels[0]  # un polígono simple no se toca
