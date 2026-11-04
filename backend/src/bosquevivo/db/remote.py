import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import Date, DateTime, Engine, Table, func, insert, select
from sqlalchemy.orm import Session

from bosquevivo.db.base import Base
from bosquevivo.db.migrate import _reset_sequences, _too_long
from bosquevivo.db.session import init_db
from bosquevivo.db.urls import is_postgres

MAX_BATCH_BYTES = 3_000_000
CLEAR_CONFIRMATION = "BORRAR"


def table_by_name(name: str) -> Table:
    table = Base.metadata.tables.get(name)
    if table is None:
        raise KeyError(name)
    return table


def _coerce(table: Table, row: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, raw in row.items():
        if key not in table.columns:
            continue
        column_type = table.columns[key].type
        value = raw
        if isinstance(raw, str) and isinstance(column_type, DateTime):
            value = datetime.fromisoformat(raw)
        elif isinstance(raw, str) and isinstance(column_type, Date):
            value = date.fromisoformat(raw)
        clean[key] = value
    return clean


def restore_rows(session: Session, table_name: str, rows: list[dict[str, Any]]) -> int:
    table = table_by_name(table_name)
    if rows:
        session.execute(insert(table), [_coerce(table, row) for row in rows])
    return len(rows)


def table_counts(session: Session) -> dict[str, int]:
    return {
        table.name: session.scalar(select(func.count()).select_from(table)) or 0
        for table in Base.metadata.sorted_tables
    }


def clear_all(session: Session) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())


def finish_restore(session: Session) -> dict[str, int]:
    session.flush()
    bind = session.get_bind()
    if isinstance(bind, Engine) and is_postgres(bind.url):
        session.commit()
        _reset_sequences(bind, list(Base.metadata.sorted_tables))
    return table_counts(session)


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(type(value).__name__)


def _batches(rows: Iterator[dict[str, Any]]) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    size = 0
    for row in rows:
        length = len(json.dumps(row, default=_json_default))
        if batch and size + length > MAX_BATCH_BYTES:
            yield batch
            batch, size = [], 0
        batch.append(row)
        size += length
    if batch:
        yield batch


@dataclass
class PushReport:
    sent: dict[str, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


def push_database(
    source: Engine,
    client: httpx.Client,
    *,
    replace: bool = False,
    on_table: Callable[[str, int], None] | None = None,
) -> PushReport:
    init_db(source)
    report = PushReport()
    tables = list(Base.metadata.sorted_tables)
    for table in tables:
        report.problems.extend(_too_long(source, table))
    if report.problems:
        return report
    remote = client.get("/api/v1/admin/restore").raise_for_status().json()
    occupied = [name for name, count in remote["counts"].items() if count]
    if occupied and not replace:
        report.problems.append(
            "la base remota ya tiene datos en: "
            + ", ".join(occupied)
            + " (use --replace para borrarlos y subir de nuevo)"
        )
        return report
    if occupied:
        client.post(
            "/api/v1/admin/restore/clear", json={"confirm": CLEAR_CONFIRMATION}
        ).raise_for_status()
    with source.connect() as reader:
        for table in tables:
            rows = (dict(row) for row in reader.execute(select(table)).mappings())
            sent = 0
            for batch in _batches(rows):
                payload = json.dumps(
                    {"table": table.name, "rows": batch}, default=_json_default
                ).encode()
                client.post(
                    "/api/v1/admin/restore",
                    content=payload,
                    headers={"Content-Type": "application/json"},
                ).raise_for_status()
                sent += len(batch)
            report.sent[table.name] = sent
            if on_table:
                on_table(table.name, sent)
    counts = client.post("/api/v1/admin/restore/finish").raise_for_status().json()["counts"]
    for name, sent in report.sent.items():
        if counts.get(name) != sent:
            report.problems.append(
                f"{name}: se enviaron {sent} filas y la base tiene {counts.get(name)}"
            )
    return report
