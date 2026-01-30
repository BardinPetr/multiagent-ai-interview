from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    llm: str = "openrouter/google/gemini-2.5-flash"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
