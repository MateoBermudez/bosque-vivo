from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bosquevivo.db.base import Base, utcnow


def project_fk():
    return mapped_column(ForeignKey("project.id", ondelete="CASCADE"), index=True)


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (UniqueConstraint("source_registry", "registry_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_registry: Mapped[str] = mapped_column(String(40))
    registry_id: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(300), index=True)
    country: Mapped[str | None] = mapped_column(String(80), index=True)
    project_type: Mapped[str | None] = mapped_column(String(80))
    start_year: Mapped[int | None] = mapped_column(Integer)
    area_ha: Mapped[float | None] = mapped_column(Float)
    geometry: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120))
    source_version: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    declarations: Mapped[list["ProjectDeclaration"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectDeclaration(Base):
    __tablename__ = "project_declaration"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    field: Mapped[str] = mapped_column(String(80))
    value: Mapped[str] = mapped_column(Text)
    source_document: Mapped[str | None] = mapped_column(String(300))
    source_quote: Mapped[str | None] = mapped_column(Text)
    source_page: Mapped[int | None] = mapped_column(Integer)
    captured_by: Mapped[str] = mapped_column(String(60), default="manual")
    reviewed: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project] = relationship(back_populates="declarations")


class NdviObservation(Base):
    __tablename__ = "ndvi_observation"
    __table_args__ = (UniqueConstraint("project_id", "period", "sensor"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    period: Mapped[date] = mapped_column(Date)
    sensor: Mapped[str] = mapped_column(String(20))
    ndvi_mean: Mapped[float | None] = mapped_column(Float)
    ndvi_p10: Mapped[float | None] = mapped_column(Float)
    ndvi_p90: Mapped[float | None] = mapped_column(Float)
    valid_fraction: Mapped[float] = mapped_column(Float, default=0.0)
    scene_count: Mapped[int] = mapped_column(Integer, default=0)


class ForestLoss(Base):
    __tablename__ = "forest_loss"
    __table_args__ = (UniqueConstraint("project_id", "year", "source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    year: Mapped[int] = mapped_column(Integer)
    ha_lost: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(80))


class AuditRun(Base):
    __tablename__ = "audit_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    git_sha: Mapped[str | None] = mapped_column(String(40))
    dataset_versions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    index_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    result: Mapped["AuditResult | None"] = relationship(back_populates="run", uselist=False)


class AuditResult(Base):
    __tablename__ = "audit_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("audit_run.id", ondelete="CASCADE"), unique=True)
    score: Mapped[float | None] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(20))
    components: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_label: Mapped[str] = mapped_column(String(20), default="baja")
    narrative: Mapped[str | None] = mapped_column(Text)

    run: Mapped[AuditRun] = relationship(back_populates="result")


class Report(Base):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("audit_run.id", ondelete="CASCADE"), index=True)
    format: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ImageAsset(Base):
    __tablename__ = "image_asset"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"), index=True
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    sensor: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(20))
    path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    quality: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    kind: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AgentRun(Base):
    __tablename__ = "agent_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_ref: Mapped[str | None] = mapped_column(String(80), index=True)
    role: Mapped[str] = mapped_column(String(20))
    query_class: Mapped[str] = mapped_column(String(20))
    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(20))
    used_fallback: Mapped[bool] = mapped_column(default=False)
    validator_passed: Mapped[bool | None] = mapped_column()
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="AgentStep.position"
    )


class AgentStep(Base):
    __tablename__ = "agent_step"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("agent_run.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    tool: Mapped[str] = mapped_column(String(60))
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)

    run: Mapped[AgentRun] = relationship(back_populates="steps")


class Job(Base):
    __tablename__ = "job"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WaUser(Base):
    __tablename__ = "wa_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_hmac: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    consents: Mapped[list["ConsentLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ConsentLog(Base):
    __tablename__ = "consent_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("wa_user.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(40))
    notice_version: Mapped[str] = mapped_column(String(20))
    granted: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[WaUser] = relationship(back_populates="consents")


class ProcessedMessage(Base):
    __tablename__ = "processed_message"

    message_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KbChunk(Base):
    __tablename__ = "kb_chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
