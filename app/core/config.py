from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "uni-reco"
    DEBUG: bool = True
    JWT_SECRET: str = "CHANGE_ME"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_NAME: str = "uni"
    DB_USER: str = "app"
    DB_PASS: str = "app"

    db_driver: str = "postgresql+asyncpg"

    # Email / SMTP (например, Gmail)
    MAIL_USERNAME: Optional[str] = None
    APP_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
        return value

    @property
    def DATABASE_URL(self) -> str:
        return f"{self.db_driver}://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
