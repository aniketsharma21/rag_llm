# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-09
### Added
- Frontend React application with chat interface and Tailwind CSS styling
- FastAPI backend with WebSocket support for real-time streaming
- Document upload and management UI with drag & drop experience
- Real-time chat functionality with streaming summaries and detail paragraphs
- Source attribution for answers rendered as interactive document cards
- `/files` inventory API and `/files/preview/{filename}` PDF preview service
- Async ingest workflow with job status polling (`/ingest`, `/status/{job_id}`) and stop-generation support
- Service layer abstractions (`src/services/ingestion_service.py`, `src/services/rag_service.py`) decoupling API from business logic
- Async CLI (`src/cli.py`) with `ingest`, `query`, `status`, and `warmup` subcommands
- Middleware observability layer (`src/middleware/observability.py`) with Prometheus metrics
- Structured logging via `structlog` (`src/logging_config.py`) and domain-specific exception hierarchy (`src/exceptions.py`)
- Persistence layer (`src/db/`) with async SQLAlchemy models and repositories for conversations, documents, and ingest jobs
- Hybrid retrieval engine (`src/retrieval.py`): semantic + BM25 ensemble retriever with conversation-aware context selection
- Advanced prompt template system (`src/prompt_templates.py`) with automatic selection and context pruning
- Shared frontend configuration via React context (`frontend/src/context/ConfigContext.js`)
- Rich source cards with document-level aggregation, snippets, page ranges, and preview buttons
- Upload workbench with history, toast feedback, and inline PDF preview modals
- Comprehensive test coverage for services, CLI, database, retrieval, and embeddings
- Sphinx documentation site with GitHub Pages deployment workflow

### Changed
- Refactored project structure: extracted services, middleware, utils, and DB packages
- Updated dependencies to LangChain 0.3.x ecosystem with pinned version ranges
- Enhanced UI/UX: improved sidebar, navigation, chat/document management, and inline PDF previews
- Aggregated sources at document-level with cleaner assistant responses

### Removed
- Legacy `src/database.py` (replaced by `src/db/` package)
- Legacy `src/job_manager.py` (replaced by `src/services/task_queue.py`)
- Redundant `read_db.py` debug script
- Redundant `test_notebook.ipynb`
- Redundant `IMPROVEMENTS.md` (consolidated into CHANGELOG)
- Redundant `tests/test_llm.py` (subsumed by `tests/test_llm_enhanced.py`)

## [0.1.0] - 2025-09-15
### Added
- Initial release of the enterprise-ready RAG pipeline
- Modular codebase: `config.py`, `ingest.py`, `embed_store.py`, `llm.py`, `main.py`
- Centralized configuration and logging
- Document ingestion and chunking with checksum-based change detection
- Embedding and persistent vector store using ChromaDB and HuggingFace models
- LLM integration via Groq API
- CLI for indexing and querying documents
- Support for PDF, DOCX, and TXT files
- Example prompts and YAML-based prompt configuration

## [0.0.1] - 2025-09-01
### Added
- Project initialization
- Basic project structure
- Initial documentation
