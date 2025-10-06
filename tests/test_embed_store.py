import json
from pathlib import Path

import pytest
from langchain_community.embeddings import FakeEmbeddings
from langchain.schema import Document

from src import embed_store


@pytest.fixture(autouse=True)
def _reset_embedding_state(tmp_path, monkeypatch):
    persist_dir = tmp_path / "chroma"
    persist_dir.mkdir()

    monkeypatch.setattr(embed_store, "CHROMA_PERSIST_DIR", str(persist_dir))
    monkeypatch.setattr(embed_store, "_EMBEDDING_CONFIG_PATH", persist_dir / "embedding_config.json")
    monkeypatch.setattr(embed_store, "EMBEDDING_BACKEND", "fake")
    monkeypatch.setattr(embed_store, "EMBEDDING_MODEL", "fake-test-model")

    embed_store._embedding_instance = None  # pylint: disable=protected-access
    embed_store._embedding_signature = None  # pylint: disable=protected-access

    return persist_dir


@pytest.fixture()
def synthetic_documents():
    return [
        Document(page_content="Synthetic document about testing the vector store.", metadata={"source": "doc1.txt"}),
        Document(page_content="Additional context helps validate retrieval.", metadata={"source": "doc2.txt"}),
    ]


def test_get_embedding_model_returns_fake():
    model = embed_store.get_embedding_model()
    assert isinstance(model, FakeEmbeddings)


def test_build_vector_store_persists_embedding_config(synthetic_documents):
    vectordb = embed_store.build_vector_store(synthetic_documents)

    assert vectordb is not None
    config_path = embed_store._EMBEDDING_CONFIG_PATH  # pylint: disable=protected-access
    assert config_path.exists()

    persisted = json.loads(config_path.read_text(encoding="utf-8"))
    assert persisted["backend"] == "fake"
    assert persisted["model"] == "fake-test-model"


def test_load_vector_store_warns_on_backend_change(synthetic_documents, caplog):
    # Build an initial store so the directory exists.
    embed_store.build_vector_store(synthetic_documents)

    config_path = embed_store._EMBEDDING_CONFIG_PATH  # pylint: disable=protected-access
    assert config_path.exists()

    # Simulate a configuration change that should trigger a warning.
    config_path.write_text(json.dumps({"backend": "huggingface", "model": "all-MiniLM-L6-v2"}), encoding="utf-8")

    embed_store._embedding_instance = None  # pylint: disable=protected-access
    embed_store._embedding_signature = None  # pylint: disable=protected-access

    with caplog.at_level("WARNING"):
        vectordb = embed_store.load_vector_store()

    assert vectordb is not None
    assert any("Embedding configuration changed" in message for message in caplog.messages)

