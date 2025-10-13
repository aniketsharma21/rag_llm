"""
Advanced retrieval system with hybrid semantic + keyword search.
Implements ensemble retrieval combining vector similarity and BM25 keyword matching.
"""

import logging
from typing import List, Dict, Any, Optional

from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document, BaseRetriever
from langchain_community.retrievers import BM25Retriever
from rank_bm25 import BM25Okapi
import structlog

logger = structlog.get_logger(__name__)

DEFAULT_CONFIG = {
    "semantic_weight": 0.7,
    "keyword_weight": 0.3,
    "k": 10,
    "query_expansion_context_size": 3,
    "query_expansion_history_size": 10,
}


class BM25FallbackRetriever(BaseRetriever):
    """Fallback BM25 retriever using rank_bm25."""
    def __init__(self, documents: List[Document], k: int):
        super().__init__()
        self.documents = documents
        self.k = k
        corpus = [doc.page_content.split() for doc in self.documents]
        self.bm25 = BM25Okapi(corpus)

    def _get_relevant_documents(self, query: str) -> List[Document]:
        query_tokens = query.split()
        scores = self.bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:self.k]

        results = []
        for idx in top_indices:
            if idx < len(self.documents):
                doc = self.documents[idx]
                if not hasattr(doc, 'metadata'):
                    doc.metadata = {}
                doc.metadata['bm25_score'] = float(scores[idx])
                results.append(doc)
        return results

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("BM25FallbackRetriever does not support async")


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
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the hybrid retriever.

        Args:
            vector_store: ChromaDB vector store instance
            documents: List of processed documents
            config: Configuration dictionary for retriever settings
        """
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.vector_store = vector_store
        self.documents = documents
        self.k = self.config["k"]

        logger.info(
            "Initializing hybrid retriever",
            num_documents=len(documents),
            config=self.config
        )

        self.vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": self.k})

        bm25_retriever = self._init_bm25_retriever()

        if bm25_retriever:
            self.retriever = EnsembleRetriever(
                retrievers=[self.vector_retriever, bm25_retriever],
                weights=[self.config["semantic_weight"], self.config["keyword_weight"]]
            )
            logger.info("Ensemble retriever initialized successfully")
        else:
            logger.warning("Could not initialize any BM25 retriever. Falling back to vector-only search.")
            self.retriever = self.vector_retriever

    def _init_bm25_retriever(self) -> Optional[BaseRetriever]:
        """Initializes the BM25 retriever with a fallback."""
        try:
            logger.info("Initializing BM25Retriever from langchain.")
            return BM25Retriever.from_documents(self.documents, k=self.k)
        except Exception as e:
            logger.error("Failed to initialize BM25Retriever, trying fallback.", error=str(e))
            try:
                logger.info("Initializing BM25FallbackRetriever.")
                return BM25FallbackRetriever(documents=self.documents, k=self.k)
            except Exception as e2:
                logger.error("Failed to initialize fallback BM25 retriever.", error=str(e2))
                return None

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents using hybrid approach.

        Args:
            query: Search query
            k: Number of documents to retrieve (overrides default)

        Returns:
            List of relevant documents with metadata
        """
        k_to_use = k or self.k
        logger.info("Starting hybrid retrieval", query=query, k=k_to_use)

        try:
            results = self.retriever.get_relevant_documents(query)
            results = results[:k_to_use]
            self._add_retrieval_metadata(results)
            logger.info("Hybrid retrieval completed", final_count=len(results))
            return results
        except Exception as e:
            logger.error("Hybrid retrieval failed, falling back to vector-only", error=str(e))
            return self._vector_only_retrieval(query, k_to_use)

    def _add_retrieval_metadata(self, documents: List[Document]):
        """Adds retrieval metadata to the documents."""
        method = "hybrid" if isinstance(self.retriever, EnsembleRetriever) else "vector_only"
        for i, doc in enumerate(documents):
            if not hasattr(doc, 'metadata'):
                doc.metadata = {}
            doc.metadata['retrieval_rank'] = i + 1
            doc.metadata['retrieval_method'] = method

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
        is_ensemble = isinstance(self.retriever, EnsembleRetriever)
        has_bm25 = False
        if is_ensemble:
            has_bm25 = any(isinstance(r, (BM25Retriever, BM25FallbackRetriever)) for r in self.retriever.retrievers)

        return {
            "total_documents": len(self.documents),
            "retrieval_k": self.k,
            "retriever_type": self.retriever.__class__.__name__,
            "is_ensemble": is_ensemble,
            "has_bm25": has_bm25,
        }


class AdvancedRetriever(HybridRetriever):
    """
    Advanced retriever with additional features like query rewriting and re-ranking.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_history = []
        self._query_expansion_enabled = True

    def _rewrite_query(self, query: str) -> str:
        """Rewrite query to improve retrieval."""
        query = query.strip()
        stop_phrases = ['what is', 'who is', 'when did', 'where is', 'how does', 'why did']
        query_lower = query.lower()
        for phrase in stop_phrases:
            if query_lower.startswith(phrase):
                query = query[len(phrase):].strip()
                break
        return query

    def retrieve_with_context(
        self,
        query: str,
        conversation_history: List[str] = None,
        k: Optional[int] = None
    ) -> List[Document]:
        """Retrieve documents with query rewriting and context."""
        rewritten_query = self._rewrite_query(query)

        if conversation_history and self._query_expansion_enabled:
            expanded_query = self._expand_query_with_context(rewritten_query, conversation_history)
        else:
            expanded_query = rewritten_query

        self.query_history.append(query)
        history_size = self.config.get("query_expansion_history_size")
        if len(self.query_history) > history_size:
            self.query_history.pop(0)

        logger.info(
            "Retrieving with rewriting and context",
            original_query=query,
            rewritten_query=rewritten_query,
            expanded_query=expanded_query[:100] + "..." if len(expanded_query) > 100 else expanded_query
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
        context_size = self.config.get("query_expansion_context_size")
        recent_context = " ".join(conversation_history[-context_size:])
        return f"{query} {recent_context}"

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """Retrieve and re-rank documents."""
        k_to_use = k or self.k
        retrieval_k = k_to_use * 2
        documents = super().retrieve(query, retrieval_k)
        reranked_docs = self._rerank_documents(query, documents)
        return reranked_docs[:k_to_use]

    def _rerank_documents(self, query: str, documents: List[Document]) -> List[Document]:
        """Re-rank documents based on relevance scores."""
        scored_docs = []
        query_terms = set(query.lower().split())

        for doc in documents:
            doc_terms = set(doc.page_content.lower().split())
            intersection = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms)
            jaccard_score = intersection / union if union > 0 else 0.0
            term_freq = sum(1 for term in query_terms if term in doc.page_content.lower())
            tf_score = term_freq / len(query_terms) if query_terms else 0.0
            combined_score = (jaccard_score * 0.6) + (tf_score * 0.4)

            if hasattr(doc, 'metadata'):
                bm25_score = doc.metadata.get('bm25_score', 0.0)
                combined_score += bm25_score * 0.2
            
            scored_docs.append((doc, combined_score))

        scored_docs.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for i, (doc, score) in enumerate(scored_docs):
            if not hasattr(doc, 'metadata'):
                doc.metadata = {}
            doc.metadata['relevance_score'] = score
            doc.metadata['retrieval_rank'] = i + 1
            reranked.append(doc)
        
        return reranked
