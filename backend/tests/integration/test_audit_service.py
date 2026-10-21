import json
from datetime import date

import pytest

from bosquevivo.audit import AuditService
from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import AuditResult, Project, ProjectDeclaration
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]


@pytest.fixture
def project(db):
    item = Project(
        source_registry="test",
        registry_id="9",
        name="Reserva Prueba",
        start_year=2018,
        area_ha=1200.0,
        geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
        source="test",
    )
    db.add(item)
    db.commit()
    return item


def load(db, project, tmp_path, provider):
    sat = SatelliteService(db, provider, tmp_path)
    sat.refresh_timeseries(
        project.id, date(2016, 1, 1), date(2024, 12, 31), sensors=(Sensor.SENTINEL2,)
    )
    sat.refresh_forest_loss(project.id)
    db.commit()


def test_audit_run_persists_result_and_traceability(db, project, tmp_path):
    load(db, project, tmp_path, FakeProvider())
    run = AuditService(db, dataset_versions={"hansen": "test"}).run(project.id)
    db.commit()
    result = db.query(AuditResult).filter_by(run_id=run.id).one()
    assert run.status == "done"
    assert run.dataset_versions == {"hansen": "test"}
    assert run.parameters["version"] == "v0"
    assert result.score is not None
    assert "no una conclusión sobre intenciones" in (result.narrative or "")


def test_forest_loss_and_ndvi_drop_reduce_score(db, project, tmp_path):
    healthy = FakeProvider()
    load(db, project, tmp_path, healthy)
    good = AuditService(db).run(project.id)
    db.commit()
    damaged = FakeProvider(drop_year=2021, loss_by_year={2021: 600.0})
    load(db, project, tmp_path, damaged)
    bad = AuditService(db).run(project.id)
    db.commit()
    assert good.result and bad.result
    assert good.result.score is not None and bad.result.score is not None
    assert bad.result.score < good.result.score - 20


def test_declared_t0_overrides_registry_year(db, project):
    db.add(ProjectDeclaration(project_id=project.id, field="t0_date", value="2020-06-15"))
    db.commit()
    assert AuditService(db).resolve_t0(project) == date(2020, 6, 15)


def test_unreviewed_declaration_is_ignored(db, project):
    db.add(
        ProjectDeclaration(
            project_id=project.id, field="t0_date", value="2020-06-15", reviewed=False
        )
    )
    db.commit()
    assert AuditService(db).resolve_t0(project) == date(2018, 1, 1)


def test_unknown_project_raises(db):
    with pytest.raises(NotFoundError):
        AuditService(db).run(404)
