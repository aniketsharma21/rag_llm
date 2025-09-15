"""
embed_store.py

Manages embedding model initialization and vector store operations for the RAG pipeline.
Provides functions to build, load, and query the Chroma vector store using HuggingFace embeddings.

Usage:
    Use this module to create or load vector stores and retrieve relevant document chunks for queries.
"""

import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from src.config import (
    CHROMA_PERSIST_DIR,
    MODELS_CACHE_DIR,
    TOP_K,
    logger
)


def get_embedding_model():
    """
    Initializes and returns the Hugging Face embedding model for document chunk embedding.
    Automatically selects GPU (CUDA) if available, otherwise uses CPU.

    Returns:
        HuggingFaceEmbeddings instance or None if loading fails.
    """
    import torch  # Import torch to check for CUDA availability

    model_name = "sentence-transformers/all-MiniLM-L6-v2"

    # Check if a CUDA-enabled GPU is available, otherwise fall back to CPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")  # Add a print statement to confirm

    model_kwargs = {'device': device}

    os.makedirs(MODELS_CACHE_DIR, exist_ok=True)

    try:
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            cache_folder=MODELS_CACHE_DIR
        )
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return None


def build_vector_store(chunks):
    """Builds a new Chroma vector store from document chunks and persists it."""
    if not chunks:
        logger.warning("No chunks provided to build vector store.")
        return None

    logger.info(f"Building new vector store with {len(chunks)} chunks using a local model...")
    embeddings = get_embedding_model()  # <-- THIS NOW GETS THE FREE MODEL
    if not embeddings:
        logger.error("Embedding model could not be loaded.")
        return None
    try:
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )
        logger.info("Vector store built and persisted.")
        return vectordb
    except Exception as e:
        logger.error(f"Failed to build vector store: {e}")
        return None


def load_vector_store():
    """Loads an existing Chroma vector store from disk."""
    if not os.path.exists(CHROMA_PERSIST_DIR):
        logger.error("Vector store not found. Please index a document first.")
        return None

    logger.info("Loading existing vector store...")
    embeddings = get_embedding_model()  # <-- THIS NOW GETS THE FREE MODEL
    if not embeddings:
        logger.error("Embedding model could not be loaded.")
        return None
    try:
        vectordb = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings
        )
        return vectordb
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        return None


def get_retriever(vectordb):
    """Creates a retriever from the vector store."""
    if not vectordb:
        logger.error("No vector store provided for retriever.")
        return None
    return vectordb.as_retriever(search_kwargs={"k": TOP_K})