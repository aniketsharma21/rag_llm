"""FastAPI application for the RAG pipeline web service.

This module implements a RESTful API and WebSocket interface for interacting with
the RAG (Retrieval-Augmented Generation) pipeline. It provides endpoints for
document ingestion, querying, and conversation management.

Key Features:
- Document upload and processing
- Real-time question answering via REST and WebSocket
- Conversation history management
- File preview and management
- Health monitoring and metrics

Dependencies:
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- SQLAlchemy: Database ORM

Environment Variables:
- DATABASE_URL: Database connection string
- LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
- DEBUG: Enable debug mode
"""
import os
import json
import asyncio
import time
from typing import List, Optional, Dict, Any

from datetime import datetime
import contextlib
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from pydantic import BaseModel, Field, field_validator
from src.llm import get_llm, run_llm_health_check
from src.logging_config import get_logger
from src.exceptions import (
    RAGException,
    DocumentProcessingError,
    VectorStoreError,
    LLMError,
    ValidationError,
    ConversationError,
)
from src.db.repositories import ConversationRepository, JobRepository
from src.db.session import get_session, init_database
from src.services.ingestion_service import IngestionService
from src.services.rag_service import RAGService, RAGApplicationService
from src.middleware.observability import setup_observability

# Initialize logger
logger = get_logger(__name__)

ingestion_service = IngestionService()
rag_service = RAGService()
app_service = RAGApplicationService(ingestion_service, rag_service)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - framework integration
    await init_database()
    warmup_task: Optional[asyncio.Task] = None
    try:
        run_llm_health_check()
        logger.info("LLM provider health check succeeded")
    except Exception as exc:
        logger.error("LLM provider health check failed", error=str(exc))
        raise

    warmup_task = asyncio.create_task(rag_service.warmup())
    try:
        yield
    finally:
        if warmup_task:
            warmup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await warmup_task


def _get_files_inventory() -> List[Dict[str, Any]]:
    from src.config import RAW_DATA_DIR

    inventory: List[Dict[str, Any]] = []
    if not os.path.exists(RAW_DATA_DIR):
        return inventory

    for entry in os.listdir(RAW_DATA_DIR):
        absolute_path = os.path.join(RAW_DATA_DIR, entry)
        if not os.path.isfile(absolute_path):
            continue

        stats = os.stat(absolute_path)
        inventory.append({
            "name": entry,
            "size": stats.st_size,
            "uploadDate": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "previewUrl": f"/files/preview/{quote(entry)}",
        })

    inventory.sort(key=lambda item: item["uploadDate"], reverse=True)
    return inventory

# Initialize FastAPI app
app = FastAPI(
    title="RAG Pipeline API",
    description="API for document ingestion and question answering using RAG",
    version="0.2.0",
    lifespan=lifespan,
)

