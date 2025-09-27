"""
exceptions.py

Custom exception classes for the RAG pipeline. Provides specific error types
for different components to enable better error handling and user feedback.
"""


class RAGException(Exception):
    """Base exception for RAG pipeline operations."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DocumentProcessingError(RAGException):
    """Raised when document processing fails."""
    pass


class VectorStoreError(RAGException):
    """Raised when vector store operations fail."""
    pass


class LLMError(RAGException):
    """Raised when LLM operations fail."""
    pass


class EmbeddingError(RAGException):
    """Raised when embedding model operations fail."""
    pass


class ValidationError(RAGException):
    """Raised when input validation fails."""
    pass


class ConversationError(RAGException):
    """Raised when conversation management operations fail."""
    pass


class ConfigurationError(RAGException):
    """Raised when configuration is invalid or missing."""
    pass
