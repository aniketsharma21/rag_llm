"""
Advanced retrieval system with hybrid semantic + keyword search.
Implements ensemble retrieval combining vector similarity and BM25 keyword matching.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from rank_bm25 import BM25Okapi
import structlog

logger = structlog.get_logger(__name__)


class HybridRetriever:
    """
    Hybrid retrieval system combining semantic vector search with keyword-based BM25 search.
    
    This retriever uses an ensemble approach to leverage both:
    1. Semantic similarity through vector embeddings
    2. Keyword matching through BM25 algorithm
    """
    
    def __init__(
        self, 
        vector_store, 
        documents: List[Document],
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        k: int = 10
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            vector_store: ChromaDB vector store instance
            documents: List of processed documents
            semantic_weight: Weight for semantic search (default: 0.7)
            keyword_weight: Weight for keyword search (default: 0.3)
            k: Number of documents to retrieve
        """
        self.vector_store = vector_store
        self.documents = documents
        self.k = k
        
        logger.info(
            "Initializing hybrid retriever",
            num_documents=len(documents),
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            k=k
        )
        
        # Initialize vector retriever
        self.vector_retriever = vector_store.as_retriever(
            search_kwargs={"k": k}
        )
        
        # Initialize BM25 retriever
        try:
            self.bm25_retriever = BM25Retriever.from_documents(
                documents, 
                k=k
            )
            logger.info("BM25 retriever initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize BM25 retriever", error=str(e))
            # Fallback: create a simple BM25 implementation
            self._init_fallback_bm25()
        
        # Create ensemble retriever
        try:
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.vector_retriever, self.bm25_retriever],
                weights=[semantic_weight, keyword_weight]
            )
            logger.info("Ensemble retriever initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize ensemble retriever", error=str(e))
            # Fallback to vector retriever only
            self.ensemble_retriever = self.vector_retriever
    
    def _init_fallback_bm25(self):
        """Initialize fallback BM25 implementation using rank_bm25."""
        try:
            # Extract text content from documents
            corpus = [doc.page_content.split() for doc in self.documents]
            self.bm25 = BM25Okapi(corpus)
            self.use_fallback_bm25 = True
            logger.info("Fallback BM25 implementation initialized")
        except Exception as e:
            logger.error("Failed to initialize fallback BM25", error=str(e))
            self.use_fallback_bm25 = False
    
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents using hybrid approach.
        
        Args:
            query: Search query
            k: Number of documents to retrieve (overrides default)
            
        Returns:
            List of relevant documents with metadata
        """
        k = k or self.k
        
        logger.info("Starting hybrid retrieval", query=query, k=k)
        
        try:
            # Use ensemble retriever if available
            if hasattr(self, 'ensemble_retriever') and self.ensemble_retriever != self.vector_retriever:
                results = self.ensemble_retriever.get_relevant_documents(query)
                logger.info("Retrieved documents using ensemble retriever", count=len(results))
            else:
                # Fallback: combine results manually
                results = self._manual_hybrid_retrieval(query, k)
                logger.info("Retrieved documents using manual hybrid approach", count=len(results))
            
            # Limit results to requested number
            results = results[:k]
            
            # Add retrieval metadata
            for i, doc in enumerate(results):
                if not hasattr(doc, 'metadata'):
                    doc.metadata = {}
                doc.metadata['retrieval_rank'] = i + 1
                doc.metadata['retrieval_method'] = 'hybrid'
            
            logger.info("Hybrid retrieval completed", final_count=len(results))
            return results
            
        except Exception as e:
            logger.error("Hybrid retrieval failed", error=str(e))
            # Fallback to vector search only
            return self._vector_only_retrieval(query, k)
    
    def _manual_hybrid_retrieval(self, query: str, k: int) -> List[Document]:
        """Manual hybrid retrieval when ensemble retriever is not available."""
        try:
            # Get vector search results
            vector_results = self.vector_retriever.get_relevant_documents(query)
            
            # Get BM25 results if available
            if hasattr(self, 'use_fallback_bm25') and self.use_fallback_bm25:
                bm25_results = self._fallback_bm25_search(query, k)
            else:
                bm25_results = []
            
            # Combine and deduplicate results
            combined_results = []
            seen_content = set()
            
            # Add vector results with higher weight
            for doc in vector_results[:k//2 + 1]:
                if doc.page_content not in seen_content:
                    combined_results.append(doc)
                    seen_content.add(doc.page_content)
            
            # Add BM25 results
            for doc in bm25_results[:k//2 + 1]:
                if doc.page_content not in seen_content:
                    combined_results.append(doc)
                    seen_content.add(doc.page_content)
            
            return combined_results[:k]
            
        except Exception as e:
            logger.error("Manual hybrid retrieval failed", error=str(e))
            return self._vector_only_retrieval(query, k)
    
    def _fallback_bm25_search(self, query: str, k: int) -> List[Document]:
        """Fallback BM25 search using rank_bm25."""
        try:
            query_tokens = query.split()
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top k document indices
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            
            # Return corresponding documents
            results = []
            for idx in top_indices:
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    # Add BM25 score to metadata
                    if not hasattr(doc, 'metadata'):
                        doc.metadata = {}
                    doc.metadata['bm25_score'] = float(scores[idx])
                    results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error("Fallback BM25 search failed", error=str(e))
            return []
    
    def _vector_only_retrieval(self, query: str, k: int) -> List[Document]:
        """Fallback to vector search only."""
        try:
            logger.warning("Falling back to vector-only retrieval")
            results = self.vector_retriever.get_relevant_documents(query)
            return results[:k]
        except Exception as e:
            logger.error("Vector-only retrieval failed", error=str(e))
            return []
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval system."""
        return {
            "total_documents": len(self.documents),
            "retrieval_k": self.k,
            "has_bm25": hasattr(self, 'bm25_retriever'),
            "has_ensemble": hasattr(self, 'ensemble_retriever'),
            "fallback_bm25": getattr(self, 'use_fallback_bm25', False)
        }


class AdvancedRetriever(HybridRetriever):
    """
    Advanced retriever with additional features like query expansion and re-ranking.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_history = []
    
    def retrieve_with_context(
        self, 
        query: str, 
        conversation_history: List[str] = None,
        k: Optional[int] = None
    ) -> List[Document]:
        """
        Retrieve documents with conversation context.
        
        Args:
            query: Current query
            conversation_history: Previous queries/responses for context
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        # Expand query with conversation context
        expanded_query = self._expand_query_with_context(query, conversation_history)
        
        # Store query for future context
        self.query_history.append(query)
        if len(self.query_history) > 10:  # Keep last 10 queries
            self.query_history.pop(0)
        
        logger.info(
            "Retrieving with context",
            original_query=query,
            expanded_query=expanded_query,
            history_length=len(conversation_history or [])
        )
        
        return self.retrieve(expanded_query, k)
    
    def _expand_query_with_context(
        self, 
        query: str, 
        conversation_history: List[str] = None
    ) -> str:
        """Expand query using conversation context."""
        if not conversation_history:
            return query
        
        # Simple context expansion - in production, use more sophisticated methods
        recent_context = " ".join(conversation_history[-3:])  # Last 3 exchanges
        expanded_query = f"{query} {recent_context}"
        
        return expanded_query
