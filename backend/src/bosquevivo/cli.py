import argparse
import getpass
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

from sqlalchemy import func, select

from bosquevivo.accounts import AccountService, build_mailer
from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.eval import EvalRunner, load_cases
from bosquevivo.assistant.runtime import build_llm, build_llm_or_unavailable
from bosquevivo.core.config import get_settings
from bosquevivo.core.errors import ExternalServiceError, ValidationFailedError
from bosquevivo.core.incidents import duration_minutes, is_critical, list_incidents, summarize
from bosquevivo.core.logging import configure_logging
from bosquevivo.db.migrate import copy_database
from bosquevivo.db.models import Project
from bosquevivo.db.session import build_engine, get_session, init_db
from bosquevivo.db.urls import describe, resolve_database_url
from bosquevivo.demo import seed_demo
from bosquevivo.measure import (
    Report,
    check_determinism,
    measure_audits,
    measure_chat,
    project_ids,
)
from bosquevivo.pipeline import (
    BatchItem,
    audit_project,
    generate_missing_reports,
    recompute_batch,
    run_batch,
    select_projects,
)
from bosquevivo.registry.importer import import_file
from bosquevivo.registry.karnik import import_karnik
from bosquevivo.satellite.factory import build_provider
from bosquevivo.setup import (
    SetupReport,
    missing_keys,
    prepare_backend_env,
    prepare_web_env,
    read_env,
    repo_root,
)


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
            strict=not args.lenient,
        )
        print(
            f"creados={summary.created} actualizados={summary.updated} "
            f"reparados={summary.repaired} omitidos={summary.skipped} "
            f"rechazados={summary.rejected}"
        )
        for project_id in summary.created_ids:
            print(f"  importado con id interno {project_id}")
        for error in summary.errors:
            print(f"  {error}")
    return 1 if summary.rejected and not summary.total else 0


