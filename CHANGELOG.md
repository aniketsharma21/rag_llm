# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Frontend React application with chat interface
- FastAPI backend with WebSocket support
- Document upload and management UI
- Real-time chat functionality
- Source attribution for answers
- Comprehensive API documentation
- Improved error handling and logging
- Environment configuration examples
- Development and production deployment guides
- Integrated `react-router-dom` for frontend routing (2025-09-22)

### Changed
- Updated project structure for better organization
- Enhanced documentation and README
- Improved error messages and validation
- Optimized build process
- Updated dependencies to latest stable versions
- Enhanced UI and UX in the React frontend: improved sidebar, navigation, and chat/document management (2025-09-22)

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
