# app/config.py
from pydantic_settings import BaseSettings
import os

# Add these constants
DATE_RANGES = {
    "discourse": ("2023-01-01", "2025-12-31"),  # (start_date, end_date)
    "docsify": ("2023-01-01", "2025-12-31")
}

DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in"
DOCSIFY_BASE = "https://your-docsify-site.com/"  # Replace with actual URL

# Keep your existing Settings class
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