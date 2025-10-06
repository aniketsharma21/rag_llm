Testing & Quality
==================

Automated tests verify ingestion logic, embedding configuration, and RAG orchestration. Execute the backend suite with ``pytest`` from the project root.

Unit Tests
----------

* **`tests/test_ingest.py`** – Validates checksum-based caching, missing file handling, and unsupported formats. Uses `tmp_path` fixtures and monkeypatching to isolate filesystem effects.
* **`tests/test_embed_store.py`** – Ensures embedding factory resolution, vector store persistence, and configuration drift warnings via `FakeEmbeddings`.
* **`tests/test_llm_enhanced.py`** – Exercises `EnhancedRAGChain` using dummy retrievers and LLMs to assert prompt invocation, citation formatting, and conversation memory behavior.

Example: Enhanced Chain Test
----------------------------

.. code-block:: python
   :caption: `tests/test_llm_enhanced.py`

   result = chain.query("What is hybrid retrieval?", k=2)

   assert dummy_llm.invocations == ["PROMPT"]
   assert result["answer"] == "Answer with citation ¹"
   assert result["template_used"] == "base"
   assert result["num_sources"] == len(sample_documents)

   sources = result["sources"]
   assert len(sources) == 1
   source_entry = sources[0]
   assert source_entry["citation"] == "¹"
   assert source_entry["metadata"]["page_numbers"] == [1, 2]

Coverage Targets
----------------

* Maintain coverage over ingestion edge cases and retrieval fallbacks.
* Add regression tests for new prompt templates or LLM providers using dummy adapters to avoid external dependencies.
* Integrate `pytest-asyncio` for coroutine-oriented tests (e.g., asynchronous service methods).

Continuous Integration
----------------------

Recommended pipeline stages:

1. **Lint** – Run `black`, `isort`, and `mypy` (already declared in `requirements.txt`).
2. **Test** – Invoke `pytest --maxfail=1` to detect regressions quickly.
3. **Build Docs** – Execute `sphinx-build -b html docs/ docs/_build/html` to surface documentation warnings.

Front-end testing is not part of this repository snapshot but should be added using React Testing Library for message rendering, upload flows, and WebSocket interactions.
