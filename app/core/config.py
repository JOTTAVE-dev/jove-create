from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="JOVE Manager", alias="APP_NAME")
    app_timezone: str = Field(default="America/Fortaleza", alias="APP_TIMEZONE")
    database_url: str = Field(default="sqlite:///./data/jove.db", alias="DATABASE_URL")
    database_pool_size: int = Field(default=1, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=0, alias="DATABASE_MAX_OVERFLOW")
    secret_key: str = Field(
        default="change-this-secret-key-before-production",
        alias="SECRET_KEY",
    )
    admin_email: str | None = Field(default=None, alias="ADMIN_EMAIL")
    admin_password: str | None = Field(default=None, alias="ADMIN_PASSWORD")
    session_cookie_name: str = Field(default="jove_session", alias="SESSION_COOKIE_NAME")
    csrf_cookie_name: str = Field(default="jove_csrf", alias="CSRF_COOKIE_NAME")
    session_expire_minutes: int = Field(default=480, alias="SESSION_EXPIRE_MINUTES")
    login_max_attempts: int = Field(default=5, alias="LOGIN_MAX_ATTEMPTS")
    login_lockout_minutes: int = Field(default=15, alias="LOGIN_LOCKOUT_MINUTES")
    vercel_environment: str | None = Field(default=None, alias="VERCEL_ENV")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
