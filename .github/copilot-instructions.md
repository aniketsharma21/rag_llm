## Quick orientation for coding agents

This project implements a Retrieval-Augmented Generation (RAG) application: a FastAPI backend that ingests documents, builds a Chroma vector store, and answers queries with a Groq LLM; a React frontend for chat/UX lives in `frontend/`.

Read these files first (high signal):
- `src/config.py` — central config, paths and where environment/YAML overrides are loaded.
- `src/ingest.py` — document loaders, checksum logic and chunking (uses `RecursiveCharacterTextSplitter`).
- `src/embed_store.py` — embedding model init (HF), Chroma persistence, and `get_retriever()`.
- `src/llm.py` — LLM initialization (Groq), `EnhancedRAGChain`, and failure modes (missing API key).
- `src/api.py` — REST + WebSocket entrypoints and streaming behavior.
- `src/cli.py` — async CLI with `ingest`, `query`, `status`, and `warmup` subcommands.
- `src/services/rag_service.py` — `RAGService` and `RAGApplicationService` that orchestrate query and ingestion flows.
- `src/services/ingestion_service.py` — document ingestion orchestration called by both API and CLI.

Big-picture points to keep in mind
- **Architecture**: API endpoints (`src/api.py`) delegate to a service layer (`src/services/`) which coordinates business logic. The CLI (`src/cli.py`) uses the same service layer. `src/main.py` is a thin delegate to `src/cli.py`.
- Ingestion uses checksum-based caching: `process_document()` writes chunks to `data/processed/*_chunks.pkl` and checksum files under `data/processed/checksums/`. If checksum matches, cached chunks are used.
- Embeddings use a local Hugging Face sentence-transformer (`sentence-transformers/all-MiniLM-L6-v2`) and will prefer CUDA if `torch.cuda.is_available()`.
- Vector store persistence directory: `CHROMA_PERSIST_DIR` → `./chroma_store` (configured in `src/config.py`). Code expects a persisted Chroma DB for queries.
- LLMs are provided by Groq and require `GROQ_API_KEY`; tests and runtime raise/skip when the key is missing.
- Prompt templates live in `src/prompts/` (e.g. `rag_prompts.yaml`) and are managed by `src/prompt_templates.py`.
- Observability: `src/middleware/observability.py` adds Prometheus metrics (request counts, duration histograms) and a `/metrics` endpoint.

Developer workflows & exact commands
- Create env and install (README also describes these): `conda env create -f environment.yml && conda activate dl_gpu_min`, or create a venv and `pip install -r requirements.txt`.
- Start backend (development):
```powershell
# Activate conda env on Windows PowerShell
conda activate dl_gpu_min
uvicorn src.api:app --reload
```
- Ingest a document via CLI (uses paths relative to `data/raw` if not absolute):
```powershell
python -m src.main ingest --file advanced-rag-interview-prep.pdf
```
- Query via CLI:
```powershell
python -m src.main query "What are the interview prep takeaways?"
```
- Check job status:
```powershell
python -m src.main status <job_id>
```
- Start frontend (separate terminal):
```powershell
cd frontend
npm install    # if dependencies are missing
npm start
```
- Run tests:
```powershell
pytest tests/
```

Project-specific conventions & patterns
- Checksums: ingestion will not reprocess files with an identical SHA-256 stored in `data/processed/checksums/` — if the checksum exists but chunk file is missing the code reprocesses.
- Vector store lifecycle: `build_vector_store(chunks)` creates/persists a Chroma DB; `load_vector_store()` expects the same persist directory.
- Service layer: `RAGApplicationService` composes `IngestionService` and `RAGService` and is the primary interface for both the API and CLI. The API uses service methods directly; the CLI calls the same methods through `_build_app_service()`.
- WebSocket: `src/api.py` implements task-based query processing, sends JSON messages of types `status`, `complete`, `error`, `ping`/`pong` — follow this format when adding real-time features.
- Database: `src/db/` contains async SQLAlchemy models (`models.py`), session management (`session.py`), and repository-pattern CRUD classes in `repositories/`.

Integration and external dependencies to watch
- Groq LLM via `langchain_groq` — requires `GROQ_API_KEY` in `.env` or `config.yaml`.
- ChromaDB for vector persistence — stored under `chroma_store/` in the repo root.
- Local HF sentence-transformer cached under `models_cache/` — embedding initialization uses `cache_folder=MODELS_CACHE_DIR`.
- Frontend proxies API requests to `http://localhost:8000` (see `frontend/package.json` `proxy` field).

CI/CD
- GitHub Actions workflow `docs.yml` deploys Sphinx documentation to GitHub Pages on pushes to `master`.

When editing code, run these quick sanity checks
1. Lint / type: run `mypy` (project has mypy in dev deps) and `black` for formatting.
2. Unit tests: `pytest tests/` (LLM tests skip if `GROQ_API_KEY` is unset).
3. Smoke-test endpoints: start uvicorn and hit `GET /health` and `POST /query` (or use the frontend).

If you change ingestion or embeddings be aware:
- Chunk size / overlap defaults are defined in `src/config.py` via YAML overrides; updating YAML or env should be reflected there.
- Changing embedding model name or device selection requires validating `models_cache/` usage and that the `HuggingFaceEmbeddings` constructor arguments are compatible.

Where to look for more context
- `README.md` — user-level quickstart and setup.
- `tests/` — examples of expected behavior (see `test_ingest.py`, `test_llm_enhanced.py`).
- `docs/` — Sphinx-based technical documentation.
