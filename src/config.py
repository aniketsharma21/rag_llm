import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
# Securely load API keys from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Paths ---
# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
CHECKSUM_DIR = os.path.join(PROCESSED_DATA_DIR, "checksums")

# Vector store persistence directory
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_store")

# --- Pipeline Settings ---
# Settings for document chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Number of relevant chunks to retrieve for a query
TOP_K = 5

# --- Models ---
# Names of the models to be used for LLM and embeddings
LLM_MODEL = "llama3-8b-8192"  # Example: Using a Groq model
EMBEDDING_MODEL = "text-embedding-3-small"