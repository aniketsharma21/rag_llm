Overview
========

The `rag_llm` project delivers an enterprise-grade Retrieval-Augmented Generation (RAG) stack with a FastAPI backend, a modern React frontend, and extensive observability. This reference targets senior engineers who need to deploy, extend, or audit the system in production.

Key Capabilities
----------------

* **Async ingestion service** – `src/services/ingestion_service.py` persists uploads, tracks SHA-256 checksums, and enqueues background processing through `AsyncTaskQueue`.
* **Hybrid retrieval** – `src/retrieval.py` combines semantic similarity and BM25 scoring with per-request fallbacks and retrieval telemetry.
* **Context-aware prompting** – `src/prompt_templates.py` provides six specialized templates with automatic selection via `PromptManager.select_template_by_query_type()`.
* **Enhanced RAG chain** – `src/llm.py` defines `EnhancedRAGChain` with conversation persistence hooks, superscript citation formatting, and confidence scoring.
* **Operationally ready API** – `src/api.py` exposes REST and WebSocket interfaces, structured logging, and Prometheus-friendly metrics via `src/middleware/observability.py`.
* **Composable persistence layer** – `src/db/models.py` and `src/db/repositories/` model conversations, ingestion jobs, and documents for both async and sync access.

Subsystem Summary
-----------------

The pipeline is organized around the following high-level flows:

* **Ingestion** – Uploads are accepted at `POST /ingest`, deduplicated by checksum, processed by `process_document()` in `src/ingest.py`, and indexed into Chroma via `build_vector_store()`.
* **Retrieval** – Queries first warm the LLM and vector store, then execute through either `HybridRetriever` or `AdvancedRetriever` with streaming telemetry.
* **Generation** – Responses are assembled by `EnhancedRAGChain.query()` with prompt selection, LLM invocation (`ChatGroq` default), and post-processing to produce citations and paragraphs.
* **Presentation** – The frontend (see `frontend/src/components/EnhancedMessage.js`) renders summaries-first responses, document cards, and file preview modals driven by backend metadata.

Deployment Targets
------------------

* **Backend workers**: Python 3.9+ with dependencies listed in `requirements.txt` and `environment.yml` (for conda installs).
* **Frontend client**: Node.js 18+ executing the React application in `frontend/`.
* **Vector persistence**: ChromaDB persists under `chroma_store/` with model configuration tracking in `embedding_config.json`.

Use the remaining sections to deep dive into architecture, service-level APIs, operational guidance, and testing practices.
