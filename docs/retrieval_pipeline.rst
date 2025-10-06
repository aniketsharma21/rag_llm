Retrieval Pipeline
==================

This section details the hybrid retrieval stack that fuses vector similarity and keyword search to deliver robust context selection.

Hybrid Retriever
----------------

`src/retrieval.py` defines `HybridRetriever`, which wraps the Chroma vector store and a BM25 retriever:

.. code-block:: python
   :caption: `HybridRetriever` initialization

   class HybridRetriever:
       def __init__(
           self,
           vector_store,
           documents: List[Document],
           semantic_weight: float = 0.7,
           keyword_weight: float = 0.3,
           k: int = 10,
       ):
           self.vector_store = vector_store
           self.documents = documents
           self.k = k

           self.vector_retriever = vector_store.as_retriever(
               search_kwargs={"k": k}
           )

           self.bm25_retriever = BM25Retriever.from_documents(documents, k=k)

           self.ensemble_retriever = EnsembleRetriever(
               retrievers=[self.vector_retriever, self.bm25_retriever],
               weights=[semantic_weight, keyword_weight],
           )

`retrieve()` returns the fused document list, annotating metadata such as `retrieval_rank` and, when the manual fallback path is triggered, `bm25_score`.

Conversation Context
--------------------

`AdvancedRetriever.retrieve_with_context()` augments the current query with recent conversation turns to bias retrieval toward topical continuity:

.. code-block:: python
   :caption: `AdvancedRetriever.retrieve_with_context()`

   def retrieve_with_context(
       self,
       query: str,
       conversation_history: List[str] | None = None,
       k: Optional[int] = None,
   ) -> List[Document]:
       expanded_query = self._expand_query_with_context(query, conversation_history)
       self.query_history.append(query)
       if len(self.query_history) > 10:
           self.query_history.pop(0)

       return self.retrieve(expanded_query, k)

Fallback Mechanics
------------------

When the ensemble cannot be constructed (e.g., BM25 unavailable), `HybridRetriever._manual_hybrid_retrieval()` interleaves vector and BM25 results, while `_vector_only_retrieval()` ensures graceful degradation.

Retrieval Telemetry
-------------------

* **Prometheus metrics** – `src/middleware/observability.py` exposes `rag_retrieval_duration_seconds` and `rag_retrieved_documents_count`, populated by `observe_rag_retrieval()` in `src/llm.py`.
* **Runtime logging** – Structured logs include query text (redacted), `k`, and fallback indicators to simplify troubleshooting.

Configuration
-------------

Retriever weights and document counts are controlled through `src/config.py` values:

.. code-block:: python

   retriever_semantic_weight: float = Field(default=_YAML_DEFAULTS.get("retriever_semantic_weight", 0.7))
   retriever_keyword_weight: float = Field(default=_YAML_DEFAULTS.get("retriever_keyword_weight", 0.3))
   retriever_k: int = Field(default=_YAML_DEFAULTS.get("retriever_k", 5))

Overriding these parameters at runtime requires re-ingestion to maintain vector store consistency.
