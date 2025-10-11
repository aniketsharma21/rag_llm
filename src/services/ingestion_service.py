"""Service abstractions for document ingestion workflows.

This module provides the IngestionService class which handles the document ingestion
pipeline including file uploads, processing, and vector store updates. It integrates
with the task queue for asynchronous processing and maintains job status tracking.

Key Features:
- Asynchronous file upload and processing
- Job status tracking and management
- Document deduplication via checksums
- Integration with vector store for embeddings
- Background task scheduling and cancellation
"""

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
    """Service for managing document ingestion workflows in the RAG pipeline.
    
    This service handles the end-to-end process of document ingestion including:
    - File upload and validation
    - Background job scheduling
    - Document processing and chunking
    - Vector store updates
    - Job status tracking
    
    Attributes:
        _task_queue: AsyncTaskQueue instance for managing background jobs.
    """

    def __init__(self, task_queue: Optional[AsyncTaskQueue] = None) -> None:
        """Initialize the IngestionService with an optional task queue.
        
        Args:
            task_queue: Optional AsyncTaskQueue instance. If not provided, a new one
                will be created. This allows sharing a task queue across services.
        """
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        self._task_queue = task_queue or AsyncTaskQueue()

    def _cleanup_file(self, file_path: str) -> None:
        """Safely remove a file if it exists.
        
        Args:
            file_path: Path to the file to be removed.
            
        Note:
            This method is safe to call even if the file doesn't exist or has been
            removed already. Any errors during removal are logged but not propagated.
        """
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
        """Process an uploaded file and enqueue it for background processing.
        
        This method performs the following steps:
        1. Reads the uploaded file content
        2. Generates a unique job ID
        3. Saves the file to persistent storage
        4. Creates database records for tracking
        5. Returns the job ID and file path
        
        Args:
            file: FastAPI UploadFile instance containing the uploaded file.
            
        Returns:
            A tuple containing (job_id, file_path) where:
            - job_id: Unique identifier for tracking the ingestion job
            - file_path: Path where the uploaded file was saved
            
        Raises:
            IOError: If there's an error saving the file.
            DatabaseError: If there's an error creating the database records.
        """
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
        """Schedule document processing in the background.
        
        Args:
            job_id: Unique identifier for the job.
            file_path: Path to the file to be processed.
            on_success: Optional async callback to be called when processing completes
                successfully. The callback receives the job result as an argument.
                
        Returns:
            asyncio.Task representing the scheduled job.
            
        Note:
            The task is automatically added to the internal task queue. Any exceptions
            during processing are logged but won't crash the application.
        """

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
        """Attempt to cancel a scheduled ingestion job.
        
        Args:
            job_id: The ID of the job to cancel.
            
        Returns:
            bool: True if the job was found and cancelled, False otherwise.
            
        Note:
            This method can only cancel jobs that have not started processing.
            Already running jobs will complete normally.
        """
        return self._task_queue.cancel(job_id)

    async def process_job(self, job_id: str, file_path: str) -> Dict[str, Optional[int]]:
        """Process an ingestion job by chunking the document and updating the vector store.
        
        This method performs the core document processing workflow:
        1. Updates job status to 'processing'
        2. Processes the document into chunks
        3. Updates the vector store with document chunks
        4. Updates job status to 'completed' or 'failed'
        
        Args:
            job_id: Unique identifier for the job.
            file_path: Path to the file to be processed.
            
        Returns:
            Dictionary containing processing results with keys:
            - chunks_processed: Number of chunks created (0 if skipped)
            - status: One of 'completed', 'skipped', or 'failed'
            
        Raises:
            ValueError: If the job record is not found.
            
        Note:
            This method handles its own error logging and status updates.
            Callers should typically use schedule_job() instead of calling this directly.
        """
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
