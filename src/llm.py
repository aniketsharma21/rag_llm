from langchain_groq import ChatGroq
from src.config import GROQ_API_KEY, LLM_MODEL


def get_llm():
    """Initializes and returns the Groq LLM."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

    return ChatGroq(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY
    )