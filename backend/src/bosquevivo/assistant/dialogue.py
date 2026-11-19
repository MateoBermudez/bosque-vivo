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
GREETING_PATTERN = re.compile(
    r"^(hola|holi|hey|buenas|buenos dias|buen dia|buenas tardes|buenas noches|saludos)"
    r"( (a todos|equipo|asistente|bosque vivo|amigo|amiga))?$"
)
THANKS_PATTERN = re.compile(
    r"^((muchas|mil) gracias|gracias|ok gracias|listo gracias|perfecto gracias|vale gracias)"
    r"( .*)?$"
)
ABOUT_PATTERN = re.compile(
    r"\b(quien eres|que eres|eres (un |una )?(robot|bot|persona|humano|humana|ia)|"
    r"eres una inteligencia artificial|como funcionas|para que sirves|que haces|"
    r"que sabes hacer|que puedes hacer)\b"
)
TOPIC_INDEX = re.compile(
    r"\b(indice|puntaje|calificacion|credibilidad|confianza|seguro|segura|confiable|fiable|resultado)\b"
)
TOPIC_ALERTS = re.compile(
    r"\b(alerta|alertas|tala|talando|talaron|deforestacion|deforestando|perdida|perdieron|"
    r"perdio|cambios recientes)\b"
)
TOPIC_STATUS = re.compile(
    r"\b(como (esta|va|vamos|anda|sigue|se ve)|que tal|estado|cuentame|informacion|resumen|"
    r"que pasa con)\b"
)
PORTFOLIO_COUNT = re.compile(
    r"^(cuantos proyectos (hay|existen|estan cargados|tienen)( cargados| en total| registrados)?|"
    r"que proyectos (hay|existen)( cargados| disponibles| registrados| en total)?|"
    r"lista de proyectos|cuales son los proyectos( cargados)?)$"
)
PORTFOLIO_WORST = re.compile(
    r"\b(peor|mas bajo|menor|mas baja)\b.*\b(indice|puntaje|calificacion|resultado)\b|"
    r"\b(indice|puntaje|calificacion)\b.*\b(mas bajo|peor|menor)\b"
)
PORTFOLIO_BEST = re.compile(
    r"\b(mejor|mas alto|mayor|mas alta)\b.*\b(indice|puntaje|calificacion|resultado)\b|"
    r"\b(indice|puntaje|calificacion)\b.*\b(mas alto|mejor|mayor)\b"
)
MAX_TOPIC_WORDS = 10
MAX_PORTFOLIO_WORDS = 12
MAX_THANKS_WORDS = 4
MAX_ABOUT_WORDS = 8


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
    if ALERT_PATTERN.match(clean):
        return "alertas"
    if STATUS_PATTERN.match(clean):
        return "estado"
    if REGISTER_PATTERN.match(clean):
        return "registro"
    return _social_intent(clean)


def _social_intent(clean: str) -> str | None:
    words = len(clean.split())
    if GREETING_PATTERN.match(clean):
        return "saludo"
    if THANKS_PATTERN.match(clean) and words <= MAX_THANKS_WORDS:
        return "gracias"
    if ABOUT_PATTERN.search(clean) and words <= MAX_ABOUT_WORDS:
        return "quien"
    return None


def detect_topic(text: str | None) -> str | None:
    clean = normalize(text or "")
    if not clean or len(clean.split()) > MAX_TOPIC_WORDS:
        return None
    if TOPIC_INDEX.search(clean):
        return "indice"
    if TOPIC_ALERTS.search(clean):
        return "alertas"
    if TOPIC_STATUS.search(clean):
        return "estado"
    return None


def detect_portfolio(text: str | None) -> str | None:
    clean = normalize(text or "")
    if not clean or len(clean.split()) > MAX_PORTFOLIO_WORDS:
        return None
    if PORTFOLIO_COUNT.match(clean):
        return "cuantos"
    names_projects = "proyecto" in clean or "cual" in clean
    if names_projects and PORTFOLIO_WORST.search(clean):
        return "peor"
    if names_projects and PORTFOLIO_BEST.search(clean):
        return "mejor"
    return None


def registered_project_id(text: str | None) -> int | None:
    match = REGISTER_PATTERN.match(normalize(text or ""))
    return int(match.group(2)) if match else None


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone)


def is_authorized(phone: str, allowed: str) -> bool:
    numbers = {normalize_phone(item) for item in allowed.split(",") if normalize_phone(item)}
    return not numbers or normalize_phone(phone) in numbers
