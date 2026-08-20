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
    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # FIX: default now includes both local dev AND production Vercel URL.
    # On Railway, set CORS_ORIGINS to exactly:
    # https://waste-iq-zeta.vercel.app
    # No trailing slash. Multiple origins: comma-separated.
    cors_origins: str = Field(
        default="http://localhost:5173,https://waste-iq-zeta.vercel.app",
        alias="CORS_ORIGINS",
    )

    admin_registration_code: str | None = Field(default=None, alias="ADMIN_REGISTRATION_CODE")
    bootstrap_admin_name: str | None = Field(default=None, alias="BOOTSTRAP_ADMIN_NAME")
    bootstrap_admin_email: str | None = Field(default=None, alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_phone: str | None = Field(default=None, alias="BOOTSTRAP_ADMIN_PHONE")
    bootstrap_admin_password: str | None = Field(default=None, alias="BOOTSTRAP_ADMIN_PASSWORD")
    cloudinary_cloud_name: str | None = Field(default=None, alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str | None = Field(default=None, alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str | None = Field(default=None, alias="CLOUDINARY_API_SECRET")

    # ------------------------------------------------------------------
    # Background Jobs (WIQ-V1-021)
    # ------------------------------------------------------------------

    enable_background_jobs: bool = Field(
        default=True,
        alias="ENABLE_BACKGROUND_JOBS",
    )

    reservation_sweep_interval_minutes: int = Field(
        default=1,
        alias="RESERVATION_SWEEP_INTERVAL_MINUTES",
        gt=0,
    )

    aging_pickup_interval_minutes: int = Field(
        default=5,
        alias="AGING_PICKUP_INTERVAL_MINUTES",
        gt=0,
    )

    aging_pickup_threshold_days: int = Field(
        default=2,
        alias="AGING_PICKUP_THRESHOLD_DAYS",
        gt=0,
    )

    # ------------------------------------------------------------------
    # Monitoring & Logging
    # ------------------------------------------------------------------

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
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

    # ------------------------------------------------------------------
    # Rate Limiting & Account Lockout (WIQ-V1-017)
    # ------------------------------------------------------------------

    login_rate_limit_max: int = Field(
        default=10,
        alias="LOGIN_RATE_LIMIT_MAX",
        ge=0,
    )

    login_account_rate_limit_max: int = Field(
        default=5,
        alias="LOGIN_ACCOUNT_RATE_LIMIT_MAX",
        ge=0,
    )

    register_rate_limit_max: int = Field(
        default=10,
        alias="REGISTER_RATE_LIMIT_MAX",
        ge=0,
    )

    forgot_password_rate_limit_max: int = Field(
        default=5,
        alias="FORGOT_PASSWORD_RATE_LIMIT_MAX",
        ge=0,
    )

    resend_verification_rate_limit_max: int = Field(
        default=5,
        alias="RESEND_VERIFICATION_RATE_LIMIT_MAX",
        ge=0,
    )

    # ------------------------------------------------------------------
    # Email Delivery & Verification (WIQ-V1-014)
    # ------------------------------------------------------------------

    email_backend: Literal["console", "smtp"] = Field(
        default="console",
        alias="EMAIL_BACKEND",
    )

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT", gt=0)
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    email_from: str | None = Field(default=None, alias="EMAIL_FROM")
    email_from_name: str = Field(default="Waste-IQ", alias="EMAIL_FROM_NAME")

    frontend_url: str = Field(
        default="http://localhost:5173",
        alias="FRONTEND_URL",
    )

    verification_token_expire_minutes: int = Field(
        default=1440,
        alias="VERIFICATION_TOKEN_EXPIRE_MINUTES",
        gt=0,
    )

    rate_limit_window_seconds: int = Field(
        default=60,
        alias="RATE_LIMIT_WINDOW_SECONDS",
        gt=0,
    )

    lockout_failed_attempt_threshold: int = Field(
        default=5,
        alias="LOCKOUT_FAILED_ATTEMPT_THRESHOLD",
        gt=0,
    )

    lockout_cooldown_minutes: int = Field(
        default=15,
        alias="LOCKOUT_COOLDOWN_MINUTES",
        gt=0,
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        # FIX: populate_by_name allows both alias and field name to work
        populate_by_name=True,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cloudinary_configured(self) -> bool:
        return all(
            [self.cloudinary_cloud_name, self.cloudinary_api_key, self.cloudinary_api_secret]
        )

    @property
    def cloudinary_required(self) -> bool:
        return self.is_production

    @property
    def sentry_enabled(self) -> bool:
        return bool(self.sentry_dsn)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
