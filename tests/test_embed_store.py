import os
import pytest
import shutil
from unittest.mock import patch
from src.embed_store import build_vector_store, load_vector_store
from src.config import CHROMA_PERSIST_DIR

@pytest.fixture
def mock_chunks():
    return [
        {"id": "1", "content": "This is a test chunk."},
        {"id": "2", "content": "Another test chunk."},
    ]

@patch("src.embed_store.get_embedding_model")
@patch("src.embed_store.Chroma")
def test_build_vector_store_create(mock_chroma, mock_get_embedding_model, mock_chunks):
    """Test creating a new vector store."""
    if os.path.exists(CHROMA_PERSIST_DIR):
        shutil.rmtree(CHROMA_PERSIST_DIR)  # Ensure no existing store

    mock_get_embedding_model.return_value = mock_chroma.return_value.embedding_function

    # Ensure from_documents returns a mock with a persist method
    mock_chroma.from_documents.return_value = mock_chroma.return_value

    build_vector_store(mock_chunks)

    mock_chroma.from_documents.assert_called_once_with(
        documents=mock_chunks,
        embedding=mock_chroma.return_value.embedding_function,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    mock_chroma.return_value.persist.assert_called_once()

@patch("src.embed_store.get_embedding_model")
@patch("src.embed_store.Chroma")
def test_build_vector_store_append(mock_chroma, mock_get_embedding_model, mock_chunks):
    """Test appending to an existing vector store."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)  # Simulate existing store

    mock_get_embedding_model.return_value = mock_chroma.return_value.embedding_function

    build_vector_store(mock_chunks)

    mock_chroma.assert_called_once_with(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=mock_chroma.return_value.embedding_function,
    )
    mock_chroma.return_value.add_documents.assert_called_once_with(documents=mock_chunks)
    mock_chroma.return_value.persist.assert_called_once()
