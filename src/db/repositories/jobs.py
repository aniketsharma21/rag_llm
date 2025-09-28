"""Async repository for ingestion job tracking."""
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
    if details is None:
        return None
    return json.dumps(details)


def _deserialize_details(payload: str | None) -> Dict[str, Any]:
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Could not decode job details", payload=payload)
        return {}


def _job_to_dict(instance: IngestJob) -> Dict[str, Any]:
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
    """CRUD access for ingest jobs."""

    def __init__(self, session: AsyncSession):
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
