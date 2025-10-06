"""
llm.py

Enhanced LLM management for the RAG pipeline with hybrid retrieval and advanced prompting.
Integrates with hybrid retrieval system and enhanced prompt templates for better responses.

Features:
- Groq LLM integration with error handling
- Enhanced RAG chain with hybrid retrieval
- Source attribution and confidence scoring
- Multiple prompt templates for different query types
- Conversation context management

Usage:
    Use get_llm() to obtain a ready-to-use LLM instance.
    Use EnhancedRAGChain for advanced RAG functionality with hybrid retrieval.
"""

import os
from urllib.parse import quote
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_groq import ChatGroq
from langchain.schema import Document
from langchain.chains import LLMChain
from src.config import GROQ_API_KEY, LLM_MODEL
from src.logging_config import get_logger
from src.exceptions import LLMError, ConfigurationError
from src.retrieval import HybridRetriever, AdvancedRetriever
from src.prompt_templates import get_enhanced_prompt, prompt_manager
import json
import re


SUPERSCRIPT_MAP = {
    "0": "\u2070",
    "1": "\u00B9",
    "2": "\u00B2",
    "3": "\u00B3",
    "4": "\u2074",
    "5": "\u2075",
    "6": "\u2076",
    "7": "\u2077",
    "8": "\u2078",
    "9": "\u2079",
}


logger = get_logger(__name__)

