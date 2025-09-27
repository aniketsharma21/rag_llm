"""
api.py

FastAPI application exposing the RAG pipeline as a web service with endpoints for
document ingestion and querying. Includes WebSocket support for real-time updates.
"""
import os
import json
import asyncio
import tempfile
import time
from operator import itemgetter
from typing import List, Optional, Dict, Any
import pickle

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field, validator
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
import yaml
from src.ingest import process_document
from src.embed_store import build_vector_store, get_retriever, load_vector_store
from src.llm import get_llm, EnhancedRAGChain
from src.config import PROMPTS_DIR, BASE_DIR
from src.logging_config import get_logger
from src.exceptions import (
    RAGException, DocumentProcessingError, VectorStoreError, 
    LLMError, ValidationError, ConversationError
)
from src.database import ConversationManager, DocumentManager

# Initialize logger
logger = get_logger(__name__)

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


def _format_superscript(number: int) -> str:
    return "".join(SUPERSCRIPT_MAP.get(ch, ch) for ch in str(number))


def _normalize_source_payload(
    source_data: Dict[str, Any],
    index: int,
    default_confidence: Optional[float] = None
) -> Dict[str, Any]:
    source = dict(source_data or {})
    metadata = dict(source.get("metadata", {}) or {})

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
            source_display_path = os.path.relpath(raw_path, BASE_DIR)
        except Exception:
            source_display_path = raw_path

    display_name = source.get("source_display_name") or metadata.get("source_display_name")
    if not display_name and raw_path:
        display_name = os.path.basename(raw_path)
    if not display_name:
        display_name = f"Document {index}"

    content = source.get("content") or metadata.get("content")

    citation = source.get("citation") or _format_superscript(source.get("id", index))

    page_number = source.get("page_number") or source.get("page")
    if page_number is None:
        if isinstance(metadata.get("page_number"), int):
            page_number = metadata.get("page_number")
        elif isinstance(metadata.get("page"), int):
            page_number = metadata.get("page") + 1

    url = None
    if raw_path:
        url = f"file://{raw_path}"
        if isinstance(page_number, int):
            url = f"{url}#page={page_number}"

    # Ensure metadata includes enriched fields for downstream consumers
    metadata.update({
        "raw_file_path": raw_path,
        "source_display_path": source_display_path,
        "source_display_name": display_name,
    })

    payload: Dict[str, Any] = {
        "id": source.get("id", index),
        "citation": citation,
        "name": display_name,
        "display_name": display_name,
        "content": content,
        "source_file": raw_path,
        "raw_file_path": raw_path,
        "source_display_path": source_display_path,
        "page": page_number,
        "page_number": page_number,
        "relevance_score": source.get("relevance_score") or metadata.get("relevance_score"),
        "confidence": source.get("confidence") or default_confidence,
        "metadata": metadata,
        "url": url,
    }

    for key in ("bm25_score", "retrieval_rank", "chunk_index"):
        if key in source:
            payload[key] = source[key]
        elif key in metadata:
            payload[key] = metadata[key]

    return payload


