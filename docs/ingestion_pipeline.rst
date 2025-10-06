Ingestion Pipeline
==================

The ingestion pipeline converts uploaded documents into persisted vector indexes with auditability and resumability.

Workflow Overview
-----------------

1. **Upload** – `POST /ingest` receives a `multipart/form-data` payload and streams the file to `IngestionService.enqueue_upload()`.
2. **Job tracking** – Metadata is inserted into `ingest_jobs` and `documents` tables via `JobRepository` and `DocumentRepository`.
3. **Background execution** – `AsyncTaskQueue.submit()` dispatches `IngestionService.process_job()` without blocking the API thread.
4. **Chunking** – `process_document()` loads the source via format-aware loaders, applies `RecursiveCharacterTextSplitter`, and enriches chunk metadata.
5. **Vector rebuild** – `build_vector_store()` creates or refreshes the Chroma store and persists the embedding configuration; downstream `RAGService` warmup is invalidated.

Key Service Logic
-----------------

.. code-block:: python
   :caption: `src/services/ingestion_service.py`

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

* **Job status polling** – `GET /status/{job_id}` surfaces `status`, `message`, `chunks_count`, and error metadata. Integrate this endpoint with CI pipelines to detect ingest regressions.
* **Storage layout** – Raw files live under ``data/raw/`` while processed artifacts are stored in ``data/processed/`` and hashes in ``data/processed/checksums/``.
* **Failure handling** – Failures trigger `DocumentProcessingError` or `VectorStoreError`; the job record is marked `failed` with serialized exception details for audit.
