from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base paths
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    output_dir: Path = BASE_DIR / "data" / "outputs"
    session_dir: Path = BASE_DIR / "data" / "sessions"

    # Browser & Crawler
    headless: bool = True
    browser_timeout_ms: int = 30000
    slow_mo_ms: int = 100
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # LLM Agent
    llm_provider: str = "openai"
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"


settings = Settings()

