"""
database.py

Database models and connection management for conversation persistence.
Uses SQLAlchemy with SQLite for local development and easy deployment.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from src.config import BASE_DIR
from src.logging_config import get_logger
from src.exceptions import ConversationError

logger = get_logger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'conversations.db')}")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Conversation(Base):
    """Database model for storing conversations."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), index=True, default="default_user")
    title = Column(String(200), nullable=False)
    messages = Column(Text, nullable=False)  # JSON string of messages
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "messages": json.loads(self.messages) if self.messages else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


class Document(Base):
    """Database model for tracking uploaded documents."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    checksum = Column(String(64), nullable=False, index=True)
    chunks_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    is_processed = Column(Boolean, default=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "checksum": self.checksum,
            "chunks_count": self.chunks_count,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "is_processed": self.is_processed
        }


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise ConversationError(f"Database initialization failed: {str(e)}")


@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        session.close()


class ConversationManager:
    """Manager class for conversation database operations."""
    
    @staticmethod
    def create_conversation(
        title: str, 
        messages: List[Dict[str, Any]], 
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            title: Conversation title
            messages: List of message dictionaries
            user_id: User identifier
            
        Returns:
            Created conversation dictionary
        """
        try:
            with get_db_session() as session:
                conversation = Conversation(
                    user_id=user_id,
                    title=title,
                    messages=json.dumps(messages)
                )
                session.add(conversation)
                session.flush()  # Get the ID
                
                result = conversation.to_dict()
                logger.info("Created conversation", conversation_id=conversation.id, title=title)
                return result
                
        except Exception as e:
            logger.error("Failed to create conversation", error=str(e))
            raise ConversationError(f"Failed to create conversation: {str(e)}")
    
    @staticmethod
    def get_conversation(conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation dictionary or None if not found
        """
        try:
            with get_db_session() as session:
                conversation = session.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.is_active == True
                ).first()
                
                if conversation:
                    return conversation.to_dict()
                return None
                
        except Exception as e:
            logger.error("Failed to get conversation", conversation_id=conversation_id, error=str(e))
            raise ConversationError(f"Failed to get conversation: {str(e)}")
    
    @staticmethod
    def update_conversation(
        conversation_id: int, 
        messages: List[Dict[str, Any]], 
        title: str = None
    ) -> Dict[str, Any]:
        """
        Update an existing conversation.
        
        Args:
            conversation_id: Conversation ID
            messages: Updated list of messages
            title: Optional new title
            
        Returns:
            Updated conversation dictionary
        """
        try:
            with get_db_session() as session:
                conversation = session.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.is_active == True
                ).first()
                
                if not conversation:
                    raise ConversationError(f"Conversation {conversation_id} not found")
                
                conversation.messages = json.dumps(messages)
                if title:
                    conversation.title = title
                conversation.updated_at = datetime.utcnow()
                
                result = conversation.to_dict()
                logger.info("Updated conversation", conversation_id=conversation_id)
                return result
                
        except Exception as e:
            logger.error("Failed to update conversation", conversation_id=conversation_id, error=str(e))
            raise ConversationError(f"Failed to update conversation: {str(e)}")
    
    @staticmethod
    def list_conversations(user_id: str = "default_user", limit: int = 50) -> List[Dict[str, Any]]:
        """
        List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dictionaries
        """
        try:
            with get_db_session() as session:
                conversations = session.query(Conversation).filter(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True
                ).order_by(Conversation.updated_at.desc()).limit(limit).all()
                
                result = [conv.to_dict() for conv in conversations]
                logger.info("Listed conversations", user_id=user_id, count=len(result))
                return result
                
        except Exception as e:
            logger.error("Failed to list conversations", user_id=user_id, error=str(e))
            raise ConversationError(f"Failed to list conversations: {str(e)}")
    
    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """
        Soft delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted successfully
        """
        try:
            with get_db_session() as session:
                conversation = session.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if not conversation:
                    return False
                
                conversation.is_active = False
                conversation.updated_at = datetime.utcnow()
                
                logger.info("Deleted conversation", conversation_id=conversation_id)
                return True
                
        except Exception as e:
            logger.error("Failed to delete conversation", conversation_id=conversation_id, error=str(e))
            raise ConversationError(f"Failed to delete conversation: {str(e)}")


class DocumentManager:
    """Manager class for document database operations."""
    
    @staticmethod
    def create_document(
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        checksum: str
    ) -> Dict[str, Any]:
        """Create a new document record."""
        try:
            with get_db_session() as session:
                document = Document(
                    filename=filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=file_type,
                    checksum=checksum
                )
                session.add(document)
                session.flush()
                
                result = document.to_dict()
                logger.info("Created document record", document_id=document.id, filename=filename)
                return result
                
        except Exception as e:
            logger.error("Failed to create document record", filename=filename, error=str(e))
            raise ConversationError(f"Failed to create document record: {str(e)}")
    
    @staticmethod
    def get_document_by_checksum(checksum: str) -> Optional[Dict[str, Any]]:
        """Get document by checksum."""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter(
                    Document.checksum == checksum
                ).first()
                
                return document.to_dict() if document else None
                
        except Exception as e:
            logger.error("Failed to get document by checksum", checksum=checksum, error=str(e))
            return None
    
    @staticmethod
    def update_document_processing(document_id: int, chunks_count: int) -> bool:
        """Update document processing status."""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter(
                    Document.id == document_id
                ).first()
                
                if document:
                    document.chunks_count = chunks_count
                    document.processed_at = datetime.utcnow()
                    document.is_processed = True
                    return True
                return False
                
        except Exception as e:
            logger.error("Failed to update document processing", document_id=document_id, error=str(e))
            return False
    
    @staticmethod
    def list_documents(limit: int = 100) -> List[Dict[str, Any]]:
        """List all documents."""
        try:
            with get_db_session() as session:
                documents = session.query(Document).order_by(
                    Document.uploaded_at.desc()
                ).limit(limit).all()
                
                return [doc.to_dict() for doc in documents]
                
        except Exception as e:
            logger.error("Failed to list documents", error=str(e))
            return []


# Initialize database on import
try:
    create_tables()
except Exception as e:
    logger.warning("Database initialization failed", error=str(e))
