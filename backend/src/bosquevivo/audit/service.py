import subprocess
import time
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from bosquevivo.audit.index import IndexCalculator, IndexOutcome
from bosquevivo.audit.inputs import AuditInputs, SeriesPoint
from bosquevivo.audit.narrative import build_narrative
from bosquevivo.core.errors import NotFoundError
from bosquevivo.db.models import (
    AuditResult,
    AuditRun,
    ForestBaselineRecord,
    ForestLoss,
    NdviObservation,
    Project,
    ProjectDeclaration,
)

T0_FIELDS = ("t0_date", "crediting_start", "credit_start_year")


def current_git_sha() -> str | None:
    try:
        root = Path(__file__).resolve().parents[3]
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def parse_t0(value: str) -> date | None:
    text = value.strip()
    try:
        if len(text) == 4 and text.isdigit():
            return date(int(text), 1, 1)
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


class AuditService:
    def __init__(
        self,
        session: Session,
        calculator: IndexCalculator | None = None,
        dataset_versions: dict[str, str] | None = None,
    ) -> None:
        self.session = session
        self.calculator = calculator or IndexCalculator()
        self.dataset_versions = dataset_versions or {}

    def resolve_t0(self, project: Project) -> date | None:
        stmt = select(ProjectDeclaration).where(
            ProjectDeclaration.project_id == project.id,
            ProjectDeclaration.field.in_(T0_FIELDS),
            ProjectDeclaration.reviewed.is_(True),
        )
        for declaration in self.session.scalars(stmt):
            parsed = parse_t0(declaration.value)
            if parsed:
                return parsed
        return date(project.start_year, 1, 1) if project.start_year else None

    def build_inputs(self, project: Project) -> AuditInputs:
        rows = self.session.scalars(
            select(NdviObservation)
            .where(NdviObservation.project_id == project.id)
            .order_by(NdviObservation.period)
        ).all()
        sensors: dict[str, list[NdviObservation]] = {}
        for row in rows:
            sensors.setdefault(row.sensor, []).append(row)
        sensor = max(
            sensors,
            key=lambda name: sum(1 for r in sensors[name] if r.ndvi_mean is not None),
            default="s2",
        )
        series = [
            SeriesPoint(r.period, r.ndvi_mean, r.valid_fraction, r.scene_count)
            for r in sensors.get(sensor, [])
        ]
        loss = {
            r.year: r.ha_lost
            for r in self.session.scalars(
                select(ForestLoss).where(ForestLoss.project_id == project.id)
            )
        }
        baseline = self.session.scalars(
            select(ForestBaselineRecord).where(ForestBaselineRecord.project_id == project.id)
        ).first()
        return AuditInputs(
            t0=self.resolve_t0(project),
            declared_area_ha=project.area_ha,
            baseline_forest_ha=baseline.tree_cover_ha if baseline else None,
            series=series,
            sensor=sensor,
            loss_by_year=loss,
        )

    def run(self, project_id: int) -> AuditRun:
        project = self.session.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"proyecto {project_id} no existe")
        config = self.calculator.config
        run = AuditRun(
            project_id=project_id,
            status="running",
            parameters=config.model_dump(),
            git_sha=current_git_sha(),
            dataset_versions=self.dataset_versions,
            index_version=config.version,
        )
        self.session.add(run)
        self.session.flush()
        started = time.monotonic()
        inputs = self.build_inputs(project)
        outcome = self.calculator.calculate(inputs)
        self._store(run, project, outcome, inputs)
        run.status = "done"
        run.duration_seconds = round(time.monotonic() - started, 3)
        self.session.flush()
        return run

    def _store(
        self, run: AuditRun, project: Project, outcome: IndexOutcome, inputs: AuditInputs
    ) -> None:
        components = outcome.components_payload()
        components["_sensor"] = inputs.sensor
        components["_sensibilidad"] = outcome.sensitivity
        self.session.add(
            AuditResult(
                run_id=run.id,
                score=outcome.score,
                category=outcome.category,
                components=components,
                confidence=outcome.confidence.value,
                confidence_label=outcome.confidence.label,
                narrative=build_narrative(outcome, project.name),
            )
        )

    def latest(self, project_id: int) -> AuditRun | None:
        return self.session.scalars(
            select(AuditRun)
            .where(AuditRun.project_id == project_id, AuditRun.status == "done")
            .order_by(AuditRun.id.desc())
        ).first()
