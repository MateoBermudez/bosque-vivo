import base64
import hashlib
import hmac
import re
import secrets

SCHEME = "scrypt"
COST = 2**14
BLOCK_SIZE = 8
PARALLELISM = 1
KEY_LENGTH = 32
MIN_LENGTH = 10
MAX_LENGTH = 128
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _derive(password: str, salt: bytes, cost: int, block: int, parallel: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=cost,
        r=block,
        p=parallel,
        dklen=KEY_LENGTH,
        maxmem=64 * 1024 * 1024,
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _derive(password, salt, COST, BLOCK_SIZE, PARALLELISM)
    return f"{SCHEME}${COST}${BLOCK_SIZE}${PARALLELISM}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    parts = encoded.split("$")
    if len(parts) != 6 or parts[0] != SCHEME:
        return False
    try:
        cost, block, parallel = int(parts[1]), int(parts[2]), int(parts[3])
        salt, expected = _unb64(parts[4]), _unb64(parts[5])
    except ValueError:
        return False
    candidate = _derive(password, salt, cost, block, parallel)
    return hmac.compare_digest(candidate, expected)


DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return len(email) <= 254 and bool(EMAIL_PATTERN.match(email))


def password_problems(password: str, email: str | None = None) -> list[str]:
    problems: list[str] = []
    if len(password) < MIN_LENGTH:
        problems.append(f"debe tener al menos {MIN_LENGTH} caracteres")
    if len(password) > MAX_LENGTH:
        problems.append(f"debe tener como máximo {MAX_LENGTH} caracteres")
    if not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", password):
        problems.append("debe incluir al menos una letra")
    if not re.search(r"\d", password):
        problems.append("debe incluir al menos un número")
    if email and password.strip().lower() == normalize_email(email):
        problems.append("no puede ser igual al correo")
    return problems


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
