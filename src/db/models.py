"""SQLAlchemy database models for the RAG LLM application.

This module defines the database schema using SQLAlchemy's declarative base.
It includes models for:
- Conversations: Stores chat history and context
- Documents: Tracks uploaded and processed documents
- IngestJobs: Manages document ingestion processes

All models are designed for async usage with SQLAlchemy 2.0+ and include
timestamps for creation and updates.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models.
    
    Provides common functionality and metadata for all models.
    Automatically handles table naming and inheritance.
    """
    pass


class Conversation(Base):
    """Represents a conversation thread in the application.
    
    Attributes:
        id: Primary key
        user_id: Identifier for the user who owns the conversation
        title: Title or topic of the conversation
        messages: JSON string containing the conversation messages
        created_at: Timestamp when the conversation was created
        updated_at: Timestamp when the conversation was last updated
        is_active: Flag indicating if the conversation is active
    """
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50), index=True, default="default_user")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    messages: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Document(Base):
    """Represents a document that has been uploaded to the system.
    
    Attributes:
        id: Primary key
        filename: System-generated filename (unique)
        original_filename: Original filename from upload
        file_path: Filesystem path to the stored document
        file_size: Size of the file in bytes
        file_type: MIME type of the file
        checksum: SHA-256 checksum for file integrity
        chunks_count: Number of text chunks extracted
        uploaded_at: Timestamp of file upload
        processed_at: Timestamp when processing completed
        is_processed: Flag indicating if processing is complete
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)


class IngestJob(Base):
    """Tracks the status of document ingestion processes.
    
    Attributes:
        job_id: Unique identifier for the ingestion job
        file_name: Name of the file being processed
        status: Current status of the job (queued/processing/completed/failed)
        message: Human-readable status message
        details: Additional processing details
        error: Error message if processing failed
        created_at: Timestamp when the job was created
        updated_at: Timestamp when the job was last updated
    """
    __tablename__ = "ingest_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    message: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