def cmd_import_karnik(args: argparse.Namespace) -> int:
    init_db()
    with get_session() as session:
        summary = import_karnik(session, Path(args.path), country=args.country, limit=args.limit)
        print(
            f"creados={summary.created} actualizados={summary.updated} "
            f"reparados={summary.repaired} simplificados={summary.simplified} "
            f"con_area_de_contabilidad={summary.accounting_area_used} "
            f"omitidos_por_ser_punto={len(summary.skipped_points)} "
            f"omitidos_otros={len(summary.skipped_other)}"
        )
        for item in summary.skipped_points:
            print(f"  punto (no auditable): {item}")
        for item in summary.skipped_other:
            print(f"  omitido: {item}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    provider = build_provider(settings)
    with get_session() as session:
        start = date.fromisoformat(args.start) if args.start else None
        run = audit_project(
            session,
            provider,
            settings.images_dir,
            args.project_id,
            start=start,
            index_version=args.index_version or settings.index_version,
        )
        result = run.result
        print(f"corrida={run.id} categoria={result.category if result else None}")
    return 0


def _print_batch_item(index: int, total: int, item: BatchItem) -> None:
    area = f"{item.area_ha:,.0f} ha" if item.area_ha else "área sin dato"
    if item.ok:
        score = "—" if item.score is None else f"{item.score:.0f}"
        outcome = f"{item.category} (índice {score})"
    else:
        outcome = f"ERROR {item.error}"
    label = f"[{index}/{total}] #{item.project_id} {item.name[:48]}"
    print(f"{label} · {area} -> {outcome} · {item.seconds}s")


def cmd_gemini_check(_: argparse.Namespace) -> int:
    """Verifica la clave de Gemini, lista los modelos disponibles y prueba el configurado."""
    from google import genai  # noqa: PLC0415 - solo se importa si se usa este comando

    settings = get_settings()
    if not settings.gemini_api_key:
        print(
            "Falta GEMINI_API_KEY en backend/.env (se crea en https://aistudio.google.com/apikey)"
        )
        return 1
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        models = sorted(
            (m.name or "").removeprefix("models/")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
        )
    except Exception as exc:  # clave inválida, sin red o sin cuota
        print(f"No se pudo consultar Gemini: {exc}")
        return 1
    print(f"La clave funciona. Modelos que permiten generar texto ({len(models)}):")
    for name in models:
        print(f"  {name}")
    for label, model in (
        ("GEMINI_MODEL", settings.gemini_model),
        ("GEMINI_MODEL_LIGHT", settings.gemini_model_light),
    ):
        if not model:
            print(f"{label}: sin configurar (elige uno de la lista y ponlo en backend/.env)")
            continue
        try:
            reply = client.models.generate_content(
                model=model, contents="Responde solo con la palabra: listo"
            )
            print(f"{label}={model}: responde «{(reply.text or '').strip()[:40]}»")
        except Exception as exc:
            print(f"{label}={model}: ERROR {str(exc)[:160]}")
            return 1
    return 0


def cmd_reports(_: argparse.Namespace) -> int:
    init_db()
    with get_session() as session:
        created = generate_missing_reports(session, get_settings().reports_dir)
    print(f"reportes HTML generados: {created}")
    return 0


def _parse_shard(value: str | None) -> tuple[int, int] | None:
    """«2/4» → (1, 4): la parte 2 de 4 (numeradas desde 1)."""
    if not value:
        return None
    part, total = (int(piece) for piece in value.split("/"))
    if not 1 <= part <= total:
        raise SystemExit("--shard debe ser i/n con 1 <= i <= n, por ejemplo 2/4")
    return part - 1, total


def cmd_audit_batch(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    provider = build_provider(settings)
    with get_session() as session:
        projects = select_projects(
            session,
            country=args.country,
            include_arr=args.include_arr,
            max_area_ha=args.max_area_ha,
            redo=args.redo,
            missing_index=args.missing_index,
            limit=args.limit,
            shard=_parse_shard(args.shard),
        )
        print(f"{len(projects)} proyectos por calcular con el proveedor «{provider.name}»")
        began = time.monotonic()
        items = run_batch(
            session,
            provider,
            settings.images_dir,
            projects,
            start=date.fromisoformat(args.start) if args.start else None,
            index_version=args.index_version or settings.index_version,
            reports_dir=settings.reports_dir,
            on_item=_print_batch_item,
        )
    failed = [item for item in items if not item.ok]
    print(
        f"terminados: {len(items) - len(failed)} bien, {len(failed)} con error, "
        f"{time.monotonic() - began:.0f}s en total"
    )
    return 1 if failed else 0


def cmd_recompute(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    version = args.index_version or settings.index_version
    with get_session() as session:
        items = recompute_batch(
            session,
            version,
            settings.reports_dir,
            country=args.country,
            on_item=_print_batch_item,
        )
    failed = [item for item in items if not item.ok]
    print(f"índice {version} recalculado: {len(items) - len(failed)} bien, {len(failed)} con error")
    return 1 if failed else 0


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


def _read_password() -> str:
    from_env = os.environ.get("BOSQUEVIVO_PASSWORD")
    if from_env:
        return from_env
    first = getpass.getpass("Contraseña: ")
    if first != getpass.getpass("Repite la contraseña: "):
        raise ValidationFailedError("las contraseñas no coinciden")
    return first


def _accounts(session) -> AccountService:
    settings = get_settings()
    return AccountService(session, build_mailer(settings), settings)


def cmd_user_create(args: argparse.Namespace) -> int:
    init_db()
    try:
        password = _read_password()
        with get_session() as session:
            user = _accounts(session).create_user(args.email, args.name or "", password)
            print(f"usuario creado: {user.email} (id {user.id})")
    except ValidationFailedError as exc:
        print(f"No se creó el usuario: {exc}")
        return 1
    return 0


def cmd_user_invite(args: argparse.Namespace) -> int:
    init_db()
    try:
        with get_session() as session:
            user, link = _accounts(session).invite_user(args.email, args.name or "")
            print(f"invitación creada para {user.email}")
            if build_mailer(get_settings()).name == "outbox":
                print(f"sin SMTP configurado, el correo quedó en data/outbox. Enlace: {link}")
    except (ValidationFailedError, ExternalServiceError) as exc:
        print(f"No se envió la invitación: {exc}")
        return 1
    return 0


def _print_setup(report: SetupReport, values: dict[str, str], projects: int) -> None:
    for item in report.created:
        print(f"creado: {item}")
    for key in report.generated:
        print(f"generado: {key}")
    for note in report.notes:
        print(f"nota: {note}")
    print(f"proyectos en la base: {projects}")
    pending = missing_keys(values)
    if not pending:
        print("Todo configurado.")
        return
    print("Para activar estas funciones complete backend/.env:")
    for requirement, keys in pending:
        label = "opcional" if requirement.optional else "falta"
        print(f"  [{label}] {requirement.feature}: {', '.join(keys)} ({requirement.guide})")


def cmd_setup(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    report = SetupReport()
    backend_env = prepare_backend_env(root, report)
    prepare_web_env(root, backend_env, args.api_port, report)
    os.chdir(root / "backend")
    get_settings.cache_clear()
    init_db()
    settings = get_settings()
    with get_session() as session:
        projects = session.scalar(select(func.count(Project.id))) or 0
        if projects == 0 and not args.no_demo:
            projects = len(seed_demo(session, settings.images_dir))
            report.notes.append("se cargaron 3 proyectos de demostración (bosquevivo seed-demo)")
        accounts = AccountService(session, build_mailer(settings), settings)
        if args.admin and not accounts.find(args.admin):
            _, link = accounts.invite_user(args.admin, args.name or "")
            report.notes.append(f"cuenta de auditor {args.admin}: elija la contraseña en {link}")
    _print_setup(report, read_env(backend_env), projects)
    return 0


def cmd_migrate_db(args: argparse.Namespace) -> int:
    settings = get_settings()
    source_url = resolve_database_url(args.source)
    target_url = resolve_database_url(
        args.target or settings.database_url, settings.database_password
    )
    if source_url == target_url:
        print("El origen y el destino son la misma base.")
        return 1
    print(f"origen:  {describe(source_url)}")
    print(f"destino: {describe(target_url)}")
    report = copy_database(
        build_engine(source_url),
        build_engine(target_url, pool="null"),
        replace=args.replace,
        on_table=lambda name, count: print(f"  {name}: {count} filas"),
    )
    for problem in report.problems:
        print(f"PROBLEMA: {problem}")
    if report.problems:
        return 1
    print(f"Migración completa: {sum(report.copied.values())} filas en {len(report.copied)} tablas")
    return 0


def cmd_mail_test(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    mailer = build_mailer(settings)
    try:
        with get_session() as session:
            AccountService(session, mailer, settings).send_test(args.email)
    except ExternalServiceError as exc:
        print(f"El correo NO funciona: {exc}")
        return 1
    where = "data/outbox (MAIL_BACKEND sin SMTP)" if mailer.name == "outbox" else "SMTP"
    print(f"Correo de prueba enviado a {args.email} por {where}")
    return 0


def cmd_user_list(_: argparse.Namespace) -> int:
    init_db()
    with get_session() as session:
        users = _accounts(session).list_users()
        for user in users:
            state = "activo" if user.active else "inactivo"
            print(f"{user.id}\t{user.email}\t{user.name}\t{state}")
        print(f"{len(users)} usuarios")
    return 0


def cmd_user_state(args: argparse.Namespace) -> int:
    init_db()
    try:
        with get_session() as session:
            user = _accounts(session).set_active(args.email, args.command == "user-enable")
            print(f"{user.email}: {'activo' if user.active else 'inactivo'}")
    except ValidationFailedError as exc:
        print(str(exc))
        return 1
    return 0


def cmd_user_reset(args: argparse.Namespace) -> int:
    init_db()
    with get_session() as session:
        print(_accounts(session).request_reset(args.email))
    return 0


def cmd_incidents(args: argparse.Namespace) -> int:
    init_db()
    with get_session() as session:
        incidents = list_incidents(session, days=args.days)
        for item in incidents:
            minutes = duration_minutes(item)
            span = "abierto" if minutes is None else f"{minutes} min"
            flag = " CRITICO" if is_critical(item) else ""
            print(
                f"{item.started_at:%Y-%m-%d %H:%M} [{item.origin}] {item.component} "
                f"({span}){flag}: {item.cause[:120]}"
            )
        totals = summarize(incidents)
        print(" ".join(f"{key}={value}" for key, value in totals.items()))
    return 0


def _add_account_commands(sub) -> None:
    user_create = sub.add_parser("user-create", help="Crea una cuenta de auditor del sitio web")
    user_create.add_argument("email")
    user_create.add_argument("--name")
    user_create.set_defaults(func=cmd_user_create)
    user_invite = sub.add_parser(
        "user-invite", help="Crea una cuenta y envía por correo el enlace para elegir contraseña"
    )
    user_invite.add_argument("email")
    user_invite.add_argument("--name")
    user_invite.set_defaults(func=cmd_user_invite)
    setup = sub.add_parser(
        "setup", help="Crea los .env con secretos generados, la base y los datos de demostración"
    )
    setup.add_argument("--admin", help="correo de la primera cuenta de auditor (se invita)")
    setup.add_argument("--name", help="nombre de esa cuenta")
    setup.add_argument("--api-port", type=int, default=8000)
    setup.add_argument("--no-demo", action="store_true", help="no carga proyectos de demostración")
    setup.add_argument("--root", help="raíz del repositorio (por defecto se detecta)")
    setup.set_defaults(func=cmd_setup)
    migrate = sub.add_parser(
        "migrate-db", help="Copia todos los datos de SQLite a PostgreSQL (Supabase)"
    )
    migrate.add_argument("--from", dest="source", default="sqlite:///data/bosquevivo.db")
    migrate.add_argument("--to", dest="target", help="por defecto, DATABASE_URL")
    migrate.add_argument("--replace", action="store_true", help="borra lo que haya en el destino")
    migrate.set_defaults(func=cmd_migrate_db)
    mail_test = sub.add_parser("mail-test", help="Envía un correo de prueba con la configuración")
    mail_test.add_argument("email")
    mail_test.set_defaults(func=cmd_mail_test)
    sub.add_parser("user-list", help="Lista las cuentas de auditor").set_defaults(
        func=cmd_user_list
    )
    for name in ("user-enable", "user-disable"):
        toggle = sub.add_parser(name, help="Activa o desactiva una cuenta de auditor")
        toggle.add_argument("email")
        toggle.set_defaults(func=cmd_user_state)
    user_reset = sub.add_parser(
        "user-reset", help="Envía el correo de restablecimiento de contraseña"
    )
    user_reset.add_argument("email")
    user_reset.set_defaults(func=cmd_user_reset)
    incidents = sub.add_parser("incidents", help="Muestra los incidentes registrados")
    incidents.add_argument("--days", type=int, default=30)
    incidents.set_defaults(func=cmd_incidents)
    measure = sub.add_parser("medir-rnf", help="Mide los requisitos no funcionales (3.3.1, 3.3.3)")
    measure.add_argument("--rounds", type=int, default=50)
    measure.add_argument("--projects", type=int, default=3)
    measure.add_argument("--index-version")
    measure.add_argument("--output", default="data/medicion/rnf.json")
    measure.set_defaults(func=cmd_measure)


def cmd_measure(args: argparse.Namespace) -> int:
    init_db()
    settings = get_settings()
    version = args.index_version or settings.index_version
    llm = build_llm_or_unavailable(settings)
    provider = build_provider(settings)
    with get_session() as session:
        ids = project_ids(session, args.projects)
        report = Report(llm_model=llm.model, satellite_provider=provider.name)
        report.chat = measure_chat(session, settings, llm, ids[0] if ids else None, args.rounds)
        if ids:
            report.audit, report.audit_by_project = measure_audits(
                session, provider, settings.images_dir, ids, version
            )
            report.deterministic, report.determinism_detail = check_determinism(
                session, ids, version
            )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
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
    imp.add_argument(
        "--lenient",
        action="store_true",
        help="actualiza proyectos existentes y repara geometrías en vez de rechazarlos",
    )
    imp.set_defaults(func=cmd_import)
    karnik = sub.add_parser("import-karnik", help="Importa la base de Karnik et al. (2025)")
    karnik.add_argument("path", help="GeoPackage continental, p. ej. south_america.gpkg")
    karnik.add_argument("--country")
    karnik.add_argument("--limit", type=int)
    karnik.set_defaults(func=cmd_import_karnik)
    batch = sub.add_parser("audit-batch", help="Calcula las auditorías de varios proyectos")
    batch.add_argument("--country")
    batch.add_argument("--limit", type=int, help="máximo de proyectos (los más chicos primero)")
    batch.add_argument("--max-area-ha", type=float, help="omite proyectos más grandes que esto")
    batch.add_argument("--include-arr", action="store_true", help="incluye reforestación (ARR)")
    batch.add_argument("--redo", action="store_true", help="recalcula los que ya tienen auditoría")
    batch.add_argument(
        "--missing-index",
        action="store_true",
        help="solo los que aún no tienen índice completo (sin auditoría o con resultado parcial)",
    )
    batch.add_argument("--start", help="AAAA-MM-DD; por defecto, 3 años antes de T0 de cada uno")
    batch.add_argument(
        "--shard", help="i/n: calcula solo la parte i de n, para correr varios procesos"
    )
    batch.add_argument("--index-version", help="v0 o v1; por defecto INDEX_VERSION (v1)")
    batch.set_defaults(func=cmd_audit_batch)
    recompute = sub.add_parser(
        "recompute", help="Recalcula el índice con otra versión usando los datos ya guardados"
    )
    recompute.add_argument("--country")
    recompute.add_argument("--index-version", help="v0 o v1; por defecto INDEX_VERSION (v1)")
    recompute.set_defaults(func=cmd_recompute)
    gemini = sub.add_parser("gemini-check", help="Verifica la clave y los modelos de Gemini")
    gemini.set_defaults(func=cmd_gemini_check)
    reports = sub.add_parser("reports", help="Genera los reportes HTML que falten")
    reports.set_defaults(func=cmd_reports)
    audit = sub.add_parser("audit")
    audit.add_argument("project_id", type=int)
    audit.add_argument(
        "--start", help="AAAA-MM-DD; por defecto, 3 años antes de T0 (mínimo el año 2000)"
    )
    audit.add_argument("--index-version", help="v0 o v1; por defecto INDEX_VERSION (v1)")
    audit.set_defaults(func=cmd_audit)
    _add_account_commands(sub)
    evaluate = sub.add_parser("eval")
    evaluate.add_argument("--output", default="data/eval/report.json")
    evaluate.set_defaults(func=cmd_eval)
    return parser


def main(argv: list[str] | None = None) -> int:
    # La consola de Windows usa cp1252: un carácter que no exista allí no debe tumbar el comando.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(errors="replace")
    configure_logging()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
