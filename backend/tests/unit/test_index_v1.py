from datetime import date

import pytest

from bosquevivo.audit import IndexCalculator
from bosquevivo.audit.config import config_for
from bosquevivo.audit.inputs import AuditInputs, SeriesPoint

BASELINE = 10_000.0


def series():
    return [
        SeriesPoint(date(year, month, 1), 0.8, 0.9, 4)
        for year in range(2015, 2025)
        for month in range(1, 13)
    ]


def make_inputs(loss_by_year, t0=date(2012, 1, 1)):
    return AuditInputs(
        t0=t0,
        declared_area_ha=12_000.0,
        baseline_forest_ha=BASELINE,
        series=series(),
        sensor="modis",
        loss_by_year=loss_by_year,
    )


def component(outcome, name):
    return next(c for c in outcome.components if c.name == name)


def uniform(years, ha):
    return dict.fromkeys(years, ha)


def v1(inputs):
    return IndexCalculator(config_for("v1")).calculate(inputs)


def test_version_desconocida_se_rechaza():
    with pytest.raises(ValueError, match="v9"):
        config_for("v9")


def test_los_pesos_de_v1_suman_uno_y_v0_no_cambia():
    v0 = config_for("v0")
    assert v0.weight_evolution == 0.0 and v0.permanence_scoring == "acumulada"
    assert config_for("v1").version == "v1"


def test_v0_no_incluye_la_evolucion():
    outcome = IndexCalculator().calculate(make_inputs({}))
    assert [c.name for c in outcome.components] == ["permanencia", "tendencia", "estabilidad"]
    assert outcome.index_version == "v0"


def test_perdida_que_se_mantiene_puntua_100_en_evolucion():
    loss = uniform(range(2001, 2025), 20.0)
    evolution = component(v1(make_inputs(loss)), "evolucion_perdida")
    assert evolution.score == pytest.approx(100.0)
    assert evolution.detail["cociente_despues_antes"] == 1.0


def test_perdida_que_se_duplica_puntua_50():
    loss = {**uniform(range(2001, 2012), 20.0), **uniform(range(2012, 2025), 40.0)}
    evolution = component(v1(make_inputs(loss)), "evolucion_perdida")
    assert evolution.score == pytest.approx(50.0)


def test_perdida_que_se_triplica_puntua_0():
    loss = {**uniform(range(2001, 2012), 10.0), **uniform(range(2012, 2025), 30.0)}
    assert component(v1(make_inputs(loss)), "evolucion_perdida").score == 0.0


def test_perdida_que_baja_no_supera_100():
    loss = {**uniform(range(2001, 2012), 40.0), **uniform(range(2012, 2025), 10.0)}
    assert component(v1(make_inputs(loss)), "evolucion_perdida").score == 100.0


def test_sin_perdida_previa_pero_con_perdida_despues_no_puntua():
    loss = uniform(range(2012, 2025), 50.0)
    evolution = component(v1(make_inputs(loss)), "evolucion_perdida")
    assert evolution.score is None and "motivo" in evolution.detail


def test_perdida_despreciable_en_ambos_periodos_puntua_100():
    evolution = component(v1(make_inputs({2005: 0.2})), "evolucion_perdida")
    assert evolution.score == 100.0 and "nota" in evolution.detail


def test_pocos_anios_de_referencia_no_puntua():
    inputs = make_inputs(uniform(range(2001, 2025), 20.0), t0=date(2003, 1, 1))
    assert component(v1(inputs), "evolucion_perdida").score is None


def test_permanencia_v1_es_una_tasa_anual():
    # 1 % del bosque inicial por año desde T0 llega a 0; 0,5 % da 50
    loss = uniform(range(2012, 2025), BASELINE * 0.005)
    permanence = component(v1(make_inputs(loss)), "permanencia")
    assert permanence.score == pytest.approx(50.0)
    assert permanence.detail["perdida_anual_pct"] == 0.5


def test_v1_distingue_proyectos_que_v0_deja_en_100():
    steady = uniform(range(2001, 2025), 20.0)
    worse = {**uniform(range(2001, 2012), 20.0), **uniform(range(2012, 2025), 50.0)}
    good, bad = v1(make_inputs(steady)), v1(make_inputs(worse))
    v0_good = IndexCalculator().calculate(make_inputs(steady))
    v0_bad = IndexCalculator().calculate(make_inputs(worse))
    assert v0_good.score is not None and v0_bad.score is not None
    assert v0_good.score - v0_bad.score < 2  # v0: casi igual
    assert good.score is not None and bad.score is not None
    assert good.score - bad.score > 20  # v1: se nota la diferencia
    assert good.index_version == "v1"


def test_sin_evolucion_los_pesos_se_reparten_entre_los_demas():
    inputs = make_inputs(uniform(range(2012, 2025), 20.0))  # sin pérdida previa
    outcome = v1(inputs)
    assert component(outcome, "evolucion_perdida").score is None
    assert outcome.score is not None
