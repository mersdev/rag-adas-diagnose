"""
Main ingestion pipeline for ADAS Diagnostics Co-pilot.

This module orchestrates the complete document processing pipeline including
text extraction, chunking, embedding generation, entity extraction, and
knowledge graph population.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

import click
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent.config import get_settings
from agent.db_utils import get_db_manager, initialize_database, DocumentRepository, ChunkRepository
from agent.graph_utils import get_graph_manager, initialize_graph, AutomotiveGraphRepository
from agent.models import (
    DocumentCreate, ChunkCreate, ProcessingStatus, 
    AutomotiveEntityCreate, EntityRelationshipCreate
)

from .document_processor import AutomotiveDocumentProcessor, DocumentChunk
from .embedding_service import get_embedding_manager
from .entity_extractor import AutomotiveEntityExtractor, ExtractedEntity, ExtractedRelationship

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Main ingestion pipeline orchestrator."""
    
    def __init__(self):
        """Initialize the ingestion pipeline."""
        self.settings = get_settings()
        self.document_processor = AutomotiveDocumentProcessor()
        self.entity_extractor = AutomotiveEntityExtractor()
        self.embedding_manager = get_embedding_manager()
        
        # Database repositories
        self.db_manager = None
        self.doc_repo = None
        self.chunk_repo = None
        
        # Graph repository
        self.graph_manager = None
        self.graph_repo = None
        
        # Processing statistics
        self.stats = {
            'documents_processed': 0,
            'documents_failed': 0,
            'chunks_created': 0,
            'entities_extracted': 0,
            'relationships_extracted': 0,
            'processing_time': 0.0
        }
    
    async def initialize(self):
        """Initialize database and graph connections."""
        try:
            # Initialize database manager
            logger.info("Initializing database connection...")
            await initialize_database(self.settings.database.database_url)
            self.db_manager = await get_db_manager()
            self.doc_repo = DocumentRepository(self.db_manager)
            self.chunk_repo = ChunkRepository(self.db_manager)
            logger.info("Database initialized successfully")

            # Initialize graph database
            try:
                logger.info("Initializing graph database connection...")
                await initialize_graph()
                self.graph_manager = await get_graph_manager()
                self.graph_repo = AutomotiveGraphRepository(self.graph_manager)
                logger.info("Graph database initialized successfully")
            except Exception as e:
                logger.warning(f"Graph database initialization failed: {e}")
                logger.warning("Continuing without graph database - some features may be limited")
                self.graph_repo = None

            logger.info("Ingestion pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ingestion pipeline: {e}")
            raise
    
    async def process_file(self, file_path: Path) -> bool:
        """
        Process a single file through the complete ingestion pipeline.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            True if processing succeeded, False otherwise
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Check if file can be processed
            if not self.document_processor.can_process(file_path):
                logger.warning(f"Cannot process file: {file_path}")
                return False
            
            # Check if file already exists in database
            existing_doc = await self.doc_repo.get_document_by_path(str(file_path))
            if existing_doc:
                # Check if file has been modified
                current_hash = self.document_processor._calculate_file_hash(file_path)
                if existing_doc.file_hash == current_hash:
                    logger.info(f"File already processed and unchanged: {file_path}")
                    return True
                else:
                    logger.info(f"File modified, reprocessing: {file_path}")
                    # Delete existing document and chunks
                    await self.doc_repo.delete_document(existing_doc.id)
            
            # Step 1: Extract text and create document metadata
            document, chunks = self.document_processor.process_document(file_path)
            
            # Step 2: Generate embeddings for chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_manager.get_embeddings(chunk_texts)
            
            # Step 3: Extract entities and relationships
            full_text = ' '.join(chunk_texts)
            entities = self.entity_extractor.extract_entities(full_text)
            relationships = self.entity_extractor.extract_relationships(full_text, entities)
            
            # Step 4: Save to database
            await self._save_document_data(document, chunks, embeddings, entities, relationships)
            
            # Update statistics
            self.stats['documents_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            self.stats['entities_extracted'] += len(entities)
            self.stats['relationships_extracted'] += len(relationships)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.stats['processing_time'] += processing_time
            
            logger.info(f"Successfully processed {file_path} in {processing_time:.2f}s")
            logger.info(f"Created {len(chunks)} chunks, {len(entities)} entities, {len(relationships)} relationships")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            self.stats['documents_failed'] += 1
            return False
    
    async def _save_document_data(
        self,
        document: DocumentCreate,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        entities: List[ExtractedEntity],
        relationships: List[ExtractedRelationship]
    ):
        """Save document data to database and knowledge graph."""
        
        # Save document
        saved_doc = await self.doc_repo.create_document(document)
        
        # Save chunks with embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_create = ChunkCreate(
                document_id=saved_doc.id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                content_hash=chunk.get_content_hash(),
                embedding=embedding,
                metadata={
                    'contains_dtc_codes': chunk.contains_dtc_codes,
                    'contains_version_info': chunk.contains_version_info,
                    'contains_component_info': chunk.contains_component_info,
                    **chunk.metadata
                }
            )
            await self.chunk_repo.create_chunk(chunk_create)
        
        # Save entities and relationships to knowledge graph
        if self.graph_repo:
            await self._save_to_knowledge_graph(saved_doc.id, entities, relationships)
        
        # Update document status
        await self.doc_repo.update_document_status(saved_doc.id, ProcessingStatus.COMPLETED)
    
    async def _save_to_knowledge_graph(
        self,
        document_id: str,
        entities: List[ExtractedEntity],
        relationships: List[ExtractedRelationship]
    ):
        """Save entities and relationships to the knowledge graph."""
        try:
            # Create entities
            entity_map = {}
            for entity in entities:
                entity_create = AutomotiveEntityCreate(
                    name=entity.name,
                    entity_type=entity.entity_type,
                    properties={
                        'confidence': entity.confidence,
                        'context': entity.context,
                        'document_id': document_id,
                        **entity.properties
                    }
                )
                
                created_entity = await self.graph_repo.create_entity(entity_create)
                entity_map[entity.name.lower()] = created_entity
            
            # Create relationships
            for relationship in relationships:
                source_entity = entity_map.get(relationship.source_entity.lower())
                target_entity = entity_map.get(relationship.target_entity.lower())
                
                if source_entity and target_entity:
                    rel_create = EntityRelationshipCreate(
                        source_entity_id=source_entity.id,
                        target_entity_id=target_entity.id,
                        relationship_type=relationship.relationship_type.value,
                        properties={
                            'confidence': relationship.confidence,
                            'context': relationship.context,
                            'document_id': document_id,
                            **relationship.properties
                        }
                    )
                    
                    await self.graph_repo.create_relationship(rel_create)
            
            logger.info(f"Saved {len(entities)} entities and {len(relationships)} relationships to knowledge graph")
            
        except Exception as e:
            logger.error(f"Failed to save to knowledge graph: {e}")
    
    async def process_directory(self, directory_path: Path, recursive: bool = True) -> Dict[str, Any]:
        """
        Process all supported files in a directory.
        
        Args:
            directory_path: Path to the directory to process
            recursive: Whether to process subdirectories recursively
            
        Returns:
            Processing statistics
        """
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        logger.info(f"Processing directory: {directory_path}")
        
        # Find all supported files
        files_to_process = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and self.document_processor.can_process(file_path):
                files_to_process.append(file_path)
        
        logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process files
        for file_path in files_to_process:
            await self.process_file(file_path)
        
        return self.get_statistics()
    
    async def process_sample_data(self):
        """Process sample automotive documents for testing."""
        logger.info("Processing sample automotive data")

        # Use the actual sample data directory
        sample_dir = Path("data/sample-data")

        if not sample_dir.exists():
            logger.error(f"Sample data directory not found: {sample_dir}")
            raise FileNotFoundError(f"Sample data directory not found: {sample_dir}")

        # Process the sample directory
        return await self.process_directory(sample_dir)
    
    async def _create_sample_documents(self, sample_dir: Path):
        """Create sample automotive documents for testing."""
        
        # Sample OTA update document
        ota_content = """# OTA Update Release Notes v2.1.3

