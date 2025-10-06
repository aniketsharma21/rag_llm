Configuration
=============

The application centralizes configuration in `src/config.py` using `AppSettings`, which merges settings from `.env` files, `config.yaml`, and hard-coded defaults.

Configuration Precedence
------------------------

The settings are loaded in the following order of precedence (from highest to lowest):

.. mermaid::

   graph TD
       A[Environment Variables (.env)] --> B[config.yaml];
       B --> C[Code Defaults];

1.  **Environment Variables (`.env`)**: Secrets and environment-specific overrides. This has the highest precedence.
2.  **YAML Configuration (`config.yaml`)**: Non-secret defaults that can be committed to the repository. This has medium precedence.
3.  **Code Defaults**: Fallback constants embedded in the `AppSettings` class. This has the lowest precedence.

Key Configuration Settings
--------------------------

The following table details the most important configuration settings available in the `AppSettings` class:

.. list-table:: AppSettings Configuration
   :header-rows: 1
   :widths: 25 15 60

   * - Setting
     - Default
     - Description
   * - `llm_provider`
     - `groq`
     - The LLM provider to use (`groq` or `openai`).
   * - `llm_model`
     - `llama-3.1-8b-instant`
     - The specific LLM model to use.
   * - `llm_temperature`
     - `0.1`
     - The sampling temperature for the LLM.
   * - `llm_max_output_tokens`
     - `2048`
     - The maximum number of tokens to generate.
   * - `embedding_backend`
     - `huggingface`
     - The embedding backend to use (`huggingface`, `openai`, or `fake`).
   * - `embedding_model`
     - `all-MiniLM-L6-v2`
     - The specific embedding model to use.
   * - `chunk_size`
     - `1000`
     - The number of characters per text chunk.
   * - `chunk_overlap`
     - `150`
     - The number of characters to overlap between chunks.
   * - `retriever_semantic_weight`
     - `0.7`
     - The weight of the semantic search in the hybrid retriever.
   * - `retriever_keyword_weight`
     - `0.3`
     - The weight of the keyword search in the hybrid retriever.
   * - `retriever_k`
     - `5`
     - The number of documents to retrieve.
   * - `database_url_sync`
     - `sqlite:///conversations.db`
     - The synchronous database URL.
   * - `database_url_async`
     - `sqlite+aiosqlite:///conversations.db`
     - The asynchronous database URL.

Environment-Specific Configurations
---------------------------------

For different environments, you can create separate `.env` files (e.g., `.env.development`, `.env.production`). The application will automatically load the appropriate file based on the `APP_ENV` environment variable. If `APP_ENV` is not set, it defaults to `.env`.

For example, in a production environment, you might want to use a more robust database and a different LLM provider:

.. code-block:: bash
   :caption: .env.production

   APP_ENV=production
   GROQ_API_KEY=your_production_groq_api_key
   DATABASE_URL=postgresql://user:password@host:port/database

Embedding Configuration Drift
-----------------------------

`src/embed_store.py` persists the embedding signature to `chroma_store/embedding_config.json`. On startup, `load_vector_store()` compares this signature to the active settings, logging warnings when drift is detected and re-ingestion is required. This ensures that the vector store remains consistent with the current configuration.
