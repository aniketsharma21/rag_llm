"""Lightweight asyncio-based task queue abstraction."""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Dict, Optional

from src.logging_config import get_logger

logger = get_logger(__name__)


class AsyncTaskQueue:
    """Wraps ``asyncio.create_task`` and tracks submitted jobs."""

    def __init__(self) -> None:
        self._tasks: Dict[str, asyncio.Task[None]] = {}

    def submit(self, job_id: str, coroutine_factory: Callable[[], Awaitable[None]]) -> asyncio.Task[None]:
        if job_id in self._tasks:
            previous = self._tasks[job_id]
            if not previous.done():
                logger.warning("Cancelling existing task for job", job_id=job_id)
                previous.cancel()
        task = asyncio.create_task(coroutine_factory())
        self._tasks[job_id] = task
        task.add_done_callback(lambda t, jid=job_id: self._tasks.pop(jid, None))
        return task

    def get(self, job_id: str) -> Optional[asyncio.Task[None]]:
        return self._tasks.get(job_id)

    def cancel(self, job_id: str) -> bool:
        task = self._tasks.pop(job_id, None)
        if task is None:
            return False
        cancelled = task.cancel()
        if cancelled:
            logger.info("Cancelled task", job_id=job_id)
        return cancelled
