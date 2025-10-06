API Reference
=============

This section documents the FastAPI surface area, including request/response schemas, WebSocket semantics, and representative payloads.

REST Endpoints
--------------

`src/api.py` defines the primary REST endpoints. All responses are JSON and leverage structured logging plus Prometheus metrics.

`GET /health`
~~~~~~~~~~~~~

* **Purpose**: Validates LLM provider connectivity by invoking `get_llm()`.
* **Response model**: ``HealthResponse``

.. code-block:: json

   {
     "status": "healthy",
     "model": "llama-3.1-8b-instant"
   }

`POST /ingest`
~~~~~~~~~~~~~~

* **Consumes**: ``multipart/form-data`` with single ``file`` field.
* **Response model**: ``IngestResponse``

.. code-block:: json
   :caption: Example ingest response

   {
     "job_id": "8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793",
     "status": "queued",
     "message": "Document 'retention-policy.pdf' received. Processing has started."
   }

`GET /status/{job_id}`
~~~~~~~~~~~~~~~~~~~~~~

* **Response model**: ``JobStatusResponse``
* **Common status values**: ``queued``, ``processing``, ``completed``, ``skipped``, ``failed``

.. code-block:: json

   {
     "job_id": "8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793",
     "file_name": "retention-policy.pdf",
     "status": "completed",
     "message": "Document processed successfully",
     "details": {
       "chunks_count": 42,
       "document_id": 12
     },
     "created_at": "2025-10-03T02:35:41.352896",
     "updated_at": "2025-10-03T02:37:12.604401"
   }

`GET /files`
~~~~~~~~~~~~

Returns inventory metadata: name, size, upload date, and `previewUrl`. Data is sourced by `_get_files_inventory()` scanning ``data/raw/``.

`GET /files/preview/{filename}`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Streams the pre-sanitized PDF preview stored during ingestion. Suitable for embedding within frontend modals.

`POST /query`
~~~~~~~~~~~~~

* **Request model**: ``QueryRequest``
* **Response model**: ``QueryResponse``

.. code-block:: json
   :caption: Representative query response

   {
     "answer": "\u2026",
     "sources": [
       {
         "title": "Advanced RAG Playbook",
         "snippet": "Hybrid retrieval blends semantic similarity with BM25 scoring.",
         "confidence": 0.82,
         "metadata": {
           "page_numbers": [3, 4],
           "raw_file_path": "C:/Users/anike/PycharmProjects/rag_llm/data/raw/playbook.pdf"
         },
         "citation": "¹",
         "preview_url": "/files/preview/playbook.pdf"
       }
     ],
     "confidence_score": 0.82,
     "template_used": "analysis",
     "num_sources": 3
   }

WebSocket Interface
-------------------

Endpoint: ``/ws/chat``

Message flow:

1. Client sends JSON payload containing ``question``, optional ``chat_history`` array, and optional ``conversation_id``.
2. Server responds with status updates and answer chunks:

   * ``{"type": "status", "status": "processing"}``
   * ``{"type": "answer_chunk", "content": "Executive summary …"}``
   * ``{"type": "sources", "payload": [...]}``
   * ``{"type": "final", "payload": {...}}``

Stop generation is honored via messages matching ``{"type": "stop"}``, which cancel the currently running task in `ConnectionManager`.

Exception Handling
------------------

Custom exceptions in `src/exceptions.py` map to structured JSON responses:

* **DocumentProcessingError** → HTTP 422 with detail payload.
* **VectorStoreError** → HTTP 500 indicating vector operations failed.
* **LLMError** → HTTP 503 with upstream provider diagnostics.
* **ValidationError** → HTTP 400 when request payloads fail business validation.

Refer to the `/metrics` endpoint supplied by `setup_observability()` for Prometheus-formatted counters and histograms covering request latency, retrieval duration, and token usage.
