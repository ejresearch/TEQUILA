"""Configuration settings for the Latin A curriculum system."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
