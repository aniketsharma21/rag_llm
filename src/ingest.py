# src/ingest.py
import os
import pickle
import hashlib
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    CHECKSUM_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

def _get_loader(file_path):
    """Selects the appropriate document loader based on file extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext == ".docx":
        return UnstructuredWordDocumentLoader(file_path)
    elif ext == ".txt":
        return TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def _calculate_checksum(file_path):
    """Calculates the SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def process_document(file_path):
    """
    Processes a single document:
    1. Checks if the document has been modified using checksums.
    2. If modified or new, loads and splits the document into chunks.
    3. Saves the chunks and the new checksum.
    Returns the chunks if the file was processed, otherwise None.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    # Create directories if they don't exist
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(CHECKSUM_DIR, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    chunk_save_path = os.path.join(PROCESSED_DATA_DIR, f"{base_name}_chunks.pkl")
    checksum_save_path = os.path.join(CHECKSUM_DIR, f"{base_name}.sha256")

    # Check if file has changed
    current_checksum = _calculate_checksum(file_path)
    stored_checksum = None
    if os.path.exists(checksum_save_path):
        with open(checksum_save_path, 'r') as f:
            stored_checksum = f.read()

    if current_checksum == stored_checksum:
        print(f"'{os.path.basename(file_path)}' has not changed. Loading chunks from cache.")
        if os.path.exists(chunk_save_path):
            with open(chunk_save_path, "rb") as f:
                return pickle.load(f)
        else:
            # This case handles if chunks were deleted but checksum remains
            print("Warning: Checksum found but chunk file is missing. Re-processing.")
    else:
        print(f"'{os.path.basename(file_path)}' is new or has been modified. Processing...")

    # Load and split the document
    try:
        loader = _get_loader(file_path)
        docs = loader.load()
    except Exception as e:
        print(f"Error loading document {os.path.basename(file_path)}: {e}")
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)

    # Save chunks and new checksum
    with open(chunk_save_path, "wb") as f:
        pickle.dump(chunks, f)
    with open(checksum_save_path, 'w') as f:
        f.write(current_checksum)

    print(f"Successfully processed and saved {len(chunks)} chunks for '{os.path.basename(file_path)}'.")
    return chunks