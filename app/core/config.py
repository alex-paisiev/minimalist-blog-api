import typing
from functools import cached_property, lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # PostgreSQL
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int

    # Redis
    CACHE_HOST: str
    CACHE_PORT: int

    # App
    APP_ENV: typing.Literal["development", "production", "testing"]
    LOG_LEVEL: typing.Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int 
    MAX_PAGE_SIZE: int

    # Cache TTL in seconds
    CACHE_TTL: int

    @cached_property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @cached_property
    def redis_url(self) -> str:
        return f"redis://{self.CACHE_HOST}:{self.CACHE_PORT}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
