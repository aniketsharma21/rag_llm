"""
ingest.py

Enhanced document ingestion, chunking, and checksum management for the RAG pipeline.
Supports multiple file formats: PDF, Word, Text, Markdown, CSV, JSON, PowerPoint, and Excel.
Ensures only changed documents are reprocessed using checksum verification.

Supported File Types:
- PDF (.pdf) - Using UnstructuredPDFLoader (requires Poppler)
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

# Keep OneDNN disabled as a safety net for CPU-only fallback scenarios.
# With paddlepaddle-gpu these are harmless but prevent crashes if GPU init fails.
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_use_onednn", "0")
os.environ.setdefault("FLAGS_enable_onednn_fusion", "0")

import torch  # Required first to prevent WinError 127 with PaddleOCR DLLs
import pickle
import hashlib

# Inject local binary paths for Poppler
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_poppler_path = os.path.join(_project_root, "bin", "poppler", "poppler-24.02.0", "Library", "bin")
os.environ["PATH"] = f"{_poppler_path};{os.environ.get('PATH', '')}"

# Detect whether PaddlePaddle has GPU support
_paddle_use_gpu = False
try:
    import paddle
    _paddle_use_gpu = paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
except Exception:
    pass

# Configure Unstructured to use PaddleOCR if available
try:
    import paddle
    import unstructured_paddleocr
    os.environ["OCR_AGENT"] = "unstructured.partition.utils.ocr_models.paddle_ocr.OCRAgentPaddle"
    
    # Monkey-patch PaddleOCR to fix "eng" language mapping, enable GPU, and fix NameError
    _original_init = unstructured_paddleocr.PaddleOCR.__init__
    def _patched_init(self, **kwargs):
        if kwargs.get("lang") == "eng":
            kwargs["lang"] = "en"
        # Enable GPU acceleration when available
        if _paddle_use_gpu:
            kwargs.setdefault("use_gpu", True)
            kwargs.setdefault("use_angle_cls", True)
        _original_init(self, **kwargs)
    unstructured_paddleocr.PaddleOCR.__init__ = _patched_init
    
    # Fix NameError in unstructured
    import unstructured.partition.utils.ocr_models.paddle_ocr as _paddle_ocr_module
    from unstructured_inference.inference.layoutelement import LayoutElements
    _paddle_ocr_module.LayoutElements = LayoutElements
except ImportError:
    # If paddle or unstructured_paddleocr is not available, we don't set OCR_AGENT
    # so Unstructured will fall back to default PDF partitioning strategy (e.g. pdfminer)
    pass



from langchain_community.document_loaders import (
    UnstructuredPDFLoader, 
    UnstructuredWordDocumentLoader, 
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredPowerPointLoader
)
import pandas as pd
import json
from langchain_experimental.text_splitter import SemanticChunker
from src.embed_store import get_embedding_model
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
            return _create_pdf_loader(file_path)
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

def _create_pdf_loader(file_path):
    """
    Create a PDF loader with graceful OCR fallback.
    
    Tries UnstructuredPDFLoader with OCR (PaddleOCR) first. If PaddleOCR crashes
    (e.g., due to OneDNN fused_conv2d errors), falls back to 'fast' strategy
    which uses pdfminer for text extraction without OCR.
    
    Args:
        file_path (str): Path to the PDF file.
    Returns:
        A loader whose .load() will attempt OCR first, then fall back.
    """
    class _RobustPDFLoader:
        def __init__(self, path):
            self._path = path
        
        def load(self):
            # Attempt 1: full Unstructured pipeline with OCR
            try:
                loader = UnstructuredPDFLoader(
                    self._path, mode="single", languages=["en"]
                )
                return loader.load()
            except Exception as ocr_err:
                logger.warning(
                    "PDF OCR extraction failed, falling back to fast (pdfminer) strategy",
                    file_path=self._path,
                    error=str(ocr_err)[:200],
                )
            
            # Attempt 2: fast strategy (pdfminer, no OCR)
            try:
                loader = UnstructuredPDFLoader(
                    self._path, mode="single", strategy="fast"
                )
                return loader.load()
            except Exception as fast_err:
                logger.error(
                    "PDF fast-strategy extraction also failed",
                    file_path=self._path,
                    error=str(fast_err)[:200],
                )
                raise DocumentProcessingError(
                    f"All PDF extraction strategies failed for {os.path.basename(self._path)}",
                    {"file_path": self._path, "ocr_error": str(ocr_err)[:200], "fast_error": str(fast_err)[:200]},
                ) from fast_err
    
    return _RobustPDFLoader(file_path)


def _create_excel_loader(file_path):
    """
    Create a custom loader for Excel files by converting the workbook to
    a single in-memory document. This avoids persisting temporary files
    on disk and keeps lifecycle management straightforward.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        Loader compatible with LangChain's document interface.
    """
    from langchain.schema import Document

    try:
        # Read every sheet and render a textual representation so downstream
        # chunking receives a single unified payload.
        df = pd.read_excel(file_path, sheet_name=None)

        sections = []
        for sheet_name, sheet_df in df.items():
            sections.append(f"Sheet: {sheet_name}\n")
            sections.append(sheet_df.to_string(index=False))
            sections.append("\n\n")

        combined_text = "".join(sections).strip()
        document = Document(
            page_content=combined_text,
            metadata={
                "source": file_path,
                "file_type": "xlsx",
                "sheet_names": list(df.keys()),
            },
        )

        class _ExcelInlineLoader:
            def __init__(self, doc):
                self._doc = doc

            def load(self):
                return [self._doc]

        return _ExcelInlineLoader(document)

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
        while chunk := f.read(8192):
            hasher.update(chunk)
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

    embedding_model = get_embedding_model()
    splitter = SemanticChunker(embedding_model)
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