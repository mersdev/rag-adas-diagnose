"""
Neo4j knowledge graph utilities for ADAS Diagnostics Co-pilot.

This module provides graph database operations for relationship mapping,
entity extraction, and knowledge graph traversal for automotive diagnostics.
"""

import logging
import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError
import google.generativeai as genai

from .config import get_neo4j_config, get_settings
from .models import AutomotiveEntity, EntityType

logger = logging.getLogger(__name__)


class KnowledgeGraphExtractor:
    """Extract knowledge graph entities and relationships using Gemini 2.5 Flash."""

    def __init__(self, api_key: str):
        """Initialize the knowledge graph extractor."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def extract_entities_and_relationships(self, text: str, context: str = "automotive") -> Dict[str, Any]:
        """Extract entities and relationships from text using Gemini."""
        prompt = f"""
        Extract entities and relationships from the following automotive technical text.
        Focus on automotive components, systems, diagnostic codes, symptoms, and their relationships.

        Text: {text}

        Return a JSON object with the following structure:
        {{
            "entities": [
                {{
                    "name": "entity_name",
                    "type": "entity_type",
                    "properties": {{
                        "description": "entity_description",
                        "category": "automotive_category"
                    }}
                }}
            ],
            "relationships": [
                {{
                    "source": "source_entity",
                    "target": "target_entity",
                    "type": "relationship_type",
                    "properties": {{
                        "description": "relationship_description",
                        "strength": 0.8
                    }}
                }}
            ]
        }}

        Entity types should include: COMPONENT, SYSTEM, SYMPTOM, DIAGNOSTIC_CODE, PROCEDURE, VEHICLE_MODEL
        Relationship types should include: PART_OF, CAUSES, DIAGNOSED_BY, CONNECTED_TO, AFFECTS, REQUIRES

        Only return valid JSON, no additional text.
        """

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048
                )
            )

            # Extract JSON from response
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]

            return json.loads(json_text)

        except Exception as e:
            logger.error(f"Failed to extract entities and relationships: {e}")
            return {"entities": [], "relationships": []}


class GraphManager:
    """Neo4j graph database manager."""
    
    def __init__(self):
        """Initialize graph manager."""
        self.driver: Optional[AsyncDriver] = None
        self.uri, self.user, self.password = get_neo4j_config()
    
    async def initialize(self) -> None:
        """Initialize Neo4j connection."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # Test connection
            await self.verify_connectivity()
            logger.info("Neo4j connection initialized successfully")
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Neo4j: {e}")
            raise
    
    async def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")
    
    async def verify_connectivity(self) -> bool:
        """Verify Neo4j connectivity."""
        if not self.driver:
            return False
        
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                return record["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j connectivity test failed: {e}")
            return False
    
    async def create_indexes(self) -> None:
        """Create necessary indexes for automotive entities."""
        indexes = [
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX component_name_idx IF NOT EXISTS FOR (c:Component) ON (c.name)",
            "CREATE INDEX system_name_idx IF NOT EXISTS FOR (s:System) ON (s.name)",
            "CREATE INDEX supplier_name_idx IF NOT EXISTS FOR (sup:Supplier) ON (sup.name)",
            "CREATE INDEX document_id_idx IF NOT EXISTS FOR (d:Document) ON (d.document_id)",
            "CREATE INDEX vin_pattern_idx IF NOT EXISTS FOR (v:VIN) ON (v.pattern)"
        ]
        
        async with self.driver.session() as session:
            for index_query in indexes:
                try:
                    await session.run(index_query)
                    logger.debug(f"Created index: {index_query}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")


