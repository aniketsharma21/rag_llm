"""Async repository for conversation persistence."""
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
    """Encapsulates async CRUD operations for conversations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        title: str,
        messages: List[Dict[str, Any]],
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
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
