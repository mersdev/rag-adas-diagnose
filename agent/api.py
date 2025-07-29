"""
FastAPI backend for ADAS Diagnostics Co-pilot.

This module provides the REST API endpoints for the Streamlit frontend
to communicate with the agent and access diagnostic capabilities.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from .agent import get_agent, initialize_agent, close_agent
from .models import (
    ChatRequest, ChatResponse,
    HealthResponse, IngestionRequest, IngestionResponse,
    SessionCreate, SessionResponse, MessageResponse
)
from .db_utils import create_session, get_session, add_message, get_session_messages
from .db_utils import get_db_manager, initialize_database, close_database
from .config import get_settings
from ingestion import IngestionPipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ADAS Diagnostics Co-pilot API")
    try:
        # Initialize database
        settings = get_settings()
        await initialize_database(settings.database.database_url)
        logger.info("Database initialized successfully")

        # Initialize agent
        await initialize_agent()
        logger.info("Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ADAS Diagnostics Co-pilot API")
    await close_agent()
    await close_database()


# Create FastAPI app
app = FastAPI(
    title="ADAS Diagnostics Co-pilot API",
    description="AI-powered automotive diagnostics assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        agent = await get_agent()
        return HealthResponse(
            status="healthy",
            message="ADAS Diagnostics Co-pilot is running",
            agent_initialized=agent is not None
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"Service error: {str(e)}",
            agent_initialized=False
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat request with the ADAS agent."""
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = await create_session(request.user_id)
        else:
            # Verify session exists
            session = await get_session(session_id)
            if not session:
                session_id = await create_session(request.user_id)

        # Save user message
        await add_message(session_id, "user", request.message, {"user_id": request.user_id})

        # Get conversation context
        messages = await get_session_messages(session_id, limit=20)
        conversation_context = []
        for msg in messages[:-1]:  # Exclude the message we just added
            conversation_context.append(f"{msg['role']}: {msg['content']}")

        # Create enhanced request with context
        if conversation_context:
            context_str = "\n".join(conversation_context[-10:])  # Last 5 turns
            enhanced_message = f"Previous conversation:\n{context_str}\n\nCurrent question: {request.message}"
        else:
            enhanced_message = request.message

        # Create new request with enhanced message
        enhanced_request = ChatRequest(
            message=enhanced_message,
            user_id=request.user_id,
            session_id=session_id,
            search_type=request.search_type,
            max_results=request.max_results
        )

        agent = await get_agent()
        response = await agent.chat(enhanced_request)

        # Save assistant response
        await add_message(session_id, "assistant", response.message, {
            "tools_used": [tool.model_dump() for tool in response.tools_used],
            "sources": [source.model_dump() for source in response.sources],
            "processing_time": response.processing_time
        })

        # Add session_id to response
        response.session_id = session_id
        return response

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response from the ADAS agent."""
    async def generate_response():
        try:
            agent = await get_agent()
            
            # For now, we'll simulate streaming by yielding the complete response
            # In a full implementation, you'd integrate with Pydantic AI's streaming capabilities
            response = await agent.chat(request)
            
            # Yield response in chunks
            import json
            from .models import UUIDEncoder
            response_data = response.model_dump()
            yield f"data: {json.dumps(response_data, cls=UUIDEncoder)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            error_response = {
                "error": str(e),
                "message": "Failed to process chat request"
            }
            yield f"data: {json.dumps(error_response, cls=UUIDEncoder)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )





@app.post("/ingest", response_model=IngestionResponse)
async def ingest_documents(request: IngestionRequest, background_tasks: BackgroundTasks):
    """Ingest documents into the system."""
    try:
        # Run ingestion in background
        background_tasks.add_task(run_ingestion, request)
        
        return IngestionResponse(
            message="Ingestion started",
            status="processing",
            task_id=None  # Could implement task tracking
        )
    except Exception as e:
        logger.error(f"Failed to start ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_ingestion(request: IngestionRequest):
    """Run document ingestion in background."""
    try:
        pipeline = IngestionPipeline()
        await pipeline.initialize()
        
        if request.file_paths:
            for file_path in request.file_paths:
                await pipeline.process_file(file_path)
        
        if request.directory_path:
            await pipeline.process_directory(
                request.directory_path,
                recursive=request.recursive
            )
        
        if request.sample_data:
            await pipeline.process_sample_data()
        
        logger.info("Ingestion completed successfully")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")


@app.post("/sessions", response_model=SessionResponse)
async def create_new_session(request: SessionCreate):
    """Create a new chat session."""
    try:
        session_id = await create_session(request.user_id, request.metadata)
        session = await get_session(session_id)

        return SessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            metadata=session["metadata"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            expires_at=session["expires_at"]
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information."""
    try:
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            id=session["id"],
            user_id=session["user_id"],
            metadata=session["metadata"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            expires_at=session["expires_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, limit: int = 50):
    """Get messages for a session."""
    try:
        # Verify session exists
        session = await get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = await get_session_messages(session_id, limit)

        return [
            MessageResponse(
                id=msg["id"],
                session_id=msg["session_id"],
                role=msg["role"],
                content=msg["content"],
                metadata=msg["metadata"],
                created_at=msg["created_at"]
            )
            for msg in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        db_manager = await get_db_manager()

        # Get document count
        async with db_manager.get_connection() as conn:
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
            session_count = await conn.fetchval("SELECT COUNT(*) FROM sessions WHERE expires_at > CURRENT_TIMESTAMP OR expires_at IS NULL")

        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "sessions": session_count,
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_documents(
    query: str,
    limit: int = 10,
    content_type: Optional[str] = None,
    vehicle_system: Optional[str] = None
):
    """Search documents using hybrid search."""
    try:
        agent = await get_agent()
        
        # Use the agent's hybrid search tool
        from agent.tools import HybridSearchQuery
        search_query = HybridSearchQuery(
            query=query,
            limit=limit,
            content_type=content_type,
            vehicle_system=vehicle_system
        )
        
        # Initialize tools if needed
        if not agent.tools.db_manager:
            await agent.tools.initialize()
        
        results = await agent.tools.hybrid_search(search_query)
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import os
    from agent.config import get_settings
    
    settings = get_settings()
    
    uvicorn.run(
        "agent.api:app",
        host="0.0.0.0",
        port=settings.app.app_port,
        reload=True,
        log_level="info"
    )