class AutomotiveGraphRepository:
    """Repository for automotive knowledge graph operations."""

    def __init__(self, graph_manager: GraphManager):
        self.graph = graph_manager
        self.extractor = None
        self._initialize_extractor()

    def _initialize_extractor(self):
        """Initialize the Gemini knowledge graph extractor."""
        try:
            settings = get_settings()
            self.extractor = KnowledgeGraphExtractor(settings.llm.llm_api_key)
            logger.info("Gemini knowledge graph extractor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini extractor: {e}")
            self.extractor = None
    
    async def create_entity(self, entity: AutomotiveEntity) -> bool:
        """Create an entity in the knowledge graph."""
        try:
            # Determine node label based on entity type
            label_map = {
                EntityType.COMPONENT: "Component",
                EntityType.SYSTEM: "System", 
                EntityType.SUPPLIER: "Supplier",
                EntityType.DTC: "DiagnosticCode",
                EntityType.VIN: "VIN",
                EntityType.SOFTWARE_VERSION: "SoftwareVersion"
            }
            
            label = label_map.get(entity.entity_type, "Entity")
            
            query = f"""
            MERGE (e:{label} {{name: $name}})
            SET e.type = $type,
                e.value = $value,
                e.document_id = $document_id,
                e.chunk_id = $chunk_id,
                e.confidence_score = $confidence_score,
                e.extraction_method = $extraction_method,
                e.created_at = datetime(),
                e.updated_at = datetime()
            RETURN e
            """
            
            async with self.graph.driver.session() as session:
                result = await session.run(
                    query,
                    name=entity.entity_name,
                    type=entity.entity_type.value,
                    value=entity.entity_value,
                    document_id=str(entity.document_id) if entity.document_id else None,
                    chunk_id=str(entity.chunk_id) if entity.chunk_id else None,
                    confidence_score=entity.confidence_score,
                    extraction_method=entity.extraction_method
                )
                
                record = await result.single()
                return record is not None
                
        except Exception as e:
            logger.error(f"Failed to create entity {entity.entity_name}: {e}")
            return False

    async def process_document_for_knowledge_graph(self, text: str, document_id: str = None) -> Dict[str, Any]:
        """Process a document to extract and store knowledge graph entities and relationships."""
        if not self.extractor:
            logger.warning("Gemini extractor not available, skipping knowledge graph extraction")
            return {"entities_created": 0, "relationships_created": 0}

        try:
            # Extract entities and relationships using Gemini
            extraction_result = await self.extractor.extract_entities_and_relationships(text)

            entities_created = 0
            relationships_created = 0

            # Create entities
            for entity_data in extraction_result.get("entities", []):
                try:
                    # Map entity type to our enum
                    entity_type_map = {
                        "COMPONENT": EntityType.COMPONENT,
                        "SYSTEM": EntityType.SYSTEM,
                        "DIAGNOSTIC_CODE": EntityType.DTC,
                        "SYMPTOM": EntityType.COMPONENT,  # Treat symptoms as components for now
                        "PROCEDURE": EntityType.COMPONENT,
                        "VEHICLE_MODEL": EntityType.COMPONENT
                    }

                    entity_type = entity_type_map.get(
                        entity_data.get("type", "").upper(),
                        EntityType.COMPONENT
                    )

                    # Create AutomotiveEntity
                    entity = AutomotiveEntity(
                        entity_name=entity_data["name"],
                        entity_type=entity_type,
                        entity_value=entity_data.get("properties", {}).get("description", ""),
                        document_id=document_id,
                        confidence_score=0.8,  # Default confidence for Gemini extraction
                        extraction_method="gemini_2_5_flash"
                    )

                    if await self.create_entity(entity):
                        entities_created += 1

                except Exception as e:
                    logger.error(f"Failed to create entity {entity_data.get('name', 'unknown')}: {e}")

            # Create relationships
            for rel_data in extraction_result.get("relationships", []):
                try:
                    relationship_type = rel_data.get("type", "RELATED_TO").upper()
                    properties = {
                        "description": rel_data.get("properties", {}).get("description", ""),
                        "strength": rel_data.get("properties", {}).get("strength", 0.5),
                        "extraction_method": "gemini_2_5_flash"
                    }

                    if await self.create_relationship(
                        rel_data["source"],
                        rel_data["target"],
                        relationship_type,
                        properties
                    ):
                        relationships_created += 1

                except Exception as e:
                    logger.error(f"Failed to create relationship: {e}")

            logger.info(f"Knowledge graph extraction completed: {entities_created} entities, {relationships_created} relationships")

            return {
                "entities_created": entities_created,
                "relationships_created": relationships_created,
                "extraction_result": extraction_result
            }

        except Exception as e:
            logger.error(f"Failed to process document for knowledge graph: {e}")
            return {"entities_created": 0, "relationships_created": 0}
    
    async def create_relationship(
        self, 
        from_entity: str, 
        to_entity: str, 
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a relationship between two entities."""
        try:
            props = properties or {}
            prop_string = ", ".join([f"r.{k} = ${k}" for k in props.keys()])
            set_clause = f"SET {prop_string}" if prop_string else ""
            
            query = f"""
            MATCH (a:Entity {{name: $from_name}})
            MATCH (b:Entity {{name: $to_name}})
            MERGE (a)-[r:{relationship_type}]->(b)
            {set_clause}
            SET r.created_at = datetime()
            RETURN r
            """
            
            params = {
                "from_name": from_entity,
                "to_name": to_entity,
                **props
            }
            
            async with self.graph.driver.session() as session:
                result = await session.run(query, **params)
                record = await result.single()
                return record is not None
                
        except Exception as e:
            logger.error(f"Failed to create relationship {from_entity} -> {to_entity}: {e}")
            return False
    
    async def find_related_entities(
        self, 
        entity_name: str, 
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Find entities related to a given entity."""
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            query = f"""
            MATCH path = (start:Entity {{name: $entity_name}})-[r{rel_filter}*1..{max_depth}]-(related:Entity)
            RETURN DISTINCT 
                related.name as name,
                related.type as type,
                related.value as value,
                length(path) as distance,
                [rel in relationships(path) | type(rel)] as relationship_path
            ORDER BY distance, related.name
            LIMIT 100
            """
            
            async with self.graph.driver.session() as session:
                result = await session.run(query, entity_name=entity_name)
                
                related_entities = []
                async for record in result:
                    entity_data = {
                        "name": record["name"],
                        "type": record["type"],
                        "value": record["value"],
                        "distance": record["distance"],
                        "relationship_path": record["relationship_path"]
                    }
                    related_entities.append(entity_data)
                
                return related_entities
                
        except Exception as e:
            logger.error(f"Failed to find related entities for {entity_name}: {e}")
            return []
    
    async def find_component_dependencies(self, component_name: str) -> Dict[str, List[str]]:
        """Find dependencies for a specific component."""
        try:
            query = """
            MATCH (c:Component {name: $component_name})
            OPTIONAL MATCH (c)-[:DEPENDS_ON]->(dep:Component)
            OPTIONAL MATCH (req:Component)-[:DEPENDS_ON]->(c)
            OPTIONAL MATCH (c)-[:PART_OF]->(sys:System)
            OPTIONAL MATCH (c)-[:SUPPLIED_BY]->(sup:Supplier)
            RETURN 
                collect(DISTINCT dep.name) as dependencies,
                collect(DISTINCT req.name) as required_by,
                collect(DISTINCT sys.name) as systems,
                collect(DISTINCT sup.name) as suppliers
            """
            
            async with self.graph.driver.session() as session:
                result = await session.run(query, component_name=component_name)
                record = await result.single()
                
                if record:
                    return {
                        "dependencies": [dep for dep in record["dependencies"] if dep],
                        "required_by": [req for req in record["required_by"] if req],
                        "systems": [sys for sys in record["systems"] if sys],
                        "suppliers": [sup for sup in record["suppliers"] if sup]
                    }
                else:
                    return {
                        "dependencies": [],
                        "required_by": [],
                        "systems": [],
                        "suppliers": []
                    }
                    
        except Exception as e:
            logger.error(f"Failed to find dependencies for {component_name}: {e}")
            return {
                "dependencies": [],
                "required_by": [],
                "systems": [],
                "suppliers": []
            }
    
    async def find_system_components(self, system_name: str) -> List[Dict[str, Any]]:
        """Find all components belonging to a system."""
        try:
            query = """
            MATCH (s:System {name: $system_name})<-[:PART_OF]-(c:Component)
            OPTIONAL MATCH (c)-[:SUPPLIED_BY]->(sup:Supplier)
            RETURN 
                c.name as component_name,
                c.value as component_value,
                collect(DISTINCT sup.name) as suppliers
            ORDER BY c.name
            """
            
            async with self.graph.driver.session() as session:
                result = await session.run(query, system_name=system_name)
                
                components = []
                async for record in result:
                    component_data = {
                        "name": record["component_name"],
                        "value": record["component_value"],
                        "suppliers": [sup for sup in record["suppliers"] if sup]
                    }
                    components.append(component_data)
                
                return components
                
        except Exception as e:
            logger.error(f"Failed to find components for system {system_name}: {e}")
            return []
    
    async def search_by_pattern(self, pattern: str, entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search entities by name pattern."""
        try:
            # Build entity type filter
            type_filter = ""
            if entity_types:
                type_conditions = " OR ".join([f"e.type = '{t}'" for t in entity_types])
                type_filter = f"AND ({type_conditions})"
            
            query = f"""
            MATCH (e:Entity)
            WHERE e.name =~ $pattern {type_filter}
            RETURN 
                e.name as name,
                e.type as type,
                e.value as value,
                e.confidence_score as confidence_score
            ORDER BY e.confidence_score DESC, e.name
            LIMIT 50
            """
            
            async with self.graph.driver.session() as session:
                result = await session.run(query, pattern=f"(?i).*{pattern}.*")
                
                entities = []
                async for record in result:
                    entity_data = {
                        "name": record["name"],
                        "type": record["type"],
                        "value": record["value"],
                        "confidence_score": record["confidence_score"]
                    }
                    entities.append(entity_data)
                
                return entities
                
        except Exception as e:
            logger.error(f"Failed to search entities by pattern {pattern}: {e}")
            return []
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        try:
            query = """
            MATCH (e:Entity)
            OPTIONAL MATCH ()-[r]->()
            RETURN 
                count(DISTINCT e) as total_entities,
                count(DISTINCT r) as total_relationships,
                collect(DISTINCT e.type) as entity_types
            """
            
            async with self.graph.driver.session() as session:
                result = await session.run(query)
                record = await result.single()
                
                if record:
                    return {
                        "total_entities": record["total_entities"],
                        "total_relationships": record["total_relationships"],
                        "entity_types": [t for t in record["entity_types"] if t]
                    }
                else:
                    return {
                        "total_entities": 0,
                        "total_relationships": 0,
                        "entity_types": []
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {
                "total_entities": 0,
                "total_relationships": 0,
                "entity_types": []
            }


# Global graph manager instance
graph_manager: Optional[GraphManager] = None


async def get_graph_manager() -> GraphManager:
    """Get the global graph manager instance."""
    global graph_manager
    if not graph_manager:
        raise RuntimeError("Graph manager not initialized")
    return graph_manager


async def initialize_graph() -> None:
    """Initialize the global graph manager."""
    global graph_manager
    graph_manager = GraphManager()
    await graph_manager.initialize()
    await graph_manager.create_indexes()


async def close_graph() -> None:
    """Close the global graph manager."""
    global graph_manager
    if graph_manager:
        await graph_manager.close()
        graph_manager = None
