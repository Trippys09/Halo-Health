"""
HALO Health – Central Configuration
All environment variables loaded via pydantic-settings.
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory where this config file lives (backend/)
_BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    pro_model: str = "gemini-2.5-flash"
    flash_model: str = "gemini-2.5-flash"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # Database
    database_url: str = "sqlite:///./aura.db"

    # ChromaDB
    chroma_db_path: str = "./chroma_data"

    # Insurance API
    insurance_api_base_url: str = (
        "https://nagur-shareef-shaik-insucompass-ai.hf.space/api"
    )

    # Search
    tavily_api_key: str = ""

    # Backend URL (used by frontend)
    backend_url: str = "http://localhost:8000"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
