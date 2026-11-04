import re
import secrets
from dataclasses import dataclass, field
from pathlib import Path

GENERATED_BACKEND = ("ADMIN_TOKEN", "PHONE_HMAC_KEY", "WHATSAPP_VERIFY_TOKEN")
LINE = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=(.*)$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = LINE.match(line)
        if match:
            values[match.group(1)] = match.group(2).strip()
    return values


def write_env(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    pending = dict(updates)
    for index, line in enumerate(lines):
        match = LINE.match(line)
        if match and match.group(1) in pending:
            key = match.group(1)
            lines[index] = f"{key}={pending.pop(key)}"
    lines.extend(f"{key}={value}" for key, value in pending.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass
class SetupReport:
    created: list[str] = field(default_factory=list)
    generated: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def prepare_backend_env(root: Path, report: SetupReport, database_url: str | None = None) -> Path:
    env_path = root / "backend" / ".env"
    if not env_path.exists():
        example = root / ".env.example"
        env_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        report.created.append("backend/.env")
    values = read_env(env_path)
    updates: dict[str, str] = {}
    for key in GENERATED_BACKEND:
        if not values.get(key) or values.get(key) == "dev-only-change-me":
            updates[key] = secrets.token_hex(32)
            report.generated.append(key)
    if values.get("SATELLITE_PROVIDER", "gee") == "gee" and not values.get("GEE_PROJECT"):
        updates["SATELLITE_PROVIDER"] = "open"
        report.notes.append(
            "SATELLITE_PROVIDER=open (datos abiertos MODIS + Hansen; con GEE_PROJECT use gee)"
        )
    if database_url:
        updates["DATABASE_URL"] = database_url
        report.notes.append("DATABASE_URL actualizado (PostgreSQL)")
    if updates:
        write_env(env_path, updates)
    return env_path


def prepare_web_env(root: Path, backend_env: Path, api_port: int, report: SetupReport) -> Path:
    web_env = root / "web" / ".env.local"
    if not web_env.exists():
        report.created.append("web/.env.local")
    values = read_env(web_env)
    admin = read_env(backend_env).get("ADMIN_TOKEN", "")
    updates = {
        "BV_DATA_SOURCE": values.get("BV_DATA_SOURCE") or "live",
        "BACKEND_URL": values.get("BACKEND_URL") or f"http://127.0.0.1:{api_port}",
        "ADMIN_TOKEN": admin,
    }
    if not values.get("SESSION_SECRET"):
        updates["SESSION_SECRET"] = secrets.token_hex(32)
        report.generated.append("SESSION_SECRET")
    write_env(web_env, updates)
    return web_env


@dataclass(frozen=True)
class Requirement:
    feature: str
    keys: tuple[str, ...]
    guide: str
    optional: bool = False


GUIDES = "docs/guias"

REQUIREMENTS = (
    Requirement(
        "IA (Gemini, capa gratuita)",
        ("GEMINI_API_KEY", "GEMINI_MODEL"),
        f"{GUIDES}/gemini.md",
    ),
    Requirement(
        "WhatsApp Cloud API",
        ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_APP_SECRET"),
        f"{GUIDES}/whatsapp.md",
    ),
    Requirement(
        "Correo SMTP (2FA, avisos, recuperación)",
        ("SMTP_USER", "SMTP_PASSWORD"),
        f"{GUIDES}/correo.md",
    ),
    Requirement(
        "Google Earth Engine",
        ("GEE_PROJECT",),
        "docs/fuentes-de-datos/datos-abiertos.md",
        optional=True,
    ),
)


DATABASE_REQUIREMENT = Requirement(
    "Base PostgreSQL en Supabase (para Vercel; sin ella se usa SQLite local)",
    ("DATABASE_URL", "DATABASE_PASSWORD"),
    f"{GUIDES}/despliegue.md",
)


def missing_keys(values: dict[str, str]) -> list[tuple[Requirement, list[str]]]:
    result = []
    url = values.get("DATABASE_URL", "")
    if not url.startswith(("postgres://", "postgresql")):
        result.append((DATABASE_REQUIREMENT, ["DATABASE_URL", "DATABASE_PASSWORD"]))
    elif "[YOUR-PASSWORD]" in url and not values.get("DATABASE_PASSWORD"):
        result.append((DATABASE_REQUIREMENT, ["DATABASE_PASSWORD"]))
    for requirement in REQUIREMENTS:
        missing = [key for key in requirement.keys if not values.get(key)]
        if missing:
            result.append((requirement, missing))
    return result


API_KEYS = (
    "DATABASE_URL",
    "DATABASE_PASSWORD",
    "ADMIN_TOKEN",
    "PHONE_HMAC_KEY",
    "INDEX_VERSION",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_MODEL_LIGHT",
    "WHATSAPP_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_VERIFY_TOKEN",
    "WHATSAPP_APP_SECRET",
    "WHATSAPP_ALLOWED_PHONES",
    "WHATSAPP_API_VERSION",
    "MAIL_BACKEND",
    "MAIL_FROM",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_STARTTLS",
    "SMTP_SSL",
    "AUTH_TWO_FACTOR",
    "AUTH_CODE_TTL_MINUTES",
    "AUTH_LOGIN_ALERTS",
    "PASSWORD_RESET_TTL_MINUTES",
    "INVITATION_TTL_HOURS",
    "AGENT_DAILY_LIMIT_PER_USER",
)
WEB_KEYS = ("PRIVACY_CONTACT_EMAIL", "WHATSAPP_PUBLIC_NUMBER")


def vercel_env_blocks(
    backend: dict[str, str], web: dict[str, str], api_url: str, web_url: str
) -> tuple[str, str]:
    api = {key: backend[key] for key in API_KEYS if backend.get(key)}
    api["WEB_BASE_URL"] = web_url.rstrip("/")
    site = {
        "BV_DATA_SOURCE": "live",
        "BACKEND_URL": api_url.rstrip("/"),
        "ADMIN_TOKEN": backend.get("ADMIN_TOKEN", ""),
        "SESSION_SECRET": web.get("SESSION_SECRET") or secrets.token_hex(32),
        "SITE_URL": web_url.rstrip("/"),
    }
    site.update({key: web[key] for key in WEB_KEYS if web.get(key)})

    def render(values: dict[str, str]) -> str:
        return "".join(f"{key}={value}\n" for key, value in values.items())

    return render(api), render(site)
