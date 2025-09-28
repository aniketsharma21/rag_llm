"""
ingest.py

Enhanced document ingestion, chunking, and checksum management for the RAG pipeline.
Supports multiple file formats: PDF, Word, Text, Markdown, CSV, JSON, PowerPoint, and Excel.
Ensures only changed documents are reprocessed using checksum verification.

Supported File Types:
- PDF (.pdf) - Using PyPDFLoader
- Word Documents (.docx) - Using UnstructuredWordDocumentLoader  
- Text files (.txt) - Using TextLoader
- Markdown (.md) - Using TextLoader with UTF-8 encoding
- CSV files (.csv) - Using CSVLoader with UTF-8 encoding
- JSON files (.json) - Using JSONLoader
- PowerPoint (.pptx) - Using UnstructuredPowerPointLoader
- Excel (.xlsx) - Custom loader converting to text format

Usage:
    Use process_document(file_path) to ingest and chunk documents, with automatic checksum verification.
"""

# src/ingest.py
import os
import pickle
import hashlib
from langchain_community.document_loaders import (
    PyPDFLoader, 
    UnstructuredWordDocumentLoader, 
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredPowerPointLoader
)
import pandas as pd
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import (
    BASE_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    CHECKSUM_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from src.logging_config import get_logger
from src.exceptions import DocumentProcessingError

logger = get_logger(__name__)

def _get_loader(file_path):
    """
    Enhanced loader with support for multiple file types.
    
    Supported formats:
    - PDF (.pdf)
    - Word Documents (.docx)
    - Text files (.txt)
    - Markdown (.md)
    - CSV files (.csv)
    - JSON files (.json)
    - PowerPoint (.pptx)
    - Excel (.xlsx)
    
    Args:
        file_path (str): Path to the document file.
    Returns:
        Document loader instance.
    Raises:
        DocumentProcessingError: If file type is unsupported.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    supported_types = [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".pptx", ".xlsx"]
    
    try:
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".docx":
            return UnstructuredWordDocumentLoader(file_path)
        elif ext in [".txt", ".md"]:
            return TextLoader(file_path, encoding='utf-8')
        elif ext == ".csv":
            return CSVLoader(file_path, encoding='utf-8')
        elif ext == ".json":
            return JSONLoader(file_path, jq_schema='.', text_content=False)
        elif ext == ".pptx":
            return UnstructuredPowerPointLoader(file_path)
        elif ext == ".xlsx":
            return _create_excel_loader(file_path)
        else:
            raise DocumentProcessingError(
                f"Unsupported file type: {ext}", 
                {"file_type": ext, "supported_types": supported_types}
            )
    except Exception as e:
        logger.error("Failed to create loader", file_path=file_path, error=str(e))
        raise DocumentProcessingError(
            f"Failed to create loader for {ext} file: {str(e)}",
            {"file_path": file_path, "file_type": ext, "error": str(e)}
        )

def _create_excel_loader(file_path):
    """
    Create a custom loader for Excel files by converting to text format.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        TextLoader: Loader for the converted text content
    """
    from langchain.schema import Document
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
        
        # Convert to text format
        text_content = []
        for sheet_name, sheet_df in df.items():
            text_content.append(f"Sheet: {sheet_name}\n")
            text_content.append(sheet_df.to_string(index=False))
            text_content.append("\n\n")
        
        # Create a temporary text file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        temp_file.write("".join(text_content))
        temp_file.close()
        
        # Return TextLoader for the temporary file
        return TextLoader(temp_file.name, encoding='utf-8')
        
    except Exception as e:
        logger.error("Failed to process Excel file", file_path=file_path, error=str(e))
        raise DocumentProcessingError(
            f"Failed to process Excel file: {str(e)}",
            {"file_path": file_path, "error": str(e)}
        )


def _enrich_chunk_metadata(chunks, file_path):
    """Ensure each chunk points back to the original raw document."""
    absolute_path = os.path.abspath(file_path)
    relative_path = os.path.relpath(absolute_path, BASE_DIR)
    display_name = os.path.basename(file_path)

    for idx, chunk in enumerate(chunks):
        metadata = dict(getattr(chunk, "metadata", {}) or {})

        metadata["source"] = absolute_path
        metadata["raw_file_path"] = absolute_path
        metadata["source_file"] = absolute_path
        metadata["source_display_path"] = relative_path
        metadata["source_display_name"] = display_name
        metadata["chunk_index"] = idx

        if "page" in metadata and isinstance(metadata["page"], int):
            metadata["page_number"] = metadata["page"] + 1 if metadata["page"] >= 0 else metadata["page"]
        elif "page_number" not in metadata:
            metadata["page_number"] = None

        chunk.metadata = metadata

    return chunks

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
        logger.error("File not found", file_path=file_path)
        raise DocumentProcessingError(f"File not found at {file_path}", {"file_path": file_path})

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
        try:
            with open(checksum_save_path, 'r') as f:
                stored_checksum = f.read()
        except Exception as e:
            logger.warning(f"Failed to read checksum file: {e}")

    if current_checksum == stored_checksum:
        logger.info(f"'{os.path.basename(file_path)}' has not changed. Loading chunks from cache.")
        if os.path.exists(chunk_save_path):
            try:
                with open(chunk_save_path, "rb") as f:
                    cached_chunks = pickle.load(f)
                return _enrich_chunk_metadata(cached_chunks, file_path)
            except Exception as e:
                logger.warning(f"Failed to load cached chunks: {e}. Re-processing.")
        else:
            logger.warning("Checksum found but chunk file is missing. Re-processing.")
    else:
        logger.info(f"'{os.path.basename(file_path)}' is new or has been modified. Processing...")

    # Load and split the document
    try:
        loader = _get_loader(file_path)
        docs = loader.load()
    except DocumentProcessingError:
        raise
    except Exception as e:
        logger.error("Error loading document", file_name=os.path.basename(file_path), error=str(e))
        raise DocumentProcessingError(
            f"Failed to load document: {e}",
            {"file_path": file_path, "error": str(e)},
        ) from e

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)

    # Ensure chunk metadata references the original raw document
    chunks = _enrich_chunk_metadata(chunks, file_path)

    # Save chunks and new checksum
    try:
        with open(chunk_save_path, "wb") as f:
            pickle.dump(chunks, f)
        with open(checksum_save_path, 'w') as f:
            f.write(current_checksum)
        logger.info(f"Successfully processed and saved {len(chunks)} chunks for '{os.path.basename(file_path)}'.")
    except Exception as e:
        logger.error(f"Failed to save chunks or checksum: {e}")
        return None
    return chunks