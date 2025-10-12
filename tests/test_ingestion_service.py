import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

import src.services.ingestion_service as ingestion_module
from src.services.ingestion_service import IngestionService


@pytest.fixture(autouse=True)
def _patch_raw_dir(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    monkeypatch.setattr(ingestion_module, "RAW_DATA_DIR", str(raw_dir))
    return raw_dir


@pytest.fixture
def repo_stubs(monkeypatch):
    jobs = {}
    documents = {}
    document_counter = 0

    class StubDocumentRepository:
        def __init__(self, _session):
            pass

        async def create(
            self,
            *,
            filename: str,
            original_filename: str,
            file_path: str,
            file_size: int,
            file_type: str,
            checksum: str,
        ):
            nonlocal document_counter
            document_counter += 1
            record = {
                "id": document_counter,
                "filename": filename,
                "original_filename": original_filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "checksum": checksum,
                "chunks_count": 0,
                "is_processed": False,
            }
            documents[document_counter] = record
            return record

        async def update_processing(self, document_id: int, *, chunks_count: int) -> bool:
            record = documents.get(document_id)
            if record is None:
                return False
            record["chunks_count"] = chunks_count
            record["is_processed"] = True
            record["processed_at"] = datetime.now(timezone.utc)
            return True

    class StubJobRepository:
        def __init__(self, _session):
            pass

        async def create(
            self,
            *,
            job_id: str,
            file_name: str,
            status: str = "queued",
            message: str | None = None,
            details: dict | None = None,
        ):
            record = {
                "job_id": job_id,
                "file_name": file_name,
                "status": status,
                "message": message,
                "details": details or {},
                "error": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            jobs[job_id] = record
            return record

        async def get(self, job_id: str):
            return jobs.get(job_id)

        async def update(
            self,
            job_id: str,
            *,
            status: str | None = None,
            message: str | None = None,
            details: dict | None = None,
            error: str | None = None,
        ):
            record = jobs.get(job_id)
            if record is None:
                return None
            if status is not None:
                record["status"] = status
            if message is not None:
                record["message"] = message
            if details is not None:
                record["details"].update(details)
            if error is not None:
                record["error"] = error
            record["updated_at"] = datetime.now(timezone.utc)
            return record

    @asynccontextmanager
    async def fake_get_session():
        yield object()

    monkeypatch.setattr(ingestion_module, "DocumentRepository", StubDocumentRepository)
    monkeypatch.setattr(ingestion_module, "JobRepository", StubJobRepository)
    monkeypatch.setattr(ingestion_module, "get_session", fake_get_session)

    return {
        "jobs": jobs,
        "documents": documents,
        "job_factory": StubJobRepository,
        "document_factory": StubDocumentRepository,
    }


@pytest.mark.asyncio
async def test_enqueue_upload_persists_file(repo_stubs):
    service = IngestionService()
    upload = UploadFile(filename="doc.txt", file=BytesIO(b"hello world"))

    job_id, stored_path = await service.enqueue_upload(upload)

    assert repo_stubs["jobs"][job_id]["file_name"] == "doc.txt"
    assert Path(stored_path).exists()
    assert Path(stored_path).read_bytes() == b"hello world"


@pytest.mark.asyncio
async def test_process_job_success(monkeypatch, tmp_path, repo_stubs):
    file_path = tmp_path / "raw" / "doc.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("content")

    monkeypatch.setattr(ingestion_module, "process_document", lambda path: ["chunk1", "chunk2"])

    captured = {}

    def fake_build_vector_store(chunks):
        captured["chunks"] = chunks
        return "vectordb"

    monkeypatch.setattr(ingestion_module, "build_vector_store", fake_build_vector_store)

    service = IngestionService()
    job_id = "job-success"

    doc_repo = repo_stubs["document_factory"](None)
    document = await doc_repo.create(
        filename="doc.txt",
        original_filename="doc.txt",
        file_path=str(file_path),
        file_size=len("content"),
        file_type="txt",
        checksum="checksum",
    )

    job_repo = repo_stubs["job_factory"](None)
    await job_repo.create(
        job_id=job_id,
        file_name="doc.txt",
        message="queued",
        details={"file_path": str(file_path), "document_id": document["id"]},
    )

    result = await service.process_job(job_id, str(file_path))

    assert result == {"chunks_processed": 2, "status": "completed"}
    record = repo_stubs["jobs"][job_id]
    assert record["status"] == "completed"
    assert record["details"].get("chunks_count") == 2
    assert captured["chunks"] == ["chunk1", "chunk2"]
    stored_document = repo_stubs["documents"][document["id"]]
    assert stored_document["is_processed"] is True
    assert stored_document["chunks_count"] == 2


@pytest.mark.asyncio
async def test_process_job_skipped(monkeypatch, tmp_path, repo_stubs):
    file_path = tmp_path / "raw" / "doc.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("content")

    monkeypatch.setattr(ingestion_module, "process_document", lambda path: [])

    service = IngestionService()
    job_id = "job-skip"
    doc_repo = repo_stubs["document_factory"](None)
    document = await doc_repo.create(
        filename="doc.txt",
        original_filename="doc.txt",
        file_path=str(file_path),
        file_size=len("content"),
        file_type="txt",
        checksum="checksum",
    )
    job_repo = repo_stubs["job_factory"](None)
    await job_repo.create(
        job_id=job_id,
        file_name="doc.txt",
        message="queued",
        details={"file_path": str(file_path), "document_id": document["id"]},
    )

    result = await service.process_job(job_id, str(file_path))

    assert result == {"chunks_processed": 0, "status": "skipped"}
    record = repo_stubs["jobs"][job_id]
    assert record["status"] == "skipped"


@pytest.mark.asyncio
async def test_process_job_failure(monkeypatch, tmp_path, repo_stubs):
    file_path = tmp_path / "raw" / "doc.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("content")

    def raise_error(path):
        raise ValueError("boom")

    monkeypatch.setattr(ingestion_module, "process_document", raise_error)

    service = IngestionService()
    job_id = "job-fail"
    doc_repo = repo_stubs["document_factory"](None)
    document = await doc_repo.create(
        filename="doc.txt",
        original_filename="doc.txt",
        file_path=str(file_path),
        file_size=len("content"),
        file_type="txt",
        checksum="checksum",
    )
    job_repo = repo_stubs["job_factory"](None)
    await job_repo.create(
        job_id=job_id,
        file_name="doc.txt",
        message="queued",
        details={"file_path": str(file_path), "document_id": document["id"]},
    )

    with pytest.raises(ValueError):
        await service.process_job(job_id, str(file_path))

    record = repo_stubs["jobs"][job_id]
    assert record["status"] == "failed"
    assert record["error"] == "boom"
    assert not Path(file_path).exists()


@pytest.mark.asyncio
async def test_schedule_job_processes_and_invokes_callback(monkeypatch, tmp_path, repo_stubs):
    file_path = tmp_path / "raw" / "doc.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("content")

    chunks = ["chunk1"]
    monkeypatch.setattr(ingestion_module, "process_document", lambda path: chunks)
    monkeypatch.setattr(ingestion_module, "build_vector_store", lambda processed: "vectordb")

    service = IngestionService()
    job_id = "job-async"

    doc_repo = repo_stubs["document_factory"](None)
    document = await doc_repo.create(
        filename="doc.txt",
        original_filename="doc.txt",
        file_path=str(file_path),
        file_size=len("content"),
        file_type="txt",
        checksum="checksum",
    )

    job_repo = repo_stubs["job_factory"](None)
    await job_repo.create(
        job_id=job_id,
        file_name="doc.txt",
        message="queued",
        details={"file_path": str(file_path), "document_id": document["id"]},
    )

    callback_event = asyncio.Event()
    callback_payload = {}

    async def on_success(result):
        callback_payload.update(result=result)
        callback_event.set()

    class ImmediateQueue:
        def submit(self, _job_id, coroutine_fn):
            return asyncio.create_task(coroutine_fn())

    service._task_queue = ImmediateQueue()

    task = service.schedule_job(job_id, str(file_path), on_success=on_success)
    await task
    await asyncio.wait_for(callback_event.wait(), timeout=1)

    record = repo_stubs["jobs"][job_id]
    assert record["status"] == "completed"
    assert record["details"].get("chunks_count") == 1
    assert callback_payload["result"]["status"] == "completed"
    stored_document = repo_stubs["documents"][document["id"]]
    assert stored_document["is_processed"] is True
