import os
import pytest
from src.ingest import process_document
from src.config import RAW_DATA_DIR

def test_process_document_valid_pdf():
    test_pdf = os.path.join(RAW_DATA_DIR, "advanced-rag-interview-prep.pdf")
    chunks = process_document(test_pdf)
    assert chunks is not None
    assert isinstance(chunks, list)
    assert len(chunks) > 0

def test_process_document_invalid_path():
    chunks = process_document("nonexistent.pdf")
    assert chunks is None

def test_process_document_unsupported_type():
    with pytest.raises(ValueError):
        process_document(os.path.join(RAW_DATA_DIR, "unsupported.xyz"))