def get_llm():
    """
    Initializes and returns the Groq LLM instance for text generation.

    Raises:
        ConfigurationError: If GROQ_API_KEY is missing.
        LLMError: If LLM initialization fails.

    Returns:
        ChatGroq instance: A configured instance of the ChatGroq class for generating text.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not found", model=LLM_MODEL)
        raise ConfigurationError("GROQ_API_KEY not found. Please set it in your .env file.", 
                               {"model": LLM_MODEL})
    try:
        llm = ChatGroq(
            model=LLM_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.1,  # Lower temperature for more consistent responses
            max_tokens=2048   # Reasonable token limit
        )
        logger.info("Successfully initialized Groq LLM", model=LLM_MODEL)
        return llm
    except Exception as e:
        logger.error("Failed to initialize Groq LLM", model=LLM_MODEL, error=str(e))
        raise LLMError(f"Failed to initialize Groq LLM: {str(e)}", 
                      {"model": LLM_MODEL, "error": str(e)})


class EnhancedRAGChain:
    """
    Enhanced RAG chain with hybrid retrieval, source attribution, and advanced prompting.
    """
    
    def __init__(self, vector_store, documents: List[Document]):
        """
        Initialize the enhanced RAG chain.
        
        Args:
            vector_store: ChromaDB vector store instance
            documents: List of processed documents for BM25 retrieval
        """
        self.llm = get_llm()
        self.vector_store = vector_store
        self.documents = documents
        self.conversation_history: List[Dict[str, Any]] = []

        # Initialize hybrid retriever
        try:
            self.retriever = HybridRetriever(vector_store, documents)
            logger.info("Initialized hybrid retriever", num_documents=len(documents))
        except Exception as e:
            logger.error("Failed to initialize hybrid retriever", error=str(e))
            # Fallback to vector retriever only
            self.retriever = vector_store.as_retriever()
        
        # Initialize advanced retriever for context-aware queries
        try:
            self.advanced_retriever = AdvancedRetriever(vector_store, documents)
            logger.info("Initialized advanced retriever")
        except Exception as e:
            logger.warning("Failed to initialize advanced retriever", error=str(e))
            self.advanced_retriever = None
        
    def query(
        self,
        question: str,
        template_type: Optional[str] = None,
        k: int = 5,
        include_sources: bool = True,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        conversation_context: bool = True,
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
        try:
            history = chat_history or []
            use_context = bool(history) and conversation_context

            logger.info(
                "Processing RAG query",
                question=question,
                k=k,
                use_context=use_context,
            )
            
            # Retrieve relevant documents
            if use_context and self.advanced_retriever:
                history_strings = self._prepare_history(history)
                documents = self.advanced_retriever.retrieve_with_context(
                    question, 
                    history_strings,
                    k=k
                )
            else:
                documents = self.retriever.retrieve(question, k=k)
            
            logger.info("Retrieved documents", count=len(documents))
            
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
            
            # Generate response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Extract source information and confidence scores
            sources = self._extract_source_info(documents, answer) if include_sources else []
            answer = self._apply_superscript_citations(answer, sources)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(answer, documents)
            
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
            raise LLMError(f"RAG query failed: {str(e)}", {"question": question, "error": str(e)})
    
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

    def _extract_source_info(self, documents: List[Document], answer: str) -> List[Dict[str, Any]]:
        """Aggregate chunk metadata into document-level source entries."""
        grouped_sources: Dict[str, Dict[str, Any]] = {}
        insertion_order: List[str] = []

        for doc in documents:
            metadata = dict(getattr(doc, "metadata", {}) or {})
            raw_path = metadata.get("raw_file_path") or metadata.get("source")
            display_name = metadata.get("source_display_name")
            if not display_name and raw_path:
                display_name = os.path.basename(raw_path)

            source_key = metadata.get("document_id") or raw_path or display_name or str(id(doc))

            preview_url = metadata.get("preview_url")
            if not preview_url and raw_path:
                filename = os.path.basename(raw_path)
                if filename:
                    preview_url = f"/files/preview/{quote(filename)}"

            page_number = metadata.get("page_number")
            if page_number is None and isinstance(metadata.get("page"), int):
                page_number = metadata["page"] + 1

            snippet = metadata.get("snippet") or (doc.page_content or "")
            if snippet:
                snippet = snippet.strip()
                if len(snippet) > 320:
                    truncated = snippet[:320].rsplit(" ", 1)[0]
                    snippet = f"{truncated}…" if truncated else snippet[:320] + "…"

            relevance = self._calculate_relevance_score(doc, answer)

            entry = grouped_sources.get(source_key)
            if not entry:
                entry = {
                    "raw_file_path": raw_path,
                    "source_display_name": display_name or "Document",
                    "source_display_path": metadata.get("source_display_path"),
                    "preview_url": preview_url,
                    "relevance_score": relevance,
                    "snippet": snippet,
                    "snippet_score": relevance if snippet else -1,
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": dict(metadata),
                    "page_numbers": set([page_number]) if page_number is not None else set(),
                    "chunk_count": 1,
                    "bm25_score": metadata.get("bm25_score"),
                    "retrieval_rank": metadata.get("retrieval_rank"),
                }
                grouped_sources[source_key] = entry
                insertion_order.append(source_key)
            else:
                entry["chunk_count"] += 1
                entry["relevance_score"] = max(entry["relevance_score"], relevance)
                if preview_url and not entry.get("preview_url"):
                    entry["preview_url"] = preview_url
                if page_number is not None:
                    entry["page_numbers"].add(page_number)
                if snippet and (entry["snippet"] is None or relevance > entry.get("snippet_score", -1)):
                    entry["snippet"] = snippet
                    entry["snippet_score"] = relevance
                    entry["content"] = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                if metadata.get("bm25_score") is not None:
                    if entry["bm25_score"] is None or metadata["bm25_score"] > entry["bm25_score"]:
                        entry["bm25_score"] = metadata["bm25_score"]
                if metadata.get("retrieval_rank") is not None:
                    if entry["retrieval_rank"] is None or metadata["retrieval_rank"] < entry["retrieval_rank"]:
                        entry["retrieval_rank"] = metadata["retrieval_rank"]

        aggregated_sources: List[Dict[str, Any]] = []
        for index, key in enumerate(insertion_order, start=1):
            entry = grouped_sources[key]
            page_numbers = sorted(n for n in entry["page_numbers"] if n is not None)
            if page_numbers:
                if len(page_numbers) == 1:
                    page_label = f"Page {page_numbers[0]}"
                else:
                    if len(page_numbers) <= 5:
                        page_label = "Pages " + ", ".join(str(n) for n in page_numbers)
                    else:
                        page_label = f"Pages {page_numbers[0]}–{page_numbers[-1]}"
            else:
                page_label = None

            metadata = dict(entry.get("metadata") or {})
            metadata.update({
                "snippet": entry.get("snippet"),
                "preview_url": entry.get("preview_url"),
                "page_numbers": page_numbers,
                "page_label": page_label,
                "chunk_count": entry.get("chunk_count", 0),
                "source_display_name": entry.get("source_display_name"),
                "raw_file_path": entry.get("raw_file_path"),
            })

            source_info = {
                "id": index,
                "content": entry.get("content", ""),
                "snippet": entry.get("snippet"),
                "metadata": metadata,
                "relevance_score": entry.get("relevance_score", 0.0),
                "source_file": entry.get("raw_file_path"),
                "raw_file_path": entry.get("raw_file_path"),
                "source_display_path": entry.get("source_display_path"),
                "source_display_name": entry.get("source_display_name"),
                "page": page_numbers[0] if page_numbers else None,
                "page_number": page_numbers[0] if page_numbers else None,
                "page_numbers": page_numbers,
                "page_label": page_label,
                "preview_url": entry.get("preview_url"),
                "chunk_count": entry.get("chunk_count"),
                "citation": self._format_superscript(index),
            }

            if entry.get("bm25_score") is not None:
                source_info["bm25_score"] = entry["bm25_score"]
            if entry.get("retrieval_rank") is not None:
                source_info["retrieval_rank"] = entry["retrieval_rank"]

            aggregated_sources.append(source_info)

        aggregated_sources.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        return aggregated_sources

    def _format_superscript(self, number: int) -> str:
        return "".join(SUPERSCRIPT_MAP.get(ch, ch) for ch in str(number))

    def _replace_bracket_citations(self, text: str) -> str:
        if not text:
            return text

        def replace_match(match):
            return self._format_superscript(match.group(1))

        updated = re.sub(r"\[(\d+)\]", replace_match, text)
        updated = re.sub(r"\^\{?(\d+)\}?", replace_match, updated)
        return updated

    def _apply_superscript_citations(self, answer: str, sources: List[Dict[str, Any]]) -> str:
        formatted_answer = self._replace_bracket_citations(answer or "").strip()
        return formatted_answer
    
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