def _apply_superscript_citations(answer: str, sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return answer

    formatted_answer = (answer or "").rstrip()

    # Remove any existing Sources block to prevent duplication
    if "\nSources:" in formatted_answer:
        formatted_answer = formatted_answer.split("\nSources:", 1)[0].rstrip()

    citation_lines = []
    for source in sources:
        citation = source.get("citation") or _format_superscript(source.get("id", 0))
        display_name = source.get("name") or source.get("display_name") or "Document"
        page_number = source.get("page") or source.get("page_number")
        page_text = f" (Page {page_number})" if page_number else ""
        citation_lines.append(f"{citation} {display_name}{page_text}")

    if citation_lines:
        citations_block = "\n".join(citation_lines)
        formatted_answer = f"{formatted_answer}\n\nSources:\n{citations_block}"

    return formatted_answer

# Initialize FastAPI app
app = FastAPI(
    title="RAG Pipeline API",
    description="API for document ingestion and question answering using RAG",
    version="0.2.0"
)

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
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        # Basic sanitization
        v = v.strip()
        if len(v) > 2000:
            raise ValueError('Question too long (max 2000 characters)')
        return v
    
    @validator('chat_history')
    def validate_chat_history(cls, v):
        if v and len(v) > 50:  # Limit chat history size
            return v[-50:]  # Keep only last 50 messages
        return v

class ConversationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Conversation title")
    user_id: str = Field(default="default_user", description="User ID for the conversation")
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        v = v.strip()
        if len(v) > 200:
            raise ValueError('Title too long (max 200 characters)')
        return v

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
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

# Global enhanced RAG chain instance
enhanced_rag_chain = None

def get_enhanced_rag_chain():
    """Get or create the enhanced RAG chain instance."""
    global enhanced_rag_chain
    
    if enhanced_rag_chain is None:
        try:
            vectordb = load_vector_store()
            if not vectordb:
                logger.warning("Vector store not found, cannot create enhanced RAG chain")
                return None
            
            # Load all processed documents for BM25 retrieval
            from src.config import PROCESSED_DATA_DIR
            documents = []
            
            if os.path.exists(PROCESSED_DATA_DIR):
                for filename in os.listdir(PROCESSED_DATA_DIR):
                    if filename.endswith('_chunks.pkl'):
                        chunk_path = os.path.join(PROCESSED_DATA_DIR, filename)
                        try:
                            with open(chunk_path, 'rb') as f:
                                chunks = pickle.load(f)
                                documents.extend(chunks)
                        except Exception as e:
                            logger.warning(f"Failed to load chunks from {filename}: {e}")
            
            if documents:
                enhanced_rag_chain = EnhancedRAGChain(vectordb, documents)
                logger.info(f"Created enhanced RAG chain with {len(documents)} documents")
            else:
                logger.warning("No documents found for enhanced RAG chain")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create enhanced RAG chain: {e}")
            return None
    
    return enhanced_rag_chain

def reset_enhanced_rag_chain():
    """Reset the enhanced RAG chain (call after new documents are added)."""
    global enhanced_rag_chain
    enhanced_rag_chain = None

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify the API is running."""
    try:
        llm = get_llm()
        return {
            "status": "healthy",
            "model": llm.model_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )

# Document upload endpoint
@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload and index a document for the RAG pipeline.
    
    Args:
        file: The document file to upload (PDF, DOCX, TXT, CSV, JSON, MD, PPTX, XLSX)
    """
    try:
        from src.config import RAW_DATA_DIR
        
        # Ensure raw data directory exists
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        
        # Save the uploaded file to /data/raw with original filename
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = file.filename.replace(" ", "_").replace("..", "")
        permanent_file_path = os.path.join(RAW_DATA_DIR, safe_filename)
        
        # Handle duplicate filenames by adding a counter
        counter = 1
        original_path = permanent_file_path
        while os.path.exists(permanent_file_path):
            name_without_ext = os.path.splitext(safe_filename)[0]
            permanent_file_path = os.path.join(RAW_DATA_DIR, f"{name_without_ext}_{counter}{file_extension}")
            counter += 1
        
        # Write the uploaded file to permanent location
        with open(permanent_file_path, "wb") as f:
            f.write(await file.read())
        
        logger.info(f"Saved uploaded file to: {permanent_file_path}")
        
        # Process the document from the permanent location
        chunks = process_document(permanent_file_path)
        if chunks:
            build_vector_store(chunks)
            # Reset enhanced RAG chain to include new documents
            reset_enhanced_rag_chain()
            return {
                "status": "success", 
                "message": f"Document '{file.filename}' uploaded and processed successfully",
                "file_path": permanent_file_path
            }
        else:
            return {
                "status": "skipped", 
                "message": "Document not processed (no changes detected)",
                "file_path": permanent_file_path
            }
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        # Clean up file if processing failed
        if 'permanent_file_path' in locals() and os.path.exists(permanent_file_path):
            try:
                os.remove(permanent_file_path)
                logger.info(f"Cleaned up failed upload: {permanent_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup file: {cleanup_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
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
        # Try to use enhanced RAG chain first
        enhanced_chain = get_enhanced_rag_chain()
        
        if enhanced_chain:
            # Use enhanced RAG chain with hybrid retrieval
            result = enhanced_chain.query(
                question=query.question,
                template_type=None,  # Auto-select template
                k=5,
                include_sources=True,
                conversation_context=bool(query.chat_history)
            )
            
            raw_sources = result.get("sources", [])
            formatted_sources = [
                _normalize_source_payload(source, idx + 1, result.get("confidence_score"))
                for idx, source in enumerate(raw_sources)
            ]

            answer = _apply_superscript_citations(result.get("answer", ""), formatted_sources)

            return QueryResponse(
                answer=answer,
                sources=formatted_sources,
                confidence_score=result.get("confidence_score"),
                template_used=result.get("template_used"),
                num_sources=result.get("num_sources")
            )
        
        else:
            # Fallback to original RAG implementation
            logger.warning("Enhanced RAG chain not available, using fallback")
            
            llm = get_llm()
            vectordb = load_vector_store()
            if not vectordb:
                raise HTTPException(
                    status_code=500,
                    detail="Vector store not found. Please upload and ingest a document first."
                )
            retriever = get_retriever(vectordb)
            if not retriever:
                raise HTTPException(
                    status_code=500,
                    detail="Retriever could not be created."
                )
            
            prompt_path = os.path.join(PROMPTS_DIR, "rag_prompts.yaml")
            with open(prompt_path, 'r') as f:
                prompt_config = yaml.safe_load(f)
            template = prompt_config['template']

            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )
            
            async def get_context(x):
                docs = await retriever.ainvoke(x["question"])
                context = "\n\n".join([
                    f"[Source: {getattr(d, 'metadata', {}).get('source', 'unknown')}] {d.page_content}" for d in docs
                ])
                x["_retrieved_docs"] = docs  # Attach docs for later use
                return context
            
            rag_chain = (
                {"context": get_context, "question": lambda x: x["question"]}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            # Run the chain and get docs
            input_obj = {"question": query.question}
            answer = await rag_chain.ainvoke(input_obj)
            docs = input_obj.get("_retrieved_docs", [])
            formatted_sources = [
                _normalize_source_payload(
                    {
                        "id": idx + 1,
                        "content": doc.page_content,
                        "metadata": getattr(doc, 'metadata', {})
                    },
                    idx + 1
                )
                for idx, doc in enumerate(docs)
            ]

            answer = _apply_superscript_citations(answer, formatted_sources)
            
            return QueryResponse(
                answer=answer,
                sources=formatted_sources,
                confidence_score=None,
                template_used="fallback",
                num_sources=len(formatted_sources)
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

# WebSocket endpoint for chat
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with the RAG pipeline."""
    try:
        await manager.connect(websocket)
        logger.info(f"New WebSocket connection from {websocket.client}")
        
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({"type": "status", "status": "connected"}),
            websocket
        )
        
        while True:
            try:
                # Set a timeout for receiving messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300)  # 5 minute timeout
                
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {data}")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }),
                        websocket
                    )
                    continue
                
                if message.get("type") == "query":
                    # Process the query
                    question = message.get("question", "")
                    if not question.strip():
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "error",
                                "message": "Question cannot be empty"
                            }),
                            websocket
                        )
                        continue
                        
                    chat_history = message.get("chat_history", [])
                    
                    # Send acknowledgment
                    await manager.send_personal_message(
                        json.dumps({"type": "status", "status": "processing"}),
                        websocket
                    )
                    
                    try:
                        # Try to use enhanced RAG chain first
                        enhanced_chain = get_enhanced_rag_chain()
                        
                        if enhanced_chain:
                            # Use enhanced RAG chain with streaming simulation
                            result = enhanced_chain.query(
                                question=question,
                                template_type=None,  # Auto-select template
                                k=5,
                                include_sources=True,
                                conversation_context=bool(chat_history)
                            )

                            raw_sources = result.get("sources", [])
                            formatted_sources = [
                                _normalize_source_payload(source, idx + 1, result.get("confidence_score"))
                                for idx, source in enumerate(raw_sources)
                            ]

                            formatted_answer = _apply_superscript_citations(result.get("answer", ""), formatted_sources)

                            # Simulate streaming by sending the formatted answer in chunks
                            chunk_size = 10  # Send 10 characters at a time
                            
                            for i in range(0, len(formatted_answer), chunk_size):
                                chunk = formatted_answer[i:i + chunk_size]
                                try:
                                    await manager.send_personal_message(
                                        json.dumps({
                                            "type": "chunk", 
                                            "content": chunk
                                        }),
                                        websocket
                                    )
                                    # Small delay to simulate streaming
                                    await asyncio.sleep(0.05)
                                except Exception as send_error:
                                    logger.error(f"Error sending chunk: {str(send_error)}")
                                    raise
                            
                            # Send completion message with enhanced metadata
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "complete", 
                                    "content": formatted_answer,
                                    "sources": formatted_sources,
                                    "confidence_score": result.get("confidence_score"),
                                    "template_used": result.get("template_used"),
                                    "num_sources": result.get("num_sources")
                                }),
                                websocket
                            )
                            
                        else:
                            # Fallback to original implementation
                            logger.warning("Enhanced RAG chain not available, using fallback for WebSocket")
                            
                            llm = get_llm()
                            vectordb = load_vector_store()
                            if not vectordb:
                                await manager.send_personal_message(
                                    json.dumps({
                                        "type": "error",
                                        "message": "Vector store not found. Please upload and ingest a document first."
                                    }),
                                    websocket
                                )
                                continue
                            retriever = get_retriever(vectordb)
                            if not retriever:
                                await manager.send_personal_message(
                                    json.dumps({
                                        "type": "error",
                                        "message": "Retriever could not be created."
                                    }),
                                    websocket
                                )
                                continue
                            formatted_history = "\n".join([
                                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}" 
                                for msg in chat_history if isinstance(msg, dict)
                            ])
                            template = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.\nIf you don't know the answer, just say that you don't know, don't try to make up an answer.\n\nContext:\n{context}\n\nChat History:\n{chat_history}\n\nQuestion: {question}\nAnswer:"""
                            prompt = PromptTemplate(
                                template=template,
                                input_variables=["context", "chat_history", "question"]
                            )
                            async def get_context(x):
                                docs = await retriever.ainvoke(x["question"])
                                context = "\n\n".join([
                                    f"[Source: {getattr(d, 'metadata', {}).get('source', 'unknown')}] {d.page_content}" for d in docs
                                ])
                                x["_retrieved_docs"] = docs
                                return context
                            rag_chain = (
                                {
                                    "context": get_context,
                                    "chat_history": lambda x: x["chat_history"],
                                    "question": lambda x: x["question"]
                                }
                                | prompt
                                | llm
                                | StrOutputParser()
                            )
                            # Stream the response and collect sources
                            full_response = ""
                            sources = []
                            try:
                                input_obj = {"question": question, "chat_history": formatted_history}
                                async for chunk in rag_chain.astream(input_obj):
                                    if chunk and isinstance(chunk, str):
                                        full_response += chunk
                                        try:
                                            await manager.send_personal_message(
                                                json.dumps({
                                                    "type": "chunk", 
                                                    "content": chunk
                                                }),
                                                websocket
                                            )
                                        except Exception as send_error:
                                            logger.error(f"Error sending chunk: {str(send_error)}")
                                            raise
                                retrieved_docs = input_obj.get("_retrieved_docs", [])
                                formatted_sources = [
                                    _normalize_source_payload(
                                        {
                                            "id": idx + 1,
                                            "content": getattr(doc, 'page_content', ''),
                                            "metadata": getattr(doc, 'metadata', {})
                                        },
                                        idx + 1
                                    )
                                    for idx, doc in enumerate(retrieved_docs)
                                ]

                                formatted_full_response = _apply_superscript_citations(full_response, formatted_sources)

                                # Send completion message with sources
                                await manager.send_personal_message(
                                    json.dumps({
                                        "type": "complete", 
                                        "content": formatted_full_response,
                                        "sources": formatted_sources
                                    }),
                                    websocket
                                )
                            except asyncio.CancelledError:
                                logger.info("Generation was cancelled by the client")
                                await manager.send_personal_message(
                                    json.dumps({
                                        "type": "status",
                                        "status": "cancelled"
                                    }),
                                    websocket
                                )
                                raise
                    except Exception as e:
                        logger.error(f"Error processing query: {str(e)}", exc_info=True)
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "error", 
                                "message": f"Error processing your request: {str(e)}"
                            }),
                            websocket
                        )
                
                elif message.get("type") == "ping":
                    # Handle ping/pong for keep-alive
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )
                
                elif message.get("type") == "stop_generation":
                    # Handle stop generation request
                    # TODO: Implement the logic to stop the generation process
                    logger.info("Received stop generation request")
                    await manager.send_personal_message(
                        json.dumps({"type": "status", "status": "stopped"}),
                        websocket
                    )

            except asyncio.TimeoutError:
                # Handle client timeout (no data received for a while)
                logger.warning(f"Connection timeout for {websocket.client}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Connection timeout"
                    }),
                    websocket
                )
                break
                
            except WebSocketDisconnect:
                logger.info(f"Client {websocket.client} disconnected")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in WebSocket: {str(e)}", exc_info=True)
                try:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "An unexpected error occurred"
                        }),
                        websocket
                    )
                except:
                    pass
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
    finally:
        # Ensure the connection is properly closed
        try:
            manager.disconnect(websocket)
            logger.info(f"WebSocket connection closed for {getattr(websocket, 'client', 'unknown')}")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}")

