Operations
==========

This chapter outlines deployment, observability, and operational workflows for running the RAG platform in production.

Deployment
----------

* **Backend** – Launch via `uvicorn src.api:app --host 0.0.0.0 --port 8000`. For production, configure multiple workers (Gunicorn + Uvicorn workers) and point `GROQ_API_KEY` to a secret store.
* **Frontend** – Build the React bundle (`npm run build`) and serve via a CDN or reverse proxy (e.g., Nginx). Ensure `/ws/chat` traffic is proxied with WebSocket upgrades enabled.
* **Process supervision** – Use systemd or a container orchestrator (Kubernetes) to manage both FastAPI and background workers. Health probes should hit `/health`.

Monitoring & Metrics
--------------------

`src/middleware/observability.py` registers Prometheus metrics under `/metrics`. Key series:

* **rag_http_requests_total** – Tagged by method/path/status.
* **rag_http_request_duration_seconds** – Request latency histograms.
* **rag_retrieval_duration_seconds** – Hybrid retrieval latency by mode (`hybrid`, `context`).
* **rag_generation_duration_seconds** – LLM invocation latency, keyed by provider/model.
* **rag_generation_tokens_total** – Token counts emitted by upstream models.
* **rag_pipeline_errors_total** – Error counter with component labels.

Expose `/metrics` via a service monitor (Prometheus Operator) and construct Grafana dashboards for ingest throughput, latency, and token usage trends.

Logging
-------

Structured logging uses `structlog` with request contextualization. `RequestMetricsMiddleware` injects `request_id`, `client_ip`, and latency into every log event. Forward logs to a centralized platform (Elastic, Loki) for long-term retention.

Scaling Considerations
----------------------

* **Vector store** – Chroma runs in embedded mode; shard by document corpus for large deployments or switch to a networked vector DB (e.g., Qdrant) by adapting `src/embed_store.py`.
* **Cold start** – The FastAPI lifespan hook invokes `run_llm_health_check()` and asynchronously warms the hybrid retriever (`RAGService.warmup()`). Plan for 2–4 seconds of startup latency.
* **Concurrency** – WebSockets are managed through `ConnectionManager`; ensure application server supports sufficient event loop capacity. For heavy workloads, horizontally scale behind a load balancer and route sessions with sticky affinity if conversation state is stored in memory.

Backup & Recovery
-----------------

* **Database** – Snapshot ``conversations.db`` and ``chroma_store/`` regularly. Conversation and job repositories can be rebuilt from raw data if the SQLite file is lost.
* **Documents** – Retain originals under ``data/raw/``. Checksums allow reconciliation; missing processed chunks trigger automatic reprocessing on next ingest.

Incident Response
-----------------

1. Inspect `/metrics` for elevated `rag_pipeline_errors_total`.
2. Consult logs filtered by `component` or request ID.
3. Use `GET /status/{job_id}` to audit ingest failures; details include serialized exception context.
4. If embeddings drift, re-run ingestion jobs after updating configuration to rebuild the Chroma store.
