from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "uni-reco"
    DEBUG: bool = True  # dev режим — включить /docs и SQL-логи

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "uni"
    DB_USER: str = "app"
    DB_PASS: str = "app"

    db_driver: str = "postgresql+asyncpg"

    # JWT — ОБЯЗАТЕЛЬНО задать в .env (иначе будет сгенерирован случайный)
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_hex(32))

    # Rate limiting
    RATE_LIMIT_AUTH: str = "10/minute"   # для login/register

    @property
    def DATABASE_URL(self) -> str:
        return f"{self.db_driver}://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
