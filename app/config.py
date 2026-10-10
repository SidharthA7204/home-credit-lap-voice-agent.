from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    company_name: str = "Home Credit"
    agent_name: str = "Riya"
    agent_gender: str = "female"
    default_language: str = "en"
    max_unclear_retries: int = 3
    data_dir: str = "data/calls"


@lru_cache
def get_settings() -> Settings:
    return Settings()
