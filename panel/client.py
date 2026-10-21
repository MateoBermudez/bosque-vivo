import os
from typing import Any

import httpx

API_URL = os.environ.get("BOSQUEVIVO_API_URL", "http://127.0.0.1:8000")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")


class ApiError(Exception):
    pass


def request(method: str, path: str, **kwargs: Any) -> Any:
    headers = kwargs.pop("headers", {})
    if ADMIN_TOKEN:
        headers["X-Admin-Token"] = ADMIN_TOKEN
    try:
        response = httpx.request(method, f"{API_URL}{path}", headers=headers, timeout=120, **kwargs)
    except httpx.HTTPError as exc:
        raise ApiError("No se pudo conectar con la API de Bosque Vivo.") from exc
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise ApiError(f"La API respondió {response.status_code}: {response.text[:200]}")
    return response.json()


def projects(country: str | None = None) -> list[dict]:
    params = {"limit": 500}
    if country:
        params["country"] = country
    return request("GET", "/api/v1/projects", params=params) or []


def audit(project_id: int) -> dict | None:
    return request("GET", f"/api/v1/projects/{project_id}/audit")


def series(project_id: int) -> dict | None:
    return request("GET", f"/api/v1/projects/{project_id}/series")


def geometry(project_id: int) -> dict | None:
    return request("GET", f"/api/v1/projects/{project_id}/geometry")


def chat(message: str, session_ref: str) -> dict:
    return request("POST", "/api/v1/chat", json={"message": message, "session_ref": session_ref})


def traces(limit: int = 50) -> list[dict]:
    return request("GET", "/api/v1/traces", params={"limit": limit}) or []


def health() -> bool:
    try:
        return request("GET", "/health") is not None
    except ApiError:
        return False
