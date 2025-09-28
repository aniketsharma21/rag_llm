"""Async repository for document metadata."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Document
from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger

logger = get_logger(__name__)


def _document_to_dict(instance: Document) -> Dict[str, Any]:
    return {
        "id": instance.id,
        "filename": instance.filename,
        "original_filename": instance.original_filename,
        "file_path": instance.file_path,
        "file_size": instance.file_size,
        "file_type": instance.file_type,
        "checksum": instance.checksum,
        "chunks_count": instance.chunks_count,
        "uploaded_at": instance.uploaded_at.isoformat() if instance.uploaded_at else None,
        "processed_at": instance.processed_at.isoformat() if instance.processed_at else None,
        "is_processed": instance.is_processed,
    }


class DocumentRepository:
    """Handles CRUD operations for documents."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        checksum: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            record = Document(
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                checksum=checksum,
            )
            self._session.add(record)
            await self._session.flush()
            await self._session.refresh(record)
            logger.info("Created document record", document_id=record.id, filename=filename)
            payload = _document_to_dict(record)
            if details:
                payload["details"] = json.loads(json.dumps(details))
            return payload
        except SQLAlchemyError as exc:
            logger.error("Failed to create document record", filename=filename, error=str(exc))
            raise DocumentProcessingError("Failed to create document record", details={"error": str(exc)})

    async def get_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        stmt = select(Document).where(Document.checksum == checksum)
        result = await self._session.scalar(stmt)
        return _document_to_dict(result) if result else None

    async def update_processing(self, document_id: int, *, chunks_count: int) -> bool:
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(chunks_count=chunks_count, is_processed=True)
            .returning(Document)
        )
        result = await self._session.scalar(stmt)
        return result is not None

    async def list(self, *, limit: int = 100) -> List[Dict[str, Any]]:
        stmt = select(Document).order_by(Document.uploaded_at.desc()).limit(limit)
        result = await self._session.scalars(stmt)
        return [_document_to_dict(instance) for instance in result]
