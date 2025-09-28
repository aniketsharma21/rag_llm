import pytest
from langchain.schema import Document

from src.retrieval import HybridRetriever


def _make_documents():
    return [
        Document(page_content="Doc vector 1", metadata={"source": "doc1"}),
        Document(page_content="Doc vector 2", metadata={"source": "doc2"}),
        Document(page_content="Doc vector 3", metadata={"source": "doc3"}),
    ]


class _DummyVectorRetriever:
    def __init__(self, docs):
        self._docs = docs
        self.queries = []

    def get_relevant_documents(self, query):
        self.queries.append(query)
        return list(self._docs)


class _DummyVectorStore:
    def __init__(self, docs):
        self._retriever = _DummyVectorRetriever(docs)

    def as_retriever(self, search_kwargs=None):
        return self._retriever


class _DummyBM25Retriever:
    def __init__(self, docs):
        self._docs = docs
        self.queries = []

    @classmethod
    def from_documents(cls, docs, k):
        # Return reversed order to validate hybrid combination logic.
        return cls(list(reversed(docs)))

    def get_relevant_documents(self, query):
        self.queries.append(query)
        return list(self._docs)


class _DummyEnsembleRetriever:
    def __init__(self, retrievers, weights):
        self._retrievers = retrievers
        self._weights = weights
        self.queries = []

    def get_relevant_documents(self, query):
        self.queries.append(query)
        docs = []
        for retriever in self._retrievers:
            docs.extend(retriever.get_relevant_documents(query))
        return docs


@pytest.fixture
def patched_retrievers(monkeypatch):
    monkeypatch.setattr("src.retrieval.BM25Retriever", _DummyBM25Retriever)
    monkeypatch.setattr("src.retrieval.EnsembleRetriever", _DummyEnsembleRetriever)


def test_hybrid_retriever_populates_metadata(patched_retrievers):
    docs = _make_documents()
    vector_store = _DummyVectorStore(docs)

    retriever = HybridRetriever(vector_store, docs, k=3)
    results = retriever.retrieve("what is rag?", k=2)

    assert len(results) == 2
    assert [doc.page_content for doc in results] == ["Doc vector 1", "Doc vector 2"]
    for idx, doc in enumerate(results, start=1):
        assert doc.metadata["retrieval_rank"] == idx
        assert doc.metadata["retrieval_method"] == "hybrid"

    stats = retriever.get_retrieval_stats()
    assert stats["total_documents"] == 3
    assert stats["has_ensemble"] is True


def test_hybrid_retriever_vector_only_fallback(monkeypatch):
    docs = _make_documents()
    vector_store = _DummyVectorStore(docs)

    class _FailingEnsemble:
        def __init__(self, *args, **kwargs):  # pragma: no cover - simple failure stub
            raise RuntimeError("ensemble unavailable")

    monkeypatch.setattr("src.retrieval.BM25Retriever", _DummyBM25Retriever)
    monkeypatch.setattr("src.retrieval.EnsembleRetriever", _FailingEnsemble)

    retriever = HybridRetriever(vector_store, docs, k=3)
    results = retriever.retrieve("hybrid fallback", k=2)

    assert len(results) == 2
    assert [doc.page_content for doc in results] == ["Doc vector 1", "Doc vector 2"]
    assert all(doc.metadata["retrieval_method"] == "hybrid" for doc in results)
