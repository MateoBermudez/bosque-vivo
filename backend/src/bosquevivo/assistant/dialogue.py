import re
import unicodedata

CONSENT_WORDS = {"acepto", "si acepto", "acepto datos"}
MEDIA_WORDS = {"acepto fotos", "acepto audios", "acepto fotos y audios"}
DELETE_PATTERN = re.compile(r"\bborrar?\s+(mis\s+)?datos\b|\belimin\w+\s+(mis\s+)?datos\b")
HELP_PATTERN = re.compile(r"^(ayuda|menu|opciones|ayudame|que puedo (preguntar|hacer))$")
ALERT_PATTERN = re.compile(r"\balertas?\b")
STATUS_PATTERN = re.compile(
    r"^(estado|estado de mi bosque|como esta mi bosque|como va mi bosque|"
    r"como esta (el bosque de )?mi (finca|proyecto|bosque)|mi bosque)$"
)
REGISTER_PATTERN = re.compile(r"^(proyecto|registrar|mi proyecto)\s+(\d{1,7})$")


def normalize(text: str) -> str:
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", stripped)).strip()


def wants_consent(text: str | None) -> bool:
    return normalize(text or "") in CONSENT_WORDS


def wants_media_consent(text: str | None) -> bool:
    return normalize(text or "") in MEDIA_WORDS


def wants_deletion(text: str | None) -> bool:
    return bool(DELETE_PATTERN.search(normalize(text or "")))


def split_message(text: str, limit: int = 300) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(current) + len(sentence) + 1 > limit and current:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return [c[:limit] for c in chunks]


def detect_intent(text: str | None) -> str | None:
    clean = normalize(text or "")
    if not clean:
        return None
    if HELP_PATTERN.match(clean):
        return "ayuda"
    if ALERT_PATTERN.search(clean) and len(clean.split()) <= 6:
        return "alertas"
    if STATUS_PATTERN.match(clean):
        return "estado"
    if REGISTER_PATTERN.match(clean):
        return "registro"
    return None


def registered_project_id(text: str | None) -> int | None:
    match = REGISTER_PATTERN.match(normalize(text or ""))
    return int(match.group(2)) if match else None


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def is_authorized(phone: str, allowed: str) -> bool:
    numbers = {normalize_phone(item) for item in allowed.split(",") if normalize_phone(item)}
    return not numbers or normalize_phone(phone) in numbers
