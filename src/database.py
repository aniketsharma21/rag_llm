"""Database models and connection management for the RAG application.

This module previously provided synchronous SQLAlchemy models and utilities. It has been refactored to use the async-first approach defined in `src/db/`.

For database interactions, use the async models and session from `src/db/`.
"""

# This file is deprecated. All database interactions should use `src/db/`.

raise DeprecationWarning(
    "The `src/database.py` module is deprecated. Use `src/db/` for async database operations."
)
