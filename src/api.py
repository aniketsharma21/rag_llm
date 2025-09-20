"""
api.py

FastAPI application exposing the RAG pipeline as a web service with endpoints for
document ingestion and querying. Includes WebSocket support for real-time updates.
"""
import os
import json
import asyncio
from operator import itemgetter
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

from src.ingest import process_document
from src.embed_store import build_vector_store, get_retriever, load_vector_store
from src.llm import get_llm
from src.config import logger

# Initialize FastAPI app
app = FastAPI(
    title="RAG Pipeline API",
    description="API for document ingestion and question answering using RAG",
    version="0.2.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="List of previous messages in the conversation"
    )

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of source documents with metadata"
    )

class HealthResponse(BaseModel):
    status: str
    model: str

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
        file: The document file to upload (PDF, DOCX, or TXT)
    """
    file_path = None  # Ensure file_path is always defined
    try:
        # Save the uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process the document
        chunks = process_document(file_path)
        if chunks:
            build_vector_store(chunks)
            return {"status": "success", "message": f"Document '{file.filename}' processed successfully"}
        else:
            return {"status": "skipped", "message": "Document not processed (no changes detected)"}
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_rag(query: QueryRequest):
    """
    Query the RAG pipeline with a question.
    
    Args:
        query: The query request containing the question and optional chat history
    """
    try:
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
        template = """Answer the question based on the following context. Cite the source document if possible.\n{context}\n\nQuestion: {question}\n"""
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
        sources = [getattr(d, 'metadata', {}) for d in docs]
        return {
            "answer": answer,
            "sources": sources
        }
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
                        template = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.\nIf you don't know the answer, just say that you don't know, don't try to make up an answer.\n\nContext:\n{context}\n\nChat History:\n{chat_history}\n\nQuestion: {question}\nAnswer: (Cite the source document if possible)"""
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
                            docs = input_obj.get("_retrieved_docs", [])
                            sources = [getattr(d, 'metadata', {}) for d in docs]
                            # Send completion message with sources
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "complete", 
                                    "content": full_response,
                                    "sources": sources
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

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
