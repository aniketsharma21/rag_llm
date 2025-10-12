from __future__ import annotations

import asyncio
import io
from unittest import mock

import pytest

import src.cli as cli


@pytest.fixture(autouse=True)
def prevent_real_database(monkeypatch):
    monkeypatch.setattr(cli, "init_database", mock.AsyncMock())


@pytest.fixture
def app_service_mock():
    service = mock.AsyncMock()
    service.ingest_document.return_value = ("job-123", "stored/path")
    service.get_job_status.side_effect = [
        {"status": "processing", "message": "working"},
        {"status": "completed", "message": "done"},
    ]
    service.query.return_value = {"answer": "42", "sources": [], "confidence_score": 0.9}
    service.warmup.return_value = True
    return service


@pytest.fixture(autouse=True)
def patch_build_app_service(monkeypatch, app_service_mock):
    monkeypatch.setattr(cli, "_build_app_service", lambda: app_service_mock)


async def run_cli(command: list[str]) -> int:
    parser = cli._create_parser()  # pylint: disable=protected-access
    args = parser.parse_args(command)
    return await cli._run_async(args)  # pylint: disable=protected-access


@pytest.mark.asyncio
async def test_ingest_command(monkeypatch, app_service_mock, tmp_path):
    sample_file = tmp_path / "doc.txt"
    sample_file.write_text("hello")

    monkeypatch.setattr(cli, "_resolve_file_path", lambda _: sample_file)
    monkeypatch.setattr(cli, "_open_spooled", lambda _: io.BytesIO(b"hello"))

    exit_code = await run_cli(["ingest", "--file", str(sample_file), "--poll-interval", "0", "--timeout", "1"])

    assert exit_code == 0
    app_service_mock.ingest_document.assert_awaited()
    assert app_service_mock.get_job_status.await_count == 2


@pytest.mark.asyncio
async def test_query_command_raw_output(capsys, app_service_mock):
    exit_code = await run_cli(["query", "What?", "--raw"])

    assert exit_code == 0
    app_service_mock.query.assert_awaited_with(question="What?", chat_history=None, conversation_id=None)
    captured = capsys.readouterr()
    assert "\"answer\": \"42\"" in captured.out


@pytest.mark.asyncio
async def test_status_command(capsys, app_service_mock):
    exit_code = await run_cli(["status", "job-123"])

    assert exit_code == 0
    app_service_mock.get_job_status.assert_awaited_with("job-123")
    captured = capsys.readouterr()
    assert "\"status\": \"processing\"" in captured.out


@pytest.mark.asyncio
async def test_warmup_command(app_service_mock):
    exit_code = await run_cli(["warmup"])

    assert exit_code == 0
    app_service_mock.warmup.assert_awaited()
