"""Centralized configuration management using Pydantic settings.

This module provides a centralized configuration system that loads settings from
multiple sources with the following precedence order:
1. Environment variables
2. config.yaml file
3. Default values defined in the code

Configuration includes:
- API keys and service endpoints
- Model and embedding configurations
- File system paths
- Retrieval and generation parameters

Example config.yaml:
    ```yaml
    openai_api_key: "your-key-here"
    llm_model: "gpt-4"
    chunk_size: 1000
    chunk_overlap: 200
    ```
"""

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
    """Load configuration defaults from a YAML file.
    
    Args:
        path: Path to the YAML configuration file.
        
    Returns:
        Dict containing the loaded configuration with lowercase keys, or an empty
        dict if the file doesn't exist or is invalid.
        
    Note:
        - Silently handles missing files and invalid YAML
        - Converts all keys to lowercase for case-insensitive access
        - Logs warnings for any issues encountered
    """
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

    llm_provider: str = Field(default=_YAML_DEFAULTS.get("llm_provider", "groq"))
    llm_model: str = Field(default=_YAML_DEFAULTS.get("llm_model", "llama-3.1-8b-instant"))
    llm_temperature: float = Field(default=_YAML_DEFAULTS.get("llm_temperature", 0.1))
    llm_max_output_tokens: int = Field(default=_YAML_DEFAULTS.get("llm_max_output_tokens", 2048))
    llm_request_timeout: Optional[int] = Field(default=_YAML_DEFAULTS.get("llm_request_timeout"))
    llm_max_retries: int = Field(default=_YAML_DEFAULTS.get("llm_max_retries", 3))

    retriever_semantic_weight: float = Field(default=_YAML_DEFAULTS.get("retriever_semantic_weight", 0.7))
    retriever_keyword_weight: float = Field(default=_YAML_DEFAULTS.get("retriever_keyword_weight", 0.3))
    retriever_k: int = Field(default=_YAML_DEFAULTS.get("retriever_k", 5))

    embedding_backend: str = Field(default=_YAML_DEFAULTS.get("embedding_backend", "huggingface"))
    embedding_model: str = Field(default=_YAML_DEFAULTS.get("embedding_model", "all-MiniLM-L6-v2"))
    embedding_endpoint: Optional[str] = Field(default=_YAML_DEFAULTS.get("embedding_endpoint"))
    embedding_api_key: Optional[str] = Field(default=_YAML_DEFAULTS.get("embedding_api_key"))

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


def _mask_value(key: str, value: Any) -> Any:
    """Mask sensitive values in configuration for logging.
    
    Args:
        key: Configuration key name
        value: Configuration value to potentially mask
        
    Returns:
        The original value, or a masked version if the key indicates sensitive data.
        
    Note:
        - Masks any value where the key contains 'api_key' or matches known sensitive keys
        - Truncates long string values (over 64 chars) for readability
    """
    if value is None:
        return None
    sensitive_keys = {"api_key", "openai_api_key", "groq_api_key", "embedding_api_key"}
    if any(token in key.lower() for token in sensitive_keys):
        return "***"
    if isinstance(value, str) and len(value) > 64:
        return value[:61] + "…"
    return value


def _log_effective_settings(settings: AppSettings) -> None:
    """Log the effective configuration settings with sensitive data masked.
    
    Args:
        settings: The AppSettings instance to log
        
    Note:
        - Masks sensitive data before logging
        - Shows the effective configuration after all overrides are applied
        - Logs the precedence order for configuration sources
    """
    values = settings.model_dump()
    sanitized = {key: _mask_value(key, value) for key, value in values.items()}
    logger.info(
        "Configuration loaded",
        precedence="environment variables > config.yaml > defaults",
        settings=sanitized,
    )


@lru_cache()
def get_settings() -> AppSettings:
    """Get the application settings with caching.
    
    Returns:
        AppSettings: The application configuration
        
    Note:
        - Uses LRU caching to avoid reloading settings
        - Logs the effective configuration on first load
        - Subsequent calls return the cached instance
    """
    settings = AppSettings()
    _log_effective_settings(settings)
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

LLM_PROVIDER = settings.llm_provider
LLM_TEMPERATURE = settings.llm_temperature
LLM_MAX_OUTPUT_TOKENS = settings.llm_max_output_tokens
LLM_REQUEST_TIMEOUT = settings.llm_request_timeout
LLM_MAX_RETRIES = settings.llm_max_retries

RETRIEVER_SEMANTIC_WEIGHT = settings.retriever_semantic_weight
RETRIEVER_KEYWORD_WEIGHT = settings.retriever_keyword_weight
RETRIEVER_K = settings.retriever_k

EMBEDDING_BACKEND = settings.embedding_backend
EMBEDDING_ENDPOINT = settings.embedding_endpoint
EMBEDDING_API_KEY = settings.embedding_api_key
