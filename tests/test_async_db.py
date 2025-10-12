import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text
from src.db.models import Conversation, Document
from src.db.session import get_session

@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    async with get_session() as session:
        await session.execute(text("DELETE FROM conversations"))
        await session.execute(text("DELETE FROM documents"))
        await session.commit()

@pytest.mark.asyncio
async def test_create_conversation():
    async with get_session() as session:
        conversation = Conversation(
            user_id="test_user",
            title="Test Conversation",
            messages="[]",
        )
        session.add(conversation)
        await session.commit()

        result = await session.execute(select(Conversation).where(Conversation.user_id == "test_user"))
        retrieved = result.scalar_one()

        assert retrieved.title == "Test Conversation"
        assert retrieved.messages == "[]"


@pytest.mark.asyncio
async def test_create_document():
    async with get_session() as session:
        document = Document(
            filename="test_file.pdf",
            original_filename="original_file.pdf",
            file_path="/path/to/test_file.pdf",
            file_size=1024,
            file_type="application/pdf",
            checksum="dummychecksum",
        )
        session.add(document)
        await session.commit()

        result = await session.execute(select(Document).where(Document.filename == "test_file.pdf"))
        retrieved = result.scalar_one()

        assert retrieved.original_filename == "original_file.pdf"
        assert retrieved.file_path == "/path/to/test_file.pdf"
