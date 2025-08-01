-- Migration to update embedding dimensions from 1536 to 768 for Gemini embeddings
-- This migration changes the vector dimension to support Gemini text-embedding-004

-- Drop the existing index on embeddings
DROP INDEX IF EXISTS idx_chunks_embedding;

-- Drop the existing embedding column
ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;

-- Add the new embedding column with 768 dimensions for Gemini
ALTER TABLE chunks ADD COLUMN embedding VECTOR(768);

-- Recreate the index for the new embedding dimension
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Update any existing chunks to have NULL embeddings (they will need to be regenerated)
UPDATE chunks SET embedding = NULL;

COMMENT ON COLUMN chunks.embedding IS 'Vector embedding (768 dimensions for Gemini text-embedding-004)';
