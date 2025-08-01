"""
Pydantic models for ADAS Diagnostics Co-pilot.

This module contains all data models used throughout the application,
including automotive-specific models for documents, diagnostics, and agent interactions.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict
import json


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder for UUID objects."""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class ContentType(str, Enum):
    """Document content types for automotive diagnostics."""
    OTA_UPDATE = "ota_update"
    HARDWARE_SPEC = "hardware_spec"
    DIAGNOSTIC_LOG = "diagnostic_log"
    REPAIR_NOTE = "repair_note"
    SUPPLIER_DOC = "supplier_doc"
    SYSTEM_ARCHITECTURE = "system_architecture"


class VehicleSystem(str, Enum):
    """Vehicle system categories."""
    ADAS = "ADAS"
    BRAKING = "braking"
    STEERING = "steering"
    POWERTRAIN = "powertrain"
    INFOTAINMENT = "infotainment"
    HVAC = "hvac"
    LIGHTING = "lighting"
    BODY_CONTROL = "body_control"
    NETWORK = "network"


class SeverityLevel(str, Enum):
    """Severity levels for issues and updates."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class EntityType(str, Enum):
    """Automotive entity types."""
    COMPONENT = "component"
    SYSTEM = "system"
    SUPPLIER = "supplier"
    DTC = "dtc"
    VIN = "vin"
    SOFTWARE_VERSION = "software_version"


class UpdateType(str, Enum):
    """OTA update types."""
    SECURITY = "security"
    FEATURE = "feature"
    BUGFIX = "bugfix"
    RECALL = "recall"
    MAINTENANCE = "maintenance"


# Base Models
class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UUIDModel(BaseModel):
    """Base model with UUID primary key."""
    id: UUID = Field(default_factory=uuid4)

    model_config = ConfigDict(from_attributes=True)


# Document Models
class DocumentBase(BaseModel):
    """Base document model."""
    filename: str = Field(..., max_length=255)
    title: Optional[str] = Field(None, max_length=500)
    content_type: ContentType
    file_path: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = Field(None, max_length=64)
    
    # Automotive-specific metadata
    vehicle_system: Optional[VehicleSystem] = None
    component_name: Optional[str] = Field(None, max_length=200)
    supplier: Optional[str] = Field(None, max_length=200)
    model_years: Optional[List[int]] = None
    vin_patterns: Optional[List[str]] = None
    severity_level: Optional[SeverityLevel] = None
    
    # Processing status
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(DocumentBase):
    """Model for creating documents."""
    pass


class DocumentUpdate(BaseModel):
    """Model for updating documents."""
    title: Optional[str] = None
    vehicle_system: Optional[VehicleSystem] = None
    component_name: Optional[str] = None
    supplier: Optional[str] = None
    model_years: Optional[List[int]] = None
    vin_patterns: Optional[List[str]] = None
    severity_level: Optional[SeverityLevel] = None
    processing_status: Optional[ProcessingStatus] = None
    chunk_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class Document(UUIDModel, DocumentBase, TimestampedModel):
    """Complete document model."""
    pass


# Chunk Models
class ChunkBase(BaseModel):
    """Base chunk model."""
    document_id: UUID
    chunk_index: int
    content: str
    content_hash: Optional[str] = Field(None, max_length=64)
    
    # Chunk metadata
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    token_count: Optional[int] = None
    
    # Automotive-specific flags
    contains_dtc_codes: bool = False
    contains_version_info: bool = False
    contains_component_info: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChunkCreate(ChunkBase):
    """Model for creating chunks."""
    embedding: Optional[List[float]] = None


class Chunk(UUIDModel, ChunkBase):
    """Complete chunk model."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Embedding stored separately for performance
    embedding: Optional[List[float]] = None


class ChunkWithDocument(Chunk):
    """Chunk model with associated document."""
    document: Document


# Search Result Models
class SearchResult(BaseModel):
    """Base search result model."""
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float

    # Document metadata
    document_title: Optional[str] = None
    document_filename: str
    content_type: str  # Made flexible to handle any content type
    vehicle_system: Optional[str] = None  # Made flexible to handle any vehicle system
    component_name: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )


class VectorSearchResult(SearchResult):
    """Vector search result with similarity score."""
    similarity_score: float
    chunk_index: int


class GraphSearchResult(BaseModel):
    """Knowledge graph search result."""
    entity_name: str
    entity_type: EntityType
    relationships: List[Dict[str, Any]]
    related_documents: List[UUID]
    confidence_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)





# Automotive-Specific Models
class AutomotiveEntity(UUIDModel, TimestampedModel):
    """Automotive entity model."""
    entity_type: EntityType
    entity_name: str = Field(..., max_length=200)
    entity_value: Optional[str] = None
    
    # References
    document_id: Optional[UUID] = None
    chunk_id: Optional[UUID] = None
    
    # Entity metadata
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_method: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(from_attributes=True)


