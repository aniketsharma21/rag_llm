import pytest
from src.llm import get_llm
from src.config import GROQ_API_KEY

def test_llm_initialization():
    if not GROQ_API_KEY:
        pytest.skip("GROQ_API_KEY not set. Skipping LLM initialization test.")
    llm = get_llm()
    assert llm is not None

