from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Waste-IQ API"
    database_url: str = Field(
        default="postgresql+psycopg://wasteiq:wasteiq@db:5432/wasteiq",
        alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # FIX: populate_by_name allows both alias and field name to work
        populate_by_name=True,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
