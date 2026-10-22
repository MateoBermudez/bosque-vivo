from datetime import date
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import box, mapping

from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.satellite.models import Sensor, ThumbnailKind
from bosquevivo.satellite.providers.opendata import (
    CompositeReading,
    OpenDataProvider,
    merge_by_day,
    monthly_points,
)


def reading(day, values, total=100):
    return CompositeReading(day=day, values=np.array(values, dtype=float), total_pixels=total)


def test_agrupa_los_compuestos_por_mes():
    readings = [
        reading(date(2019, 3, 5), [0.6, 0.8], total=4),
        reading(date(2019, 3, 21), [0.7], total=4),
        reading(date(2019, 4, 6), [0.5], total=4),
    ]

    points = monthly_points(readings, Sensor.MODIS, date(2019, 1, 1), date(2019, 12, 31))

    assert [p.period for p in points] == [date(2019, 3, 1), date(2019, 4, 1)]
    march = points[0]
    assert march.sensor == Sensor.MODIS
    assert march.ndvi_mean == pytest.approx(0.7)  # promedio de los tres píxeles buenos
    assert march.scene_count == 2
    assert march.valid_fraction == pytest.approx((2 / 4 + 1 / 4) / 2)
    assert march.ndvi_p10 is not None and march.ndvi_p90 is not None


def test_un_mes_sin_pixeles_buenos_queda_sin_valor_pero_con_fraccion_cero():
    points = monthly_points(
        [reading(date(2019, 3, 5), [], total=50)], Sensor.MODIS, date(2019, 1, 1), date(2020, 1, 1)
    )

    assert points[0].ndvi_mean is None
    assert points[0].valid_fraction == 0.0 and points[0].scene_count == 1


def test_descarta_los_meses_fuera_del_rango():
    readings = [
        reading(date(2018, 12, 20), [0.5]),
        reading(date(2019, 2, 3), [0.6]),
        reading(date(2020, 3, 1), [0.7]),
    ]

    points = monthly_points(readings, Sensor.MODIS, date(2019, 1, 15), date(2020, 1, 1))

    assert [p.period for p in points] == [date(2019, 2, 1)]


def test_une_las_baldosas_de_una_misma_fecha():
    merged = merge_by_day(
        [
            reading(date(2019, 3, 5), [0.6], total=10),
            reading(date(2019, 3, 5), [0.8, 0.7], total=20),
            reading(date(2019, 3, 21), [0.5], total=10),
        ]
    )

    assert [m.day for m in merged] == [date(2019, 3, 5), date(2019, 3, 21)]
    assert merged[0].total_pixels == 30 and merged[0].values.size == 3


def item(start, h=10, v=8):
    return SimpleNamespace(
        properties={
            "start_datetime": f"{start}T00:00:00Z",
            "modis:horizontal-tile": h,
            "modis:vertical-tile": v,
        },
        assets={},
    )


GEOMETRY = mapping(box(-77.5, 2.5, -77.4, 2.6))


def make_provider(items, reader):
    return OpenDataProvider(searcher=lambda bounds, start, end: items, reader=reader, workers=2)


def test_calcula_la_serie_mensual_a_partir_de_los_compuestos():
    def reader(it, polygon):
        day = date.fromisoformat(it.properties["start_datetime"][:10])
        return CompositeReading(day=day, values=np.array([0.7, 0.8]), total_pixels=4)

    provider = make_provider([item("2019-03-01"), item("2019-03-17"), item("2019-04-02")], reader)

    points = provider.get_timeseries(GEOMETRY, date(2019, 1, 1), date(2019, 12, 1), Sensor.MODIS)

    assert [p.period for p in points] == [date(2019, 3, 1), date(2019, 4, 1)]
    assert points[0].scene_count == 2 and points[0].ndvi_mean == pytest.approx(0.75)


def test_un_compuesto_que_falla_no_pierde_la_serie():
    def reader(it, polygon):
        if it.properties["start_datetime"].startswith("2019-03-17"):
            raise OSError("red caída")
        return CompositeReading(day=date(2019, 3, 9), values=np.array([0.6]), total_pixels=1)

    points = make_provider([item("2019-03-01"), item("2019-03-17")], reader).get_timeseries(
        GEOMETRY, date(2019, 1, 1), date(2019, 12, 1), Sensor.MODIS
    )

    assert len(points) == 1 and points[0].scene_count == 1


def test_si_todos_fallan_se_informa():
    def reader(it, polygon):
        raise OSError("sin conexión")

    with pytest.raises(ExternalServiceError, match="ningún compuesto"):
        make_provider([item("2019-03-01")], reader).get_timeseries(
            GEOMETRY, date(2019, 1, 1), date(2019, 12, 1), Sensor.MODIS
        )


def test_si_la_busqueda_falla_se_informa_con_un_error_claro():
    def searcher(bounds, start, end):
        raise RuntimeError("503")

    provider = OpenDataProvider(searcher=searcher, reader=lambda i, p: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(ExternalServiceError, match="MODIS"):
        provider.get_timeseries(GEOMETRY, date(2019, 1, 1), date(2019, 12, 1), Sensor.MODIS)


def test_otros_sensores_devuelven_vacio_y_no_hay_miniaturas():
    provider = make_provider([item("2019-03-01")], lambda i, p: None)  # type: ignore[arg-type,return-value]

    assert (
        provider.get_timeseries(GEOMETRY, date(2019, 1, 1), date(2019, 12, 1), Sensor.LANDSAT) == []
    )
    assert provider.default_sensors == (Sensor.MODIS,)
    with pytest.raises(ExternalServiceError):
        provider.get_thumbnail(
            GEOMETRY, date(2019, 1, 1), date(2019, 2, 1), ThumbnailKind.NATURAL, Sensor.MODIS
        )
    assert set(provider.dataset_versions()) == {"hansen", "modis"}
