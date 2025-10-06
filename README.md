# 🚀 Enterprise-Ready RAG Pipeline

A robust, modular, and production-oriented framework for building Retrieval-Augmented Generation (RAG) applications. This project features a FastAPI backend and a modern React frontend styled with Tailwind CSS, designed for enterprise use cases with a focus on configuration-driven design, cost-efficiency, and extensibility.

## 🌟 Features

### Backend
- **Document Processing**: Handles 8+ formats (PDF, DOCX, TXT, MD, CSV, JSON, PPTX, XLSX) with smart chunking, checksum validation, and graceful error handling via custom exceptions.
- **Vector & Hybrid Retrieval**: Builds persistent ChromaDB stores and combines semantic search with BM25 keyword ranking through an ensemble retriever with configurable weights.
- **LLM Orchestration**: Integrates Groq-hosted models alongside HuggingFace embeddings, advanced prompt templates, conversation memory, and confidence scoring.
- **API & Infrastructure**: FastAPI layer with REST and WebSocket streaming, structured logging (via `structlog`), database-backed conversation persistence, and resilient fallbacks.
- **Async Ingest Workflow**: `/ingest` returns `job_id`s, `/status/{job_id}` provides progress updates, and post-ingest payloads automatically refresh vector stores.
- **Document Services**: `/files` lists uploaded sources (with metadata and preview URLs) and `/files/preview/{filename}` streams sanitized PDF previews for inline viewing.

### Frontend
- **Modern React Interface**: Responsive React + Tailwind UI with polished animations, mobile-first layouts, and accessibility-focused interactions.
- **Real-time Chat**: Interactive WebSocket streaming with executive-summary-first delivery, enhanced message actions (copy, share, timestamps), and improved loading states.
- **Intuitive Workflows**: Drag & drop uploads, advanced document search in the sidebar, rich document-level source cards, toast notifications, and inline PDF preview modals.
- **Customizable**: Light/dark themes, configurable model settings, and modular components ready for enterprise branding.

## ✨ Recent Enhancements

-   **Hybrid Retrieval Engine** (`src/retrieval.py`): Semantic + BM25 ensemble retriever with conversation-aware context selection.
-   **Advanced Prompting** (`src/prompt_templates.py`): Six specialized templates with automatic selection, context pruning, and source-aware formatting.
-   **Structured Logging & Exceptions** (`src/logging_config.py`, `src/exceptions.py`): JSON logs, contextual metadata, and domain-specific exception hierarchy.
-   **Persistence Layer** (`src/database.py`): SQLAlchemy models for conversation/document history with CRUD helpers.
-   **Streaming UX** (`src/api.py`, `frontend/src/App.js`): Summaries stream before detail paragraphs, stop-generation is honored immediately, and chat messages merge role-tagged chunks automatically.
-   **Service Layer Abstractions** (`src/services/ingestion_service.py`, `src/services/rag_service.py`): API endpoints now orchestrate ingestion and query flows through dedicated services with improved error handling and async patterns.
-   **Shared Frontend Configuration** (`frontend/src/context/ConfigContext.js`): Centralized WebSocket/API configuration exposed through a React context provider, simplifying consumption in `App.js` and upload/chat components.
-   **Test Coverage** (`tests/test_ingestion_service.py`, `tests/test_rag_service.py`): Added focused unit suites for the new services and updated ingestion tests to rely on temporary fixtures instead of cached artifacts.
-   **Rich Source Cards** (`frontend/src/components/EnhancedMessage.js`): Document-level aggregation with snippets, page ranges, relevance hints, preview buttons, and accessibility tweaks.
-   **Upload Workbench** (`frontend/src/components/EnhancedFileUpload.js` + `/files` endpoint): Drag & drop uploads with history, toast feedback, and inline PDF preview modals backed by sanitized download URLs.

## 🏗️ Project Structure

```
rag_llm/
├── chroma_store/          # Vector database storage
├── data/                  # Document storage (raw and processed)
├── frontend/              # React + Tailwind CSS frontend
├── src/                   # Python backend source code
│   ├── api.py             # FastAPI application (REST + WebSocket)
│   ├── config.py          # Configuration settings & environment loading
│   ├── database.py        # Conversation/document persistence layer
│   ├── embed_store.py     # Vector store operations
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── ingest.py          # Document processing & loaders
│   ├── llm.py             # LLM orchestration and prompt routing
│   ├── logging_config.py  # Structured logging setup
│   ├── prompt_templates.py# Advanced prompt templates & manager
│   ├── retrieval.py       # Hybrid retriever implementations
│   └── main.py            # CLI entry point for indexing/querying
├── tests/                 # Test files
├── environment.yml        # Conda environment definition
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
-   Python 3.9+
-   Node.js 18+ and npm 9+
-   Conda (recommended for Python environment management)

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd rag_llm
    ```

2.  **Set Up the Backend**
    -   **Create Environment**:
        ```bash
        # Using conda (recommended)
        conda env create -f environment.yml
        conda activate rag_llm

        # Or with a standard virtual environment
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        pip install -r requirements.txt -r requirements-clean.txt
        ```
    -   **Configure Environment Variables**: Runtime configuration is powered by the [`AppSettings`](src/config.py) Pydantic settings object, which merges `.env` values with optional `config.yaml` defaults. Create a `.env` file in the project root to supply required secrets.
        ```env
        # Required for LLM integration
        GROQ_API_KEY=your_groq_api_key_here

        # Optional: For using OpenAI models
        OPENAI_API_KEY=your_openai_key_here
        ```
        You can also populate `config.yaml` with non-secret defaults (for example, `chunk_size`, `embedding_model`). Both files are loaded automatically during startup.

3.  **Set Up the Frontend**
    ```bash
    cd frontend
    npm install
    cd ..
    ```

4.  **(Optional) Seed Documents**
    Place PDFs and other supported files under `data/raw/` or upload from the UI. The backend will create previews under `/files/preview/{filename}` automatically.

## 🖥️ Usage

1.  **Start the Backend Server**
    From the project root, run:
    ```bash
    uvicorn src.api:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

2.  **Start the Frontend Development Server**
    In a **new terminal**, from the project root, run:
    ```bash
    cd frontend
    npm start
    ```
    The web interface will be available at `http://localhost:3000`.

3.  **Upload Documents and Chat**
    -   Navigate to the "Upload Documents" page to drag & drop new files, monitor ingest status, and open the preview modal via the eye icon.
    -   Use the "New Chat" view to ask questions; summaries stream first, followed by grouped detail bullets and document cards.
    -   Source cards provide quick "Preview" and "Open" options using the backend preview service.

### Using the Backend CLI (Optional)

You can also interact with the RAG pipeline directly via the command line.

-   **Index a document**:
    ```bash
    python -m src.main index --file path/to/your/document.pdf
    ```
-   **Query the system**:
    ```bash
    python -m src.main query "Your question here"
    ```

## 🧪 Testing

To run the backend test suite, use `pytest` from the project root:
```bash
pytest
```

## 📡 API Reference

* **`POST /ingest`** — Accepts multipart uploads, responds with `job_id` for async processing.
* **`GET /status/{job_id}`** — Returns ingest progress, completion state, and diagnostics.
* **`GET /files`** — Lists uploaded documents with size, timestamps, and preview URLs.
* **`GET /files/preview/{filename}`** — Streams the sanitized PDF preview used by the frontend modal.
* **`POST /query`** — REST query interface (non-streaming fallback).
* **`/ws/chat`** — WebSocket endpoint supporting streaming replies, stop-generation, and feedback events.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

This project is distributed under the MIT License. See the `LICENSE` file for more information.