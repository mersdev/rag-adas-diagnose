-- ADAS Diagnostics Co-pilot Database Schema
-- PostgreSQL with pgvector extension for automotive diagnostics

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS chunk_metadata CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS automotive_entities CASCADE;
DROP TABLE IF EXISTS ota_updates CASCADE;
DROP TABLE IF EXISTS diagnostic_codes CASCADE;

-- Documents table for storing automotive document metadata
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    content_type VARCHAR(100) NOT NULL, -- 'ota_update', 'hardware_spec', 'diagnostic_log', 'repair_note', 'supplier_doc'
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_hash VARCHAR(64) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Automotive-specific metadata
    vehicle_system VARCHAR(100), -- 'ADAS', 'braking', 'steering', 'powertrain', etc.
    component_name VARCHAR(200),
    supplier VARCHAR(200),
    model_years INTEGER[],
    vin_patterns TEXT[],
    severity_level VARCHAR(20), -- 'critical', 'high', 'medium', 'low'
    
    -- Document processing status
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    chunk_count INTEGER DEFAULT 0,
    
    -- Full-text search
    content_tsvector TSVECTOR
);

-- Chunks table for storing document chunks with embeddings
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    
    -- Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    -- Adjust dimensions based on your embedding model
    embedding VECTOR(1536),
    
    -- Chunk metadata
    start_char INTEGER,
    end_char INTEGER,
    token_count INTEGER,
    
    -- Automotive-specific chunk data
    contains_dtc_codes BOOLEAN DEFAULT FALSE,
    contains_version_info BOOLEAN DEFAULT FALSE,
    contains_component_info BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(document_id, chunk_index)
);

-- Chunk metadata for additional structured data
CREATE TABLE chunk_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    data_type VARCHAR(50) DEFAULT 'string', -- 'string', 'number', 'date', 'json'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(chunk_id, key)
);



-- Automotive entities for structured data
CREATE TABLE automotive_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- 'component', 'system', 'supplier', 'dtc', 'vin'
    entity_name VARCHAR(200) NOT NULL,
    entity_value TEXT,
    
    -- References
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
    
    -- Entity metadata
    confidence_score FLOAT,
    extraction_method VARCHAR(50), -- 'regex', 'llm', 'manual'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(entity_type, entity_name, document_id)
);

-- OTA Updates tracking
CREATE TABLE ota_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) NOT NULL,
    release_date DATE,
    description TEXT,
    
    -- Affected systems and components
    affected_systems TEXT[],
    affected_components TEXT[],
    
    -- Vehicle applicability
    applicable_vins TEXT[],
    applicable_models TEXT[],
    applicable_years INTEGER[],
    
    -- Update metadata
    update_type VARCHAR(50), -- 'security', 'feature', 'bugfix', 'recall'
    severity VARCHAR(20),
    rollback_available BOOLEAN DEFAULT FALSE,
    
    -- References
    document_id UUID REFERENCES documents(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(version)
);

-- Diagnostic Trouble Codes
CREATE TABLE diagnostic_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dtc_code VARCHAR(10) NOT NULL, -- e.g., 'P0420', 'B1234'
    description TEXT NOT NULL,
    
    -- Code classification
    system_type CHAR(1), -- 'P' (Powertrain), 'B' (Body), 'C' (Chassis), 'U' (Network)
    code_type CHAR(1), -- '0' (Generic), '1' (Manufacturer specific)
    
    -- Diagnostic information
    possible_causes TEXT[],
    diagnostic_steps TEXT[],
    repair_procedures TEXT[],
    
    -- Related components
    related_components TEXT[],
    related_systems TEXT[],
    
    -- References
    document_id UUID REFERENCES documents(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(dtc_code)
);

-- Sessions table for chat session management
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'default_user',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Messages table for storing conversation history
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_documents_content_type ON documents(content_type);
CREATE INDEX idx_documents_vehicle_system ON documents(vehicle_system);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_tsvector ON documents USING GIN(content_tsvector);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);



CREATE INDEX idx_automotive_entities_type ON automotive_entities(entity_type);
CREATE INDEX idx_automotive_entities_name ON automotive_entities(entity_name);
CREATE INDEX idx_automotive_entities_document ON automotive_entities(document_id);

CREATE INDEX idx_ota_updates_version ON ota_updates(version);
CREATE INDEX idx_ota_updates_release_date ON ota_updates(release_date);
CREATE INDEX idx_ota_updates_systems ON ota_updates USING GIN(affected_systems);

CREATE INDEX idx_diagnostic_codes_code ON diagnostic_codes(dtc_code);
CREATE INDEX idx_diagnostic_codes_system_type ON diagnostic_codes(system_type);

-- Session management indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Create functions for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



CREATE TRIGGER update_diagnostic_codes_updated_at BEFORE UPDATE ON diagnostic_codes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for full-text search updates
CREATE OR REPLACE FUNCTION update_document_tsvector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_tsvector = to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.filename, ''));
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_tsvector BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_document_tsvector();
