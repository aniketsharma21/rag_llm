"""Service abstractions for document ingestion workflows."""
from __future__ import annotations

import asyncio
import hashlib
import os
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from fastapi import UploadFile

from src.config import RAW_DATA_DIR
from src.db.repositories import DocumentRepository, JobRepository
from src.db.session import get_session
from src.embed_store import build_vector_store
from src.ingest import process_document
from src.logging_config import get_logger
from src.services.task_queue import AsyncTaskQueue

logger = get_logger(__name__)


class IngestionService:
    """Encapsulates document ingestion logic for reuse across transports."""

    def __init__(self, task_queue: Optional[AsyncTaskQueue] = None) -> None:
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        self._task_queue = task_queue or AsyncTaskQueue()

    def _cleanup_file(self, file_path: str) -> None:
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Removed staged upload", file_path=file_path)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                "Failed to remove staged upload",
                file_path=file_path,
                error=str(exc),
            )

    async def enqueue_upload(self, file: UploadFile) -> Tuple[str, str]:
        """Persist the upload and register a background job."""
        payload = await file.read()

        job_id = str(uuid.uuid4())
        original_name = file.filename or "document"
        safe_filename = self._sanitize_filename(original_name)
        permanent_file_path = self._persist_payload(safe_filename, payload)

        checksum = hashlib.sha256(payload).hexdigest()
        file_ext = os.path.splitext(safe_filename)[1].lstrip(".").lower() or "unknown"

        async with get_session() as session:
            job_repo = JobRepository(session)
            document_repo = DocumentRepository(session)

            document_record = await document_repo.create(
                filename=os.path.basename(permanent_file_path),
                original_filename=original_name,
                file_path=permanent_file_path,
                file_size=len(payload),
                file_type=file_ext,
                checksum=checksum,
            )

            job_details = {
                "file_path": permanent_file_path,
                "document_id": document_record["id"],
                "checksum": document_record["checksum"],
            }

            await job_repo.create(
                job_id=job_id,
                file_name=original_name,
                status="queued",
                message="Upload received",
                details=job_details,
            )

        logger.info("Saved uploaded file", file_path=permanent_file_path, job_id=job_id)
        return job_id, permanent_file_path

    def schedule_job(
        self,
        job_id: str,
        file_path: str,
        *,
        on_success: Optional[Callable[[Dict[str, Any]], Awaitable[None] | None]] = None,
    ) -> asyncio.Task[None]:
        """Schedule processing on the internal task queue."""

        async def _runner() -> None:
            try:
                result = await self.process_job(job_id, file_path)
                if result.get("status") == "completed" and on_success is not None:
                    maybe_awaitable = on_success(result)
                    if asyncio.iscoroutine(maybe_awaitable):
                        await maybe_awaitable  # pragma: no cover - callback behaviour
            except Exception as exc:  # pragma: no cover - log at caller
                logger.error(
                    "Scheduled ingest job failed",
                    job_id=job_id,
                    file_path=file_path,
                    error=str(exc),
                    exc_info=True,
                )

        return self._task_queue.submit(job_id, _runner)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled ingestion job if it has not completed."""
        return self._task_queue.cancel(job_id)

    async def process_job(self, job_id: str, file_path: str) -> Dict[str, Optional[int]]:
        """Process a queued ingestion job and update status records."""
        details: Dict[str, Any] = {}
        try:
            async with get_session() as session:
                job_repo = JobRepository(session)
                job_record = await job_repo.get(job_id)
                if job_record is None:
                    raise ValueError(f"Ingest job {job_id} not found")

                details = dict(job_record.get("details") or {})
                details["file_path"] = file_path

                await job_repo.update(
                    job_id,
                    status="processing",
                    message="Chunking document",
                    details=details,
                )

            chunks = await asyncio.to_thread(process_document, file_path)

            if not chunks:
                async with get_session() as session:
                    job_repo = JobRepository(session)
                    details["chunks_count"] = 0
                    await job_repo.update(
                        job_id,
                        status="skipped",
                        message="Document unchanged; using cached chunks",
                        details=details,
                    )
                logger.info("Ingest job skipped", job_id=job_id, file_path=file_path)
                self._cleanup_file(file_path)
                return {"chunks_processed": 0, "status": "skipped"}

            details["chunks_count"] = len(chunks)

            await asyncio.to_thread(build_vector_store, chunks)

            async with get_session() as session:
                job_repo = JobRepository(session)
                document_repo = DocumentRepository(session)

                await job_repo.update(
                    job_id,
                    status="completed",
                    message="Document processed successfully",
                    details=details,
                )

                document_id = details.get("document_id")
                if document_id is not None:
                    await document_repo.update_processing(int(document_id), chunks_count=len(chunks))

            logger.info(
                "Ingest job completed",
                job_id=job_id,
                file_path=file_path,
                chunks=len(chunks),
            )
            return {"chunks_processed": len(chunks), "status": "completed"}

        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Ingest job failed", job_id=job_id, file_path=file_path, error=str(exc))
            try:
                async with get_session() as session:
                    job_repo = JobRepository(session)
                    await job_repo.update(
                        job_id,
                        status="failed",
                        message="Document processing failed",
                        error=str(exc),
                        details=details or {"file_path": file_path},
                    )
            except Exception as update_exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Failed to persist job failure",
                    job_id=job_id,
                    error=str(update_exc),
                )

            self._cleanup_file(file_path)

            raise

    def _persist_payload(self, filename: str, payload: bytes) -> str:
        file_extension = os.path.splitext(filename)[1]
        safe_filename = filename.replace("..", "")
        permanent_file_path = os.path.join(RAW_DATA_DIR, safe_filename)

        counter = 1
        while os.path.exists(permanent_file_path):
            name_without_ext = os.path.splitext(safe_filename)[0]
            permanent_file_path = os.path.join(
                RAW_DATA_DIR, f"{name_without_ext}_{counter}{file_extension}"
            )
            counter += 1

        with open(permanent_file_path, "wb") as destination:
            destination.write(payload)

        return permanent_file_path

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        return filename.replace(" ", "_").replace("..", "")