class OTAUpdate(UUIDModel, TimestampedModel):
    """OTA update model."""
    version: str = Field(..., max_length=50)
    release_date: Optional[date] = None
    description: Optional[str] = None
    
    # Affected systems and components
    affected_systems: Optional[List[str]] = None
    affected_components: Optional[List[str]] = None
    
    # Vehicle applicability
    applicable_vins: Optional[List[str]] = None
    applicable_models: Optional[List[str]] = None
    applicable_years: Optional[List[int]] = None
    
    # Update metadata
    update_type: Optional[UpdateType] = None
    severity: Optional[SeverityLevel] = None
    rollback_available: bool = False
    
    # References
    document_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class DiagnosticCode(UUIDModel, TimestampedModel):
    """Diagnostic Trouble Code model."""
    dtc_code: str = Field(..., max_length=10)
    description: str
    
    # Code classification
    system_type: Optional[str] = Field(None, max_length=1)  # P, B, C, U
    code_type: Optional[str] = Field(None, max_length=1)    # 0, 1
    
    # Diagnostic information
    possible_causes: Optional[List[str]] = None
    diagnostic_steps: Optional[List[str]] = None
    repair_procedures: Optional[List[str]] = None
    
    # Related components
    related_components: Optional[List[str]] = None
    related_systems: Optional[List[str]] = None
    
    # References
    document_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# Enhanced Response Models
class Suggestion(BaseModel):
    """Model for contextual suggestions."""
    title: str
    description: str
    category: str  # "diagnostic", "maintenance", "safety", "related_component"
    priority: str = "medium"  # "high", "medium", "low"
    action_type: str = "information"  # "information", "diagnostic", "maintenance", "safety_check"

    model_config = ConfigDict(from_attributes=True)


class NextStep(BaseModel):
    """Model for suggested next steps."""
    step_number: int
    title: str
    description: str
    estimated_time: Optional[str] = None
    required_tools: List[str] = []
    safety_notes: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class RelatedTopic(BaseModel):
    """Model for related topics and components."""
    title: str
    description: str
    relationship: str  # "related_component", "dependent_system", "common_issue", "preventive_measure"
    relevance_score: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class DiagnosticGuidance(BaseModel):
    """Model for diagnostic guidance information."""
    procedure_name: str
    steps: List[NextStep]
    prerequisites: List[str] = []
    expected_results: List[str] = []
    troubleshooting_tips: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class SafetyConsideration(BaseModel):
    """Model for safety considerations."""
    level: str  # "critical", "important", "advisory"
    title: str
    description: str
    precautions: List[str] = []

    model_config = ConfigDict(from_attributes=True)


# Tool and Agent Models
class ToolCall(BaseModel):
    """Model for tracking agent tool usage."""
    tool_name: str
    args: Dict[str, Any]
    result: Optional[Any] = None
    execution_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )


# API Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    user_id: str = "default_user"
    session_id: Optional[str] = None
    search_type: str = "hybrid"  # vector, graph, hybrid
    max_results: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Enhanced chat response model with proactive information."""
    message: str
    session_id: Optional[str] = None
    tools_used: List[ToolCall] = []
    sources: List[SearchResult] = []
    processing_time: Optional[float] = None

    # Enhanced proactive information
    suggestions: List[Suggestion] = []
    next_steps: List[NextStep] = []
    related_topics: List[RelatedTopic] = []
    diagnostic_guidance: Optional[DiagnosticGuidance] = None
    safety_considerations: List[SafetyConsideration] = []

    # Quick actions and contextual information
    quick_actions: List[str] = []
    preventive_tips: List[str] = []
    common_issues: List[str] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )


class SessionCreate(BaseModel):
    """Session creation request model."""
    user_id: str = "default_user"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    """Session response model."""
    id: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Message response model."""
    id: str
    session_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    agent_initialized: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    database_status: Optional[str] = None
    neo4j_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IngestionRequest(BaseModel):
    """Request for document ingestion."""
    file_paths: Optional[List[Path]] = None
    directory_path: Optional[Path] = None
    recursive: bool = False
    sample_data: bool = False

    model_config = ConfigDict(from_attributes=True)


class IngestionResponse(BaseModel):
    """Response for document ingestion."""
    message: str
    status: str
    task_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Entity and Relationship Models for Knowledge Graph
class AutomotiveEntityCreate(BaseModel):
    """Model for creating automotive entities."""
    name: str
    entity_type: str
    properties: Dict[str, Any] = {}
    source_document_id: Optional[UUID] = None
    confidence: float = 1.0

    model_config = ConfigDict(from_attributes=True)


class EntityRelationshipCreate(BaseModel):
    """Model for creating entity relationships."""
    source_entity: str
    target_entity: str
    relationship_type: str
    properties: Dict[str, Any] = {}
    confidence: float = 1.0

    model_config = ConfigDict(from_attributes=True)
