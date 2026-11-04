from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import Engine, String, Table, func, insert, select, text

from bosquevivo.db.base import Base
from bosquevivo.db.session import init_db
from bosquevivo.db.urls import is_postgres

BATCH = 500


@dataclass
class MigrationReport:
    copied: dict[str, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


def _count(engine: Engine, table: Table) -> int:
    with engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(table)) or 0


def _too_long(engine: Engine, table: Table) -> list[str]:
    problems: list[str] = []
    with engine.connect() as connection:
        for column in table.columns:
            if isinstance(column.type, String) and column.type.length:
                longest = connection.scalar(select(func.max(func.length(column))))
                if longest and longest > column.type.length:
                    problems.append(
                        f"{table.name}.{column.name}: hay valores de {longest} caracteres "
                        f"(máximo {column.type.length})"
                    )
    return problems


def _reset_sequences(engine: Engine, tables: list[Table]) -> None:
    with engine.begin() as connection:
        for table in tables:
            if "id" not in table.columns or not table.columns["id"].autoincrement:
                continue
            if table.columns["id"].type.python_type is not int:
                continue
            connection.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence(:table, 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table.name}), 1), "
                    f"(SELECT MAX(id) FROM {table.name}) IS NOT NULL)"
                ),
                {"table": table.name},
            )


def _clear(engine: Engine, tables: list[Table]) -> None:
    with engine.begin() as connection:
        for table in reversed(tables):
            connection.execute(table.delete())


def copy_database(
    source: Engine,
    target: Engine,
    *,
    replace: bool = False,
    on_table: Callable[[str, int], None] | None = None,
) -> MigrationReport:
    init_db(source)
    init_db(target)
    tables = list(Base.metadata.sorted_tables)
    report = MigrationReport()
    for table in tables:
        report.problems.extend(_too_long(source, table))
    occupied = [table.name for table in tables if _count(target, table)]
    if occupied and not replace:
        report.problems.append(
            "la base de destino ya tiene datos en: "
            + ", ".join(occupied)
            + " (use --replace para borrarlos y copiar de nuevo)"
        )
    if report.problems:
        return report
    if occupied:
        _clear(target, tables)
    with source.connect() as reader:
        for table in tables:
            copied = 0
            result = reader.execution_options(stream_results=True).execute(select(table))
            with target.begin() as writer:
                while rows := result.mappings().fetchmany(BATCH):
                    writer.execute(insert(table), [dict(row) for row in rows])
                    copied += len(rows)
            report.copied[table.name] = copied
            if on_table:
                on_table(table.name, copied)
    if is_postgres(target.url):
        _reset_sequences(target, tables)
    for table in tables:
        if _count(target, table) != report.copied[table.name]:
            report.problems.append(f"{table.name}: el conteo en el destino no coincide")
    return report
