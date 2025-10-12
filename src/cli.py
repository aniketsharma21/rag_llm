
"""Async CLI entry point built on the RAG application services."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from io import BufferedReader
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import Iterable, Optional

from fastapi import UploadFile

from src.config import RAW_DATA_DIR, logger
from src.db.session import init_database
from src.services.ingestion_service import IngestionService
from src.services.rag_service import RAGApplicationService, RAGService


TERMINAL_JOB_STATUSES = {"completed", "failed", "skipped"}


def _build_app_service() -> RAGApplicationService:
    ingestion_service = IngestionService()
    rag_service = RAGService()
    return RAGApplicationService(ingestion_service, rag_service)


def _resolve_candidate_paths(file_name: str) -> Iterable[Path]:
    candidate = Path(file_name)
    yield candidate
    if not candidate.is_absolute():
        yield Path(os.getcwd()) / candidate
        yield Path(RAW_DATA_DIR) / candidate


def _resolve_file_path(file_name: str) -> Path:
    for candidate in _resolve_candidate_paths(file_name):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"File not found: {file_name}")


def _open_spooled(file_path: Path) -> SpooledTemporaryFile:
    spool = SpooledTemporaryFile(max_size=10 * 1024 * 1024)
    with file_path.open("rb") as src:
        shutil_copyfileobj(src, spool)
    spool.seek(0)
    return spool


async def _ingest_command(app_service: RAGApplicationService, *, file: str, poll_interval: float, timeout: Optional[float]) -> int:
    file_path = _resolve_file_path(file)
    logger.info(f"Starting ingestion for file: {file_path}")

    spool = _open_spooled(file_path)
    upload = UploadFile(
        filename=file_path.name,
        file=spool,
    )

    try:
        job_id, stored_path = await app_service.ingest_document(upload)
    finally:
        await upload.close()

    logger.info(f"Ingestion job {job_id} created for stored file: {stored_path}")

    start = time.monotonic()
    while True:
        record = await app_service.get_job_status(job_id)
        if record is None:
            logger.error("Job status record missing", job_id=job_id)
            return 1

        status = record.get("status")
        message = record.get("message")
        logger.info(f"Job status: {status} - {message}")

        if status in TERMINAL_JOB_STATUSES:
            if status == "failed":
                logger.error("Ingestion failed", details=record.get("error"))
                return 1
            if status == "skipped":
                logger.warning("Ingestion skipped", reason=message)
            else:
                logger.info("Ingestion completed successfully")
            return 0

        if timeout is not None and timeout > 0 and (time.monotonic() - start) > timeout:
            logger.error("Timed out waiting for ingestion job", job_id=job_id)
            return 1

        await asyncio.sleep(poll_interval)


async def _query_command(
    app_service: RAGApplicationService,
    *,
    question: str,
    conversation_id: Optional[int],
    raw: bool,
) -> int:
    logger.info(f"Running query: {question}")
    response = await app_service.query(question=question, chat_history=None, conversation_id=conversation_id)

    if raw:
        print(json.dumps(response, indent=2))
    else:
        answer = response.get("answer", "")
        print("\nAnswer:\n--------")
        print(answer)

        sources = response.get("sources", []) or []
        if sources:
            print("\nSources:")
            for source in sources:
                label = source.get("label") or source.get("title") or source.get("metadata", {}).get("source", "unknown")
                confidence = source.get("confidence_score")
                if confidence is not None:
                    print(f"- {label} (confidence: {confidence:.2f})")
                else:
                    print(f"- {label}")

        confidence_score = response.get("confidence_score")
        if confidence_score is not None:
            print(f"\nConfidence score: {confidence_score:.2f}")

    return 0


async def _status_command(app_service: RAGApplicationService, *, job_id: str) -> int:
    record = await app_service.get_job_status(job_id)
    if record is None:
        logger.error("Job not found", job_id=job_id)
        return 1

    print(json.dumps(record, indent=2, default=str))
    return 0


async def _warmup_command(app_service: RAGApplicationService) -> int:
    logger.info("Triggering RAG service warmup")
    success = await app_service.warmup()
    if success:
        logger.info("Warmup completed with cached chain")
        return 0

    logger.warning("Warmup completed without enhanced chain; ensure documents are ingested")
    return 1


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG pipeline command-line interface")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    ingest_parser = subparsers.add_parser("ingest", aliases=["index"], help="Ingest a document into the RAG pipeline")
    ingest_parser.add_argument("--file", required=True, help="Path to the document to ingest")
    ingest_parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between job status checks")
    ingest_parser.add_argument("--timeout", type=float, default=600.0, help="Maximum seconds to wait for completion (0 to disable)")

    query_parser = subparsers.add_parser("query", help="Query the RAG pipeline")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument("--conversation-id", type=int, help="Existing conversation ID for persistence")
    query_parser.add_argument("--raw", action="store_true", help="Print raw JSON response")

    status_parser = subparsers.add_parser("status", help="Check ingestion job status")
    status_parser.add_argument("job_id", help="Identifier returned from ingest command")

    subparsers.add_parser("warmup", help="Warm up the RAG pipeline caches")

    return parser


async def _run_async(args: argparse.Namespace) -> int:
    await init_database()
    app_service = _build_app_service()

    command = args.command
    if command in {"ingest", "index"}:
        timeout = args.timeout if args.timeout and args.timeout > 0 else None
        return await _ingest_command(app_service, file=args.file, poll_interval=args.poll_interval, timeout=timeout)
    if command == "query":
        return await _query_command(
            app_service,
            question=args.question,
            conversation_id=args.conversation_id,
            raw=args.raw,
        )
    if command == "status":
        return await _status_command(app_service, job_id=args.job_id)
    if command == "warmup":
        return await _warmup_command(app_service)

    logger.error(f"Unknown command: {command}")
    return 1


def main(argv: Optional[list[str]] = None) -> None:
    parser = _create_parser()
    args = parser.parse_args(argv)

    try:
        exit_code = asyncio.run(_run_async(args))
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        exit_code = 1

    sys.exit(exit_code)


def shutil_copyfileobj(src: BufferedReader, dst: SpooledTemporaryFile, length: int = 64 * 1024) -> None:
    while True:
        chunk = src.read(length)
        if not chunk:
            break
        dst.write(chunk)


if __name__ == "__main__":
    main()
