import re
import unicodedata

CONSENT_WORDS = {"acepto", "si acepto", "acepto datos"}
MEDIA_WORDS = {"acepto fotos", "acepto audios", "acepto fotos y audios"}
DELETE_PATTERN = re.compile(r"\bborrar?\s+(mis\s+)?datos\b|\belimin\w+\s+(mis\s+)?datos\b")


def normalize(text: str) -> str:
    stripped = "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^\w\s]", "", stripped).strip()


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
