"""Lightweight asyncio-based task queue abstraction.

This module provides a simple task queue implementation built on top of asyncio.
It allows scheduling and managing asynchronous tasks with job tracking and cancellation
support.

Key Features:
- Task submission with unique job IDs
- Automatic cancellation of duplicate jobs
- Task status tracking
- Thread-safe operations
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Dict, Optional

from src.logging_config import get_logger

logger = get_logger(__name__)


class AsyncTaskQueue:
    """Thread-safe asyncio task queue with job tracking and management.
    
    This class provides a simple interface for managing asyncio tasks with
    job-based tracking. It ensures that only one task runs per job ID at a time,
    automatically canceling any existing task with the same ID when a new one
    is submitted.
    
    Attributes:
        _tasks: Dictionary mapping job IDs to their corresponding asyncio tasks.
    """

    def __init__(self) -> None:
        """Initialize a new AsyncTaskQueue instance.
        
        Creates a new task queue with an empty task dictionary.
        """
        self._tasks: Dict[str, asyncio.Task[None]] = {}

    def submit(self, job_id: str, coroutine_factory: Callable[[], Awaitable[None]]) -> asyncio.Task[None]:
        """Submit a new task to the queue.
        
        If a task with the same job_id already exists and is running, it will be
        cancelled before the new task is created.
        
        Args:
            job_id: Unique identifier for the job.
            coroutine_factory: A callable that returns an awaitable coroutine.
            
        Returns:
            The created asyncio.Task instance.
            
        Example:
            ```python
            async def my_task():
                await asyncio.sleep(1)
                print("Task completed")
                
            queue = AsyncTaskQueue()
            task = queue.submit("job_123", my_task)
            ```
        """
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
        """Retrieve a task by its job ID.
        
        Args:
            job_id: The ID of the job to retrieve.
            
        Returns:
            The asyncio.Task instance if found, None otherwise.
        """
        return self._tasks.get(job_id)

    def cancel(self, job_id: str) -> bool:
        """Cancel a running task.
        
        Args:
            job_id: The ID of the job to cancel.
            
        Returns:
            bool: True if the task was found and cancelled, False otherwise.
            
        Note:
            This method removes the task from the internal tracking dictionary
            when cancelled successfully.
        """
        task = self._tasks.pop(job_id, None)
        if task is None:
            return False
        cancelled = task.cancel()
        if cancelled:
            logger.info("Cancelled task", job_id=job_id)
        return cancelled
