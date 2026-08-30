import asyncio
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.task_queue import AsyncTaskQueue
from src.services.ingestion_service import IngestionService
from src.prompt_templates import prompt_manager
from src.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_task_queue_callback_race_condition():
    """Verify that cancelled task done callbacks do not clear new tasks with same ID."""
    queue = AsyncTaskQueue()
    job_id = "test-job-id"
    
    # Task A that will be cancelled
    async def task_a_func():
        await asyncio.sleep(0.5)

    # Task B that replaces it
    async def task_b_func():
        await asyncio.sleep(0.5)

    # Submit task A
    t_a = queue.submit(job_id, task_a_func)
    assert queue.get(job_id) is t_a

    # Submit task B immediately, which cancels task A
    t_b = queue.submit(job_id, task_b_func)
    assert queue.get(job_id) is t_b

    # Allow event loop to run so task A is cancelled and triggers its done callback
    await asyncio.sleep(0.1)

    # Task B should still be tracked! (The race condition would have popped it)
    assert queue.get(job_id) is t_b

    # Clean up remaining tasks
    t_b.cancel()
    await asyncio.sleep(0.1)


def test_cleanup_file_does_not_propagate_error(monkeypatch):
    """Verify that cleanup failures log but do not raise or propagate exceptions."""
    service = IngestionService()
    
    # Mock os.path.exists to return True and os.remove to raise an error
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    
    def failing_remove(path):
        raise PermissionError("Mocked permission error (e.g. locked file on Windows)")
        
    monkeypatch.setattr(os, "remove", failing_remove)
    
    # This should not raise any exceptions
    try:
        service._cleanup_file("some_locked_file.txt")
    except Exception as exc:
        pytest.fail(f"_cleanup_file raised an exception: {exc}")


def test_format_chat_history_new_format():
    """Verify format_chat_history handles list of messages with role/content keys."""
    chat_history = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."}
    ]
    formatted = prompt_manager.format_chat_history(chat_history)
    assert formatted == "User: What is the capital of France?\nAssistant: The capital of France is Paris."


def test_format_chat_history_old_format():
    """Verify format_chat_history handles older exchange dictionaries with user/assistant keys."""
    chat_history = [
        {"user": "What is the capital of France?", "assistant": "The capital of France is Paris."}
    ]
    formatted = prompt_manager.format_chat_history(chat_history)
    assert formatted == "User: What is the capital of France?\nAssistant: The capital of France is Paris."


def test_format_chat_history_empty():
    """Verify format_chat_history handles empty history."""
    assert prompt_manager.format_chat_history([]) == "No previous conversation."
    assert prompt_manager.format_chat_history(None) == "No previous conversation."


@pytest.mark.asyncio
async def test_rag_service_runs_in_executor(monkeypatch):
    """Verify that generate_response offloads heavy operations to run_in_executor."""
    service = RAGService()
    
    dummy_chain = MagicMock()
    monkeypatch.setattr(service, "get_enhanced_chain", lambda: dummy_chain)
    
    dummy_result = {"answer": "Paris", "sources": [], "mode": "enhanced"}
    monkeypatch.setattr(service, "_run_enhanced_chain", lambda *args, **kwargs: dummy_result)
    
    # Track executor calls
    executor_calls = []
    
    async def mock_run_in_executor(executor, func, *args, **kwargs):
        executor_calls.append(func)
        return func(*args, **kwargs)
        
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "run_in_executor", mock_run_in_executor)
    
    result = await service.generate_response(question="capital of France")
    
    assert result == dummy_result
    # get_enhanced_chain and _run_enhanced_chain should both be executed in the threadpool
    assert service.get_enhanced_chain in executor_calls
    assert service._run_enhanced_chain in executor_calls
