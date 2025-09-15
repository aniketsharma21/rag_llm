"""
llm.py

Initializes and manages the Large Language Model (LLM) for the RAG pipeline using Groq API.
Handles authentication and error reporting for LLM setup.

Usage:
    Use get_llm() to obtain a ready-to-use LLM instance for generating answers.
"""

from langchain_groq import ChatGroq
from src.config import GROQ_API_KEY, LLM_MODEL, logger


def get_llm():
    """
    Initializes and returns the Groq LLM instance for text generation.

    Raises:
        ValueError: If GROQ_API_KEY is missing.
        Exception: If LLM initialization fails.

    Returns:
        ChatGroq instance: A configured instance of the ChatGroq class for generating text.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not found. Please set it in your .env file or config.yaml.")
        raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")
    try:
        llm = ChatGroq(
            model=LLM_MODEL,
            api_key=GROQ_API_KEY
        )
        logger.info(f"Initialized Groq LLM with model '{LLM_MODEL}'.")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM: {e}")
        raise
