"""Job management utilities for tracking asynchronous ingestion tasks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, Any, Optional


class JobNotFoundError(Exception):
    """Raised when a job identifier cannot be located."""


@dataclass
class JobRecord:
    job_id: str
    file_name: str
    status: str = "queued"
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "file_name": self.file_name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class JobManager:
    """Thread-safe in-memory job registry."""

    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = Lock()

    def create_job(self, job_id: str, file_name: str, message: Optional[str] = None) -> JobRecord:
        record = JobRecord(job_id=job_id, file_name=file_name, message=message)
        with self._lock:
            self._jobs[job_id] = record
        return record

    def get_job(self, job_id: str) -> JobRecord:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                raise JobNotFoundError(job_id)
            return record

    def update_job(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> JobRecord:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                raise JobNotFoundError(job_id)

            if status is not None:
                record.status = status
            if message is not None:
                record.message = message
            if details:
                record.details.update(details)
            if error is not None:
                record.error = error

            record.updated_at = datetime.utcnow()
            return record


job_manager = JobManager()