## Vehicle Systems Affected
- ADAS System
- Braking System (ABS/ESP)
- Infotainment Module

## Changes
- Fixed lane keeping assist calibration issue (DTC P0123)
- Updated brake controller firmware to v1.2.1
- Improved radar sensor performance in rain conditions

## Applicable Vehicles
- VIN Pattern: 1HGBH41JXMN*
- Model Years: 2022-2024
- Supplier: Bosch (Brake Controller), Continental (Radar)

## Installation Notes
The brake controller module requires recalibration after update.
Communication via CAN bus with ECM and BCM modules.
"""
        
        # Sample diagnostic log
        diagnostic_content = """# Diagnostic Report - Vehicle Fault Analysis

## Vehicle Information
VIN: 1HGBH41JXMN109186
System: ADAS
Component: Lane Keeping Assist Module

## Diagnostic Trouble Codes
- P0123: Throttle Position Sensor Circuit High
- B1234: Lane Departure Warning System Malfunction
- U0100: Lost Communication with ECM

## Component Analysis
The lane keeping assist sensor depends on the steering angle sensor.
The radar module communicates with the ADAS ECU via CAN bus.
Brake actuator is controlled by the ESP module.

## Repair Procedure
1. Check steering angle sensor calibration
2. Verify CAN bus communication between modules
3. Update ADAS ECU firmware to latest version
"""
        
        # Sample hardware specification
        hardware_content = """# Brake Controller Module Specification

