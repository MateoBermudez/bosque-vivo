from datetime import date

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.satellite.factory import build_provider
from bosquevivo.satellite.models import Sensor, ThumbnailKind
from bosquevivo.satellite.providers.hansen import (
    HansenOpenProvider,
    pixel_area_ha,
    tile_name,
    tiles_for,
)

PIXEL = 0.001  # grados (~110 m)
# Un píxel de 0,001° a ~2,5° de latitud mide ~110,6 m x 111,3 m ≈ 1,231 ha
HA_PER_PIXEL = 1.2312


def write_tile(path, array, west, north):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(west, north, PIXEL, PIXEL),
    ) as destination:
        destination.write(array, 1)


def make_layers(tmp_path, tile, *, west, north, cover, loss):
    write_tile(tmp_path / f"lossyear_{tile}.tif", loss, west, north)
    write_tile(tmp_path / f"treecover2000_{tile}.tif", cover, west, north)


@pytest.fixture
def template(tmp_path):
    return str(tmp_path / "{layer}_{tile}.tif")


def test_los_tiles_se_nombran_por_su_esquina_superior_izquierda():
    assert tile_name(-80, 10) == "10N_080W"
    assert tile_name(-70, 0) == "00N_070W"
    assert tile_name(-70, -10) == "10S_070W"
    assert tile_name(10, 40) == "40N_010E"


def test_busca_los_tiles_que_toca_un_poligono():
    assert [n for n, _ in tiles_for((-77.355, 3.288, -77.022, 3.595))] == ["10N_080W"]
    cruce = {n for n, _ in tiles_for((-70.5, -0.5, -69.5, 0.5))}
    assert cruce == {"10N_080W", "10N_070W", "00N_080W", "00N_070W"}


def test_el_area_del_pixel_disminuye_hacia_los_polos():
    equator, mid, high = pixel_area_ha(np.array([0.0, 45.0, 70.0]), PIXEL)
    assert equator == pytest.approx(1.2321, rel=0.01)
    assert equator > mid > high


def test_calcula_bosque_base_y_perdida_solo_dentro_del_bosque(tmp_path, template):
    cover = np.full((100, 100), 80, dtype="uint8")
    cover[:10, :] = 20  # primeras 10 filas: no es bosque (< 30 %)
    loss = np.zeros((100, 100), dtype="uint8")
    loss[20:30, :10] = 5  # 100 px en 2005, dentro del bosque
    loss[40:45, :10] = 22  # 50 px en 2022, dentro del bosque
    loss[0:5, :10] = 7  # 50 px en 2007 pero fuera del bosque: no cuenta
    make_layers(tmp_path, "10N_080W", west=-77.5, north=2.6, cover=cover, loss=loss)
    provider = HansenOpenProvider(template)
    geometry = mapping(box(-77.5, 2.5, -77.4, 2.6))

    baseline = provider.get_forest_baseline(geometry)
    losses = {p.year: p.ha_lost for p in provider.get_forest_loss(geometry)}

    assert baseline.threshold_percent == 30
    assert baseline.tree_cover_ha == pytest.approx(9000 * HA_PER_PIXEL, rel=0.015)
    assert set(losses) == {2005, 2022}
    assert losses[2005] == pytest.approx(100 * HA_PER_PIXEL, rel=0.015)
    assert losses[2022] == pytest.approx(50 * HA_PER_PIXEL, rel=0.015)


def test_suma_los_tiles_cuando_el_poligono_cruza_un_limite(tmp_path, template):
    forest = np.full((100, 100), 80, dtype="uint8")
    none = np.zeros((100, 100), dtype="uint8")
    make_layers(tmp_path, "10N_080W", west=-70.1, north=2.6, cover=forest, loss=none)
    make_layers(tmp_path, "10N_070W", west=-70.0, north=2.6, cover=forest, loss=none)
    provider = HansenOpenProvider(template)

    baseline = provider.get_forest_baseline(mapping(box(-70.05, 2.5, -69.95, 2.6)))

    # 50 columnas en cada tile x 100 filas
    assert baseline.tree_cover_ha == pytest.approx(10_000 * HA_PER_PIXEL, rel=0.015)


def test_lee_cada_capa_una_sola_vez_por_poligono(tmp_path, template):
    forest = np.full((100, 100), 80, dtype="uint8")
    make_layers(
        tmp_path, "10N_080W", west=-77.5, north=2.6, cover=forest, loss=np.zeros_like(forest)
    )
    provider = HansenOpenProvider(template)
    reads: list[str] = []
    original = provider._read_window

    def counting(layer, tile, geometry):
        reads.append(layer)
        return original(layer, tile, geometry)

    provider._read_window = counting  # type: ignore[method-assign]
    geometry = mapping(box(-77.5, 2.5, -77.4, 2.6))

    provider.get_forest_loss(geometry)
    provider.get_forest_baseline(geometry)

    assert reads == ["lossyear", "treecover2000"]


def test_no_calcula_ndvi_ni_miniaturas(template):
    provider = HansenOpenProvider(template)
    geometry = mapping(box(-77.5, 2.5, -77.4, 2.6))

    assert (
        provider.get_timeseries(geometry, date(2015, 1, 1), date(2016, 1, 1), Sensor.LANDSAT) == []
    )
    with pytest.raises(ExternalServiceError):
        provider.get_thumbnail(
            geometry, date(2015, 1, 1), date(2016, 1, 1), ThumbnailKind.NATURAL, Sensor.SENTINEL2
        )
    assert "hansen" in provider.dataset_versions()


def test_un_archivo_inexistente_da_un_error_claro(template):
    provider = HansenOpenProvider(template)

    with pytest.raises(ExternalServiceError, match="Hansen"):
        provider.get_forest_baseline(mapping(box(-77.5, 2.5, -77.4, 2.6)))


def test_la_fabrica_ofrece_el_proveedor_hansen():
    assert isinstance(build_provider(Settings(satellite_provider="hansen")), HansenOpenProvider)
