"""
Advanced retrieval system with hybrid semantic + keyword search.
Implements ensemble retrieval combining vector similarity and BM25 keyword matching.
"""

from typing import List, Dict, Any, Optional

from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document, BaseRetriever
from langchain_community.retrievers import BM25Retriever
from rank_bm25 import BM25Okapi
import structlog
from sentence_transformers import CrossEncoder
from src.config import RERANKER_MODEL

logger = structlog.get_logger(__name__)

# Initialize cross-encoder lazily
_cross_encoder = None

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading CrossEncoder: {RERANKER_MODEL}", device=device)
        _cross_encoder = CrossEncoder(RERANKER_MODEL, device=device, max_length=512)
    return _cross_encoder

DEFAULT_CONFIG = {
    "semantic_weight": 0.7,
    "keyword_weight": 0.3,
    "k": 10,
    "query_expansion_context_size": 3,
    "query_expansion_history_size": 10,
}




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
        k: Optional[int] = None,
    ):
        """
        Initialize the hybrid retriever.

        Args:
            vector_store: ChromaDB vector store instance
            documents: List of processed documents
            config: Configuration dictionary for retriever settings
            k: Backward-compatible shortcut for config["k"]
        """
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        if k is not None:
            self.config["k"] = k
        self.vector_store = vector_store
        self.documents = documents
        self.k = self.config["k"]
        self._uses_ensemble = False

        logger.info(
            "Initializing hybrid retriever",
            num_documents=len(documents),
            config=self.config
        )

        self.vector_retriever = self.vector_store.as_retriever(search_kwargs={"k": self.k})

        bm25_retriever = self._init_bm25_retriever()

        if bm25_retriever:
            try:
                self.retriever = EnsembleRetriever(
                    retrievers=[self.vector_retriever, bm25_retriever],
                    weights=[self.config["semantic_weight"], self.config["keyword_weight"]]
                )
                self._uses_ensemble = True
                logger.info("Ensemble retriever initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize ensemble retriever. Falling back to vector-only search.", error=str(e))
                self.retriever = self.vector_retriever
        else:
            logger.warning("Could not initialize any BM25 retriever. Falling back to vector-only search.")
            self.retriever = self.vector_retriever

    def _init_bm25_retriever(self) -> Optional[BaseRetriever]:
        """Initializes the BM25 retriever."""
        if not self.documents:
            logger.warning("No documents provided; skipping BM25 initialization.")
            return None
        try:
            logger.info("Initializing BM25Retriever from langchain.")
            return BM25Retriever.from_documents(self.documents, k=self.k)
        except Exception as e:
            logger.error("Failed to initialize BM25Retriever.", error=str(e))
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
            results = self.retriever.invoke(query)
            results = results[:k_to_use]
            self._add_retrieval_metadata(results)
            logger.info("Hybrid retrieval completed", final_count=len(results))
            return results
        except Exception as e:
            logger.error("Hybrid retrieval failed, falling back to vector-only", error=str(e))
            return self._vector_only_retrieval(query, k_to_use)

    def _add_retrieval_metadata(self, documents: List[Document]):
        """Adds retrieval metadata to the documents."""
        for i, doc in enumerate(documents):
            if not hasattr(doc, 'metadata'):
                doc.metadata = {}
            doc.metadata['retrieval_rank'] = i + 1
            doc.metadata['retrieval_method'] = "hybrid"

    def _vector_only_retrieval(self, query: str, k: int) -> List[Document]:
        """Fallback to vector search only."""
        try:
            logger.warning("Falling back to vector-only retrieval")
            results = self.vector_retriever.invoke(query)
            results = results[:k]
            self._add_retrieval_metadata(results)
            return results
        except Exception as e:
            logger.error("Vector-only retrieval failed", error=str(e))
            return []

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval system."""
        is_ensemble = self._uses_ensemble
        has_bm25 = False
        if is_ensemble:
            retrievers = getattr(self.retriever, "retrievers", getattr(self.retriever, "_retrievers", []))
            has_bm25 = any(isinstance(r, BM25Retriever) for r in retrievers)

        return {
            "total_documents": len(self.documents),
            "retrieval_k": self.k,
            "retriever_type": self.retriever.__class__.__name__,
            "is_ensemble": is_ensemble,
            "has_ensemble": is_ensemble,
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
        """Re-rank documents using CrossEncoder."""
        if not documents:
            return []
        try:
            encoder = get_cross_encoder()
            pairs = [[query, doc.page_content] for doc in documents]
            scores = encoder.predict(pairs)
            
            scored_docs = []
            for doc, score in zip(documents, scores):
                bm25_score = getattr(doc, 'metadata', {}).get('bm25_score', 0.0) if hasattr(doc, 'metadata') else 0.0
                combined_score = float(score) + (bm25_score * 0.1)
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
        except Exception as e:
            logger.error("CrossEncoder reranking failed, falling back", error=str(e))
            return documents