## Part Information
Part Number: BCM-2024-001
Supplier: Bosch
Version: Hardware v2.1, Firmware v1.2.1

## System Integration
- Part of Braking System
- Communicates with ABS Module
- Monitors wheel speed sensors
- Controls brake actuators

## Dependencies
- Requires power from BCM
- Depends on wheel speed sensor data
- Interfaces with ESP controller

## Technical Specifications
- Operating Voltage: 12V ±2V
- CAN Bus Speed: 500 kbps
- Temperature Range: -40°C to +85°C
"""
        
        # Write sample files
        (sample_dir / "ota_update_v2.1.3.md").write_text(ota_content)
        (sample_dir / "diagnostic_report_001.md").write_text(diagnostic_content)
        (sample_dir / "brake_controller_spec.md").write_text(hardware_content)
        
        logger.info("Created sample automotive documents")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'documents_processed': 0,
            'documents_failed': 0,
            'chunks_created': 0,
            'entities_extracted': 0,
            'relationships_extracted': 0,
            'processing_time': 0.0
        }


# CLI Interface
@click.group()
def cli():
    """ADAS Diagnostics Co-pilot Ingestion Pipeline."""
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def process_file_cmd(file_path: Path, verbose: bool):
    """Process a single file."""
    async def _process():
        if verbose:
            logging.basicConfig(level=logging.INFO)

        pipeline = IngestionPipeline()
        await pipeline.initialize()

        success = await pipeline.process_file(file_path)
        stats = pipeline.get_statistics()

        if success:
            click.echo(f"✅ Successfully processed {file_path}")
            click.echo(f"📊 Statistics: {stats}")
        else:
            click.echo(f"❌ Failed to process {file_path}")
            sys.exit(1)

    asyncio.run(_process())


@cli.command()
@click.argument('directory_path', type=click.Path(exists=True, path_type=Path))
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories recursively')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def process_directory_cmd(directory_path: Path, recursive: bool, verbose: bool):
    """Process all files in a directory."""
    async def _process():
        if verbose:
            logging.basicConfig(level=logging.INFO)

        pipeline = IngestionPipeline()
        await pipeline.initialize()

        try:
            stats = await pipeline.process_directory(directory_path, recursive)

            click.echo(f"✅ Processing completed!")
            click.echo(f"📊 Statistics:")
            click.echo(f"   Documents processed: {stats['documents_processed']}")
            click.echo(f"   Documents failed: {stats['documents_failed']}")
            click.echo(f"   Chunks created: {stats['chunks_created']}")
            click.echo(f"   Entities extracted: {stats['entities_extracted']}")
            click.echo(f"   Relationships extracted: {stats['relationships_extracted']}")
            click.echo(f"   Total processing time: {stats['processing_time']:.2f}s")

        except Exception as e:
            click.echo(f"❌ Processing failed: {e}")
            sys.exit(1)

    asyncio.run(_process())


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def sample_data(verbose: bool):
    """Process sample automotive data for testing."""
    async def _process():
        if verbose:
            logging.basicConfig(level=logging.INFO)

        pipeline = IngestionPipeline()
        await pipeline.initialize()

        try:
            stats = await pipeline.process_sample_data()

            click.echo(f"✅ Sample data processing completed!")
            click.echo(f"📊 Statistics:")
            click.echo(f"   Documents processed: {stats['documents_processed']}")
            click.echo(f"   Chunks created: {stats['chunks_created']}")
            click.echo(f"   Entities extracted: {stats['entities_extracted']}")
            click.echo(f"   Relationships extracted: {stats['relationships_extracted']}")

        except Exception as e:
            click.echo(f"❌ Sample data processing failed: {e}")
            sys.exit(1)

    asyncio.run(_process())


if __name__ == '__main__':
    cli()
