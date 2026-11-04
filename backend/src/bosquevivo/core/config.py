import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    database_url: str = Field(
        default="sqlite:///data/bosquevivo.db",
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"),
    )
    database_password: str = Field(
        default="",
        validation_alias=AliasChoices(
            "DATABASE_PASSWORD", "SUPABASE_DB_PASSWORD", "POSTGRES_PASSWORD"
        ),
    )
    db_pool: str = "auto"
    jobs_mode: str = "auto"
    data_dir: Path = Field(
        default_factory=lambda: Path(
            os.environ.get("DATA_DIR")
            or ("/tmp/bosquevivo" if os.environ.get("VERCEL") else "data")
        )
    )
    gemini_api_key: str = ""
    gemini_model: str = ""
    gemini_model_light: str = ""
    gee_project: str = ""
    satellite_provider: str = "gee"
    # versión del índice con la que se calculan las auditorías nuevas (v0 sigue disponible)
    index_version: str = "v1"
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    phone_hmac_key: str = Field(default="dev-only-change-me")
    admin_token: str = ""
    agent_max_steps: int = 5
    agent_daily_limit_per_user: int = 30
    whatsapp_allowed_phones: str = ""
    whatsapp_api_url: str = "https://graph.facebook.com"
    whatsapp_api_version: str = "v25.0"
    cloud_max_percent: float = Field(default=20.0, ge=0.0, le=100.0)
    web_base_url: str = "http://localhost:3000"
    password_reset_ttl_minutes: int = Field(default=30, ge=5, le=1440)
    mail_backend: str = "auto"
    mail_from: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    auth_two_factor: str = "auto"
    auth_code_ttl_minutes: int = Field(default=10, ge=2, le=60)
    auth_login_alerts: bool = True
    invitation_ttl_hours: int = Field(default=72, ge=1, le=720)

    @property
    def serverless(self) -> bool:
        return bool(os.environ.get("VERCEL"))

    @property
    def inline_jobs(self) -> bool:
        mode = self.jobs_mode.strip().lower()
        return mode == "inline" or (mode == "auto" and self.serverless)

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def outbox_dir(self) -> Path:
        return self.data_dir / "outbox"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"


@lru_cache
def get_settings() -> Settings:
    return Settings()
