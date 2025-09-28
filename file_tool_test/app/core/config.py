"""Configuration for professional file tool."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Settings for professional file tool."""

    openai_api_key: str | None = Field(default=None)
    storage_dir: Path = Field(default=Path("./data"))

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached settings instance."""
    settings = AppSettings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
