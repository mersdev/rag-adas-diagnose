"""
ADAS Diagnostics Co-pilot Ingestion Package.

This package contains the document processing pipeline for automotive data,
including OTA updates, hardware specifications, and diagnostic logs.
"""

from .document_processor import AutomotiveDocumentProcessor, DocumentChunk
from .embedding_service import (
    EmbeddingManager,
    get_embedding_manager,
    BaseEmbeddingService,
    OpenAIEmbeddingService,
    OllamaEmbeddingService,
    GeminiEmbeddingService
)
from .entity_extractor import (
    AutomotiveEntityExtractor,
    ExtractedEntity,
    ExtractedRelationship,
    RelationshipType
)
from .ingest import IngestionPipeline

__version__ = "1.0.0"

__all__ = [
    'AutomotiveDocumentProcessor',
    'DocumentChunk',
    'EmbeddingManager',
    'get_embedding_manager',
    'BaseEmbeddingService',
    'OpenAIEmbeddingService',
    'OllamaEmbeddingService',
    'GeminiEmbeddingService',
    'AutomotiveEntityExtractor',
    'ExtractedEntity',
    'ExtractedRelationship',
    'RelationshipType',
    'IngestionPipeline'
]
