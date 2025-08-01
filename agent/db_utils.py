"""
Database utilities for ADAS Diagnostics Co-pilot.

This module provides database connection management and utility functions
for PostgreSQL with pgvector extension.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, Tuple, AsyncGenerator
from uuid import UUID

import asyncpg
import numpy as np
from asyncpg import Pool, Connection

from .models import (
    Document, DocumentCreate, DocumentUpdate,
    Chunk, ChunkCreate,
    SearchResult, VectorSearchResult, ProcessingStatus
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and operation manager."""
    
    def __init__(self, database_url: str, min_connections: int = 5, max_connections: int = 20):
        """
        Initialize database manager.
        
        Args:
            database_url: PostgreSQL connection URL
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: Optional[Pool] = None
    
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=60,
                server_settings={
                    'jit': 'off'  # Disable JIT for better performance with short queries
                }
            )
            logger.info("Database connection pool initialized")
            
            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                logger.info("Database connection test successful")
                
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get database connection from pool."""
        if not self._pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self._pool.acquire() as conn:
            yield conn
    
    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return result."""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch one row as dictionary."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results."""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)


class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_document(self, document: DocumentCreate) -> Document:
        """Create a new document."""
        query = """
        INSERT INTO documents (
            filename, title, content_type, file_path, file_size, file_hash,
            vehicle_system, component_name, supplier, model_years, vin_patterns,
            severity_level, processing_status, chunk_count
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        RETURNING *
        """
        
        row = await self.db.fetch_one(
            query,
            document.filename, document.title, document.content_type.value,
            document.file_path, document.file_size, document.file_hash,
            document.vehicle_system.value if document.vehicle_system else None,
            document.component_name, document.supplier,
            document.model_years, document.vin_patterns,
            document.severity_level.value if document.severity_level else None,
            document.processing_status.value, document.chunk_count
        )
        
        return Document(**row)
    
    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        query = "SELECT * FROM documents WHERE id = $1"
        row = await self.db.fetch_one(query, document_id)
        return Document(**row) if row else None

    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """Get document by file path."""
        query = "SELECT * FROM documents WHERE file_path = $1"
        row = await self.db.fetch_one(query, file_path)
        return Document(**row) if row else None

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete document and its associated chunks."""
        try:
            # Delete chunks first (due to foreign key constraint)
            await self.db.execute("DELETE FROM chunks WHERE document_id = $1", document_id)

            # Delete document
            result = await self.db.execute("DELETE FROM documents WHERE id = $1", document_id)

            # Check if any rows were affected
            return "DELETE 1" in result
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    async def update_document_status(self, document_id: UUID, status: ProcessingStatus) -> bool:
        """Update document processing status."""
        try:
            result = await self.db.execute(
                "UPDATE documents SET processing_status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                status.value, document_id
            )
            return "UPDATE 1" in result
        except Exception as e:
            logger.error(f"Failed to update document status {document_id}: {e}")
            return False
    
    async def update_document(self, document_id: UUID, update: DocumentUpdate) -> Optional[Document]:
        """Update document."""
        # Build dynamic update query
        set_clauses = []
        values = []
        param_count = 1
        
        for field, value in update.model_dump(exclude_unset=True).items():
            if value is not None:
                if hasattr(value, 'value'):  # Enum
                    value = value.value
                set_clauses.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not set_clauses:
            return await self.get_document(document_id)
        
        query = f"""
        UPDATE documents 
        SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ${param_count}
        RETURNING *
        """
        values.append(document_id)
        
        row = await self.db.fetch_one(query, *values)
        return Document(**row) if row else None
    
    async def list_documents(
        self, 
        content_type: Optional[str] = None,
        vehicle_system: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List documents with optional filters."""
        conditions = []
        values = []
        param_count = 1
        
        if content_type:
            conditions.append(f"content_type = ${param_count}")
            values.append(content_type)
            param_count += 1
        
        if vehicle_system:
            conditions.append(f"vehicle_system = ${param_count}")
            values.append(vehicle_system)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        SELECT * FROM documents 
        {where_clause}
        ORDER BY created_at DESC 
        LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        values.extend([limit, offset])
        
        rows = await self.db.fetch_all(query, *values)
        return [Document(**row) for row in rows]


