"""Utilities for formatting and normalizing RAG source metadata and answers.

This module provides functions to process and format source documents and their metadata
for display in the RAG pipeline. It handles tasks like source normalization,
citation formatting, and answer text processing.

Key Features:
- Source metadata normalization
- Superscript citation formatting
- Answer text cleaning and formatting
- Source attribution and display
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from src.config import BASE_DIR

SUPERSCRIPT_MAP = {
    "0": "\u2070",
    "1": "\u00B9",
    "2": "\u00B2",
    "3": "\u00B3",
    "4": "\u2074",
    "5": "\u2075",
    "6": "\u2076",
    "7": "\u2077",
    "8": "\u2078",
    "9": "\u2079",
}


def format_superscript(number: int) -> str:
    """Convert an integer into its superscript representation.
    
    Args:
        number: The integer to convert to superscript.
        
    Returns:
        str: The number formatted as a superscript string.
        
    Example:
        >>> format_superscript(123)
        '¹²³'
    """
    return "".join(SUPERSCRIPT_MAP.get(ch, ch) for ch in str(number))


def normalize_source_payload(
    source_data: Dict[str, Any],
    index: int,
    default_confidence: Optional[float] = None,
    base_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize heterogeneous source metadata into a consistent payload.
    
    This function takes source metadata from various formats and normalizes it into
    a consistent dictionary structure with standard field names and formats.
    
    Args:
        source_data: Raw source metadata dictionary from the RAG pipeline.
        index: Index of the source in the results (used for fallback citation).
        default_confidence: Default confidence score if not provided in source_data.
        base_dir: Base directory for resolving relative file paths.
        
    Returns:
        Dict[str, Any]: Normalized source payload with consistent field names.
        
    The returned dictionary includes these standardized fields:
        - source_display_path: Display-friendly path to the source
        - source_display_name: Display name for the source
        - snippet: Extracted text snippet from the source
        - citation: Formatted citation (e.g., superscript number)
        - page_number: Page number if available
        - preview_url: URL for previewing the source
        - url: Direct URL to access the source
    """
    source = dict(source_data or {})
    metadata = dict(source.get("metadata", {}) or {})

    base_dir = base_dir or BASE_DIR

    raw_path = (
        source.get("raw_file_path")
        or source.get("source_file")
        or metadata.get("raw_file_path")
        or metadata.get("source")
    )
    if raw_path:
        raw_path = os.path.abspath(raw_path)

    source_display_path = source.get("source_display_path") or metadata.get("source_display_path")
    if not source_display_path and raw_path:
        try:
            source_display_path = os.path.relpath(raw_path, base_dir)
        except Exception:
            source_display_path = raw_path

    display_name = source.get("source_display_name") or metadata.get("source_display_name")
    if not display_name and raw_path:
        display_name = os.path.basename(raw_path)
    if not display_name:
        display_name = f"Document {index}"

    content = source.get("content") or metadata.get("content")

    snippet = (
        source.get("snippet")
        or metadata.get("snippet")
        or (content.strip() if isinstance(content, str) else None)
    )
    if snippet:
        snippet = snippet.strip()
        if len(snippet) > 320:
            truncated = snippet[:320].rsplit(" ", 1)[0]
            snippet = f"{truncated}\u2026" if truncated else snippet[:320] + "\u2026"

    citation = source.get("citation") or format_superscript(source.get("id", index))

    page_number = source.get("page_number") or source.get("page")
    if page_number is None:
        if isinstance(metadata.get("page_number"), int):
            page_number = metadata.get("page_number")
        elif isinstance(metadata.get("page"), int):
            page_number = metadata.get("page") + 1

    preview_url = source.get("preview_url") or metadata.get("preview_url")
    if not preview_url and raw_path:
        filename = os.path.basename(raw_path)
        if filename:
            preview_url = f"/files/preview/{quote(filename)}"

    page_label = source.get("page_label") or metadata.get("page_label")
    if not page_label and page_number is not None:
        page_label = f"Page {page_number}"

    url = preview_url
    if not url and raw_path:
        url = f"file://{raw_path}"
        if isinstance(page_number, int):
            url = f"{url}#page={page_number}"

    metadata.update(
        {
            "raw_file_path": raw_path,
            "source_display_path": source_display_path,
            "source_display_name": display_name,
            "snippet": snippet,
            "page_number": page_number,
            "page_label": page_label,
            "preview_url": preview_url,
        }
    )

    payload: Dict[str, Any] = {
        "id": source.get("id", index),
        "citation": citation,
        "name": display_name,
        "display_name": display_name,
        "content": content,
        "snippet": snippet,
        "source_file": raw_path,
        "raw_file_path": raw_path,
        "source_display_path": source_display_path,
        "page": page_number,
        "page_number": page_number,
        "page_label": page_label,
        "relevance_score": source.get("relevance_score") or metadata.get("relevance_score"),
        "confidence": source.get("confidence") or default_confidence,
        "metadata": metadata,
        "preview_url": preview_url,
        "url": url,
    }

    for key in ("bm25_score", "retrieval_rank", "chunk_index"):
        if key in source:
            payload[key] = source[key]
        elif key in metadata:
            payload[key] = metadata[key]

    return payload


