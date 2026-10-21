import hashlib
import hmac


def phone_hmac(phone: str, key: str) -> str:
    normalized = "".join(ch for ch in phone if ch.isdigit())
    return hmac.new(key.encode(), normalized.encode(), hashlib.sha256).hexdigest()
