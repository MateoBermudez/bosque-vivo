import json
from datetime import date
from pathlib import Path

import pytest

from bosquevivo.audit import AuditService
from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import Project
from bosquevivo.reports import ReportService
from bosquevivo.satellite import SatelliteService, Sensor
from bosquevivo.satellite.providers import FakeProvider

RING = [[-75.0, 5.0], [-74.9, 5.0], [-74.9, 5.1], [-75.0, 5.1], [-75.0, 5.0]]


@pytest.fixture
def run(db, tmp_path):
    project = Project(
        source_registry="test",
        registry_id="7",
        name="Reserva <Demo>",
        country="Colombia",
        start_year=2018,
        area_ha=1000.0,
        geometry=json.dumps({"type": "Polygon", "coordinates": [RING]}),
        source="test",
    )
    db.add(project)
    db.commit()
    sat = SatelliteService(db, FakeProvider(), tmp_path)
    sat.refresh_timeseries(
        project.id, date(2016, 1, 1), date(2024, 12, 31), sensors=(Sensor.SENTINEL2,)
    )
    sat.refresh_forest_loss(project.id)
    created = AuditService(db, dataset_versions={"hansen": "test"}).run(project.id)
    db.commit()
    return created


def test_html_report_contains_traceability_and_limitations(db, run, tmp_path):
    report = ReportService(db, tmp_path / "reports").generate(run.id, "html")
    text = Path(report.path).read_text(encoding="utf-8")
    assert "Trazabilidad" in text
    assert "Limitaciones" in text
    assert "hansen" in text
    assert len(report.sha256) == 64


def test_html_report_escapes_project_name(db, run, tmp_path):
    report = ReportService(db, tmp_path / "reports").generate(run.id, "html")
    text = Path(report.path).read_text(encoding="utf-8")
    assert "Reserva &lt;Demo&gt;" in text
    assert "Reserva <Demo>" not in text


def test_html_report_avoids_accusatory_language(db, run, tmp_path):
    report = ReportService(db, tmp_path / "reports").generate(run.id, "html")
    text = Path(report.path).read_text(encoding="utf-8").lower()
    assert "fraude" not in text
    assert "estafa" not in text


def test_pdf_report_is_valid_pdf(db, run, tmp_path):
    report = ReportService(db, tmp_path / "reports").generate(run.id, "pdf")
    assert Path(report.path).read_bytes()[:5] == b"%PDF-"


def test_unknown_run_raises(db, tmp_path):
    with pytest.raises(NotFoundError):
        ReportService(db, tmp_path).generate(999)
