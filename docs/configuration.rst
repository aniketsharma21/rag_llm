Configuration
=============

The application centralizes configuration in `src/config.py` using `AppSettings`, merging `.env`, `config.yaml`, and hard-coded defaults.

Configuration Sources
---------------------

1. `.env` – Secrets and per-environment overrides (highest precedence).
2. `config.yaml` – Non-secret defaults committed to the repo (medium precedence).
3. Code defaults – Fallback constants embedded in `AppSettings` (lowest precedence).

Environment Variables
---------------------

Key environment variables expected in `.env`:

.. code-block:: bash
   :caption: `.env` example

   GROQ_API_KEY=your_groq_api_key
   OPENAI_API_KEY=optional_openai_key
   LLM_PROVIDER=groq
   LLM_MODEL=llama-3.1-8b-instant
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=150

YAML Configuration
------------------

`config.yaml` supplements non-secret defaults. Example:

.. code-block:: yaml
   :caption: `config.yaml`

   llm_provider: groq
   llm_model: llama-3.1-8b-instant
   llm_temperature: 0.1
   llm_max_output_tokens: 2048
   retriever_semantic_weight: 0.7
   retriever_keyword_weight: 0.3
   top_k: 5
   embedding_backend: huggingface
   embedding_model: all-MiniLM-L6-v2

Programmatic Access
-------------------

`AppSettings` exposes strongly typed properties; downstream modules import module-level constants (e.g., `LLM_MODEL`, `RETRIEVER_SEMANTIC_WEIGHT`) for convenience.

.. code-block:: python
   :caption: `src/config.py`

   settings = get_settings()

   LLM_MODEL = settings.llm_model
   RETRIEVER_SEMANTIC_WEIGHT = settings.retriever_semantic_weight
   RETRIEVER_KEYWORD_WEIGHT = settings.retriever_keyword_weight

    @computed_field(return_type=str)
    def chroma_persist_dir(self) -> str:
        return str(self.base_dir / "chroma_store")

Embedding Configuration Drift
-----------------------------

`src/embed_store.py` persists the embedding signature to ``chroma_store/embedding_config.json``. On startup `load_vector_store()` compares this signature to the active settings, logging warnings when drift is detected and re-ingestion is required.

Database URLs
-------------

`AppSettings.database_url_sync` and `.database_url_async` derive SQLite defaults pointing to ``conversations.db``. Override `DATABASE_URL` in `.env` to point to PostgreSQL or other backends; async URLs automatically swap `sqlite:///` for `sqlite+aiosqlite:///` when necessary.

Cache Directories
-----------------

* ``data/raw/`` – Raw uploads persisted by ingestion service.
* ``data/processed/`` – Pickled chunk payloads.
* ``chroma_store/`` – Vector store persistence and embedding config.
* ``models_cache/`` – HuggingFace model cache controlled by `MODELS_CACHE_DIR`.

Changing any embedding- or retriever-related parameter warrants re-running ingestion to maintain consistent embeddings.
