from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "uni-reco"
    DEBUG: bool = True

    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_NAME: str = "uni"
    DB_USER: str = "app"
    DB_PASS: str = "app"

    db_driver: str = "postgresql+asyncpg"

    @property
    def DATABASE_URL(self) -> str:
        return f"{self.db_driver}://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

