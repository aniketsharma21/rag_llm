# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-09-15
### Added
- Initial release of the enterprise-ready RAG pipeline.
- Modular codebase: `config.py`, `ingest.py`, `embed_store.py`, `llm.py`, `main.py`.
- Centralized configuration and logging.
- Document ingestion and chunking with checksum-based change detection.
- Embedding and persistent vector store using ChromaDB and HuggingFace models.
- LLM integration via Groq API.
- CLI for indexing and querying documents.
- Support for PDF, DOCX, and TXT files.
- Example prompts and YAML-based prompt configuration.
- Comprehensive README and improved docstrings for all modules.

