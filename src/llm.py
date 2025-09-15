from langchain_groq import ChatGroq
from src.config import GROQ_API_KEY, LLM_MODEL, logger


def get_llm():
    """Initializes and returns the Groq LLM."""
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