# File management endpoints
@app.get("/files")
def list_files():
    """List uploaded/ingested files with metadata and preview URLs."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    files = []
    for fname in os.listdir(data_dir):
        fpath = os.path.join(data_dir, fname)
        if os.path.isfile(fpath):
            files.append({
                'name': fname,
                'url': f"/files/preview/{fname}"
            })
    return {"files": files}

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
    try:
        start_time = time.time()
        conversations = ConversationManager.list_conversations(user_id, limit)
        duration = time.time() - start_time
        
        logger.info("Listed conversations", 
                   user_id=user_id, 
                   count=len(conversations), 
                   duration=duration)
        
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations)
        )
    except ConversationError as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error listing conversations", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list conversations")

@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int):
    """Get a specific conversation by ID."""
    try:
        conversation = ConversationManager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info("Retrieved conversation", conversation_id=conversation_id)
        return ConversationResponse(**conversation)
    except ConversationError as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error getting conversation", 
                    conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get conversation")

@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreateRequest):
    """Create a new conversation."""
    try:
        conversation = ConversationManager.create_conversation(
            title=request.title.strip(),
            messages=[],
            user_id=request.user_id
        )
        
        logger.info("Created new conversation", 
                   conversation_id=conversation["id"], 
                   title=request.title)
        
        return ConversationResponse(**conversation)
    except ConversationError as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error creating conversation", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create conversation")

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation."""
    try:
        success = ConversationManager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info("Deleted conversation", conversation_id=conversation_id)
        return {"message": "Conversation deleted successfully"}
    except ConversationError as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error deleting conversation", 
                    conversation_id=conversation_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
