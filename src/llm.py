"""Enhanced LLM and RAG orchestration utilities."""

from __future__ import annotations

import os
import re
import time
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote

from groq import Groq
from langchain.schema import Document
from langchain_groq import ChatGroq

try:  # Optional dependency
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional provider
    ChatOpenAI = None

from src.config import (
    GROQ_API_KEY,
    OPENAI_API_KEY,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_REQUEST_TIMEOUT,
    LLM_TEMPERATURE,
    RETRIEVER_KEYWORD_WEIGHT,
    RETRIEVER_K,
    RETRIEVER_SEMANTIC_WEIGHT,
)
from src.exceptions import ConfigurationError, LLMError
from src.logging_config import get_logger
from src.middleware.observability import (
    increment_rag_error,
    observe_rag_generation,
    observe_rag_retrieval,
)
from src.prompt_templates import get_enhanced_prompt, prompt_manager
from src.retrieval import AdvancedRetriever, HybridRetriever
from src.utils.source_formatting import (
    normalize_source_payload,
    replace_bracket_citations,
)


logger = get_logger(__name__)


class LLMProviderRegistry:
    """Registry for managing LLM provider factories and health checks."""

    def __init__(self) -> None:
        self._factories: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._health_checks: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._cache: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], Any] = {}
        self._lock = Lock()

    def register(
        self,
        name: str,
        *,
        factory: Callable[[Dict[str, Any]], Any],
        health_check: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self._factories[name.lower()] = factory
        if health_check:
            self._health_checks[name.lower()] = health_check

    def create(self, name: str, options: Dict[str, Any]) -> Any:
        clean_options = tuple(sorted((key, value) for key, value in options.items() if value is not None))
        key = (name.lower(), clean_options)
        with self._lock:
            cached = self._cache.get(key)
            if cached:
                return cached

        factory = self._factories.get(name.lower())
        if not factory:
            raise ConfigurationError(
                f"Unsupported LLM provider '{name}'.",
                {"provider": name, "available_providers": list(self._factories)},
            )

        try:
            instance = factory(options)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to create LLM instance", provider=name, error=str(exc))
            raise LLMError(
                f"Failed to create LLM instance: {exc}",
                {"provider": name, "options": options},
            ) from exc

        with self._lock:
            self._cache[key] = instance
        return instance

    def run_health_check(self, name: str, options: Dict[str, Any]) -> None:
        health_check = self._health_checks.get(name.lower())
        if not health_check:
            return
        health_check(options)


registry = LLMProviderRegistry()


def _create_groq_llm(options: Dict[str, Any]) -> ChatGroq:
    api_key = options.get("api_key") or GROQ_API_KEY
    if not api_key:
        raise ConfigurationError("GROQ_API_KEY not found.", {"provider": "groq"})
    params = {
        "api_key": api_key,
        "model": options.get("model", LLM_MODEL),
        "temperature": options.get("temperature", LLM_TEMPERATURE),
        "max_tokens": options.get("max_output_tokens", LLM_MAX_OUTPUT_TOKENS),
        "max_retries": options.get("max_retries", LLM_MAX_RETRIES),
    }
    timeout = options.get("request_timeout")
    if timeout:
        params["request_timeout"] = timeout
    return ChatGroq(**params)


def _groq_health_check(options: Dict[str, Any]) -> None:
    api_key = options.get("api_key") or GROQ_API_KEY
    if not api_key:
        raise ConfigurationError("GROQ_API_KEY not found.", {"provider": "groq"})
    client = Groq(api_key=api_key)
    try:
        client.models.list()
    except Exception as exc:  # pragma: no cover - depends on network
        logger.error("Groq health check failed", error=str(exc))
        raise LLMError("Groq health check failed", {"error": str(exc)}) from exc


def _create_openai_llm(options: Dict[str, Any]):  # pragma: no cover - optional dependency
    if ChatOpenAI is None:
        raise ConfigurationError(
            "OpenAI provider requested but langchain-openai is not installed.",
            {"provider": "openai"},
        )
    api_key = options.get("api_key") or OPENAI_API_KEY
    if not api_key:
        raise ConfigurationError("OPENAI_API_KEY not found.", {"provider": "openai"})
    return ChatOpenAI(
        api_key=api_key,
        model=options.get("model", LLM_MODEL),
        temperature=options.get("temperature", LLM_TEMPERATURE),
        max_tokens=options.get("max_output_tokens", LLM_MAX_OUTPUT_TOKENS),
        max_retries=options.get("max_retries", LLM_MAX_RETRIES),
        timeout=options.get("request_timeout") or LLM_REQUEST_TIMEOUT,
    )


def _openai_health_check(options: Dict[str, Any]) -> None:  # pragma: no cover
    if ChatOpenAI is None:
        raise ConfigurationError(
            "OpenAI provider requested but langchain-openai is not installed.",
            {"provider": "openai"},
        )
    api_key = options.get("api_key") or OPENAI_API_KEY
    if not api_key:
        raise ConfigurationError("OPENAI_API_KEY not found.", {"provider": "openai"})
    client = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo")
    client.invoke("ping")


registry.register("groq", factory=_create_groq_llm, health_check=_groq_health_check)
registry.register("openai", factory=_create_openai_llm, health_check=_openai_health_check)


def get_llm(
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    request_timeout: Optional[int] = None,
    api_key: Optional[str] = None,
    max_retries: Optional[int] = None,
) -> Any:
    """Return a configured LLM instance using the registry and caching."""

    options = {
        "model": model or LLM_MODEL,
        "temperature": temperature if temperature is not None else LLM_TEMPERATURE,
        "max_output_tokens": max_output_tokens or LLM_MAX_OUTPUT_TOKENS,
    }
    if api_key:
        options["api_key"] = api_key
    timeout = request_timeout if request_timeout is not None else LLM_REQUEST_TIMEOUT
    if timeout:
        options["request_timeout"] = timeout
    retries = max_retries if max_retries is not None else LLM_MAX_RETRIES
    if retries is not None:
        options["max_retries"] = retries

    selected_provider = (provider or LLM_PROVIDER).lower()
    logger.debug(
        "Creating LLM instance",
        provider=selected_provider,
        model=options["model"],
        temperature=options["temperature"],
    )
    return registry.create(selected_provider, options)


def run_llm_health_check() -> None:
    """Validate configured LLM provider credentials at startup."""

    options = {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_output_tokens": LLM_MAX_OUTPUT_TOKENS,
    }
    registry.run_health_check(LLM_PROVIDER, options)


class EnhancedRAGChain:
    """
    Enhanced RAG chain with hybrid retrieval, source attribution, and advanced prompting.
    """
    
    def __init__(
        self,
        vector_store,
        documents: List[Document],
        *,
        retriever_semantic_weight: float = RETRIEVER_SEMANTIC_WEIGHT,
        retriever_keyword_weight: float = RETRIEVER_KEYWORD_WEIGHT,
        retriever_k: int = RETRIEVER_K,
    ):
        """
        Initialize the enhanced RAG chain.
        
        Args:
            vector_store: ChromaDB vector store instance
            documents: List of processed documents for BM25 retrieval
        """
        self.llm_provider = LLM_PROVIDER
        self.llm_model = LLM_MODEL
        self.vector_store = vector_store
        self.documents = documents
        self.conversation_history: List[Dict[str, Any]] = []

        # Initialize hybrid retriever
        try:
            self.retriever = HybridRetriever(
                vector_store,
                documents,
                semantic_weight=retriever_semantic_weight,
                keyword_weight=retriever_keyword_weight,
                k=retriever_k,
            )
            logger.info("Initialized hybrid retriever", num_documents=len(documents))
        except Exception as e:
            logger.error("Failed to initialize hybrid retriever", error=str(e))
            # Fallback to vector retriever only
            self.retriever = vector_store.as_retriever()
        
        # Initialize advanced retriever for context-aware queries
        try:
            self.advanced_retriever = AdvancedRetriever(
                vector_store,
                documents,
                semantic_weight=retriever_semantic_weight,
                keyword_weight=retriever_keyword_weight,
                k=retriever_k,
            )
            logger.info("Initialized advanced retriever")
        except Exception as e:
            logger.warning("Failed to initialize advanced retriever", error=str(e))
            self.advanced_retriever = None
        
    def _handle_direct_query(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Check for and handle direct queries that don't require RAG.
        """
        # Case-insensitive check for date-related questions
        if "date" in question.lower() and "today" in question.lower():
            from datetime import datetime
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            answer = f"Today's date is {current_date}."
            logger.info("Handling direct query for today's date")
            return {
                "answer": answer,
                "sources": [],
                "confidence_score": 1.0,
                "template_used": "direct_query",
                "num_sources": 0,
                "retrieval_stats": {}
            }
        return None

    def query(
        self,
        question: str,
        template_type: Optional[str] = None,
        k: int = 5,
        include_sources: bool = True,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        conversation_context: bool = True,
        retriever_overrides: Optional[Dict[str, Any]] = None,
        llm_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a query using enhanced RAG with hybrid retrieval.
        
        Args:
            question: User's question
            template_type: Specific prompt template to use
            k: Number of documents to retrieve
            include_sources: Whether to include source attribution
            chat_history: Conversation messages for additional context
            conversation_context: Whether to leverage and persist conversation history
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Check for direct queries first
        direct_result = self._handle_direct_query(question)
        if direct_result:
            return direct_result
            
        try:
            history = chat_history or []
            use_context = bool(history) and conversation_context

            logger.info(
                "Processing RAG query",
                question=question,
                k=k,
                use_context=use_context,
            )
            
            retriever = self._select_retriever(retriever_overrides)

            retrieval_start = time.perf_counter()
            if use_context and self.advanced_retriever:
                history_strings = self._prepare_history(history)
                documents = self.advanced_retriever.retrieve_with_context(
                    question,
                    history_strings,
                    k=retriever_overrides.get("k") if retriever_overrides else k,
                )
            else:
                documents = retriever.retrieve(question, k=retriever_overrides.get("k") if retriever_overrides else k)

            retrieval_duration = time.perf_counter() - retrieval_start
            observe_rag_retrieval(
                duration_seconds=retrieval_duration,
                document_count=len(documents),
                mode="context" if use_context and self.advanced_retriever else "hybrid",
            )
            logger.info("Retrieved documents", count=len(documents), duration=round(retrieval_duration, 4))
            
            # Auto-select template if not specified
            if template_type is None:
                template_type = prompt_manager.select_template_by_query_type(
                    question, len(documents)
                )
            
            # Generate enhanced prompt
            prompt = get_enhanced_prompt(
                question=question,
                documents=documents,
                template_type=template_type,
                chat_history=history if use_context else None,
            )
            
            llm = self._resolve_llm(llm_overrides)

            generation_start = time.perf_counter()
            response = llm.invoke(prompt)
            generation_duration = time.perf_counter() - generation_start
            answer = response.content if hasattr(response, "content") else str(response)
            answer = replace_bracket_citations(answer)
            
            # Extract source information and confidence scores
            sources = self._extract_source_info(documents) if include_sources else []
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(answer, documents)

            token_usage = {}
            if hasattr(response, "response_metadata"):
                token_usage = response.response_metadata.get("token_usage", {})
            observe_rag_generation(
                provider=self.llm_provider,
                model=self.llm_model,
                duration_seconds=generation_duration,
                token_usage=token_usage,
            )
            
            result = {
                "answer": answer,
                "sources": sources,
                "confidence_score": confidence_score,
                "template_used": template_type,
                "num_sources": len(documents),
                "retrieval_stats": self.retriever.get_retrieval_stats() if hasattr(self.retriever, 'get_retrieval_stats') else {}
            }
            
            if conversation_context:
                self._record_interaction(question, answer, sources if include_sources else [])

            logger.info("RAG query completed", 
                       template_type=template_type, 
                       confidence=confidence_score,
                       num_sources=len(sources))
            
            return result
            
        except Exception as e:
            logger.error("RAG query failed", question=question, error=str(e))
            increment_rag_error(component="rag_chain", exception_type=e.__class__.__name__)
            raise LLMError(
                f"RAG query failed: {str(e)}",
                {"question": question, "error": str(e)},
            )
    
    def _prepare_history(self, chat_history: List[Dict[str, Any]]) -> List[str]:
        """Convert structured chat history into flat strings for the retriever."""
        history_strings: List[str] = []
        for message in chat_history[-6:]:  # Limit to last 6 messages (3 exchanges)
            content = message.get("content")
            if not content:
                continue
            role = message.get("role", "")
            if role == "user":
                prefix = "User: "
            elif role == "assistant":
                prefix = "Assistant: "
            else:
                prefix = ""
            history_strings.append(f"{prefix}{content}")
        return history_strings

    def _extract_source_info(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Aggregate chunk metadata into normalized source payloads."""
        grouped: Dict[str, Dict[str, Any]] = {}

        for doc in documents:
            metadata = dict(getattr(doc, "metadata", {}) or {})
            raw_path = metadata.get("raw_file_path") or metadata.get("source")
            key = metadata.get("document_id") or raw_path or metadata.get("source_display_name") or str(id(doc))
            entry = grouped.setdefault(
                key,
                {
                    "content": doc.page_content,
                    "metadata": metadata,
                    "chunks": [],
                },
            )
            entry["chunks"].append(doc)

        sources: List[Dict[str, Any]] = []
        for index, (key, entry) in enumerate(grouped.items(), start=1):
            metadata = dict(entry.get("metadata") or {})
            page_numbers: set[int] = set()
            for chunk in entry["chunks"]:
                chunk_meta = getattr(chunk, "metadata", {}) or {}
                candidate = chunk_meta.get("page_number")
                if isinstance(candidate, int):
                    page_numbers.add(candidate)
                candidate = chunk_meta.get("page")
                if isinstance(candidate, int):
                    page_numbers.add(candidate + 1)
                if isinstance(chunk_meta.get("page_numbers"), (list, tuple)):
                    for value in chunk_meta["page_numbers"]:
                        if isinstance(value, int):
                            page_numbers.add(value)
            if page_numbers:
                sorted_pages = sorted(page_numbers)
                metadata["page_numbers"] = sorted_pages
            else:
                sorted_pages = []
            best_chunk = max(
                entry["chunks"],
                key=lambda chunk: metadata.get("bm25_score", 0.0) if metadata else 0.0,
            )
            payload = {
                "id": index,
                "content": best_chunk.page_content if best_chunk else entry.get("content"),
                "metadata": metadata,
                "raw_file_path": metadata.get("raw_file_path"),
                "relevance_score": metadata.get("relevance_score"),
                "bm25_score": metadata.get("bm25_score"),
                "retrieval_rank": metadata.get("retrieval_rank"),
                "page_numbers": sorted_pages,
            }
            sources.append(normalize_source_payload(payload, index))

        sources.sort(key=lambda src: src.get("relevance_score", 0.0) or 0.0, reverse=True)
        for idx, source in enumerate(sources, start=1):
            source["id"] = idx
            source["citation"] = source.get("citation") or source.get("display_name")
        return sources

    def _select_retriever(self, overrides: Optional[Dict[str, Any]]):
        if not overrides:
            return self.retriever
        semantic_weight = overrides.get("semantic_weight")
        keyword_weight = overrides.get("keyword_weight")
        k = overrides.get("k", RETRIEVER_K)
        if semantic_weight is None and keyword_weight is None:
            return self.retriever
        return HybridRetriever(
            self.vector_store,
            self.documents,
            semantic_weight=semantic_weight or RETRIEVER_SEMANTIC_WEIGHT,
            keyword_weight=keyword_weight or RETRIEVER_KEYWORD_WEIGHT,
            k=k,
        )

    def _resolve_llm(self, overrides: Optional[Dict[str, Any]]):
        if not overrides:
            self.llm_provider = LLM_PROVIDER
            self.llm_model = LLM_MODEL
            return get_llm()

        provider = overrides.get("provider", LLM_PROVIDER)
        model = overrides.get("model", LLM_MODEL)
        temperature = overrides.get("temperature")
        max_output_tokens = overrides.get("max_output_tokens")
        api_key = overrides.get("api_key")
        request_timeout = overrides.get("request_timeout")
        max_retries = overrides.get("max_retries")

        self.llm_provider = provider
        self.llm_model = model
        return get_llm(
            provider=provider,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            request_timeout=request_timeout,
            api_key=api_key,
            max_retries=max_retries,
        )
    
    def _record_interaction(self, question: str, answer: str, sources: List[Dict[str, Any]]) -> None:
        try:
            entry = {
                "user": question,
                "assistant": answer,
                "sources": sources,
            }
            self.conversation_history.append(entry)
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to record conversation history", error=str(exc))

    def _calculate_relevance_score(self, document: Document, answer: str) -> float:
        """Calculate relevance score between document and generated answer."""
        try:
            # Simple relevance scoring based on common words
            doc_words = set(document.page_content.lower().split())
            answer_words = set(answer.lower().split())
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            doc_words -= stop_words
            answer_words -= stop_words
            
            if not doc_words or not answer_words:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = len(doc_words.intersection(answer_words))
            union = len(doc_words.union(answer_words))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.warning("Failed to calculate relevance score", error=str(e))
            return 0.0
    
    def _calculate_confidence_score(self, answer: str, documents: List[Document]) -> float:
        """Calculate confidence score for the generated answer."""
        try:
            # Factors that increase confidence:
            # 1. Answer length (reasonable length indicates completeness)
            # 2. Presence of specific details
            # 3. Number of supporting documents
            # 4. Lack of uncertainty phrases
            
            confidence = 0.5  # Base confidence
            
            # Length factor (optimal range: 50-500 characters)
            length_score = min(len(answer) / 500, 1.0) if len(answer) > 50 else len(answer) / 50
            confidence += length_score * 0.2
            
            # Specificity factor (presence of numbers, dates, names)
            specificity_patterns = [
                r'\d+',  # Numbers
                r'\d{4}',  # Years
                r'[A-Z][a-z]+ [A-Z][a-z]+',  # Proper names
                r'\$\d+',  # Money amounts
                r'\d+%'  # Percentages
            ]
            
            specificity_score = 0
            for pattern in specificity_patterns:
                if re.search(pattern, answer):
                    specificity_score += 0.1
            
            confidence += min(specificity_score, 0.3)
            
            # Document support factor
            doc_support = min(len(documents) / 5, 1.0)  # Normalize to max 5 docs
            confidence += doc_support * 0.2
            
            # Uncertainty penalty
            uncertainty_phrases = [
                "i don't know", "not sure", "unclear", "might be", "possibly", 
                "perhaps", "maybe", "i think", "seems like", "appears to"
            ]
            
            answer_lower = answer.lower()
            uncertainty_penalty = sum(0.1 for phrase in uncertainty_phrases if phrase in answer_lower)
            confidence -= min(uncertainty_penalty, 0.3)
            
            # Ensure confidence is between 0 and 1
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.warning("Failed to calculate confidence score", error=str(e))
            return 0.5
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG chain."""
        return {
            "retriever_type": type(self.retriever).__name__,
            "has_advanced_retriever": self.advanced_retriever is not None,
            "total_documents": len(self.documents)
        }
