"""Async repository for ingestion job tracking and management.

This module provides an async repository pattern implementation for managing
ingestion job records in the database. It handles tracking the status and
progress of document ingestion jobs in the RAG pipeline.

Key Features:
- Async/await support for non-blocking database operations
- Job status tracking with detailed progress information
- Error handling and retry support
- Structured logging for job lifecycle events
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import IngestJob
from src.logging_config import get_logger

logger = get_logger(__name__)


def _serialize_details(details: Dict[str, Any] | None) -> str | None:
    """Serialize job details dictionary to a JSON string.
    
    Args:
        details: Dictionary containing job details to be serialized.
        
    Returns:
        JSON-encoded string of the details, or None if input is None.
    """
    if details is None:
        return None
    return json.dumps(details)


def _deserialize_details(payload: str | None) -> Dict[str, Any]:
    """Deserialize job details from a JSON string to a dictionary.
    
    Args:
        payload: JSON-encoded string to deserialize.
        
    Returns:
        Dictionary containing the deserialized details, or an empty dict
        if payload is None or invalid JSON.
        
    Note:
        Logs a warning if the payload cannot be deserialized.
    """
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Could not decode job details", payload=payload)
        return {}


def _job_to_dict(instance: IngestJob) -> Dict[str, Any]:
    """Convert an IngestJob model instance to a dictionary.
    
    Args:
        instance: The IngestJob model instance to convert.
        
    Returns:
        Dictionary containing the job data with proper type conversion.
        
    Note:
        - Handles serialization of datetime objects
        - Converts JSON details string back to a dictionary
    """
    return {
        "job_id": instance.job_id,
        "file_name": instance.file_name,
        "status": instance.status,
        "message": instance.message,
        "details": _deserialize_details(instance.details),
        "error": instance.error,
        "created_at": instance.created_at,
        "updated_at": instance.updated_at,
    }


class JobRepository:
    """Repository for managing ingestion job records with async database operations.
    
    This class provides methods to perform CRUD operations on job records
    in the database. It handles tracking the status and progress of document
    ingestion jobs in the RAG pipeline.
    
    Attributes:
        _session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.
        
        Args:
            session: Async SQLAlchemy session for database operations.
        """
        self._session = session

    async def create(
        self,
        *,
        job_id: str,
        file_name: str,
        status: str = "queued",
        message: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Create a new ingestion job record.
        
        Args:
            job_id: Unique identifier for the job.
            file_name: Name of the file being processed.
            status: Initial status of the job. Defaults to "queued".
            message: Optional status message.
            details: Optional dictionary with additional job details.
            
        Returns:
            Dictionary containing the created job data.
            
        Raises:
            SQLAlchemyError: If there's an error creating the record.
            
        Example:
            ```python
            job = await repo.create(
                job_id="job_123",
                file_name="document.pdf",
                status="processing",
                message="Starting document processing",
                details={"pages": 10, "size_kb": 1024}
            )
            ```
        """
        record = IngestJob(
            job_id=job_id,
            file_name=file_name,
            status=status,
            message=message,
            details=_serialize_details(details),
        )
        self._session.add(record)
        try:
            await self._session.flush()
            await self._session.refresh(record)
            logger.info("Created ingest job", job_id=job_id, status=status)
            return _job_to_dict(record)
        except SQLAlchemyError as exc:
            logger.error("Failed to create job", job_id=job_id, error=str(exc))
            raise

    async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by its ID.
        
        Args:
            job_id: The unique identifier of the job to retrieve.
            
        Returns:
            Dictionary containing the job data if found, None otherwise.
            
        Note:
            The returned dictionary includes deserialized details and timestamps.
        """
        stmt = select(IngestJob).where(IngestJob.job_id == job_id)
        result = await self._session.scalar(stmt)
        return _job_to_dict(result) if result else None

    async def update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        message: str | None = None,
        details: Dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing job record.
        
        Args:
            job_id: The ID of the job to update.
            status: New status for the job.
            message: New status message.
            details: Additional details to merge with existing details.
            error: Error message if the job failed.
            
        Returns:
            Dictionary containing the updated job data if found, None otherwise.
            
        Note:
            - Only updates the fields that are not None.
            - Automatically updates the 'updated_at' timestamp.
            - If no updates are provided, returns the current job data.
        """
        values: Dict[str, Any] = {}
        if status is not None:
            values["status"] = status
        if message is not None:
            values["message"] = message
        if details is not None:
            values["details"] = _serialize_details(details)
        if error is not None:
            values["error"] = error

        if not values:
            logger.debug("No updates provided for job", job_id=job_id)
            return await self.get(job_id)

        stmt = update(IngestJob).where(IngestJob.job_id == job_id).values(**values).returning(IngestJob)
        result = await self._session.scalar(stmt)
        return _job_to_dict(result) if result else None
