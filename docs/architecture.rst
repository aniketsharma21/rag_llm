Architecture
============

The platform is split into modular services wired together through shared configuration and observability primitives. This section highlights the runtime topology, data flows, and major components.

Runtime Topology
----------------

High-level service interaction diagram:

.. mermaid::

   graph TD
     subgraph Client
       A[React Frontend]
     end
     subgraph API_Layer
       B[FastAPI Application\n`src/api.py`]
       C[Observability Middleware\n`src/middleware/observability.py`]
     end
     subgraph Services
       D[Ingestion Service\n`IngestionService`]
       E[RAG Service\n`RAGService`]
       F[Application Facade\n`RAGApplicationService`]
     end
     subgraph Persistence
       G[(SQLite conversations.db)]
       H[(Chroma Vector Store)]
       I[((Processed Chunks + Checksums))]
     end
     subgraph External
       J[Groq / LLM Provider]
       K[HuggingFace Embeddings]
     end

   A -->|REST / WebSocket| B
   B --> C
   B -->|Uploads| D
   B -->|Query| E
   D -->|Async Jobs| F
   E -->|Warmup + Query| F
   F --> G
   D --> H
   D --> I
   E --> H
   E --> J
   D --> K

Execution Sequence
------------------

1. **Frontend** dispatches document ingestion or chat messages via REST (`/ingest`, `/query`) or WebSocket (`/ws/chat`).
2. **API layer** performs validation with `QueryRequest` and structured logging, then delegates to `RAGApplicationService`.
3. **Ingestion pipeline** persists uploads, deduplicates content with SHA-256 checksums, and rebuilds vector indexes using `Chroma.from_documents`.
4. **Retrieval layer** performs weighted semantic/BM25 retrieval using `HybridRetriever` or conversation-aware `AdvancedRetriever`.

Key Modules
-----------

* **`src/api.py`** – FastAPI entrypoints, exception handlers, WebSocket flow control, and lifecycle warmup.
* **`src/services/ingestion_service.py`** – Upload staging, job persistence, checksum-based cache hits, and vector store rebuild.
* **`src/services/rag_service.py`** – Conversation persistence, chain warmup, fallback pipeline, and response enrichment.
* **`src/llm.py`** – Provider registry, health checks, and the `EnhancedRAGChain` implementation with metrics integration.
* **`src/embed_store.py`** – Embedding backend abstraction, configuration diffing, and Chroma store helpers.
* **`src/middleware/observability.py`** – Prometheus metrics, structured request logs, and error counters.
* **`src/config.py`** – Centralized Pydantic configuration with environment + YAML precedence.

The architecture is designed so that each layer can evolve independently (e.g., swapping embedding providers or retrievers) while preserving a consistent API contract and operational footprint.
