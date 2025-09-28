import textwrap

import pytest

from src.exceptions import DocumentProcessingError
from src.ingest import process_document
import src.ingest as ingest_module


@pytest.fixture(autouse=True)
def _isolated_ingest_dirs(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    checksums = tmp_path / "checksums"
    processed.mkdir()
    checksums.mkdir()

    monkeypatch.setattr(ingest_module, "PROCESSED_DATA_DIR", str(processed))
    monkeypatch.setattr(ingest_module, "CHECKSUM_DIR", str(checksums))


def test_process_document_valid_text(tmp_path):
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text(textwrap.dedent(
        """
        This is a sample document used for ingestion tests.
        It contains multiple sentences so that the splitter can create chunks.
        """
    ).strip())

    chunks = process_document(str(sample_file))

    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_process_document_invalid_path(tmp_path):
    missing_path = tmp_path / "does-not-exist.txt"
    with pytest.raises(DocumentProcessingError):
        process_document(str(missing_path))


def test_process_document_unsupported_type(tmp_path):
    unsupported = tmp_path / "file.unsupported"
    unsupported.write_text("data")
    with pytest.raises(DocumentProcessingError):
        process_document(str(unsupported))

