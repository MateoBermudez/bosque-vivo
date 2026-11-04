import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from bosquevivo.db.models import (
    AuditResult,
    AuditRun,
    ForestBaselineRecord,
    ForestLoss,
    NdviObservation,
    Project,
    ProjectDeclaration,
)

SOURCE = "snapshot del sitio (web/snapshot)"


@dataclass
class SnapshotSummary:
    projects: int = 0
    observations: int = 0
    losses: int = 0
    audits: int = 0
    declarations: int = 0


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _geometry(folder: Path, project_id: int) -> dict | None:
    for name in (f"{project_id}.detail.json", f"{project_id}.map.json"):
        feature = _read(folder / "geometry" / name)
        if feature:
            return feature.get("geometry", feature)
    return None


def load_snapshot(session: Session, folder: Path) -> SnapshotSummary:
    summary = SnapshotSummary()
    for item in _read(folder / "projects.json") or []:
        project_id = int(item["id"])
        geometry = _geometry(folder, project_id)
        if geometry is None:
            continue
        session.add(
            Project(
                id=project_id,
                source_registry=item["source_registry"],
                registry_id=item["registry_id"],
                name=item["name"],
                country=item.get("country"),
                project_type=item.get("project_type"),
                start_year=item.get("start_year"),
                area_ha=item.get("area_ha"),
                geometry=json.dumps(geometry),
                source=SOURCE,
            )
        )
        summary.projects += 1
        session.flush()
        for declaration in _read(folder / "declarations" / f"{project_id}.json") or []:
            session.add(
                ProjectDeclaration(
                    project_id=project_id,
                    field=declaration["field"],
                    value=str(declaration["value"]),
                    source_document=declaration.get("source_document"),
                    reviewed=True,
                )
            )
            summary.declarations += 1
        series = _read(folder / "series" / f"{project_id}.json") or {}
        for point in series.get("ndvi", []):
            session.add(
                NdviObservation(
                    project_id=project_id,
                    period=date.fromisoformat(point["period"]),
                    sensor=point["sensor"],
                    ndvi_mean=point.get("ndvi_mean"),
                    valid_fraction=point.get("valid_fraction") or 0.0,
                    scene_count=point.get("scene_count") or 0,
                )
            )
            summary.observations += 1
        for loss in series.get("loss", []):
            session.add(
                ForestLoss(
                    project_id=project_id,
                    year=int(loss["year"]),
                    ha_lost=float(loss["ha_lost"]),
                    source=SOURCE,
                )
            )
            summary.losses += 1
        audit = _read(folder / "audit" / f"{project_id}.json")
        if audit and audit.get("result"):
            result = audit["result"]
            run = AuditRun(
                id=int(audit["id"]),
                project_id=project_id,
                status=audit.get("status", "done"),
                index_version=audit.get("index_version", "v1"),
                git_sha=audit.get("git_sha"),
                dataset_versions=audit.get("dataset_versions") or {},
                created_at=datetime.fromisoformat(audit["created_at"]),
            )
            session.add(run)
            session.flush()
            session.add(
                AuditResult(
                    run_id=run.id,
                    score=result.get("score"),
                    category=result["category"],
                    components=result.get("components") or {},
                    confidence=result.get("confidence") or 0.0,
                    confidence_label=result.get("confidence_label") or "baja",
                    narrative=result.get("narrative"),
                )
            )
            summary.audits += 1
            permanence = (result.get("components") or {}).get("permanencia") or {}
            if permanence.get("ha_bosque_inicial"):
                session.add(
                    ForestBaselineRecord(
                        project_id=project_id,
                        tree_cover_ha=float(permanence["ha_bosque_inicial"]),
                        threshold_percent=30,
                        source=SOURCE,
                    )
                )
    session.flush()
    return summary
