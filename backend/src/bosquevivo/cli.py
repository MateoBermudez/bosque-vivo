import argparse
import sys
from datetime import date
from pathlib import Path

from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.eval import EvalRunner, load_cases
from bosquevivo.assistant.runtime import build_llm
from bosquevivo.audit.service import AuditService
from bosquevivo.core.config import get_settings
from bosquevivo.core.logging import configure_logging
from bosquevivo.db.session import get_session, init_db
from bosquevivo.demo import seed_demo
from bosquevivo.registry.importer import import_file
from bosquevivo.satellite.factory import build_provider
from bosquevivo.satellite.service import SatelliteService


def cmd_init_db(_: argparse.Namespace) -> int:
    init_db()
    return 0


def cmd_seed_demo(_: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    with get_session() as session:
        projects = seed_demo(session, settings.images_dir)
        print(f"{len(projects)} proyectos de demostración creados")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    init_db()
    with get_session() as session:
        summary = import_file(
            session,
            Path(args.path),
            source=args.source,
            source_version=args.version,
            country=args.country,
            limit=args.limit,
        )
        print(
            f"creados={summary.created} actualizados={summary.updated} "
            f"reparados={summary.repaired} omitidos={summary.skipped}"
        )
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    provider = build_provider(settings)
    with get_session() as session:
        satellite = SatelliteService(session, provider, settings.images_dir)
        satellite.refresh_timeseries(args.project_id, date.fromisoformat(args.start), date.today())
        satellite.refresh_forest_loss(args.project_id)
        run = AuditService(session, dataset_versions=provider.dataset_versions()).run(
            args.project_id
        )
        result = run.result
        print(f"corrida={run.id} categoria={result.category if result else None}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    llm = build_llm(settings)
    with get_session() as session:
        agent = Agent(session, llm, default_registry(), settings)
        report = EvalRunner(session, agent).run(load_cases())
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.to_json(), encoding="utf-8")
        print(report.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bosquevivo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db").set_defaults(func=cmd_init_db)
    sub.add_parser("seed-demo").set_defaults(func=cmd_seed_demo)
    imp = sub.add_parser("import")
    imp.add_argument("path")
    imp.add_argument("--source", required=True)
    imp.add_argument("--version")
    imp.add_argument("--country")
    imp.add_argument("--limit", type=int)
    imp.set_defaults(func=cmd_import)
    audit = sub.add_parser("audit")
    audit.add_argument("project_id", type=int)
    audit.add_argument("--start", default="2016-01-01")
    audit.set_defaults(func=cmd_audit)
    evaluate = sub.add_parser("eval")
    evaluate.add_argument("--output", default="data/eval/report.json")
    evaluate.set_defaults(func=cmd_eval)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
