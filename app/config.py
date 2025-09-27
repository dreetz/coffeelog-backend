from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DB_URL: str
    DB_USER: str
    DB_KEY: str
    DB_SCHEMA: str
    REDIS_URL: str
    REDIS_PORT: int



settings = Settings()
