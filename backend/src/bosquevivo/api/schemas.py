from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_registry: str
    registry_id: str
    name: str
    country: str | None
    project_type: str | None
    start_year: int | None
    area_ha: float | None


class AuditResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float | None
    category: str
    components: dict[str, Any]
    confidence: float
    confidence_label: str
    narrative: str | None


class AuditRunOut(BaseModel):
    id: int
    project_id: int
    status: str
    index_version: str
    git_sha: str | None
    dataset_versions: dict[str, Any]
    created_at: datetime
    result: AuditResultOut | None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    status: str
    attempts: int
    result: dict[str, Any] | None
    error: str | None


class ImportRequest(BaseModel):
    path: str
    source: str
    source_version: str | None = None
    country: str | None = None
    limit: int | None = None


class ImportOut(BaseModel):
    created: int
    updated: int
    repaired: int
    skipped: int


class SeriesPointOut(BaseModel):
    period: str
    sensor: str
    ndvi_mean: float | None
    valid_fraction: float
    scene_count: int


class LossOut(BaseModel):
    year: int
    ha_lost: float


class SeriesOut(BaseModel):
    t0: str | None
    ndvi: list[SeriesPointOut]
    loss: list[LossOut]
    comparison: list[dict[str, Any]]
