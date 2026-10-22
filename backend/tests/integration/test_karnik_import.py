import json
from datetime import date

import geopandas as gpd
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box, shape

from bosquevivo.api.routers import projects as router
from bosquevivo.audit.service import AuditService
from bosquevivo.core.errors import ValidationFailedError
from bosquevivo.db.models import Project, ProjectDeclaration
from bosquevivo.registry import ProjectRepository, import_karnik
from bosquevivo.registry.geometry import MAX_ANALYSIS_VERTICES, simplify_geometry, vertex_count

COLUMNS = [
    "Project Name",
    "ProjectID",
    "Registry Name",
    "Methodology",
    "Project Type",
    "Country",
    "Project Developer Name",
    "Project Start Date",
    "Project End Date",
    "Date of Entry",
    "Processing Approach",
    "PD Declined to Provide",
    "Geometry Type",
    "Project Area",
    "Project Accounting Area",
    "Project Reference Region",
]


def record(
    project_id,
    name,
    *,
    project_type="AD",
    country="Colombia",
    start="11/13/2013",
    geometry_type="Polygon",
    registry="Verra",
    accounting=None,
    geometry=None,
):
    row = dict.fromkeys(COLUMNS)
    row.update(
        {
            "Project Name": name,
            "ProjectID": project_id,
            "Registry Name": registry,
            "Project Type": project_type,
            "Country": country,
            "Project Start Date": start,
            "Project End Date": "11/12/2043",
            "Methodology": "VM0006",
            "Project Developer Name": "Comunidad de prueba",
            "Processing Approach": "Official",
            "Geometry Type": geometry_type,
            "Project Accounting Area": accounting,
        }
    )
    return row, geometry


@pytest.fixture
def karnik_file(tmp_path):
    bowtie = Polygon([(-74.0, 4.0), (-73.9, 4.1), (-73.9, 4.0), (-74.0, 4.1), (-74.0, 4.0)])
    huge = Point(-72.0, 3.0).buffer(0.05, quad_segs=8000)
    records = [
        record(
            "VCS1",
            "Cajambre REDD+",
            geometry=box(-77.0, 3.0, -76.9, 3.1),
            accounting=box(-77.0, 3.0, -76.95, 3.05).wkt,
        ),
        record(
            "ER2",
            "Predio con autointersección",
            project_type="ARR",
            geometry=bowtie,
            registry="EcoRegistry",
            start="01/01/2018",
        ),
        record("ER3", "Solo un punto", geometry_type="Point", geometry=Point(-75.0, 5.0)),
        record("VCS4", "Proyecto de Perú", country="Peru", geometry=box(-70.0, -5.0, -69.9, -4.9)),
        record("ER5", "Polígono gigante", project_type="IFM", geometry=huge),
    ]
    frame = gpd.GeoDataFrame(
        [r for r, _ in records], geometry=[g for _, g in records], crs="EPSG:4326"
    )
    path = tmp_path / "south_america.gpkg"
    frame.to_file(path, driver="GPKG")
    return path


def test_importa_colombia_con_las_reglas_de_karnik(db, karnik_file):
    summary = import_karnik(db, karnik_file, country="Colombia")

    assert summary.created == 3 and summary.updated == 0
    assert summary.skipped_points == ["ER3 (Solo un punto)"]
    assert summary.repaired >= 1
    assert summary.accounting_area_used == 1
    assert summary.simplified == 1
    assert {p.registry_id for p in db.query(Project)} == {"VCS1", "ER2", "ER5"}


