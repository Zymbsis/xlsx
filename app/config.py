from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: Literal["dev", "prod"] = "dev"

    api_key: str
    groq_api_key: str
    pg_database_url: str
    redis_url: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
SettingsDep = Annotated[Settings, Depends(get_settings)]
