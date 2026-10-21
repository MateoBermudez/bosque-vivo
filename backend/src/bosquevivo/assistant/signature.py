import hashlib
import hmac


def compute_signature(body: bytes, app_secret: str) -> str:
    digest = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(body: bytes, header: str | None, app_secret: str) -> bool:
    if not app_secret or not header:
        return False
    return hmac.compare_digest(compute_signature(body, app_secret), header)
