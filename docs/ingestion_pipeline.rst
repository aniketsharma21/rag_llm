Ingestion Pipeline
==================

The ingestion pipeline converts uploaded documents into persisted vector indexes with auditability and resumability.

Workflow Overview
-----------------

The following diagram illustrates the ingestion workflow from document upload to vector store regeneration:

.. mermaid::

   graph TD
       A[POST /ingest] --> B{IngestionService};
       B --> C[Enqueue Upload];
       C --> D{Job & Document Repositories};
       D --> E[Create Job & Document Records];
       E --> F{AsyncTaskQueue};
       F --> G[Process Job];
       G --> H{process_document};
       H --> I[Load & Chunk Document];
       I --> J{build_vector_store};
       J --> K[Rebuild Chroma Index];
       K --> L[Update Job Status];

Key Service Logic
-----------------

.. code-block:: python
   :caption: src/services/ingestion_service.py

   class IngestionService:
       def __init__(self, task_queue: Optional[AsyncTaskQueue] = None) -> None:
           os.makedirs(RAW_DATA_DIR, exist_ok=True)
           self._task_queue = task_queue or AsyncTaskQueue()

       async def enqueue_upload(self, file: UploadFile) -> Tuple[str, str]:
           payload = await file.read()
           job_id = str(uuid.uuid4())
           original_name = file.filename or "document"
           safe_filename = self._sanitize_filename(original_name)
           permanent_file_path = self._persist_payload(safe_filename, payload)
           checksum = hashlib.sha256(payload).hexdigest()

           async with get_session() as session:
               job_repo = JobRepository(session)
               document_repo = DocumentRepository(session)

               document_record = await document_repo.create(
                   filename=os.path.basename(permanent_file_path),
                   original_filename=original_name,
                   file_path=permanent_file_path,
                   file_size=len(payload),
                   file_type=file_ext,
                   checksum=checksum,
               )

               job_details = {
                   "file_path": permanent_file_path,
                   "document_id": document_record["id"],
                   "checksum": document_record["checksum"],
               }

               await job_repo.create(
                   job_id=job_id,
                   file_name=original_name,
                   status="queued",
                   message="Upload received",
                   details=job_details,
               )

           return job_id, permanent_file_path

       async def process_job(self, job_id: str, file_path: str) -> Dict[str, Optional[int]]:
           async with get_session() as session:
               job_repo = JobRepository(session)
               job_record = await job_repo.get(job_id)
               ...
           chunks = await asyncio.to_thread(process_document, file_path)
           if not chunks:
               await job_repo.update(... status="skipped" ...)
               return {"chunks_processed": 0, "status": "skipped"}

           await asyncio.to_thread(build_vector_store, chunks)
           await job_repo.update(... status="completed" ...)
           if document_id is not None:
               await document_repo.update_processing(...)
           return {"chunks_processed": len(chunks), "status": "completed"}

The queue invalidates cached RAG chains by invoking `RAGService.reset_chain()` upon successful completion, guaranteeing fresh retrieval behavior.

Document Processing
-------------------

`src/ingest.py` orchestrates content loading in `_get_loader()` with format-specific handlers (PDF, DOCX, TXT/MD, CSV, JSON, PPTX, XLSX). Each chunk is enriched with metadata fields such as `source_display_path`, `page_number`, and `snippet` so the frontend can render document cards.

`process_document()` persists `{basename}_chunks.pkl` and `{basename}.sha256`, enabling fast re-ingestion when the checksum matches. When a checksum hit occurs, cached pickle files are re-used and the pipeline returns early with `status="skipped"`.

Vector Store Regeneration
-------------------------

`src/embed_store.py` manages embedding lifecycles:

* `get_embedding_model()` lazily instantiates the configured backend (`huggingface`, `openai`, or `fake` test double) while caching the signature.
* `build_vector_store()` writes a new Chroma collection, logs chunk counts, and persists `embedding_config.json` so configuration drift can be detected.
* `load_vector_store()` compares the stored signature to the active settings, emitting warnings when re-ingestion is required.

Operational Considerations
--------------------------

* **Job status polling** – `GET /status/{job_id}` surfaces `status`, `message`, `chunks_count`, and error metadata. Integrate this endpoint with CI pipelines to detect ingest regressions. The job status can be one of `queued`, `processing`, `completed`, `skipped`, or `failed`.
* **Storage layout** – Raw files live under ``data/raw/`` while processed artifacts are stored in ``data/processed/`` and hashes in ``data/processed/checksums/``. This separation simplifies cleanup and auditing.
* **Failure handling** – Failures during document processing or vector store regeneration trigger `DocumentProcessingError` or `VectorStoreError`, respectively. The job record is marked `failed` with serialized exception details for audit. The system is designed to be resilient to transient failures, and jobs can be manually retried.

Configuration
-------------

The ingestion pipeline is configured through the `AppSettings` object in `src/config.py`. Key settings include:

*   **`chunk_size`**: The number of characters per chunk.
*   **`chunk_overlap`**: The number of characters to overlap between chunks.
*   **`embedding_backend`**: The embedding model to use (`huggingface`, `openai`, or `fake`).
*   **`embedding_model`**: The specific embedding model to use (e.g., `all-MiniLM-L6-v2`).

Changes to these settings may require re-ingestion of documents to ensure consistency.
