"""Centralized configuration management using Pydantic settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.logging_config import get_logger


load_dotenv()

logger = get_logger(__name__)

_BASE_DIR_DEFAULT = Path(__file__).resolve().parent.parent
_CONFIG_YAML_PATH_DEFAULT = _BASE_DIR_DEFAULT / "config.yaml"


def _load_yaml_defaults(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            logger.warning("config.yaml did not contain a mapping; ignoring contents")
            return {}
        return {str(key).lower(): value for key, value in data.items()}
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to load config.yaml", error=str(exc))
        return {}


_YAML_DEFAULTS = _load_yaml_defaults(_CONFIG_YAML_PATH_DEFAULT)


class AppSettings(BaseSettings):
    """Application configuration with environment and YAML overrides."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    base_dir: Path = Field(default=_BASE_DIR_DEFAULT)
    config_yaml_path: Path = Field(default=_CONFIG_YAML_PATH_DEFAULT)

    openai_api_key: Optional[str] = Field(default=_YAML_DEFAULTS.get("openai_api_key"))
    groq_api_key: Optional[str] = Field(default=_YAML_DEFAULTS.get("groq_api_key"))

    chunk_size: int = Field(default=_YAML_DEFAULTS.get("chunk_size", 1000))
    chunk_overlap: int = Field(default=_YAML_DEFAULTS.get("chunk_overlap", 150))
    top_k: int = Field(default=_YAML_DEFAULTS.get("top_k", 5))

    llm_model: str = Field(default=_YAML_DEFAULTS.get("llm_model", "llama-3.1-8b-instant"))
    embedding_model: str = Field(default=_YAML_DEFAULTS.get("embedding_model", "all-MiniLM-L6-v2"))
    database_url: Optional[str] = Field(default=_YAML_DEFAULTS.get("database_url"))

    @computed_field(return_type=str)
    def raw_data_dir(self) -> str:
        return str(self.base_dir / "data" / "raw")

    @computed_field(return_type=str)
    def processed_data_dir(self) -> str:
        return str(self.base_dir / "data" / "processed")

    @computed_field(return_type=str)
    def checksum_dir(self) -> str:
        return str(Path(self.processed_data_dir) / "checksums")

    @computed_field(return_type=str)
    def chroma_persist_dir(self) -> str:
        return str(self.base_dir / "chroma_store")

    @computed_field(return_type=str)
    def prompts_dir(self) -> str:
        return str(self.base_dir / "src" / "prompts")

    @computed_field(return_type=str)
    def models_cache_dir(self) -> str:
        return str(self.base_dir / "models_cache")

    @computed_field(return_type=str)
    def database_url_sync(self) -> str:
        if self.database_url:
            return str(self.database_url)

        database_path = self.base_dir / "conversations.db"
        return f"sqlite:///{database_path}"

    @computed_field(return_type=str)
    def database_url_async(self) -> str:
        url = self.database_url_sync
        if url.startswith("sqlite+aiosqlite://"):
            return url
        if url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "sqlite+aiosqlite:///")
        if url.startswith("sqlite:////"):
            return url.replace("sqlite:////", "sqlite+aiosqlite:////")
        return url


@lru_cache()
def get_settings() -> AppSettings:
    settings = AppSettings()
    logger.debug("Configuration loaded", base_dir=str(settings.base_dir))
    return settings


settings = get_settings()

BASE_DIR = str(settings.base_dir)
CONFIG_YAML_PATH = str(settings.config_yaml_path)

RAW_DATA_DIR = settings.raw_data_dir
PROCESSED_DATA_DIR = settings.processed_data_dir
CHECKSUM_DIR = settings.checksum_dir
CHROMA_PERSIST_DIR = settings.chroma_persist_dir
PROMPTS_DIR = settings.prompts_dir
MODELS_CACHE_DIR = settings.models_cache_dir

OPENAI_API_KEY = settings.openai_api_key
GROQ_API_KEY = settings.groq_api_key

CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
TOP_K = settings.top_k

LLM_MODEL = settings.llm_model
EMBEDDING_MODEL = settings.embedding_model