setup_observability(app)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Allow React frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(DocumentProcessingError)
async def document_processing_exception_handler(request: Request, exc: DocumentProcessingError):
    logger.error("Document processing error", error=str(exc), details=exc.details)
    return JSONResponse(
        status_code=422,
        content={
            "error": "Document Processing Error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(VectorStoreError)
async def vector_store_exception_handler(request: Request, exc: VectorStoreError):
    logger.error("Vector store error", error=str(exc), details=exc.details)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Vector Store Error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(LLMError)
async def llm_exception_handler(request: Request, exc: LLMError):
    logger.error("LLM error", error=str(exc), details=exc.details)
    return JSONResponse(
        status_code=503,
        content={
            "error": "LLM Service Error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning("Validation error", error=str(exc), details=exc.details)
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(ConversationError)
async def conversation_exception_handler(request: Request, exc: ConversationError):
    logger.error("Conversation error", error=str(exc), details=exc.details)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Conversation Error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(RAGException)
async def rag_exception_handler(request: Request, exc: RAGException):
    logger.error("RAG pipeline error", error=str(exc), details=exc.details)
    return JSONResponse(
        status_code=500,
        content={
            "error": "RAG Pipeline Error",
            "message": exc.message,
            "details": exc.details
        }
    )

# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User question")
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="List of previous messages in the conversation"
    )
    conversation_id: Optional[int] = Field(None, description="Conversation ID for persistence")
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        normalized = v.strip()
        if len(normalized) > 2000:
            raise ValueError('Question too long (max 2000 characters)')
        return normalized

    @field_validator('chat_history')
    @classmethod
    def validate_chat_history(cls, v: Optional[List[Dict[str, str]]]):
        if v and len(v) > 50:  # Limit chat history size
            return v[-50:]  # Keep only last 50 messages
        return v

class ConversationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Conversation title")
    user_id: str = Field(default="default_user", description="User ID for the conversation")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        normalized = v.strip()
        if len(normalized) > 200:
            raise ValueError('Title too long (max 200 characters)')
        return normalized

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of source documents with metadata"
    )
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score for the answer (0.0 to 1.0)"
    )
    template_used: Optional[str] = Field(
        None,
        description="Prompt template used for generation"
    )
    num_sources: Optional[int] = Field(
        None,
        description="Number of source documents retrieved"
    )


class IngestResponse(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    file_name: str
    status: str
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class HealthResponse(BaseModel):
    status: str
    model: str

class ConversationResponse(BaseModel):
    id: int
    title: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class ConversationListResponse(BaseModel):
    conversations: List[Dict[str, Any]]
    total: int

# WebSocket connection manager
class ConnectionManager:
    """Manages active WebSocket connections and their associated tasks.
    
    This class handles the lifecycle of WebSocket connections, including:
    - Tracking active connections
    - Managing message broadcasting
    - Cleaning up resources on disconnect
    - Handling concurrent tasks per connection
    
    Attributes:
        active_connections: List of currently active WebSocket connections.
        _active_tasks: Dictionary mapping WebSockets to their active tasks.
    """
    def __init__(self):
        """Initialize the connection manager with empty connection and task lists."""
        self.active_connections: List[WebSocket] = []
        self._active_tasks: Dict[WebSocket, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        task = self._active_tasks.pop(websocket, None)
        if task and not task.done():
            task.cancel()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                self.disconnect(connection)

    def set_task(self, websocket: WebSocket, task: asyncio.Task) -> None:
        self._active_tasks[websocket] = task

    def get_task(self, websocket: WebSocket) -> Optional[asyncio.Task]:
        return self._active_tasks.get(websocket)

    def clear_task(self, websocket: WebSocket) -> None:
        self._active_tasks.pop(websocket, None)
manager = ConnectionManager()

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint to verify the API is running.
    
    This endpoint performs a comprehensive health check of the API and its dependencies,
    including the LLM provider, database connection, and other critical services.
    
    Returns:
        HealthResponse: An object containing the API status and model information.
        
    Raises:
        HTTPException: If any critical service is unavailable.
    """
    try:
        # A more comprehensive health check can be added here
        # For now, we check if the LLM provider is healthy
        run_llm_health_check()
        llm = get_llm()
        model_name = getattr(llm, '_model_name', 'unknown')
        return HealthResponse(status="ok", model=model_name)
    except Exception as exc:
        logger.error("Health check failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {exc}",
        )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Retrieve the current status of a document ingestion job.
    
    This endpoint provides detailed status information about a specific document
    processing job, including progress, errors, and metadata.
    
    Args:
        job_id: The unique identifier of the ingestion job.
        
    Returns:
        JobStatusResponse: Detailed status information about the job.
        
    Raises:
        HTTPException: If the job ID is not found.
        
    Example:
        ```
        GET /status/123e4567-e89b-12d3-a456-426614174000
        ```
    """
    record = await app_service.get_job_status(job_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=record["job_id"],
        file_name=record["file_name"],
        status=record["status"],
        message=record.get("message"),
        details=record.get("details", {}),
        error=record.get("error"),
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


@app.get("/files")
async def list_uploaded_files():
    """List all uploaded and processed documents.
    
    Returns a list of documents that have been successfully uploaded and processed
    by the system, including their metadata and processing status.
    
    Returns:
        dict: A dictionary containing a list of files and their metadata.
        
    Raises:
        HTTPException: If there's an error retrieving the file list.
        
    Example:
        ```
        GET /files
        ```
    """
    try:
        files = await asyncio.to_thread(_get_files_inventory)
        return {"files": files}
    except Exception as exc:
        logger.error("Failed to list uploaded files", error=str(exc))
        raise HTTPException(status_code=500, detail="Unable to list uploaded files")


async def _process_websocket_query(
    websocket: WebSocket,
    question: str,
    chat_history: List[Dict[str, Any]],
    conversation_id: Optional[int] = None,
) -> None:
    """Process a single WebSocket query message and stream the answer."""
    await manager.send_personal_message(
        json.dumps({"type": "status", "status": "processing"}),
        websocket,
    )

    try:
        result = await app_service.query(
            question=question,
            chat_history=chat_history,
            conversation_id=conversation_id,
        )

        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "complete",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                    "confidence_score": result.get("confidence_score"),
                    "template_used": result.get("template_used"),
                    "num_sources": result.get("num_sources"),
                }
            ),
            websocket,
        )

    except RuntimeError as exc:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(exc)}),
            websocket,
        )
    except asyncio.CancelledError:
        logger.info("Generation cancelled for WebSocket client", websocket_client=str(getattr(websocket, "client", "unknown")))
        await manager.send_personal_message(
            json.dumps({"type": "status", "status": "stopped"}),
            websocket,
        )
        raise
    except Exception as exc:
        logger.error("Error processing WebSocket query", error=str(exc), exc_info=True)
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": f"Error processing your request: {exc}"}),
            websocket,
        )


# Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_rag(query: QueryRequest):
    """
    Enhanced query endpoint using the improved RAG pipeline with hybrid retrieval.
    
    Args:
        query: The query request containing the question and optional chat history
    """
    try:
        result = await app_service.query(
            question=query.question,
            chat_history=query.chat_history or [],
            conversation_id=query.conversation_id,
        )

        return QueryResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            confidence_score=result.get("confidence_score"),
            template_used=result.get("template_used"),
            num_sources=result.get("num_sources"),
        )

    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("Error processing query", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {exc}",
        )

# WebSocket endpoint for chat
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with the RAG pipeline.
    
    This endpoint maintains a persistent WebSocket connection for streaming
    responses to user queries. It handles connection lifecycle, message
    processing, and error handling.
    
    The WebSocket protocol:
    1. Client connects to /ws
    2. Client sends JSON messages with 'type' and 'data' fields
    3. Server streams responses with 'type' and 'data' fields
    4. Either side can close the connection with status code 1000
    
    Message Types (client → server):
    - 'query': Submit a new question
    - 'cancel': Cancel the current query
    
    Message Types (server → client):
    - 'status': Connection and query status updates
    - 'token': Streamed response tokens
    - 'sources': Source documents for the answer
    - 'error': Error message
    
    Args:
        websocket: The WebSocket connection instance.
        
    Raises:
        WebSocketDisconnect: When the client disconnects or an error occurs.
    """
    try:
        await manager.connect(websocket)
        logger.info("New WebSocket connection", client=str(getattr(websocket, "client", "unknown")))

        await manager.send_personal_message(
            json.dumps({"type": "status", "status": "connected"}),
            websocket,
        )

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300)
            except asyncio.TimeoutError:
                logger.warning("WebSocket receive timeout", client=str(getattr(websocket, "client", "unknown")))
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Connection timeout"}),
                    websocket,
                )
                break
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected", client=str(getattr(websocket, "client", "unknown")))
                break

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received", payload=data)
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON format"}),
                    websocket,
                )
                continue

            msg_type = message.get("type")

            if msg_type == "ping":
                await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
                continue

            if msg_type == "query":
                question = (message.get("question") or "").strip()
                if not question:
                    await manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Question cannot be empty"}),
                        websocket,
                    )
                    continue

                chat_history = message.get("chat_history", [])
                conversation_id = None
                raw_conversation_id = message.get("conversation_id")
                if raw_conversation_id is not None:
                    try:
                        conversation_id = int(raw_conversation_id)
                    except (TypeError, ValueError):
                        logger.warning(
                            "Invalid conversation_id received",
                            value=raw_conversation_id,
                        )

                existing_task = manager.get_task(websocket)
                if existing_task and not existing_task.done():
                    logger.info("Cancelling previous generation task before starting new query")
                    existing_task.cancel()
                    try:
                        await existing_task
                    except asyncio.CancelledError:
                        pass
                    finally:
                        manager.clear_task(websocket)

                task = asyncio.create_task(
                    _process_websocket_query(
                        websocket,
                        question,
                        chat_history,
                        conversation_id,
                    )
                )
                manager.set_task(websocket, task)
                task.add_done_callback(lambda t, ws=websocket: manager.clear_task(ws))
                continue

            if msg_type == "stop_generation":
                task = manager.get_task(websocket)
                if task and not task.done():
                    logger.info("Received stop generation request")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    finally:
                        manager.clear_task(websocket)
                else:
                    await manager.send_personal_message(
                        json.dumps({"type": "status", "status": "idle"}),
                        websocket,
                    )
                continue

            await manager.send_personal_message(
                json.dumps({"type": "error", "message": "Unsupported message type"}),
                websocket,
            )

    except Exception as exc:
        logger.error("WebSocket connection error", error=str(exc), exc_info=True)
    finally:
        try:
            task = manager.get_task(websocket)
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            manager.disconnect(websocket)
            logger.info("WebSocket connection closed", client=str(getattr(websocket, "client", "unknown")))
        except Exception as exc:
            logger.error("Error closing WebSocket", error=str(exc))

# File management endpoints
@app.get("/files/preview/{filename}")
def preview_file(filename: str):
    """Serve a file for preview (PDF, etc)."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    fpath = os.path.join(data_dir, safe_filename)
    
    # Ensure the resolved path is within the intended directory
    if not os.path.abspath(fpath).startswith(os.path.abspath(data_dir)):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not os.path.isfile(fpath):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(fpath)

