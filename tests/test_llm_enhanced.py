import types

import pytest
from langchain.schema import Document

from src import llm as llm_module


class _DummyLLM:
    def __init__(self):
        self.invocations = []

    def invoke(self, prompt):
        self.invocations.append(prompt)
        return types.SimpleNamespace(content="Answer with citation [1]")


class _DummyHybridRetriever:
    def __init__(self, vector_store, documents, *args, **kwargs):
        self.vector_store = vector_store
        self.documents = documents
        self.queries = []

    def retrieve(self, query, k=None):
        self.queries.append((query, k))
        return list(self.documents)

    def get_retrieval_stats(self):
        return {"total_documents": len(self.documents), "has_ensemble": True}


class _DummyAdvancedRetriever(_DummyHybridRetriever):
    def retrieve_with_context(self, query, conversation_history=None, k=None):
        self.queries.append((query, conversation_history, k))
        return list(self.documents)


class _DummyVectorStore:
    def __init__(self, docs):
        self.docs = docs

    def as_retriever(self, search_kwargs=None):
        retriever = _DummyHybridRetriever(self, self.docs)
        return retriever


@pytest.fixture
def sample_documents():
    return [
        Document(
            page_content="First chunk content",
            metadata={
                "raw_file_path": "data/raw/doc1.txt",
                "page_number": 1,
                "snippet": "Snippet one",
            },
        ),
        Document(
            page_content="Second chunk content",
            metadata={
                "raw_file_path": "data/raw/doc1.txt",
                "page_number": 2,
                "snippet": "Snippet two",
            },
        ),
    ]


@pytest.fixture
def patched_enhanced_chain(monkeypatch, sample_documents):
    dummy_llm = _DummyLLM()

    monkeypatch.setattr(llm_module, "get_llm", lambda: dummy_llm)
    monkeypatch.setattr(llm_module, "HybridRetriever", _DummyHybridRetriever)
    monkeypatch.setattr(llm_module, "AdvancedRetriever", _DummyAdvancedRetriever)
    monkeypatch.setattr(
        llm_module.prompt_manager,
        "select_template_by_query_type",
        lambda query, count: "base",
    )
    monkeypatch.setattr(llm_module, "get_enhanced_prompt", lambda **kwargs: "PROMPT")

    vector_store = _DummyVectorStore(sample_documents)
    chain = llm_module.EnhancedRAGChain(vector_store, sample_documents)
    return chain, dummy_llm


def test_enhanced_rag_chain_query_with_sources(patched_enhanced_chain, sample_documents):
    chain, dummy_llm = patched_enhanced_chain

    result = chain.query("What is hybrid retrieval?", k=2)

    assert dummy_llm.invocations == ["PROMPT"]
    assert result["answer"] == "Answer with citation ¹"
    assert result["template_used"] == "base"
    assert result["num_sources"] == len(sample_documents)

    sources = result["sources"]
    assert len(sources) == 1
    source_entry = sources[0]
    assert source_entry["citation"] == "¹"
    assert source_entry["metadata"]["page_numbers"] == [1, 2]
    assert source_entry["metadata"]["raw_file_path"] == "data/raw/doc1.txt"

    assert len(chain.conversation_history) == 1
    history_entry = chain.conversation_history[0]
    assert history_entry["user"] == "What is hybrid retrieval?"
    assert history_entry["assistant"] == "Answer with citation ¹"


def test_enhanced_rag_chain_without_conversation_context(patched_enhanced_chain):
    chain, _ = patched_enhanced_chain

    history_before = list(chain.conversation_history)
    result = chain.query(
        "Tell me about RAG",
        conversation_context=False,
        include_sources=False,
        k=1,
    )

    assert result["sources"] == []
    assert chain.conversation_history == history_before
