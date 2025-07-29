"""
Agent tools for ADAS Diagnostics Co-pilot.

This module implements automotive-specific tools for the Pydantic AI agent,
including timeline analysis, dependency mapping, and hybrid search capabilities.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from .config import get_settings
from .db_utils import get_db_manager, ChunkRepository, DocumentRepository
from .models import VectorSearchResult, SearchResult, ContentType, VehicleSystem

logger = logging.getLogger(__name__)


class TimelineQuery(BaseModel):
    """Model for timeline analysis queries."""
    vin: Optional[str] = Field(None, description="Vehicle VIN to filter by")
    system: Optional[str] = Field(None, description="Vehicle system to analyze")
    component: Optional[str] = Field(None, description="Specific component to track")
    days_back: int = Field(default=30, description="Number of days to look back")
    include_types: List[str] = Field(
        default=["ota_update", "diagnostic_log", "repair_note"],
        description="Document types to include in timeline"
    )


class DependencyQuery(BaseModel):
    """Model for dependency mapping queries."""
    component: str = Field(..., description="Component to analyze dependencies for")
    system: Optional[str] = Field(None, description="Vehicle system context")
    max_depth: int = Field(default=3, description="Maximum relationship depth")
    include_suppliers: bool = Field(default=True, description="Include supplier relationships")


class HybridSearchQuery(BaseModel):
    """Model for hybrid search queries."""
    query: str = Field(..., description="Natural language search query")
    search_type: str = Field(default="hybrid", description="Search type: vector, graph, or hybrid")
    max_results: int = Field(default=10, description="Maximum results to return")
    content_types: Optional[List[str]] = Field(None, description="Filter by content types")
    vehicle_systems: Optional[List[str]] = Field(None, description="Filter by vehicle systems")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity threshold")


class AutomotiveTools:
    """Collection of automotive diagnostic tools."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = None
        self.chunk_repo = None
        self.doc_repo = None
    
    async def initialize(self):
        """Initialize database connections."""
        self.db_manager = await get_db_manager()
        self.chunk_repo = ChunkRepository(self.db_manager)
        self.doc_repo = DocumentRepository(self.db_manager)
    
    async def timeline_analysis(self, query: TimelineQuery) -> Dict[str, Any]:
        """
        Analyze timeline of events for a specific vehicle, system, or component.
        
        This tool helps track chronological changes, updates, and issues
        related to specific automotive systems or vehicles.
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=query.days_back)
            
            # Build search conditions
            conditions = ["d.created_at >= $1", "d.created_at <= $2"]
            values = [start_date, end_date]
            param_count = 3
            
            if query.vin:
                conditions.append(f"$${param_count} = ANY(d.vin_patterns)")
                values.append(query.vin)
                param_count += 1
            
            if query.system:
                conditions.append(f"d.vehicle_system = ${param_count}")
                values.append(query.system)
                param_count += 1
            
            if query.component:
                conditions.append(f"d.component_name ILIKE ${param_count}")
                values.append(f"%{query.component}%")
                param_count += 1
            
            if query.include_types:
                placeholders = ", ".join([f"${i}" for i in range(param_count, param_count + len(query.include_types))])
                conditions.append(f"d.content_type IN ({placeholders})")
                values.extend(query.include_types)
                param_count += len(query.include_types)
            
            where_clause = " AND ".join(conditions)
            
            # Execute timeline query
            timeline_query = f"""
            SELECT 
                d.id,
                d.title,
                d.filename,
                d.content_type,
                d.vehicle_system,
                d.component_name,
                d.supplier,
                d.severity_level,
                d.created_at,
                COUNT(c.id) as chunk_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
            WHERE {where_clause}
            GROUP BY d.id, d.title, d.filename, d.content_type, d.vehicle_system, 
                     d.component_name, d.supplier, d.severity_level, d.created_at
            ORDER BY d.created_at DESC
            """
            
            rows = await self.db_manager.fetch_all(timeline_query, *values)
            
            # Process results into timeline format
            timeline_events = []
            for row in rows:
                event = {
                    "timestamp": row["created_at"].isoformat(),
                    "title": row["title"] or row["filename"],
                    "type": row["content_type"],
                    "system": row["vehicle_system"],
                    "component": row["component_name"],
                    "supplier": row["supplier"],
                    "severity": row["severity_level"],
                    "document_id": str(row["id"]),
                    "chunk_count": row["chunk_count"]
                }
                timeline_events.append(event)
            
            # Generate summary statistics
            summary = {
                "total_events": len(timeline_events),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "event_types": {},
                "systems_affected": set(),
                "components_affected": set(),
                "severity_distribution": {}
            }
            
            for event in timeline_events:
                # Count event types
                event_type = event["type"]
                summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
                
                # Track affected systems and components
                if event["system"]:
                    summary["systems_affected"].add(event["system"])
                if event["component"]:
                    summary["components_affected"].add(event["component"])
                
                # Count severity levels
                severity = event["severity"] or "unknown"
                summary["severity_distribution"][severity] = summary["severity_distribution"].get(severity, 0) + 1
            
            # Convert sets to lists for JSON serialization
            summary["systems_affected"] = list(summary["systems_affected"])
            summary["components_affected"] = list(summary["components_affected"])
            
            return {
                "timeline": timeline_events,
                "summary": summary,
                "query_parameters": query.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Timeline analysis failed: {e}")
            return {
                "error": f"Timeline analysis failed: {str(e)}",
                "timeline": [],
                "summary": {}
            }
    
    async def dependency_mapping(self, query: DependencyQuery) -> Dict[str, Any]:
        """
        Map dependencies and relationships for automotive components.
        
        This tool analyzes component relationships, supplier dependencies,
        and system interactions based on documentation.
        """
        try:
            # Search for documents mentioning the component
            component_search = f"""
            SELECT DISTINCT
                d.id,
                d.title,
                d.filename,
                d.content_type,
                d.vehicle_system,
                d.component_name,
                d.supplier,
                c.content
            FROM documents d
            JOIN chunks c ON d.id = c.document_id
            WHERE 
                (d.component_name ILIKE $1 OR c.content ILIKE $2)
                AND ($3::text IS NULL OR d.vehicle_system = $3)
            ORDER BY d.created_at DESC
            LIMIT 50
            """
            
            component_pattern = f"%{query.component}%"
            rows = await self.db_manager.fetch_all(
                component_search, 
                component_pattern, 
                component_pattern,
                query.system
            )
            
            # Extract relationships from content
            relationships = {
                "direct_dependencies": set(),
                "reverse_dependencies": set(),
                "suppliers": set(),
                "related_systems": set(),
                "mentioned_in_documents": []
            }
            
            # Patterns for dependency extraction
            dependency_patterns = [
                r"depends on ([A-Za-z\s]+)",
                r"requires ([A-Za-z\s]+)",
                r"interfaces with ([A-Za-z\s]+)",
                r"connected to ([A-Za-z\s]+)",
                r"communicates with ([A-Za-z\s]+)"
            ]
            
            reverse_dependency_patterns = [
                r"([A-Za-z\s]+) depends on",
                r"([A-Za-z\s]+) requires",
                r"([A-Za-z\s]+) interfaces with"
            ]
            
            for row in rows:
                content = row["content"].lower()
                component_lower = query.component.lower()
                
                # Skip if component not actually mentioned
                if component_lower not in content:
                    continue
                
                # Extract direct dependencies
                for pattern in dependency_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        clean_match = match.strip().title()
                        if clean_match and clean_match.lower() != component_lower:
                            relationships["direct_dependencies"].add(clean_match)
                
                # Extract reverse dependencies
                for pattern in reverse_dependency_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        clean_match = match.strip().title()
                        if clean_match and clean_match.lower() != component_lower:
                            relationships["reverse_dependencies"].add(clean_match)
                
                # Track suppliers
                if row["supplier"]:
                    relationships["suppliers"].add(row["supplier"])
                
                # Track related systems
                if row["vehicle_system"]:
                    relationships["related_systems"].add(row["vehicle_system"])
                
                # Track document references
                relationships["mentioned_in_documents"].append({
                    "document_id": str(row["id"]),
                    "title": row["title"] or row["filename"],
                    "content_type": row["content_type"],
                    "system": row["vehicle_system"]
                })
            
            # Convert sets to lists for JSON serialization
            result = {
                "component": query.component,
                "system_context": query.system,
                "relationships": {
                    "direct_dependencies": list(relationships["direct_dependencies"]),
                    "reverse_dependencies": list(relationships["reverse_dependencies"]),
                    "suppliers": list(relationships["suppliers"]),
                    "related_systems": list(relationships["related_systems"])
                },
                "document_references": relationships["mentioned_in_documents"],
                "analysis_summary": {
                    "total_documents_analyzed": len(rows),
                    "total_dependencies_found": len(relationships["direct_dependencies"]),
                    "total_reverse_dependencies": len(relationships["reverse_dependencies"]),
                    "suppliers_involved": len(relationships["suppliers"]),
                    "systems_involved": len(relationships["related_systems"])
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Dependency mapping failed: {e}")
            return {
                "error": f"Dependency mapping failed: {str(e)}",
                "component": query.component,
                "relationships": {}
            }
    
    async def hybrid_search(self, query: HybridSearchQuery) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector similarity and keyword matching.
        
        This tool provides comprehensive search across automotive documentation
        using both semantic similarity and exact keyword matching.
        """
        try:
            # For now, implement vector search (graph search will be added with Neo4j integration)
            if not self.chunk_repo:
                await self.initialize()
            
            # Get embedding for the query (placeholder - will be implemented with actual embedding service)
            # For now, return keyword-based search
            
            # Keyword search query - filter out stop words and use OR logic
            # Keep important automotive terms even if they're typically stop words
            stop_words = {'what', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'why', 'when', 'where', 'who', 'which', 'that', 'this', 'these', 'those', '?', '.', ',', '!'}
            important_terms = {'unit', 'system', 'module', 'component', 'part', 'sensor', 'camera', 'primary', 'secondary'}

            search_terms = []
            for term in query.query.lower().split():
                clean_term = term.strip('.,!?')
                # Keep term if it's important, not a stop word, or longer than 2 chars
                if (clean_term in important_terms or
                    clean_term not in stop_words or
                    len(clean_term) > 3):
                    if len(clean_term) > 1:  # Minimum length of 2
                        search_terms.append(clean_term)



            search_conditions = []
            search_values = []
            param_count = 1

            # Build search conditions with OR logic for better recall
            if search_terms:
                term_conditions = []
                for term in search_terms:
                    term_conditions.append(f"(LOWER(c.content) LIKE ${param_count} OR LOWER(d.title) LIKE ${param_count})")
                    search_values.append(f"%{term}%")
                    param_count += 1

                # Use OR logic for search terms
                search_conditions.append(f"({' OR '.join(term_conditions)})")
            else:
                # Fallback if no meaningful terms found
                search_conditions.append("TRUE")
            
            # Add content type filters
            if query.content_types:
                placeholders = ", ".join([f"${i}" for i in range(param_count, param_count + len(query.content_types))])
                search_conditions.append(f"d.content_type IN ({placeholders})")
                search_values.extend(query.content_types)
                param_count += len(query.content_types)
            
            # Add vehicle system filters
            if query.vehicle_systems:
                placeholders = ", ".join([f"${i}" for i in range(param_count, param_count + len(query.vehicle_systems))])
                search_conditions.append(f"d.vehicle_system IN ({placeholders})")
                search_values.extend(query.vehicle_systems)
                param_count += len(query.vehicle_systems)
            
            where_clause = " AND ".join(search_conditions) if search_conditions else "TRUE"
            
            # Execute search (simplified without complex relevance scoring for now)
            search_query = f"""
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
                d.supplier,
                d.severity_level,
                1.0 as relevance_score
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE {where_clause}
            ORDER BY
                CASE WHEN LOWER(d.title) LIKE '%camera%' THEN 1 ELSE 2 END,
                CASE WHEN LOWER(d.title) LIKE '%adas%' THEN 1 ELSE 2 END,
                d.created_at DESC
            LIMIT ${param_count}
            """

            search_values.append(query.max_results)
            
            # Debug: print the query and values
            logger.info(f"Search query: {search_query}")
            logger.info(f"Search values: {search_values}")

            rows = await self.db_manager.fetch_all(search_query, *search_values)
            
            # Process results
            search_results = []
            for i, row in enumerate(rows):
                try:
                    result = SearchResult(
                        chunk_id=row["chunk_id"],
                        document_id=row["document_id"],
                        content=row["content"][:500] + "..." if len(row["content"]) > 500 else row["content"],
                        score=float(row["relevance_score"]),
                        document_title=row["document_title"],
                        document_filename=row["document_filename"],
                        content_type=row["content_type"],
                        vehicle_system=row["vehicle_system"],
                        component_name=row["component_name"]
                    )
                    search_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to create SearchResult for row {i}: {e}")
                    logger.error(f"Row data: {dict(row)}")
            
            # Generate search summary
            summary = {
                "total_results": len(search_results),
                "search_terms": search_terms,
                "filters_applied": {
                    "content_types": query.content_types,
                    "vehicle_systems": query.vehicle_systems
                },
                "result_distribution": {}
            }
            
            # Analyze result distribution
            for result in search_results:
                content_type = result.content_type
                summary["result_distribution"][content_type] = summary["result_distribution"].get(content_type, 0) + 1
            
            return {
                "results": [result.model_dump() for result in search_results],
                "summary": summary,
                "query_parameters": query.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {
                "error": f"Hybrid search failed: {str(e)}",
                "results": [],
                "summary": {}
            }