def replace_bracket_citations(text: str) -> str:
    """Replace numeric bracket citations like [1] with superscripts.
    
    Args:
        text: Input text containing bracket citations.
        
    Returns:
        str: Text with bracket citations converted to superscript.
        
    Example:
        >>> replace_bracket_citations("See reference [1]")
        'See reference ¹'
    """
    if not text:
        return text

    def _replace(match):
        return format_superscript(match.group(1))

    updated = re.sub(r"\[(\d+)\]", _replace, text)
    updated = re.sub(r"\^\{?(\d+)\}?", _replace, updated)
    return updated


def apply_superscript_citations(
    answer: str,
    sources: List[Dict[str, Any]],
    append_sources_block: bool = True,
) -> str:
    """Apply superscript citations and optionally append a Sources block.
    
    Processes the answer text to add proper citation formatting and optionally
    appends a formatted sources section at the end.
    
    Args:
        answer: The answer text to process.
        sources: List of source dictionaries with metadata.
        append_sources_block: Whether to append the sources section.
        
    Returns:
        str: Processed answer with formatted citations and sources.
    """
    if not answer:
        return ""

    formatted_answer = replace_bracket_citations(answer).strip()

    if append_sources_block and sources:
        entries = []
        for source in sources:
            display_name = (
                source.get("source_display_name")
                or source.get("display_name")
                or source.get("name")
                or source.get("source_file")
                or "Source"
            )

            page_label = source.get("page_label")
            if not page_label:
                page_number = source.get("page") or source.get("page_number")
                if isinstance(page_number, int):
                    page_label = f"Page {page_number}"

            entry = f"- {display_name}"
            if page_label:
                entry += f" — {page_label}"

            metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
            section = metadata.get("section")
            if section:
                entry += f" (Section: {section})"

            entries.append(entry)

        if entries:
            formatted_answer = f"{formatted_answer}\n\nSources:\n" + "\n".join(entries)

    return formatted_answer


def clean_answer_text(answer: str) -> str:
    """Normalize whitespace and remove trailing Sources blocks.
    
    Args:
        answer: The answer text to clean.
        
    Returns:
        str: Cleaned answer text with normalized whitespace and no trailing sources.
        
    Note:
        This is useful for preparing text for display or further processing.
    """
    if not answer:
        return ""

    cleaned = answer.strip()
    cleaned = re.sub(r"\n+Sources?:.*$", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def split_answer_into_paragraphs(answer: str) -> List[str]:
    """Split an answer into paragraphs for streaming/UX purposes.
    
    Args:
        answer: The answer text to split.
        
    Returns:
        List[str]: List of paragraphs, where each paragraph is a string.
        
    Note:
        This is particularly useful for streaming responses where you want to
        show text progressively rather than all at once.
    """
    if not answer:
        return []
    return [paragraph.strip() for paragraph in answer.split("\n\n") if paragraph.strip()]
