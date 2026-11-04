from urllib.parse import quote_plus

from sqlalchemy.engine import URL, make_url

PASSWORD_PLACEHOLDERS = ("[YOUR-PASSWORD]", "[YOUR_PASSWORD]", "<password>")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", None, ""}


def resolve_database_url(raw: str, password: str = "") -> str:
    url = raw.strip()
    for placeholder in PASSWORD_PLACEHOLDERS:
        if placeholder in url:
            if not password:
                raise ValueError(
                    "DATABASE_URL tiene la marca de la contraseña; defina DATABASE_PASSWORD"
                )
            url = url.replace(placeholder, quote_plus(password))
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    parsed = make_url(url)
    if is_postgres(parsed) and parsed.host not in LOCAL_HOSTS and "sslmode" not in parsed.query:
        parsed = parsed.update_query_dict({"sslmode": "require"})
    return parsed.render_as_string(hide_password=False)


def is_postgres(url: URL) -> bool:
    return url.get_backend_name() == "postgresql"


def describe(raw: str) -> str:
    return make_url(raw).render_as_string(hide_password=True)
