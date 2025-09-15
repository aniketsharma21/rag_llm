"""
config.py

Centralized configuration management for the RAG pipeline. Handles environment variables, YAML config loading, logging setup, API keys, and directory paths.

Usage:
    Import settings and logger from this module for consistent configuration across the project.
"""

import os
import yaml
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Logging Setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_llm")

# --- YAML Config Loading ---
CONFIG_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
if os.path.exists(CONFIG_YAML_PATH):
    with open(CONFIG_YAML_PATH, "r") as f:
        yaml_config = yaml.safe_load(f)
else:
    yaml_config = {}

# --- API Keys ---
# Securely load API keys from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or yaml_config.get("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or yaml_config.get("GROQ_API_KEY")

# --- Paths ---
# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
CHECKSUM_DIR = os.path.join(PROCESSED_DATA_DIR, "checksums")

# Vector store persistence directory
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_store")

# Prompts directory
PROMPTS_DIR = os.path.join(BASE_DIR, "src", "prompts")

# Model cache directory
MODELS_CACHE_DIR = os.path.join(BASE_DIR, "models_cache")

# --- Pipeline Settings ---
# Settings for document chunking
CHUNK_SIZE = yaml_config.get("CHUNK_SIZE", 1000)
CHUNK_OVERLAP = yaml_config.get("CHUNK_OVERLAP", 150)

# Number of relevant chunks to retrieve for a query
TOP_K = yaml_config.get("TOP_K", 5)

# --- Models ---
# Names of the models to be used for LLM and embeddings
LLM_MODEL = yaml_config.get("LLM_MODEL", "llama-3.1-8b-instant")  # Example: Using a Groq model
EMBEDDING_MODEL = yaml_config.get("EMBEDDING_MODEL", "text-embedding-3-small")
