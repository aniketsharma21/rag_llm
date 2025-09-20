"""
Main entry point for the RAG LLM application.
This file is used to run the FastAPI application in production.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1  # For development; remove or increase for production
    )
