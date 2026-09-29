"""Scrybe Application Settings.

Centralizes all configuration loaded from environment variables and
config/sources.yaml. Uses pydantic-settings for typed validation.
"""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

from scrybe.storage.models import SourceTargetConfig


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    # ── LLM Providers ──
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # ── Model Tier Allocation ──
    extraction_model: str = "gpt-4o-mini"
    reasoning_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    # ── Scraping & Network ──
    user_agent: str = "Scrybe/1.0 (+https://scrybe.ai/bot; contact@scrybe.ai)"
    max_concurrent_scrapes: int = 3
    crawl_delay_min_seconds: float = 2.5
    proxy_url: str = ""

    # ── Storage ──
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'scrybe.db'}"
    faiss_index_path: str = str(PROJECT_ROOT / "data" / "faiss_index.bin")
    redis_url: str = "redis://localhost:6379/0"

    # ── Compliance ──
    respect_robots_txt: bool = True
    pii_filter_enabled: bool = True
    confidence_threshold: float = 0.60
    multi_source_min_count: int = 2

    # ── API ──
    api_port: int = 8000
    api_key: str = "scrybe_secret_dev_key"
    log_level: str = "INFO"

    # ── Paths ──
    sources_config_path: str = str(PROJECT_ROOT / "config" / "sources.yaml")
    prompts_dir: str = str(PROJECT_ROOT / "scrybe" / "agents" / "prompts")
    output_dir: str = str(PROJECT_ROOT / "output")

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8", "extra": "ignore"}


def load_sources(config_path: Optional[str] = None) -> List[SourceTargetConfig]:
    """Load and validate target source configurations from YAML.

    Args:
        config_path: Path to sources.yaml. Defaults to config/sources.yaml.

    Returns:
        List of validated SourceTargetConfig objects.
    """
    path = Path(config_path) if config_path else Path(Settings().sources_config_path)
    if not path.exists():
        return []

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    sources = []
    for entry in raw.get("sources", []):
        if entry.get("enabled", True):
            sources.append(SourceTargetConfig(**entry))
    return sources


def load_prompt(prompt_name: str, **kwargs: str) -> str:
    """Load a prompt template from disk and format with provided variables.

    Args:
        prompt_name: Filename of the prompt template (without .txt extension).
        **kwargs: Template variables to substitute into the prompt.

    Returns:
        The formatted prompt string.
    """
    settings = Settings()
    prompt_path = Path(settings.prompts_dir) / f"{prompt_name}.txt"
    template = prompt_path.read_text(encoding="utf-8")
    return template.format(**kwargs) if kwargs else template


# Singleton settings instance
settings = Settings()
