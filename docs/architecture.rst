Architecture
============

The platform is split into modular services wired together through shared configuration and observability primitives. This section highlights the runtime topology, data flows, and major components.

Runtime Topology
----------------

High-level service interaction diagram:

.. mermaid::
   :align: center
   :caption: Figure: System Architecture Overview

   %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#f0f0f0'}}}%%
   flowchart TD
       classDef client fill:#e1f5fe,stroke:#039be5,stroke-width:2px
       classDef api fill:#e8f5e9,stroke:#43a047,stroke-width:2px
       classDef service fill:#fff3e0,stroke:#fb8c00,stroke-width:2px
       classDef storage fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px
       classDef external fill:#ffebee,stroke:#e53935,stroke-width:2px

       subgraph Client["Client"]
           A[React Frontend]:::client
       end

       subgraph API_Layer["API Layer"]
           B[FastAPI Application<br><small>src/api.py</small>]:::api
           C[Observability Middleware<br><small>src/middleware/observability.py</small>]:::api
       end

       subgraph Services["Services"]
           D[Ingestion Service<br><code>IngestionService</code>]:::service
           E[RAG Service<br><code>RAGService</code>]:::service
           F[Application Facade<br><code>RAGApplicationService</code>]:::service
       end

       subgraph Persistence["Persistence"]
           G[(SQLite<br>conversations.db)]:::storage
           H[(Chroma<br>Vector Store)]:::storage
           I[Processed Chunks<br>+ Checksums]:::storage
       end

       subgraph External["External Services"]
           J[Groq / LLM Provider]:::external
           K[HuggingFace<br>Embeddings]:::external
       end

       %% Connections with arrows
       A <-->|REST / WebSocket| B
       B --> C
       B -->|Uploads| D
       B -->|Query| E
       D -->|Async Jobs| F
       E -->|Warmup + Query| F
       F <--> G
       D <--> H
       D --> I
       E <--> H
       E <--> J
       D <--> K

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
