"""Async repository for conversation persistence.

This module provides an async repository pattern implementation for managing
conversation data in the database. It handles all CRUD operations for conversations,
including creating, reading, updating, and soft-deleting conversation records.

Key Features:
- Async/await support for non-blocking database operations
- JSON serialization/deserialization of message history
- Soft delete functionality
- User-specific conversation isolation
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Conversation
from src.exceptions import ConversationError
from src.logging_config import get_logger

logger = get_logger(__name__)


def _conversation_to_dict(instance: Conversation) -> Dict[str, Any]:
    """Convert a Conversation model instance to a dictionary.
    
    Args:
        instance: The Conversation model instance to convert.
        
    Returns:
        Dict containing the conversation data with proper type conversion.
        
    Note:
        - Converts datetime objects to ISO format strings
        - Parses the messages JSON string into a Python list
    """
    return {
        "id": instance.id,
        "user_id": instance.user_id,
        "title": instance.title,
        "messages": json.loads(instance.messages) if instance.messages else [],
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
        "is_active": instance.is_active,
    }


class ConversationRepository:
    """Repository for managing conversation data with async database operations.
    
    This class provides methods to perform CRUD operations on conversation records
    in the database. It handles serialization/deserialization of message history
    and implements soft delete functionality.
    
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
        title: str,
        messages: List[Dict[str, Any]],
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
        """Create a new conversation record.
        
        Args:
            title: The title of the conversation.
            messages: List of message dictionaries to store in the conversation.
            user_id: ID of the user who owns the conversation. Defaults to "default_user".
            
        Returns:
            Dict containing the created conversation data.
            
        Raises:
            ConversationError: If there's an error creating the conversation.
            
        Example:
            ```python
            conversation = await repo.create(
                title="Technical Support",
                messages=[{"role": "user", "content": "Hello"}],
                user_id="user123"
            )
            ```
        """
        try:
            record = Conversation(
                user_id=user_id,
                title=title,
                messages=json.dumps(messages),
            )
            self._session.add(record)
            await self._session.flush()
            await self._session.refresh(record)
            logger.info("Created conversation", conversation_id=record.id, title=title)
            return _conversation_to_dict(record)
        except SQLAlchemyError as exc:
            logger.error("Failed to create conversation", error=str(exc))
            raise ConversationError(f"Failed to create conversation: {exc}")

    async def get(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a conversation by its ID.
        
        Args:
            conversation_id: The ID of the conversation to retrieve.
            
        Returns:
            The conversation data as a dictionary if found, None otherwise.
            Only returns active conversations (is_active=True).
        """
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.is_active.is_(True))
        )
        result = await self._session.scalar(stmt)
        if result is None:
            return None
        return _conversation_to_dict(result)

    async def update(
        self,
        conversation_id: int,
        *,
        messages: List[Dict[str, Any]],
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing conversation.
        
        Args:
            conversation_id: The ID of the conversation to update.
            messages: New list of message dictionaries to store.
            title: Optional new title for the conversation.
            
        Returns:
            Dict containing the updated conversation data.
            
        Raises:
            ConversationError: If the conversation is not found.
            
        Note:
            Only updates active conversations (is_active=True).
            Automatically updates the updated_at timestamp.
        """
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.is_active.is_(True))
            .values(messages=json.dumps(messages))
            .returning(Conversation)
        )
        if title is not None:
            stmt = stmt.values(title=title)

        result = await self._session.scalar(stmt)
        if result is None:
            raise ConversationError(f"Conversation {conversation_id} not found")
        logger.info("Updated conversation", conversation_id=conversation_id)
        return _conversation_to_dict(result)

    async def list(
        self,
        *,
        user_id: str = "default_user",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List conversations for a specific user.
        
        Args:
            user_id: ID of the user whose conversations to list. Defaults to "default_user".
            limit: Maximum number of conversations to return. Defaults to 50.
            
        Returns:
            List of conversation dictionaries, ordered by most recently updated.
            Only includes active conversations (is_active=True).
        """
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_active.is_(True))
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.scalars(stmt)
        conversations = [_conversation_to_dict(instance) for instance in result]
        logger.info("Listed conversations", user_id=user_id, count=len(conversations))
        return conversations

    async def delete(self, conversation_id: int) -> bool:
        """Soft delete a conversation.
        
        Args:
            conversation_id: The ID of the conversation to delete.
            
        Returns:
            bool: True if the conversation was found and marked as inactive,
            False if no matching conversation was found.
            
        Note:
            This is a soft delete - it sets is_active=False rather than
            removing the record from the database.
        """
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(is_active=False)
            .returning(Conversation.id)
        )
        result = await self._session.scalar(stmt)
        deleted = result is not None
        if deleted:
            logger.info("Deleted conversation", conversation_id=conversation_id)
        return deleted
