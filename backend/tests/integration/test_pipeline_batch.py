import json

import pytest
from shapely.geometry import box

from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.db.models import AuditRun, Report
from bosquevivo.pipeline import (
    audit_project,
    generate_missing_reports,
    project_kind,
    run_batch,
    select_projects,
)
from bosquevivo.registry import ProjectRepository
from bosquevivo.satellite.providers.fake import FakeProvider


def add_project(db, registry_id, *, ptype, area, west=-75.0, registry="Verra", year=2015):
    geometry = box(west, 5.0, west + 0.1, 5.1)
    project, _ = ProjectRepository(db).upsert(
        {
            "source_registry": registry,
            "registry_id": registry_id,
            "name": f"Proyecto {registry_id}",
            "country": "Colombia",
            "project_type": ptype,
            "start_year": year,
            "area_ha": area,
            "geometry": json.dumps(geometry.__geo_interface__),
            "source": "karnik",
            "source_version": "v1",
        }
    )
    db.flush()
    return project


@pytest.fixture
def projects(db):
    created = {
        "grande": add_project(
            db, "AD-G", ptype="Deforestación evitada (AD)", area=9000, west=-76.0
        ),
        "chico": add_project(db, "AD-C", ptype="Deforestación evitada (AD)", area=100, west=-75.0),
        "ifm": add_project(
            db, "IFM-1", ptype="Manejo forestal mejorado (IFM)", area=500, west=-74.0
        ),
        "arr": add_project(db, "ARR-1", ptype="Reforestación (ARR)", area=300, west=-73.0),
        "demo": add_project(db, "DEMO-1", ptype="REDD+", area=50, west=-72.0, registry="demo"),
    }
    db.commit()  # como en la base real: lo que falla en el lote no debe arrastrar a los proyectos
    return created


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Deforestación evitada (AD)", "AD"),
        ("Reforestación (ARR)", "ARR"),
        ("REDD+", None),
        (None, None),
    ],
)
def test_project_kind(text, expected):
    assert project_kind(text) == expected


def test_selecciona_de_menor_a_mayor_area_y_omite_arr_y_demo(db, projects):
    selected = select_projects(db)

    assert [p.registry_id for p in selected] == ["AD-C", "IFM-1", "AD-G"]


def test_puede_incluir_reforestacion_y_limitar_cantidad_y_area(db, projects):
    assert "ARR-1" in {p.registry_id for p in select_projects(db, include_arr=True)}
    assert [p.registry_id for p in select_projects(db, limit=2)] == ["AD-C", "IFM-1"]
    assert [p.registry_id for p in select_projects(db, max_area_ha=1000)] == ["AD-C", "IFM-1"]


def test_audit_project_guarda_series_perdida_e_indice(db, projects, tmp_path):
    run = audit_project(db, FakeProvider(), tmp_path, projects["chico"].id)

    assert run.status == "done" and run.result is not None
    assert run.result.category in {"Alta", "Media", "Baja", "Insuficiente"}


def test_el_lote_calcula_en_orden_y_omite_lo_ya_hecho(db, projects, tmp_path):
    first = run_batch(db, FakeProvider(), tmp_path, select_projects(db, limit=1))
    assert [item.project_id for item in first] == [projects["chico"].id]

    pending = select_projects(db)
    assert projects["chico"].id not in {p.id for p in pending}
    assert projects["chico"].id in {p.id for p in select_projects(db, redo=True)}


def test_un_fallo_no_detiene_el_lote_y_se_informa(db, projects, tmp_path):
    class Flaky(FakeProvider):
        def get_forest_loss(self, geometry):
            ring = geometry["coordinates"][0]
            if min(x for x, _ in ring) == -75.0:  # el proyecto «chico»
                raise ExternalServiceError("Hansen no responde")
            return super().get_forest_loss(geometry)

    progress: list[tuple[int, int, bool]] = []
    items = run_batch(
        db,
        Flaky(),
        tmp_path,
        select_projects(db),
        on_item=lambda i, n, item: progress.append((i, n, item.ok)),
    )

    by_name = {item.name: item for item in items}
    assert not by_name["Proyecto AD-C"].ok
    assert "Hansen no responde" in (by_name["Proyecto AD-C"].error or "")
    assert by_name["Proyecto IFM-1"].ok and by_name["Proyecto AD-G"].ok
    assert progress == [(1, 3, False), (2, 3, True), (3, 3, True)]
    # lo que falló no dejó una corrida a medias
    assert db.query(AuditRun).filter_by(project_id=projects["chico"].id).count() == 0


def test_el_lote_genera_el_reporte_de_cada_proyecto(db, projects, tmp_path):
    reports = tmp_path / "reportes"

    run_batch(db, FakeProvider(), tmp_path, select_projects(db, limit=2), reports_dir=reports)

    assert len(list(reports.glob("*/run_*.html"))) == 2
    assert db.query(Report).filter_by(format="html").count() == 2


def test_genera_solo_los_reportes_que_faltan(db, projects, tmp_path):
    reports = tmp_path / "reportes"
    run_batch(db, FakeProvider(), tmp_path, select_projects(db))  # sin reportes
    assert generate_missing_reports(db, reports) == 3
    assert generate_missing_reports(db, reports) == 0  # ya están todos


def test_el_reparto_en_partes_cubre_todo_sin_repetir(db, projects):
    everything = [p.id for p in select_projects(db)]
    parts = [[p.id for p in select_projects(db, shard=(i, 2))] for i in range(2)]

    assert sorted(parts[0] + parts[1]) == sorted(everything)
    assert not set(parts[0]) & set(parts[1])
    assert [p.id for p in select_projects(db, shard=(0, 1))] == everything


def test_missing_index_recalcula_solo_lo_que_no_tiene_puntaje(db, projects, tmp_path):
    # un proyecto con índice completo y otro con resultado parcial (sin NDVI)
    run_batch(db, FakeProvider(), tmp_path, [projects["chico"]])

    class NoNdvi(FakeProvider):
        def get_timeseries(self, geometry, start, end, sensor):
            return []

    run_batch(db, NoNdvi(), tmp_path, [projects["ifm"]])

    pending = {p.registry_id for p in select_projects(db, missing_index=True)}

    assert "AD-C" not in pending  # ya tiene puntaje
    assert {"IFM-1", "AD-G"} <= pending  # parcial y sin auditoría
    assert {p.registry_id for p in select_projects(db)} == {
        "AD-G"
    }  # sin la opción: solo los nunca hechos
