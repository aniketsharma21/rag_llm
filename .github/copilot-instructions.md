## Quick orientation for coding agents

This project implements a Retrieval-Augmented Generation (RAG) application: a FastAPI backend that ingests documents, builds a Chroma vector store, and answers queries with a Groq LLM; a React frontend for chat/UX lives in `frontend/`.

Read these files first (high signal):
- `src/config.py` — central config, paths and where environment/YAML overrides are loaded.
- `src/ingest.py` — document loaders, checksum logic and chunking (uses `RecursiveCharacterTextSplitter`).
- `src/embed_store.py` — embedding model init (HF), Chroma persistence, and `get_retriever()`.
- `src/llm.py` — LLM initialization (Groq) and failure modes (missing API key).
- `src/api.py` — REST + WebSocket entrypoints and streaming behavior.
- `src/main.py` — CLI commands (`index`, `query`) showing end-to-end chains and prompt usage.

Big-picture points to keep in mind
- Ingestion uses checksum-based caching: `process_document()` writes chunks to `data/processed/*_chunks.pkl` and checksum files under `data/processed/checksums/`. If checksum matches, cached chunks are used.
- Embeddings use a local Hugging Face sentence-transformer (`sentence-transformers/all-MiniLM-L6-v2`) and will prefer CUDA if `torch.cuda.is_available()`.
- Vector store persistence directory: `CHROMA_PERSIST_DIR` → `./chroma_store` (configured in `src/config.py`). Code expects a persisted Chroma DB for queries.
- LLMs are provided by Groq and require `GROQ_API_KEY`; tests and runtime raise/skip when the key is missing.
- Prompt templates live in `src/prompts/` (e.g. `rag_prompts.yaml`) and are loaded by the CLI and API chains.

Developer workflows & exact commands
- Create env and install (README also describes these): create a venv, activate it, then `pip install -r requirements.txt`.
- Start backend (development):
```powershell
# Activate venv on Windows PowerShell
.\venv\Scripts\Activate.ps1
uvicorn src.api:app --reload
```
- Index a document via CLI (uses paths relative to `data/raw` if not absolute):
```powershell
python -m src.main index --file advanced-rag-interview-prep.pdf
```
- Query via CLI:
```powershell
python -m src.main query "What are the interview prep takeaways?"
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
- Vector store lifecycle: `build_vector_store(chunks)` creates/persists a Chroma DB; `load_vector_store()` expects the same persist directory and recreates the retriever with `as_retriever(search_kwargs={"k": TOP_K})`.
- Prompt chaining: both `src/main.py` and `src/api.py` build small runnable chains where a retriever provides context and a PromptTemplate/ChatPromptTemplate is combined with the LLM. Look at `rag_chain` constructions to mirror behavior.
- WebSocket: `src/api.py` implements a streaming generator pattern (async for chunks in `rag_chain.astream`) and sends JSON messages of types `chunk`, `complete`, `status`, `error` — follow this format when adding real-time features.

Integration and external dependencies to watch
- Groq LLM via `langchain_groq` — requires `GROQ_API_KEY` in `.env` or `config.yaml`.
- ChromaDB for vector persistence — stored under `chroma_store/` in the repo root.
- Local HF sentence-transformer cached under `models_cache/` — embedding initialization uses `cache_folder=MODELS_CACHE_DIR`.
- Frontend proxies API requests to `http://localhost:8000` (see `frontend/package.json` `proxy` field).

When editing code, run these quick sanity checks
1. Lint / type: run `mypy` (project has mypy in dev deps) and `black` for formatting.
2. Unit tests: `pytest tests/` (LLM tests skip if `GROQ_API_KEY` is unset).
3. Smoke-test endpoints: start uvicorn and hit `GET /health` and `POST /query` (or use the frontend).

If you change ingestion or embeddings be aware:
- Chunk size / overlap defaults are defined in `src/config.py` via YAML overrides; updating YAML or env should be reflected there.
- Changing embedding model name or device selection requires validating `models_cache/` usage and that the `HuggingFaceEmbeddings` constructor arguments are compatible.

Where to look for more context
- `README.md` — user-level quickstart and setup.
- `tests/` — examples of expected behavior (see `test_ingest.py`, `test_llm.py`).

Questions for the repo owner (leave these as comments if unclear):
- Are there any CI steps or GitHub Actions that should run on PRs? (none found in the repo.)
- Preferred Windows dev workflow (PowerShell) vs. Unix shell for setup scripts (setup.sh is bash).

If anything here looks incomplete or you want more agent-level rules (style, testing thresholds, or PR checklist), tell me what to include and I will iterate.
