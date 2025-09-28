"""Service layer for RAG query orchestration."""
from __future__ import annotations

import asyncio
import os
import pickle
from typing import Any, Dict, List, Optional, Callable, Awaitable, Tuple

import yaml
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

from fastapi import UploadFile

from src.db.repositories import ConversationRepository, JobRepository
from src.db.session import get_session
from src.embed_store import get_retriever, load_vector_store
from src.llm import EnhancedRAGChain, get_llm
from src.logging_config import get_logger
from src.utils.source_formatting import (
    apply_superscript_citations,
    clean_answer_text,
    normalize_source_payload,
    split_answer_into_paragraphs,
)
from src.config import PROCESSED_DATA_DIR, PROMPTS_DIR
from src.exceptions import ConversationError
from src.services.ingestion_service import IngestionService

logger = get_logger(__name__)


class RAGService:
    """Provides higher-level operations for answering queries."""

    def __init__(self) -> None:
        self._enhanced_chain: Optional[EnhancedRAGChain] = None

    def reset_chain(self) -> None:
        self._enhanced_chain = None

    async def create_conversation(self, title: str, user_id: str = "default_user") -> Dict[str, Any]:
        normalized_title = title.strip()
        if not normalized_title:
            raise ConversationError("Title cannot be empty", details={"title": title})
        async with get_session() as session:
            repo = ConversationRepository(session)
            return await repo.create(title=normalized_title, messages=[], user_id=user_id)

    async def list_conversations(
        self,
        user_id: str = "default_user",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        async with get_session() as session:
            repo = ConversationRepository(session)
            return await repo.list(user_id=user_id, limit=limit)

    async def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        async with get_session() as session:
            repo = ConversationRepository(session)
            conversation = await repo.get(conversation_id)
        if not conversation:
            raise ConversationError(
                f"Conversation {conversation_id} not found",
                details={"conversation_id": conversation_id},
            )
        return conversation

    async def append_to_conversation(
        self,
        conversation_id: int,
        *,
        user_message: Dict[str, Any],
        assistant_message: Dict[str, Any],
    ) -> None:
        async with get_session() as session:
            repo = ConversationRepository(session)
            conversation = await repo.get(conversation_id)
            if not conversation:
                raise ConversationError(
                    f"Conversation {conversation_id} not found",
                    details={"conversation_id": conversation_id},
                )

            messages = list(conversation.get("messages") or [])
            messages.append(user_message)
            messages.append(assistant_message)
            await repo.update(conversation_id, messages=messages)

    async def delete_conversation(self, conversation_id: int) -> bool:
        async with get_session() as session:
            repo = ConversationRepository(session)
            return await repo.delete(conversation_id)

    def get_enhanced_chain(self) -> Optional[EnhancedRAGChain]:
        """Return a cached enhanced chain, creating it on demand."""
        if self._enhanced_chain is not None:
            return self._enhanced_chain

        try:
            vectordb = load_vector_store()
            if not vectordb:
                logger.warning("Vector store not found, cannot create enhanced RAG chain")
                return None

            documents: List[Any] = []
            if os.path.exists(PROCESSED_DATA_DIR):
                for filename in os.listdir(PROCESSED_DATA_DIR):
                    if filename.endswith("_chunks.pkl"):
                        chunk_path = os.path.join(PROCESSED_DATA_DIR, filename)
                        try:
                            with open(chunk_path, "rb") as handle:
                                chunks = pickle.load(handle)
                            documents.extend(chunks)
                        except Exception as exc:  # pylint: disable=broad-except
                            logger.warning(
                                "Failed to load chunks",
                                chunk_file=filename,
                                error=str(exc),
                            )

            if not documents:
                logger.warning("No documents found for enhanced RAG chain")
                return None

            self._enhanced_chain = EnhancedRAGChain(vectordb, documents)
            logger.info("Created enhanced RAG chain", documents=len(documents))
            return self._enhanced_chain
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to create enhanced RAG chain", error=str(exc))
            return None

    async def generate_response(
        self,
        *,
        question: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[int] = None,
        on_messages_committed: Optional[Callable[[Dict[str, Any]], Awaitable[None] | None]] = None,
    ) -> Dict[str, Any]:
        """Generate an answer for a question, using enhanced chain when possible."""
        history = chat_history or []
        chain = self.get_enhanced_chain()
        if chain:
            result = self._run_enhanced_chain(chain, question, history)
        else:
            logger.warning("Enhanced RAG chain unavailable, falling back to legacy pipeline")
            result = await self._run_fallback_pipeline(question)

        if conversation_id is not None:
            try:
                await self._persist_conversation_update(
                    conversation_id,
                    question=question,
                    answer=result["answer"],
                    sources=result.get("sources", []),
                )
            except ConversationError as exc:
                logger.warning(
                    "Failed to persist conversation update",
                    conversation_id=conversation_id,
                    error=str(exc),
                )
            else:
                if on_messages_committed is not None:
                    maybe_future = on_messages_committed(result)
                    if asyncio.iscoroutine(maybe_future):
                        await maybe_future

        return result

    def _run_enhanced_chain(
        self,
        chain: EnhancedRAGChain,
        question: str,
        chat_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        result = chain.query(
            question=question,
            template_type=None,
            k=5,
            include_sources=True,
            chat_history=chat_history,
        )

        confidence = result.get("confidence_score")
        raw_sources = result.get("sources", [])
        formatted_sources = [
            normalize_source_payload(source, idx + 1, confidence)
            for idx, source in enumerate(raw_sources)
        ]

        answer = apply_superscript_citations(result.get("answer", ""), formatted_sources)
        answer = clean_answer_text(answer)

        return {
            "answer": answer,
            "sources": formatted_sources,
            "confidence_score": confidence,
            "template_used": result.get("template_used"),
            "num_sources": result.get("num_sources"),
            "paragraphs": split_answer_into_paragraphs(answer),
            "mode": "enhanced",
        }

    async def _run_fallback_pipeline(self, question: str) -> Dict[str, Any]:
        llm = get_llm()
        vectordb = load_vector_store()
        if not vectordb:
            raise RuntimeError("Vector store not found. Please upload and ingest a document first.")

        retriever = get_retriever(vectordb)
        if not retriever:
            raise RuntimeError("Retriever could not be created.")

        prompt_path = os.path.join(PROMPTS_DIR, "rag_prompts.yaml")
        with open(prompt_path, "r", encoding="utf-8") as handle:
            prompt_config = yaml.safe_load(handle)

        template = prompt_config["template"]
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])

        async def get_context(x: Dict[str, Any]) -> str:
            docs = await retriever.ainvoke(x["question"])
            context = "\n\n".join(
                f"[Source: {getattr(doc, 'metadata', {}).get('source', 'unknown')}] {doc.page_content}"
                for doc in docs
            )
            x["_retrieved_docs"] = docs
            return context

        rag_chain = (
            {"context": get_context, "question": lambda x: x["question"]}
            | prompt
            | llm
            | StrOutputParser()
        )

        input_obj: Dict[str, Any] = {"question": question}
        answer = await rag_chain.ainvoke(input_obj)

        docs = input_obj.get("_retrieved_docs", [])
        formatted_sources = [
            normalize_source_payload(
                {
                    "id": idx + 1,
                    "content": getattr(doc, "page_content", ""),
                    "metadata": getattr(doc, "metadata", {}),
                },
                idx + 1,
            )
            for idx, doc in enumerate(docs)
        ]

        answer = apply_superscript_citations(answer, formatted_sources)
        answer = clean_answer_text(answer)

        return {
            "answer": answer,
            "sources": formatted_sources,
            "confidence_score": None,
            "template_used": "fallback",
            "num_sources": len(formatted_sources),
            "paragraphs": split_answer_into_paragraphs(answer),
            "mode": "fallback",
        }

    async def _persist_conversation_update(
        self,
        conversation_id: int,
        *,
        question: str,
        answer: str,
        sources: List[Dict[str, Any]],
    ) -> None:
        user_message = {"role": "user", "content": question}
        assistant_message = {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
        await self.append_to_conversation(
            conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )


class RAGApplicationService:
    """High-level façade coordinating ingestion and query workflows."""

    def __init__(
        self,
        ingestion_service: IngestionService,
        rag_service: RAGService,
    ) -> None:
        self._ingestion_service = ingestion_service
        self._rag_service = rag_service

    async def ingest_document(self, file: UploadFile) -> Tuple[str, str]:
        """Persist upload, enqueue job, and return (job_id, stored_path)."""
        job_id, file_path = await self._ingestion_service.enqueue_upload(file)
        self._ingestion_service.schedule_job(
            job_id,
            file_path,
            on_success=lambda _: self._rag_service.reset_chain(),
        )
        return job_id, file_path

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        async with get_session() as session:
            repo = JobRepository(session)
            return await repo.get(job_id)

    async def query(
        self,
        *,
        question: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self._rag_service.generate_response(
            question=question,
            chat_history=chat_history,
            conversation_id=conversation_id,
        )

    async def create_conversation(self, title: str, user_id: str = "default_user") -> Dict[str, Any]:
        return await self._rag_service.create_conversation(title, user_id)

    async def list_conversations(self, user_id: str = "default_user", limit: int = 50) -> List[Dict[str, Any]]:
        return await self._rag_service.list_conversations(user_id=user_id, limit=limit)

    async def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        return await self._rag_service.get_conversation(conversation_id)

    async def delete_conversation(self, conversation_id: int) -> bool:
        return await self._rag_service.delete_conversation(conversation_id)
