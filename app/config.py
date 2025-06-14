import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AIPIPE_TOKEN: str = os.getenv("AIPIPE_TOKEN", "")
    AIPIPE_BASE_URL: str = "https://aipipe.org/openai/v1"
    ALLOWED_MODELS: dict = {
        "default": "openai/gpt-4.1-nano",
        "fallback": "openai/gpt-3.5-turbo"
    }

    class Config:
        env_file = ".env"

settings = Settings()