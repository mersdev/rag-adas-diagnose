#!/usr/bin/env python3
"""
Real Document Ingestion for ADAS Diagnostics Co-pilot

This script processes the actual markdown automotive documents and ingests them into the system.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
import hashlib
from typing import List, Dict, Any

# Set environment variables
os.environ['database_url'] = 'postgresql://adas_user:adas_password@localhost:5435/adas_diagnostics'
os.environ['neo4j_uri'] = 'bolt://localhost:7687'
os.environ['neo4j_user'] = 'neo4j'
os.environ['neo4j_password'] = 'adas_neo4j_password'

async def get_db_connection():
    """Get database connection."""
    return await asyncpg.connect(
        "postgresql://adas_user:adas_password@localhost:5435/adas_diagnostics"
    )

def extract_vin_patterns(content: str) -> List[str]:
    """Extract VIN patterns from document content."""
    import re
    vin_patterns = re.findall(r'VIN Pattern[:\s]*([A-Z0-9\*]+)', content)
    return vin_patterns

def extract_dtc_codes(content: str) -> List[str]:
    """Extract DTC codes from document content."""
    import re
    dtc_codes = re.findall(r'[PBCU]\d{4}', content)
    return list(set(dtc_codes))  # Remove duplicates

def determine_vehicle_system(filename: str, content: str) -> str:
    """Determine the vehicle system based on filename and content."""
    filename_lower = filename.lower()
    content_lower = content.lower()
    
    if 'brake' in filename_lower or 'brake' in content_lower:
        return 'Brake System'
    elif 'engine' in filename_lower or 'engine' in content_lower:
        return 'Engine Control'
    elif 'transmission' in filename_lower or 'transmission' in content_lower:
        return 'Transmission'
    elif 'adas' in filename_lower or 'camera' in filename_lower:
        return 'ADAS'
    elif 'ota' in filename_lower or 'update' in filename_lower:
        return 'Software/OTA'
    else:
        return 'General'

def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split content into overlapping chunks."""
    if len(content) <= chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # Try to break at a sentence or paragraph boundary
        if end < len(content):
            # Look for sentence endings
            for i in range(end, max(start + chunk_size - 200, start), -1):
                if content[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(content):
            break
    
    return chunks

async def ingest_document(conn, file_path: Path) -> str:
    """Ingest a single document into the database."""
    print(f"📄 Processing: {file_path.name}")
    
    # Read file content
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None
    
    # Extract metadata
    vin_patterns = extract_vin_patterns(content)
    dtc_codes = extract_dtc_codes(content)
    vehicle_system = determine_vehicle_system(file_path.name, content)
    file_hash = hashlib.md5(content.encode()).hexdigest()
    
    # Create document record
    try:
        doc_id = await conn.fetchval("""
            INSERT INTO documents (
                id, filename, title, file_path, content_type, 
                processing_status, file_hash, vehicle_system,
                vin_patterns, file_size
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, 'text/markdown',
                'completed', $4, $5, $6, $7
            ) RETURNING id
        """, 
        file_path.name,
        file_path.stem.replace('_', ' ').title(),
        str(file_path),
        file_hash,
        vehicle_system,
        vin_patterns,
        len(content)
        )
        
        print(f"✅ Created document: {doc_id}")
        
        # Create chunks
        chunks = chunk_content(content)
        chunk_count = 0

        for i, chunk_text in enumerate(chunks):
            # Create a dummy embedding vector (1536 dimensions)
            dummy_vector = '[' + ','.join(['0.1'] * 1536) + ']'

            chunk_id = await conn.fetchval("""
                INSERT INTO chunks (
                    id, document_id, content, chunk_index, embedding
                ) VALUES (
                    gen_random_uuid(), $1, $2, $3, $4::vector
                ) RETURNING id
            """, doc_id, chunk_text, i, dummy_vector)

            chunk_count += 1
        
        # Update document with chunk count
        await conn.execute("""
            UPDATE documents SET chunk_count = $1 WHERE id = $2
        """, chunk_count, doc_id)
        
        print(f"✅ Created {chunk_count} chunks for {file_path.name}")
        
        # Extract and store automotive entities
        await extract_automotive_entities(conn, doc_id, content, dtc_codes)
        
        return doc_id
        
    except Exception as e:
        print(f"❌ Error ingesting {file_path}: {e}")
        return None

async def extract_automotive_entities(conn, doc_id: str, content: str, dtc_codes: List[str]):
    """Extract automotive-specific entities from content."""
    import re
    
    entities = []
    
    # Extract DTC codes
    for code in dtc_codes:
        entities.append({
            'name': code,
            'entity_type': 'DTC_CODE',
            'properties': {'category': code[0], 'number': code[1:]},
            'confidence': 0.95
        })
    
    # Extract part numbers
    part_numbers = re.findall(r'[A-Z]{2,}-[A-Z0-9\-]+', content)
    for part in set(part_numbers[:10]):  # Limit to 10 unique parts
        entities.append({
            'name': part,
            'entity_type': 'PART_NUMBER',
            'properties': {},
            'confidence': 0.9
        })
    
    # Extract system components
    components = re.findall(r'(brake pad|brake rotor|spark plug|fuel injector|turbocharger|transmission|ECM|TCM|BCM)', content, re.IGNORECASE)
    for component in set(components[:10]):  # Limit to 10 unique components
        entities.append({
            'name': component.lower(),
            'entity_type': 'COMPONENT',
            'properties': {},
            'confidence': 0.8
        })
    
    # Insert entities into database
    for entity in entities:
        try:
            await conn.execute("""
                INSERT INTO automotive_entities (
                    id, name, entity_type, properties, source_document_id, confidence
                ) VALUES (
                    gen_random_uuid(), $1, $2, $3, $4, $5
                )
            """, 
            entity['name'],
            entity['entity_type'],
            entity['properties'],
            doc_id,
            entity['confidence']
            )
        except Exception as e:
            # Skip duplicates
            pass
    
    print(f"✅ Extracted {len(entities)} entities")

async def clear_existing_data(conn):
    """Clear existing sample data to avoid conflicts."""
    print("🧹 Clearing existing sample data...")
    
    try:
        # Delete in correct order due to foreign key constraints
        await conn.execute("DELETE FROM automotive_entities")
        await conn.execute("DELETE FROM chunks")
        await conn.execute("DELETE FROM documents")
        print("✅ Cleared existing data")
    except Exception as e:
        print(f"⚠️  Error clearing data: {e}")

async def main():
    """Main ingestion process."""
    print("🚗 ADAS Diagnostics Co-pilot - Real Document Ingestion")
    print("=" * 60)
    
    # Connect to database
    try:
        conn = await get_db_connection()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1
    
    # Clear existing data
    await clear_existing_data(conn)
    
    # Find markdown documents
    sample_data_dir = Path("sample-data")
    if not sample_data_dir.exists():
        print(f"❌ Sample data directory not found: {sample_data_dir}")
        return 1
    
    markdown_files = list(sample_data_dir.glob("*.md"))
    if not markdown_files:
        print(f"❌ No markdown files found in {sample_data_dir}")
        return 1
    
    print(f"📚 Found {len(markdown_files)} markdown documents")
    
    # Process each document
    successful_ingestions = 0
    for file_path in markdown_files:
        doc_id = await ingest_document(conn, file_path)
        if doc_id:
            successful_ingestions += 1
    
    # Get final statistics
    doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
    chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
    entity_count = await conn.fetchval("SELECT COUNT(*) FROM automotive_entities")
    
    await conn.close()
    
    print("\n" + "=" * 60)
    print(f"📊 Ingestion Results:")
    print(f"   • Documents processed: {successful_ingestions}/{len(markdown_files)}")
    print(f"   • Total documents in DB: {doc_count}")
    print(f"   • Total chunks created: {chunk_count}")
    print(f"   • Total entities extracted: {entity_count}")
    
    if successful_ingestions == len(markdown_files):
        print("🎉 All documents successfully ingested!")
        return 0
    else:
        print(f"⚠️  {len(markdown_files) - successful_ingestions} documents failed to ingest")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