def test_conserva_nombre_registro_tipo_y_anio(db, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    cajambre = ProjectRepository(db).find_by_registry("Verra", "VCS1")
    arr = ProjectRepository(db).find_by_registry("EcoRegistry", "ER2")

    assert cajambre.name == "Cajambre REDD+"
    assert cajambre.project_type == "Deforestación evitada (AD)"
    assert cajambre.start_year == 2013
    assert cajambre.source == "karnik"
    assert arr.project_type == "Reforestación (ARR)"
    assert arr.start_year == 2018


def test_audita_el_area_de_contabilidad_cuando_existe(db, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    cajambre = ProjectRepository(db).find_by_registry("Verra", "VCS1")

    stored = shape(json.loads(cajambre.geometry))
    assert stored.bounds == pytest.approx((-77.0, 3.0, -76.95, 3.05))
    sources = {
        d.value
        for d in db.query(ProjectDeclaration).filter_by(
            project_id=cajambre.id, field="geometry_source"
        )
    }
    assert sources == {"área de contabilidad (Official)"}


def test_t0_sale_de_la_fecha_completa_de_inicio(db, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    cajambre = ProjectRepository(db).find_by_registry("Verra", "VCS1")

    assert AuditService(db).resolve_t0(cajambre) == date(2013, 11, 13)


def test_simplifica_poligonos_enormes_sin_cambiar_su_area(db, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    giant = db.query(Project).filter_by(registry_id="ER5").one()

    assert vertex_count(shape(json.loads(giant.geometry))) <= MAX_ANALYSIS_VERTICES
    assert "simplif." in giant.source_version
    assert len(giant.source_version) <= 80
    expected_ha = Point(-72.0, 3.0).buffer(0.05).area * (111_320**2) / 10_000  # aprox.
    assert giant.area_ha == pytest.approx(expected_ha, rel=0.15)


def test_repara_geometrias_invalidas(db, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    project = db.query(Project).filter_by(registry_id="ER2").one()

    assert shape(json.loads(project.geometry)).is_valid
    assert project.area_ha > 0


def test_importar_dos_veces_no_duplica(db, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    second = import_karnik(db, karnik_file, country="Colombia")

    assert second.created == 0 and second.updated == 3
    assert db.query(Project).count() == 3
    total = db.query(ProjectDeclaration).filter_by(captured_by="import:karnik").count()
    # crediting_start, geometry_source, methodology, developer, crediting_end, processing_approach
    assert total == 3 * 6


def test_sin_filtro_de_pais_importa_todo_lo_auditable(db, karnik_file):
    summary = import_karnik(db, karnik_file)

    assert summary.created == 4
    assert len(summary.skipped_points) == 1


def test_rechaza_archivos_que_no_son_de_karnik(db, tmp_path):
    path = tmp_path / "otro.gpkg"
    gpd.GeoDataFrame({"nombre": ["x"]}, geometry=[box(0, 0, 1, 1)], crs="EPSG:4326").to_file(
        path, driver="GPKG"
    )
    with pytest.raises(ValidationFailedError, match="Karnik"):
        import_karnik(db, path)


def test_endpoint_de_geometria_puede_aligerar_el_poligono(db, client):
    huge = Point(-72.0, 3.0).buffer(0.05, quad_segs=2000)
    project, _ = ProjectRepository(db).upsert(
        {
            "source_registry": "Verra",
            "registry_id": "ER9",
            "name": "Grande",
            "country": "Colombia",
            "project_type": None,
            "start_year": 2015,
            "area_ha": 1.0,
            "geometry": json.dumps(huge.__geo_interface__),
            "source": "karnik",
            "source_version": "v1",
        }
    )
    db.flush()

    full = client.get(f"/api/v1/projects/{project.id}/geometry").json()["geometry"]
    light = client.get(f"/api/v1/projects/{project.id}/geometry?simplify=0.002").json()["geometry"]

    assert vertex_count(shape(light)) < vertex_count(shape(full)) / 10
    assert shape(light).is_valid
    assert simplify_geometry(shape(full), 0.002).equals_exact(shape(light), 1e-9)
    assert client.get(f"/api/v1/projects/{project.id}/geometry?simplify=5").status_code == 422


def test_endpoint_de_geometria_limita_las_partes(db, client):
    parcels = MultiPolygon(
        [box(-75 + i * 0.01, 5.0, -75 + i * 0.01 + 0.005, 5.005) for i in range(30)]
    )
    project, _ = ProjectRepository(db).upsert(
        {
            "source_registry": "EcoRegistry",
            "registry_id": "ER10",
            "name": "Muchas parcelas",
            "country": "Colombia",
            "project_type": None,
            "start_year": 2015,
            "area_ha": 1.0,
            "geometry": json.dumps(parcels.__geo_interface__),
            "source": "karnik",
            "source_version": "v1",
        }
    )
    db.flush()

    light = client.get(f"/api/v1/projects/{project.id}/geometry?max_parts=5").json()["geometry"]
    full = client.get(f"/api/v1/projects/{project.id}/geometry").json()["geometry"]

    assert len(shape(light).geoms) == 5
    assert len(shape(full).geoms) == 30
    assert client.get(f"/api/v1/projects/{project.id}/geometry?max_parts=0").status_code == 422


def test_la_ficha_del_proyecto_se_expone_por_la_api(db, client, karnik_file):
    import_karnik(db, karnik_file, country="Colombia")
    project = ProjectRepository(db).find_by_registry("Verra", "VCS1")

    declarations = client.get(f"/api/v1/projects/{project.id}/declarations").json()
    by_field = {d["field"]: d["value"] for d in declarations}

    assert by_field["crediting_start"] == "2013-11-13"
    assert by_field["crediting_end"] == "2043-11-12"
    assert by_field["methodology"] == "VM0006"
    assert by_field["developer"] == "Comunidad de prueba"
    assert by_field["processing_approach"] == "Official"
    assert by_field["geometry_source"] == "área de contabilidad (Official)"
    assert all("Karnik" in (d["source_document"] or "") for d in declarations)
    assert client.get("/api/v1/projects/9999/declarations").status_code == 404


def test_el_poligono_liviano_se_calcula_una_sola_vez(db, client, monkeypatch):
    parcels = MultiPolygon(
        [box(-75 + i * 0.01, 5.0, -75 + i * 0.01 + 0.005, 5.005) for i in range(20)]
    )
    project, _ = ProjectRepository(db).upsert(
        {
            "source_registry": "EcoRegistry",
            "registry_id": "ER11",
            "name": "Con caché",
            "country": "Colombia",
            "project_type": None,
            "start_year": 2015,
            "area_ha": 1.0,
            "geometry": json.dumps(parcels.__geo_interface__),
            "source": "karnik",
            "source_version": "v1",
        }
    )
    db.flush()
    calls: list[int] = []
    original = router.simplify_geometry

    def counting(geom, tolerance, max_parts=None):
        calls.append(1)
        return original(geom, tolerance, max_parts)

    monkeypatch.setattr(router, "simplify_geometry", counting)
    router._LIGHT_CACHE.clear()
    url = f"/api/v1/projects/{project.id}/geometry?simplify=0.005&max_parts=5"

    first = client.get(url).json()
    second = client.get(url).json()

    assert first == second and len(calls) == 1
