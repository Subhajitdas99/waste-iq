from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Waste-IQ API"

    environment: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )

    database_url: str = Field(
        default="postgresql+psycopg://wasteiq:wasteiq@db:5432/wasteiq",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(
        default="change-me",
        alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=60 * 24,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,https://waste-iq-zeta.vercel.app",
        alias="CORS_ORIGINS",
    )

    # Admin bootstrap
    admin_registration_code: str | None = Field(
        default=None,
        alias="ADMIN_REGISTRATION_CODE",
    )

    bootstrap_admin_name: str | None = Field(
        default=None,
        alias="BOOTSTRAP_ADMIN_NAME",
    )

    bootstrap_admin_email: str | None = Field(
        default=None,
        alias="BOOTSTRAP_ADMIN_EMAIL",
    )

    bootstrap_admin_phone: str | None = Field(
        default=None,
        alias="BOOTSTRAP_ADMIN_PHONE",
    )

    bootstrap_admin_password: str | None = Field(
        default=None,
        alias="BOOTSTRAP_ADMIN_PASSWORD",
    )

    # Cloudinary
    cloudinary_cloud_name: str | None = Field(
        default=None,
        alias="CLOUDINARY_CLOUD_NAME",
    )

    cloudinary_api_key: str | None = Field(
        default=None,
        alias="CLOUDINARY_API_KEY",
    )

    cloudinary_api_secret: str | None = Field(
        default=None,
        alias="CLOUDINARY_API_SECRET",
    )

    # ------------------------------------------------------------------
    # Monitoring & Logging (WIQ-V1-023)
    # ------------------------------------------------------------------

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    sentry_dsn: str | None = Field(
        default=None,
        alias="SENTRY_DSN",
    )

    release: str = Field(
        default="local",
        alias="RELEASE",
    )

    enable_metrics: bool = Field(
        default=False,
        alias="ENABLE_METRICS",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cloudinary_configured(self) -> bool:
        return all(
            [
                self.cloudinary_cloud_name,
                self.cloudinary_api_key,
                self.cloudinary_api_secret,
            ]
        )

    @property
    def cloudinary_required(self) -> bool:
        return self.is_production

    @property
    def sentry_enabled(self) -> bool:
        return bool(self.sentry_dsn)

    @property
    def monitoring_enabled(self) -> bool:
        return self.enable_metrics or self.sentry_enabled


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()