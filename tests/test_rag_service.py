import pickle
from io import BytesIO
from types import SimpleNamespace

import pytest

import src.services.rag_service as rag_module
from src.exceptions import ConversationError
from src.services.rag_service import RAGService


class DummyChain:
    def query(self, **kwargs):
        return {
            "answer": "Result [1]",
            "sources": [
                {
                    "id": 1,
                    "raw_file_path": "/tmp/doc.pdf",
                    "metadata": {"snippet": "snippet"},
                }
            ],
            "confidence_score": 0.42,
            "template_used": "test",
            "num_sources": 1,
        }


@pytest.mark.asyncio
async def test_generate_response_prefers_enhanced_chain(monkeypatch):
    service = RAGService()

    dummy_chain = DummyChain()
    recorded = {}

    monkeypatch.setattr(service, "get_enhanced_chain", lambda: dummy_chain)
    def fake_run(chain, question, history):
        recorded["called"] = (chain, question, history)
        return {"mode": "enhanced"}

    monkeypatch.setattr(service, "_run_enhanced_chain", fake_run)

    result = await service.generate_response(question="What is RAG?", chat_history=["context"])

    assert result == {"mode": "enhanced"}
    assert recorded["called"][0] is dummy_chain
    assert recorded["called"][1] == "What is RAG?"
    assert recorded["called"][2] == ["context"]


@pytest.mark.asyncio
async def test_generate_response_falls_back_when_no_chain(monkeypatch):
    service = RAGService()
    monkeypatch.setattr(service, "get_enhanced_chain", lambda: None)

    async def fake_fallback(question):  # pylint: disable=unused-argument
        return {"mode": "fallback"}

    monkeypatch.setattr(service, "_run_fallback_pipeline", fake_fallback)

    result = await service.generate_response(question="Question?")
    assert result == {"mode": "fallback"}


def test_run_enhanced_chain_formats_answer(monkeypatch):
    service = RAGService()

    result = service._run_enhanced_chain(DummyChain(), "What?", [])

    assert result["mode"] == "enhanced"
    assert result["confidence_score"] == 0.42
    assert result["template_used"] == "test"
    assert result["num_sources"] == 1
    assert "¹" in result["answer"]
    assert isinstance(result["sources"], list) and result["sources"]
    assert result["paragraphs"]


@pytest.mark.asyncio
async def test_run_fallback_pipeline_requires_vector_store(monkeypatch):
    service = RAGService()
    monkeypatch.setattr(rag_module, "load_vector_store", lambda: None)

    with pytest.raises(RuntimeError):
        await service._run_fallback_pipeline("question")


@pytest.mark.asyncio
async def test_generate_response_persists_conversation(monkeypatch):
    service = RAGService()

    dummy_chain = DummyChain()
    monkeypatch.setattr(service, "get_enhanced_chain", lambda: dummy_chain)

    async def fake_persist(conversation_id, *, question, answer, sources):
        fake_persist.called = {
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    fake_persist.called = None
    monkeypatch.setattr(service, "_persist_conversation_update", fake_persist)

    result = await service.generate_response(
        question="Explain RAG",
        chat_history=[],
        conversation_id=42,
    )

    assert result["mode"] == "enhanced"
    assert fake_persist.called == {
        "conversation_id": 42,
        "question": "Explain RAG",
        "answer": "Result ¹",
        "sources": result["sources"],
    }


@pytest.mark.asyncio
async def test_generate_response_swallows_conversation_error(monkeypatch):
    service = RAGService()
    dummy_chain = DummyChain()
    monkeypatch.setattr(service, "get_enhanced_chain", lambda: dummy_chain)

    async def fake_persist(*args, **kwargs):  # pylint: disable=unused-argument
        raise ConversationError("boom")

    monkeypatch.setattr(service, "_persist_conversation_update", fake_persist)

    committed = {"called": False}

    def on_commit(_):
        committed["called"] = True

    result = await service.generate_response(
        question="Explain RAG",
        chat_history=[],
        conversation_id=7,
        on_messages_committed=on_commit,
    )

    assert result["mode"] == "enhanced"
    assert committed["called"] is False