# Conversation Management Endpoints
@app.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(user_id: str = "default_user", limit: int = 50):
    """List conversations for a user."""
    start_time = time.perf_counter()
    try:
        conversations = await app_service.list_conversations(user_id=user_id, limit=limit)
        duration = time.perf_counter() - start_time
        logger.info(
            "Listed conversations",
            user_id=user_id,
            count=len(conversations),
            duration=duration,
        )
        return ConversationListResponse(conversations=conversations, total=len(conversations))
    except ConversationError as exc:
        raise exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Unexpected error listing conversations", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to list conversations") from exc


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    """Get a specific conversation by ID."""
    try:
        conversation = await app_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info("Retrieved conversation", conversation_id=conversation_id)
        return ConversationResponse(**conversation)
    except ConversationError as exc:
        raise exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "Unexpected error getting conversation",
            conversation_id=conversation_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Failed to get conversation") from exc


@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreateRequest):
    """Create a new conversation."""
    try:
        conversation = await app_service.create_conversation(request.title, request.user_id)

        logger.info(
            "Created new conversation",
            conversation_id=conversation["id"],
            title=request.title,
        )

        return ConversationResponse(**conversation)
    except ConversationError as exc:
        raise exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Unexpected error creating conversation", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to create conversation") from exc


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation."""
    try:
        success = await app_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        logger.info("Deleted conversation", conversation_id=conversation_id)
        return {"message": "Conversation deleted successfully"}
    except ConversationError as exc:
        raise exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "Unexpected error deleting conversation",
            conversation_id=conversation_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Failed to delete conversation") from exc


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
