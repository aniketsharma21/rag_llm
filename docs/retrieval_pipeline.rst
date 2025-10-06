Retrieval Pipeline
==================

This section details the hybrid retrieval stack that fuses vector similarity and keyword search to deliver robust context selection.

.. mermaid::

   graph TD
       A[Query] --> B{AdvancedRetriever};
       B --> C[Expand with Conversation History];
       C --> D{HybridRetriever};
       D --> E[Vector & BM25 Retrievers];
       E --> F[Ensemble Retriever];
       F --> G[Fused Document List];
       G --> H[Return to RAG Chain];

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

Advanced Retriever & Conversation Context
-----------------------------------------

The `AdvancedRetriever` sits in front of the `HybridRetriever` and is responsible for managing conversational context. Its `retrieve_with_context()` method augments the current query with recent conversation turns to bias retrieval toward topical continuity:

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

This query expansion is critical for maintaining context in multi-turn conversations, ensuring that the retriever has access to the full conversational history when searching for relevant documents.

Fallback Mechanics
------------------

The system is designed to be resilient to failures in the retrieval pipeline. When the ensemble retriever cannot be constructed (e.g., if the BM25 index is not available), the `HybridRetriever` gracefully degrades to a fallback mechanism. `HybridRetriever._manual_hybrid_retrieval()` interleaves vector and BM25 results, while `_vector_only_retrieval()` ensures that the system can still provide results even if only the vector store is available. This ensures that the user always receives a response, even if it's not as accurate as a full hybrid search.

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

These settings allow for fine-tuning of the retrieval process. The `retriever_semantic_weight` and `retriever_keyword_weight` control the balance between semantic and keyword search, while `retriever_k` determines the number of documents to retrieve. Overriding these parameters at runtime may require re-ingestion to maintain vector store consistency.
