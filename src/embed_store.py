import os
from langchain_huggingface import HuggingFaceEmbeddings  # <-- IMPORT THE NEW CLASS
from langchain_community.vectorstores import Chroma
from src.config import (
    CHROMA_PERSIST_DIR,
    # EMBEDDING_MODEL is no longer needed here
    MODELS_CACHE_DIR,
    TOP_K
)


def get_embedding_model():
    """Initializes and returns the Hugging Face embedding model."""
    import torch  # Import torch to check for CUDA availability

    model_name = "sentence-transformers/all-MiniLM-L6-v2"

    # Check if a CUDA-enabled GPU is available, otherwise fall back to CPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")  # Add a print statement to confirm

    model_kwargs = {'device': device}

    os.makedirs(MODELS_CACHE_DIR, exist_ok=True)

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        cache_folder=MODELS_CACHE_DIR
    )


def build_vector_store(chunks):
    """Builds a new Chroma vector store from document chunks and persists it."""
    if not chunks:
        print("No chunks provided to build vector store.")
        return None

    print(f"Building new vector store with {len(chunks)} chunks using a local model...")
    embeddings = get_embedding_model()  # <-- THIS NOW GETS THE FREE MODEL
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    # vectordb.persist() not needed in Chroma >=0.4
    print("Vector store built and persisted.")
    return vectordb


def load_vector_store():
    """Loads an existing Chroma vector store from disk."""
    if not os.path.exists(CHROMA_PERSIST_DIR):
        print("Vector store not found. Please index a document first.")
        return None

    print("Loading existing vector store...")
    embeddings = get_embedding_model()  # <-- THIS NOW GETS THE FREE MODEL
    vectordb = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )
    return vectordb


def get_retriever(vectordb):
    """Creates a retriever from the vector store."""
    if not vectordb:
        return None
    return vectordb.as_retriever(search_kwargs={"k": TOP_K})