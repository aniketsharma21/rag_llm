import os
import pytest
from src.embed_store import build_vector_store, load_vector_store, get_embedding_model
from src.config import PROCESSED_DATA_DIR
import pickle

def test_build_vector_store_with_chunks():
    # Use cached chunks from a processed document
    chunk_file = os.path.join(PROCESSED_DATA_DIR, "advanced-rag-interview-prep_chunks.pkl")
    if not os.path.exists(chunk_file):
        pytest.skip("Chunk file not found. Run document processing first.")
    with open(chunk_file, "rb") as f:
        chunks = pickle.load(f)
    vectordb = build_vector_store(chunks)
    assert vectordb is not None


def test_load_vector_store():
    vectordb = load_vector_store()
    assert vectordb is not None


def test_get_embedding_model():
    model = get_embedding_model()
    assert model is not None

