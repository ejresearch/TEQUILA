"""Configuration settings for the Latin A curriculum system."""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Curriculum paths
    curriculum_base_path: Path = Path(__file__).parent.parent / "curriculum"
    exports_path: Path = Path(__file__).parent.parent / "curriculum" / "exports"

    # Curriculum parameters
    total_weeks: int = 36
    days_per_week: int = 4

    # LLM Configuration (OpenAI GPT-4o only)
    PROVIDER: str = "openai"  # Fixed to OpenAI
    OPENAI_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gpt-4o"
    GEN_TEMP: float = 0.25
    GEN_MAX_TOKENS: int = 3000
    TIMEOUT_S: int = 30

    # Cost Control & Safety
    DRY_RUN: bool = False
    BUDGET_USD: Optional[float] = None
    COST_WARN_PCT: float = 0.8
    MAX_WEEK: Optional[int] = None
    PROMPT_VERSION: str = "v1"
    PROMPT_COMPAT_MODE: bool = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the settings instance."""
    return settings


def get_llm_client():
    """Get the configured OpenAI GPT-4o LLM client."""
    from .services.llm_client import OpenAIClient

    s = get_settings()
    if not s.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required. Set it in .env file.")

    return OpenAIClient(
        api_key=s.OPENAI_API_KEY,
        model=s.MODEL_NAME,
        temp=s.GEN_TEMP,
        max_tokens=s.GEN_MAX_TOKENS,
        timeout=s.TIMEOUT_S
    )
