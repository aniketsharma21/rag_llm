API Reference
=============

This section documents the FastAPI surface area, including request/response schemas, WebSocket semantics, and representative payloads.

REST API
--------

.. _api-health:

**GET /health**
~~~~~~~~~~~~~~~

Checks the health status of the service and its dependencies, including connectivity to the LLM provider.

* **Response Model**: `HealthResponse`

.. code-block:: json
   :caption: Example Health Check Response

   {
     "status": "healthy",
     "model": "llama-3.1-8b-instant",
     "version": "0.2.0",
     "timestamp": "2025-10-07T01:40:00Z"
   }

If a dependency is unavailable, it returns a `503 Service Unavailable`.

.. _api-ingest:

**POST /ingest**
~~~~~~~~~~~~~~~~~

Uploads and processes a document for ingestion into the RAG pipeline.

* **Request**: `multipart/form-data` with a single `file` field.
* **Response Model**: `IngestResponse`

.. code-block:: json
   :caption: Example Ingestion Response

   {
     "job_id": "8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793",
     "status": "queued",
     "message": "Document 'document.pdf' received. Processing has started."
   }

.. _api-status:

**GET /status/{job_id}**
~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves the status of a specific ingestion job.

* **Path Parameter**: `job_id` (string)
* **Response Model**: `JobStatusResponse`

Common status values include `queued`, `processing`, `completed`, `skipped`, and `failed`.

.. code-block:: json
   :caption: Example Job Status Response

   {
     "job_id": "8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793",
     "file_name": "document.pdf",
     "status": "completed",
     "message": "Document processed successfully",
     "details": {
       "chunks_count": 42,
       "document_id": 12
     },
     "created_at": "2025-10-03T02:35:41.352896",
     "updated_at": "2025-10-03T02:37:12.604401"
   }

.. _api-query:

**POST /query**
~~~~~~~~~~~~~~~

Submits a query to the RAG pipeline for a non-streaming response.

* **Request Model**: `QueryRequest`
* **Response Model**: `QueryResponse`

.. code-block:: json
   :caption: Representative Query Response

   {
     "answer": "...",
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

.. _api-files:

**GET /files**
~~~~~~~~~~~~~~

Lists all ingested documents with their metadata.

* **Response**: A JSON object containing a list of files.

.. _api-files-preview:

**GET /files/preview/{filename}**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Streams a sanitized PDF preview of a specific document, suitable for embedding in a frontend modal.

* **Path Parameter**: `filename` (string)

WebSocket API
-------------

**GET /ws/chat**
~~~~~~~~~~~~~~~~~

Establishes a WebSocket connection for real-time, streaming chat.

.. mermaid::

   sequenceDiagram
       participant Client
       participant Server

       Client->>Server: Establishes WebSocket connection
       Server-->>Client: Connection acknowledged

       Client->>Server: Sends query message (JSON)
       Server-->>Client: Responds with status update (e.g., "processing")
       Server-->>Client: Streams answer chunks
       Server-->>Client: Sends source documents
       Server-->>Client: Sends final message

       Client->>Server: Sends stop message (optional)
       Server-->>Client: Stops generation and closes stream

The client sends a JSON payload containing the `question`, an optional `chat_history` array, and an optional `conversation_id`. The server responds with a series of messages, including status updates, answer chunks, source documents, and a final message to indicate the end of the stream.

Error Handling
--------------

Custom exceptions defined in `src/exceptions.py` are mapped to structured JSON error responses.

.. list-table:: Error Mappings
   :header-rows: 1
   :widths: 30 15 55

   * - Exception
     - HTTP Status
     - Description
   * - DocumentProcessingError
     - 422
     - Error processing an uploaded document
   * - VectorStoreError
     - 500
     - Error during vector store operations
   * - LLMError
     - 503
     - Error from the LLM provider
   * - AuthenticationError
     - 401
     - Invalid or missing authentication credentials
   * - RateLimitError
     - 429
     - Rate limit exceeded
   * - ValidationError
     - 400
     - Invalid request parameters
   * - NotFoundError
     - 404
     - The requested resource was not found
   * - ConversationError
     - 400
     - Error in conversation-related operations

All error responses follow this standard format:

.. code-block:: json
   :caption: Standard Error Response Format

   {
     "error": {
       "code": "ERROR_CODE",
       "message": "A human-readable error message.",
       "details": {
         "field_name": "Additional error details, if applicable."
       },
       "request_id": "A unique ID for the request."
     }
   }
