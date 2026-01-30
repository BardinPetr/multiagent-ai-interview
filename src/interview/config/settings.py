from pydantic_settings import BaseSettings

# noinspection PyUnresolvedReferences
import interview.interview_log


class Settings(BaseSettings):
    # llm: str = "openrouter/google/gemini-2.5-flash"
    llm: str = "openrouter/google/gemini-3-flash-preview"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
