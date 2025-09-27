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
        
        self.conversation_history = []
    
    def query(
        self, 
        question: str, 
        template_type: Optional[str] = None,
        k: int = 5,
        include_sources: bool = True,
        conversation_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process a query using enhanced RAG with hybrid retrieval.
        
        Args:
            question: User's question
            template_type: Specific prompt template to use
            k: Number of documents to retrieve
            include_sources: Whether to include source attribution
            conversation_context: Whether to use conversation history
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            logger.info("Processing RAG query", question=question, k=k)
            
            # Retrieve relevant documents
            if conversation_context and self.advanced_retriever:
                documents = self.advanced_retriever.retrieve_with_context(
                    question, 
                    self._get_recent_history(),
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
                chat_history=self.conversation_history if conversation_context else None
            )
            
            # Generate response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Extract source information and confidence scores
            sources = self._extract_source_info(documents, answer) if include_sources else []
            answer = self._apply_superscript_citations(answer, sources)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(answer, documents)
            
            # Store in conversation history
            if conversation_context:
                self.conversation_history.append({
                    "user": question,
                    "assistant": answer
                })
                # Keep only recent history
                if len(self.conversation_history) > 10:
                    self.conversation_history.pop(0)
            
            result = {
                "answer": answer,
                "sources": sources,
                "confidence_score": confidence_score,
                "template_used": template_type,
                "num_sources": len(documents),
                "retrieval_stats": self.retriever.get_retrieval_stats() if hasattr(self.retriever, 'get_retrieval_stats') else {}
            }
            
            logger.info("RAG query completed", 
                       template_type=template_type, 
                       confidence=confidence_score,
                       num_sources=len(sources))
            
            return result
            
        except Exception as e:
            logger.error("RAG query failed", question=question, error=str(e))
            raise LLMError(f"RAG query failed: {str(e)}", {"question": question, "error": str(e)})
    
    def _extract_source_info(self, documents: List[Document], answer: str) -> List[Dict[str, Any]]:
        """Extract and format source information with confidence scores."""
        sources = []
        
        for i, doc in enumerate(documents):
            metadata = dict(getattr(doc, 'metadata', {}) or {})
            source_info = {
                "id": i + 1,
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": metadata,
                "relevance_score": self._calculate_relevance_score(doc, answer)
            }
            
            # Add source-specific metadata
            if hasattr(doc, 'metadata') and doc.metadata:
                raw_path = metadata.get('raw_file_path') or metadata.get('source')
                source_info['source_file'] = raw_path
                source_info['raw_file_path'] = raw_path
                source_info['source_display_path'] = metadata.get('source_display_path')
                display_name = metadata.get('source_display_name')
                if not display_name and raw_path:
                    display_name = os.path.basename(raw_path)
                source_info['source_display_name'] = display_name or f"Document {i + 1}"

                page_number = metadata.get('page_number')
                if page_number is None and isinstance(metadata.get('page'), int):
                    page_number = metadata['page'] + 1
                source_info['page'] = page_number
                source_info['page_number'] = page_number

                if 'bm25_score' in metadata:
                    source_info['bm25_score'] = metadata['bm25_score']
                if 'retrieval_rank' in metadata:
                    source_info['retrieval_rank'] = metadata['retrieval_rank']
            
            source_info['citation'] = self._format_superscript(i + 1)
            sources.append(source_info)
        
        # Sort by relevance score
        sources.sort(key=lambda x: x['relevance_score'], reverse=True)
        return sources

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
        if not sources:
            return answer

        formatted_answer = self._replace_bracket_citations(answer).rstrip()

        citation_lines = []
        for source in sources:
            citation = source.get('citation') or self._format_superscript(source.get('id', 0))
            display_name = source.get('source_display_name') or source.get('source_file') or 'Document'
            page_number = source.get('page') or source.get('page_number')
            page_text = f" (Page {page_number})" if page_number else ""
            citation_lines.append(f"{citation} {display_name}{page_text}")

        citations_block = "\n".join(citation_lines)

        if citations_block:
            formatted_answer = f"{formatted_answer}\n\nSources:\n{citations_block}"

        return formatted_answer
    
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
    
    def _get_recent_history(self, max_exchanges: int = 3) -> List[str]:
        """Get recent conversation history for context."""
        if not self.conversation_history:
            return []
        
        recent = self.conversation_history[-max_exchanges:]
        history_strings = []
        
        for exchange in recent:
            history_strings.append(exchange['user'])
            history_strings.append(exchange['assistant'])
        
        return history_strings
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Cleared conversation history")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG chain."""
        return {
            "conversation_length": len(self.conversation_history),
            "retriever_type": type(self.retriever).__name__,
            "has_advanced_retriever": self.advanced_retriever is not None,
            "total_documents": len(self.documents)
        }
