from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENV: str = "dev"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    DATABASE_URL: str = "sqlite+aiosqlite:///./streamhub.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "dev-secret-change-me-min-32-chars-long!!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    SEARCH_CACHE_TTL: int = 900  # 15 min
    CARD_CACHE_TTL: int = 3600  # 1 hour
    PROVIDERS_CACHE_TTL: int = 86400  # 24h

    TMDB_API_KEY: str = ""
    KINOPOISK_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    SHORT_LINK_BASE: str = "https://sh.link"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    PROVIDER_TIMEOUT: float = 8.0
    PROVIDER_RPS: float = 2.0

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