class ChunkRepository:
    """Repository for chunk operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_chunk(self, chunk: ChunkCreate) -> Chunk:
        """Create a new chunk with embedding."""
        # Convert embedding to PostgreSQL vector format
        embedding_str = None
        if chunk.embedding:
            embedding_str = json.dumps(chunk.embedding)
        
        query = """
        INSERT INTO chunks (
            document_id, chunk_index, content, content_hash, embedding,
            start_char, end_char, token_count,
            contains_dtc_codes, contains_version_info, contains_component_info
        ) VALUES ($1, $2, $3, $4, $5::vector, $6, $7, $8, $9, $10, $11)
        RETURNING *
        """
        
        row = await self.db.fetch_one(
            query,
            chunk.document_id, chunk.chunk_index, chunk.content, chunk.content_hash,
            embedding_str, chunk.start_char, chunk.end_char, chunk.token_count,
            chunk.contains_dtc_codes, chunk.contains_version_info, chunk.contains_component_info
        )

        # Convert row to dict and handle embedding conversion
        row_dict = dict(row)
        if row_dict.get('embedding') and isinstance(row_dict['embedding'], str):
            # Convert string embedding back to list
            row_dict['embedding'] = json.loads(row_dict['embedding'])
        elif chunk.embedding:
            # Use the original embedding if database didn't return one
            row_dict['embedding'] = chunk.embedding

        return Chunk(**row_dict)
    
    async def get_chunks_by_document(self, document_id: UUID) -> List[Chunk]:
        """Get all chunks for a document."""
        query = """
        SELECT * FROM chunks 
        WHERE document_id = $1 
        ORDER BY chunk_index
        """
        rows = await self.db.fetch_all(query, document_id)
        return [Chunk(**row) for row in rows]
    
    async def vector_search(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        content_type: Optional[str] = None,
        vehicle_system: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Perform vector similarity search."""
        # Convert query embedding to PostgreSQL vector format
        embedding_str = json.dumps(query_embedding)
        
        # Build query with optional filters
        conditions = []
        values = [embedding_str, limit]
        param_count = 3
        
        if content_type:
            conditions.append(f"d.content_type = ${param_count}")
            values.append(content_type)
            param_count += 1
        
        if vehicle_system:
            conditions.append(f"d.vehicle_system = ${param_count}")
            values.append(vehicle_system)
            param_count += 1
        
        where_clause = "AND " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
        SELECT 
            c.id as chunk_id,
            c.document_id,
            c.content,
            c.chunk_index,
            d.title as document_title,
            d.filename as document_filename,
            d.content_type,
            d.vehicle_system,
            d.component_name,
            1 - (c.embedding <=> $1::vector) as similarity_score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL {where_clause}
        ORDER BY c.embedding <=> $1::vector
        LIMIT $2
        """
        
        rows = await self.db.fetch_all(query, *values)
        
        results = []
        for row in rows:
            result = VectorSearchResult(
                chunk_id=row['chunk_id'],
                document_id=row['document_id'],
                content=row['content'],
                score=row['similarity_score'],
                similarity_score=row['similarity_score'],
                chunk_index=row['chunk_index'],
                document_title=row['document_title'],
                document_filename=row['document_filename'],
                content_type=row['content_type'],
                vehicle_system=row['vehicle_system'],
                component_name=row['component_name']
            )
            results.append(result)
        
        return results





# Global database manager instance
db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if not db_manager:
        raise RuntimeError("Database manager not initialized")
    return db_manager


async def initialize_database(database_url: str) -> None:
    """Initialize the global database manager."""
    global db_manager
    db_manager = DatabaseManager(database_url)
    await db_manager.initialize()


async def close_database() -> None:
    """Close the global database manager."""
    global db_manager
    if db_manager:
        await db_manager.close()
        db_manager = None


# Session Management Functions
async def create_session(user_id: str = "default_user", metadata: Optional[Dict[str, Any]] = None) -> str:
    """Create a new session."""
    db = await get_db_manager()

    query = """
    INSERT INTO sessions (user_id, metadata, expires_at)
    VALUES ($1, $2, $3)
    RETURNING id::text
    """

    from datetime import datetime, timedelta, timezone
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hour session

    from .models import UUIDEncoder
    row = await db.fetch_one(query, user_id, json.dumps(metadata or {}, cls=UUIDEncoder), expires_at)
    return row["id"]


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID."""
    db = await get_db_manager()

    query = """
    SELECT id::text, user_id, metadata, created_at, updated_at, expires_at
    FROM sessions
    WHERE id = $1::uuid
    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
    """

    row = await db.fetch_one(query, session_id)
    if row:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "expires_at": row["expires_at"]
        }
    return None


async def add_message(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Add a message to a session."""
    db = await get_db_manager()

    # Get the next message index for this session
    count_query = """
    SELECT COALESCE(MAX(message_index), 0) + 1 as next_index
    FROM messages
    WHERE session_id = $1::uuid
    """
    count_row = await db.fetch_one(count_query, session_id)
    next_index = count_row["next_index"]

    query = """
    INSERT INTO messages (session_id, role, content, metadata, message_index)
    VALUES ($1::uuid, $2, $3, $4, $5)
    RETURNING id::text
    """

    from .models import UUIDEncoder
    row = await db.fetch_one(query, session_id, role, content, json.dumps(metadata or {}, cls=UUIDEncoder), next_index)
    return row["id"]


async def get_session_messages(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get messages for a session."""
    db = await get_db_manager()

    query = """
    SELECT id::text, session_id::text, role, content, metadata, created_at
    FROM messages
    WHERE session_id = $1::uuid
    ORDER BY created_at ASC
    LIMIT $2
    """

    rows = await db.fetch_all(query, session_id, limit)
    return [
        {
            "id": row["id"],
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "created_at": row["created_at"]
        }
        for row in rows
    ]
