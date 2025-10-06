"""Embedding store utilities with backend abstraction and configuration tracking."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, Optional

from langchain_chroma import Chroma

from src.config import (
    CHROMA_PERSIST_DIR,
    EMBEDDING_API_KEY,
    EMBEDDING_BACKEND,
    EMBEDDING_ENDPOINT,
    EMBEDDING_MODEL,
    MODELS_CACHE_DIR,
    OPENAI_API_KEY,
    TOP_K,
)
from src.exceptions import EmbeddingError, VectorStoreError
from src.logging_config import get_logger


logger = get_logger(__name__)

_EMBEDDING_CONFIG_PATH = Path(CHROMA_PERSIST_DIR) / "embedding_config.json"
_embedding_lock = Lock()
_embedding_instance: Optional[Any] = None
_embedding_signature: Optional[Dict[str, Any]] = None


def _current_embedding_signature() -> Dict[str, Any]:
    return {
        "backend": (EMBEDDING_BACKEND or "huggingface").lower(),
        "model": EMBEDDING_MODEL,
        "endpoint": EMBEDDING_ENDPOINT,
    }


def _load_huggingface_embeddings(options: Dict[str, Any]) -> Any:
    from langchain_huggingface import HuggingFaceEmbeddings  # lazy import

    try:
        import torch
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise EmbeddingError("Torch is required for HuggingFace embeddings.", {"error": str(exc)}) from exc

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Using HuggingFace embeddings", model=options["model"], device=device)
    os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
    return HuggingFaceEmbeddings(
        model_name=options["model"],
        model_kwargs={"device": device},
        cache_folder=MODELS_CACHE_DIR,
    )


def _load_openai_embeddings(options: Dict[str, Any]) -> Any:
    try:  # pragma: no cover - optional dependency
        from langchain_openai import OpenAIEmbeddings
    except ImportError as exc:  # pragma: no cover
        raise EmbeddingError(
            "OpenAI embeddings requested but langchain-openai is not installed.",
            {},
        ) from exc

    api_key = EMBEDDING_API_KEY or OPENAI_API_KEY
    if not api_key:
        raise EmbeddingError("OPENAI_API_KEY not configured for OpenAI embedding backend.", {})

    logger.info("Using OpenAI embeddings", model=options["model"])
    return OpenAIEmbeddings(
        api_key=api_key,
        model=options["model"],
        max_retries=options.get("max_retries", 3),
        request_timeout=options.get("request_timeout", 30),
    )


def _load_fake_embeddings(options: Dict[str, Any]) -> Any:
    try:
        from langchain_community.embeddings import FakeEmbeddings
    except ImportError as exc:  # pragma: no cover - langchain core missing
        raise EmbeddingError("langchain-community is required for fake embeddings.", {}) from exc

    logger.info("Using FakeEmbeddings backend for testing", size=options.get("size", 1536))
    return FakeEmbeddings(size=options.get("size", 1536))


_EMBEDDING_ADAPTERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "huggingface": _load_huggingface_embeddings,
    "openai": _load_openai_embeddings,
    "fake": _load_fake_embeddings,
}


def _resolve_embedding_adapter(backend: str) -> Callable[[Dict[str, Any]], Any]:
    adapter = _EMBEDDING_ADAPTERS.get(backend)
    if adapter:
        return adapter
    raise EmbeddingError(
        "Unsupported embedding backend.",
        {"backend": backend, "available_backends": list(_EMBEDDING_ADAPTERS)},
    )


def _load_previous_embedding_config() -> Optional[Dict[str, Any]]:
    if not _EMBEDDING_CONFIG_PATH.exists():
        return None
    try:
        with _EMBEDDING_CONFIG_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:  # pragma: no cover - config corruption
        logger.warning("Failed to read embedding configuration file", error=str(exc))
        return None


def _persist_embedding_config(config: Dict[str, Any]) -> None:
    try:
        _EMBEDDING_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _EMBEDDING_CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
    except Exception as exc:  # pragma: no cover - disk issues
        logger.warning("Failed to persist embedding configuration", error=str(exc))


def _emit_embedding_change_warning(current: Dict[str, Any]) -> None:
    previous = _load_previous_embedding_config()
    if previous and previous != current:
        logger.warning(
            "Embedding configuration changed since last ingestion; please re-ingest documents.",
            previous=previous,
            current=current,
        )


def _get_or_create_embedding() -> Any:
    global _embedding_instance, _embedding_signature

    signature = _current_embedding_signature()
    backend = signature["backend"]

    if _embedding_instance is not None and _embedding_signature == signature:
        return _embedding_instance

    adapter = _resolve_embedding_adapter(backend)
    options = {
        "model": signature["model"],
        "endpoint": signature.get("endpoint"),
        "max_retries": 3,
        "request_timeout": 30,
    }

    if backend == "openai" and signature.get("endpoint"):
        options["endpoint"] = signature["endpoint"]

    _embedding_instance = adapter(options)
    _embedding_signature = signature
    return _embedding_instance


def get_embedding_model() -> Any:
    """Return the configured embedding model, instantiating it if necessary."""

    with _embedding_lock:
        try:
            return _get_or_create_embedding()
        except EmbeddingError:
            raise
        except Exception as exc:
            logger.error("Failed to load embedding model", backend=EMBEDDING_BACKEND, error=str(exc))
            raise EmbeddingError("Failed to load embedding model", {"backend": EMBEDDING_BACKEND, "error": str(exc)}) from exc


def build_vector_store(chunks):
    """Build a new Chroma vector store from document chunks and persist metadata."""

    if not chunks:
        logger.warning("No chunks provided to build vector store.")
        return None

    embeddings = get_embedding_model()
    try:
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )
        logger.info("Vector store built and persisted", chunks_count=len(chunks))
        _persist_embedding_config(_current_embedding_signature())
        return vectordb
    except Exception as exc:
        logger.error("Failed to build vector store", chunks_count=len(chunks), error=str(exc))
        raise VectorStoreError(
            f"Failed to build vector store: {exc}",
            {"chunks_count": len(chunks), "error": str(exc)},
        ) from exc


def load_vector_store():
    """Load a persisted Chroma vector store, emitting configuration warnings if needed."""

    if not os.path.exists(CHROMA_PERSIST_DIR):
        logger.error("Vector store not found. Please index a document first.")
        return None

    embeddings = get_embedding_model()
    _emit_embedding_change_warning(_current_embedding_signature())

    try:
        vectordb = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )
        logger.info("Vector store loaded successfully")
        return vectordb
    except Exception as exc:
        logger.error("Failed to load vector store", error=str(exc))
        raise VectorStoreError(f"Failed to load vector store: {exc}", {"error": str(exc)}) from exc


def get_retriever(vectordb):
    """Create a retriever from the vector store respecting configured top-K."""

    if not vectordb:
        logger.error("No vector store provided for retriever.")
        return None
    return vectordb.as_retriever(search_kwargs={"k": TOP_K})