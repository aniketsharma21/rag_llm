"""Async repository for document metadata management.

This module provides an async repository pattern implementation for managing
document metadata in the database. It handles all CRUD operations for documents,
including tracking document processing status and chunking information.

Key Features:
- Async/await support for non-blocking database operations
- Document metadata management with checksum-based deduplication
- Processing status tracking
- Support for various document types and sizes
"""
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
    """Convert a Document model instance to a dictionary.
    
    Args:
        instance: The Document model instance to convert.
        
    Returns:
        Dict containing the document metadata with proper type conversion.
        
    Note:
        - Converts datetime objects to ISO format strings
        - Handles optional fields gracefully
    """
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
    """Repository for managing document metadata with async database operations.
    
    This class provides methods to perform CRUD operations on document records
    in the database. It handles document metadata, processing status, and
    chunking information for the RAG pipeline.
    
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
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        checksum: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new document metadata record.
        
        Args:
            filename: System-generated filename (unique).
            original_filename: Original filename as uploaded by the user.
            file_path: Filesystem path where the document is stored.
            file_size: Size of the file in bytes.
            file_type: MIME type of the file (e.g., 'application/pdf').
            checksum: SHA-256 checksum of the file content for deduplication.
            details: Optional additional metadata about the document.
            
        Returns:
            Dict containing the created document metadata.
            
        Raises:
            DocumentProcessingError: If there's an error creating the record.
            
        Example:
            ```python
            doc = await repo.create(
                filename="doc_123.pdf",
                original_filename="report.pdf",
                file_path="/uploads/doc_123.pdf",
                file_size=1024,
                file_type="application/pdf",
                checksum="a1b2c3...",
                details={"pages": 5, "author": "User"}
            )
            ```
        """
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
        """Retrieve a document by its content checksum.
        
        Args:
            checksum: The SHA-256 checksum of the document content.
            
        Returns:
            Document metadata as a dictionary if found, None otherwise.
            
        Note:
            This is typically used for deduplication before uploading new documents.
        """
        stmt = select(Document).where(Document.checksum == checksum)
        result = await self._session.scalar(stmt)
        return _document_to_dict(result) if result else None

    async def update_processing(self, document_id: int, *, chunks_count: int) -> bool:
        """Update document processing status after successful chunking.
        
        Args:
            document_id: The ID of the document to update.
            chunks_count: Number of chunks the document was split into.
            
        Returns:
            bool: True if the document was found and updated, False otherwise.
            
        Note:
            This method marks the document as processed and records the number
            of chunks generated during processing.
        """
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(chunks_count=chunks_count, is_processed=True)
            .returning(Document)
        )
        result = await self._session.scalar(stmt)
        return result is not None

    async def list(self, *, limit: int = 100) -> List[Dict[str, Any]]:
        """List all documents in the system.
        
        Args:
            limit: Maximum number of documents to return. Defaults to 100.
            
        Returns:
            List of document dictionaries, ordered by most recently uploaded.
            
        Note:
            The result includes both processed and unprocessed documents.
            Use the 'is_processed' flag to filter if needed.
        """
        stmt = select(Document).order_by(Document.uploaded_at.desc()).limit(limit)
        result = await self._session.scalars(stmt)
        return [_document_to_dict(instance) for instance in result]
