API Reference
=============

This section documents the FastAPI surface area, including request/response schemas, WebSocket semantics, and representative payloads.

REST API
--------

.. _api-health:

Health Check
~~~~~~~~~~~~

.. http:get:: /health

   Check the health status of the service and its dependencies.

   **Response**:

   .. list-table:: Response Fields
      :header-rows: 1
      :widths: 20 10 70

      * - Field
        - Type
        - Description
      * - status
        - string
        - Service status (``healthy`` or ``unhealthy``)
      * - model
        - string
        - Currently loaded LLM model name
      * - version
        - string
        - API version

   **Example Request**:

   .. code-block:: http

      GET /health HTTP/1.1
      Host: api.example.com
      Accept: application/json

   **Example Response**:

   .. code-block:: json
      :caption: Health Check Response

      {
        "status": "healthy",
        "model": "llama-3.1-8b-instant",
        "version": "0.2.0",
        "timestamp": "2025-10-07T01:40:00Z"
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 503
        - SERVICE_UNAVAILABLE
        - One or more dependencies are not available

.. _api-ingest:

Document Ingestion
~~~~~~~~~~~~~~~~~

.. http:post:: /ingest

   Upload and process a document for ingestion into the RAG pipeline.

   .. note::
      The maximum file size is 50MB. Supported formats: PDF, DOCX, TXT, MD, CSV, PPTX, XLSX.

   **Request Headers**:

   .. list-table:: Headers
      :header-rows: 1
      :widths: 20 80

      * - Header
        - Description
      * - Content-Type
        - Must be ``multipart/form-data``
      * - X-File-Name
        - (Optional) Custom filename

   **Form Data**:

   .. list-table:: Form Fields
      :header-rows: 1
      :widths: 20 10 70

      * - Field
        - Type
        - Description
      * - file
        - file
        - The file to upload
      * - chunk_size
        - integer
        - (Optional) Size of text chunks (default: 1000)
      * - chunk_overlap
        - integer
        - (Optional) Overlap between chunks (default: 200)

   **Response**:

   .. list-table:: Response Fields
      :header-rows: 1
      :widths: 20 10 70

      * - Field
        - Type
        - Description
      * - job_id
        - string
        - Unique identifier for the ingestion job
      * - status
        - string
        - Current status of the job
      * - message
        - string
        - Human-readable status message
      * - file_name
        - string
        - Name of the uploaded file
      * - file_size
        - integer
        - Size of the file in bytes
      * - created_at
        - string
        - ISO 8601 timestamp of job creation

   **Example Request**:

   .. code-block:: http

      POST /ingest HTTP/1.1
      Host: api.example.com
      Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
      Authorization: Bearer your-api-key-here

      ------WebKitFormBoundary7MA4YWxkTrZu0gW
      Content-Disposition: form-data; name="file"; filename="document.pdf"
      Content-Type: application/pdf

      <file content here>
      ------WebKitFormBoundary7MA4YWxkTrZu0gW--

   **Example Response**:

   .. code-block:: json
      :caption: Successful Ingestion Response

      {
        "job_id": "8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793",
        "status": "queued",
        "message": "Document 'document.pdf' received. Processing has started.",
        "file_name": "document.pdf",
        "file_size": 1234567,
        "created_at": "2025-10-07T01:42:00Z"
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 400
        - INVALID_FILE_TYPE
        - Unsupported file type
      * - 413
        - FILE_TOO_LARGE
        - File exceeds maximum size
      * - 401
        - UNAUTHORIZED
        - Missing or invalid API key
      * - 429
        - RATE_LIMIT_EXCEEDED
        - Too many requests

.. _api-status:

Job Status
~~~~~~~~~~

.. http:get:: /status/{job_id}

   Get the status of an ingestion job.

   **Path Parameters**:

   .. list-table:: Path Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - job_id
        - string
        - The ID of the job to check

   **Response**:

   .. list-table:: Response Fields
      :header-rows: 1
      :widths: 20 10 70

      * - Field
        - Type
        - Description
      * - job_id
        - string
        - Unique identifier for the job
      * - status
        - string
        - Current status (``queued``, ``processing``, ``completed``, ``failed``, ``skipped``)
      * - progress
        - number
        - Completion percentage (0-100)
      * - file_name
        - string
        - Name of the processed file
      * - created_at
        - string
        - ISO 8601 timestamp of job creation
      * - updated_at
        - string
        - ISO 8601 timestamp of last update
      * - error
        - object
        - Error details (if any)

   **Example Request**:

   .. code-block:: http

      GET /status/8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793 HTTP/1.1
      Host: api.example.com
      Accept: application/json
      Authorization: Bearer your-api-key-here

   **Example Response**:

   .. code-block:: json
      :caption: Job Status Response

      {
        "job_id": "8f4c5eaa-7f4d-4de9-9e3d-c17b0a2bb793",
        "status": "completed",
        "progress": 100,
        "file_name": "document.pdf",
        "created_at": "2025-10-07T01:42:00Z",
        "updated_at": "2025-10-07T01:43:15Z",
        "chunks_processed": 24,
        "vector_count": 24
      }

   **Error Responses**:

   .. list-table:: Error Responses
      :header-rows: 1
      :widths: 15 15 70

      * - Status Code
        - Error Code
        - Description
      * - 404
        - JOB_NOT_FOUND
        - The specified job ID was not found
      * - 401
        - UNAUTHORIZED
        - Missing or invalid API key

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

WebSocket Interface
------------------

.. _ws-chat:

Chat
~~~~

.. http:websocket:: /ws/chat

   Establish a WebSocket connection for real-time chat with the RAG system.

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - conversation_id
        - string
        - (Optional) Existing conversation ID to continue
      * - model
        - string
        - (Optional) Override default model
      * - temperature
        - float
        - (Optional) Sampling temperature (0.0 to 2.0)

   **Message Format (Client → Server)**:

   .. code-block:: json

      {
        "type": "query",
        "query": "Your question here",
        "conversation_id": "uuid-string-or-null",
        "stream": true,
        "sources": true
      }

   **Message Format (Server → Client)**:

   .. code-block:: json
      :caption: Stream Update

      {
        "type": "chunk",
        "content": "streaming text",
        "conversation_id": "uuid-string",
        "message_id": "uuid-string"
      }

      {
        "type": "sources",
        "sources": [
          {
            "title": "Document Title",
            "url": "#page=3",
            "content": "Relevant text excerpt...",
            "score": 0.87
          }
        ]
      }

      {
        "type": "complete",
        "message_id": "uuid-string",
        "conversation_id": "uuid-string"
      }

   **Error Responses**:

   .. list-table:: Error Messages
      :header-rows: 1
      :widths: 20 20 60

      * - Status Code
        - Error Code
        - Description
      * - 1008
        - INVALID_MESSAGE_FORMAT
        - Malformed message format
      * - 1011
        - PROCESSING_ERROR
        - Error generating response
      * - 1008
        - RATE_LIMIT_EXCEEDED
        - Too many requests

   **Example Flow**:

   .. code-block:: text

      Client: ws://api.example.com/ws/chat?conversation_id=123
      Server: (connection established)
      
      Client: {"type":"query","query":"What is RAG?","stream":true}
      Server: {"type":"chunk","content":"RAG (Retrieval-Augmented Generation)",...}
      Server: {"type":"chunk","content":" combines retrieval of documents..."}
      Server: {"type":"sources","sources":[...]}
      Server: {"type":"complete",...}

Additional Endpoints
-------------------

List Files
~~~~~~~~~~

.. http:get:: /files

   List all ingested documents with metadata.

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - limit
        - integer
        - Maximum number of files to return (default: 100)
      * - offset
        - integer
        - Pagination offset (default: 0)

   **Response**:

   .. code-block:: json

      {
        "files": [
          {
            "id": "uuid",
            "name": "document.pdf",
            "size": 1234567,
            "status": "processed",
            "ingested_at": "2025-10-07T01:42:00Z",
            "metadata": {
              "pages": 10,
              "chunks": 15,
              "file_type": "application/pdf"
            }
          }
        ],
        "total": 1,
        "limit": 100,
        "offset": 0
      }

Document Preview
~~~~~~~~~~~~~~~

.. http:get:: /files/preview/{file_id}

   Get preview content of a specific document.

   **Path Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - file_id
        - string
        - ID of the file to preview

   **Query Parameters**:

   .. list-table:: Parameters
      :header-rows: 1
      :widths: 20 10 70

      * - Parameter
        - Type
        - Description
      * - page
        - integer
        - Page number (for paginated formats)
      * - limit
        - integer
        - Number of lines/chunks to return

   **Response**:

   .. code-block:: json

      {
        "id": "uuid",
        "name": "document.pdf",
        "content": "Extracted text content...",
        "page": 1,
        "total_pages": 10,
        "metadata": {
          "file_type": "application/pdf",
          "size": 1234567,
          "extracted_at": "2025-10-07T01:42:30Z"
        }
Error Handling
-------------

Custom exceptions in `src/exceptions.py` map to structured JSON responses:

.. list-table:: Error Mappings
   :header-rows: 1
   :widths: 30 15 55

   * - Exception
     - HTTP Status
     - Description
   * - DocumentProcessingError
     - 422
     - Error processing uploaded document
   * - VectorStoreError
     - 500
     - Error in vector store operations
   * - LLMError
     - 503
     - Error from LLM provider
   * - AuthenticationError
     - 401
     - Invalid or missing authentication
   * - RateLimitError
     - 429
     - Rate limit exceeded
   * - ValidationError
     - 400
     - Invalid request parameters
   * - NotFoundError
     - 404
     - Requested resource not found
   * - ConversationError
     - 400
     - Error in conversation operations

All error responses follow this format:

.. code-block:: json

   {
     "error": {
       "code": "ERROR_CODE",
       "message": "Human-readable error message",
       "details": {
         "field_name": "Additional error details"
       },
       "request_id": "uuid"
     }
   }
* **ValidationError** → HTTP 400 when request payloads fail business validation.

Refer to the `/metrics` endpoint supplied by `setup_observability()` for Prometheus-formatted counters and histograms covering request latency, retrieval duration, and token usage.
