"""Configuration settings for the Latin A curriculum system."""
from pathlib import Path
from typing import Literal, Optional
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

    # LLM Configuration
    PROVIDER: Literal["openai", "anthropic"] = "openai"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gpt-4o"
    GEN_TEMP: float = 0.25
    GEN_MAX_TOKENS: int = 3000
    TIMEOUT_S: int = 30


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the settings instance."""
    return settings


def get_llm_client():
    """Get the configured LLM client based on provider setting."""
    from .services.llm_client import OpenAIClient, AnthropicClient

    s = get_settings()
    if s.PROVIDER == "anthropic":
        if not s.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when PROVIDER=anthropic")
        return AnthropicClient(
            api_key=s.ANTHROPIC_API_KEY,
            model=s.MODEL_NAME,
            temp=s.GEN_TEMP,
            max_tokens=s.GEN_MAX_TOKENS,
            timeout=s.TIMEOUT_S
        )
    else:
        if not s.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when PROVIDER=openai")
        return OpenAIClient(
            api_key=s.OPENAI_API_KEY,
            model=s.MODEL_NAME,
            temp=s.GEN_TEMP,
            max_tokens=s.GEN_MAX_TOKENS,
            timeout=s.TIMEOUT_S
        )
