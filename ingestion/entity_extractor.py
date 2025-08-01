"""
Entity extraction pipeline for ADAS Diagnostics Co-pilot.

This module extracts automotive entities and relationships from documents
to populate the knowledge graph for enhanced diagnostic capabilities.
"""

import logging
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from agent.models import EntityType, VehicleSystem

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between automotive entities."""
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    CONNECTS_TO = "connects_to"
    CONTROLS = "controls"
    MONITORS = "monitors"
    SUPPLIES = "supplies"
    AFFECTS = "affects"
    COMMUNICATES_WITH = "communicates_with"
    REPLACES = "replaces"
    REQUIRES = "requires"


@dataclass
class ExtractedEntity:
    """Represents an extracted automotive entity."""
    name: str
    entity_type: EntityType
    confidence: float
    context: str
    properties: Dict[str, Any]
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class ExtractedRelationship:
    """Represents an extracted relationship between entities."""
    source_entity: str
    target_entity: str
    relationship_type: RelationshipType
    confidence: float
    context: str
    properties: Dict[str, Any]


class AutomotiveEntityExtractor:
    """Extracts automotive entities and relationships from text."""
    
    def __init__(self):
        """Initialize the entity extractor with automotive patterns."""
        self._init_patterns()
        self._init_keywords()
    
    def _init_patterns(self):
        """Initialize regex patterns for entity extraction."""
        # Component patterns
        self.component_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:ECU|Module|Controller|Unit)\b',
            r'\b(?:ECU|Module|Controller|Unit)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Sensor|Actuator|Motor|Pump)\b',
            r'\b(?:Sensor|Actuator|Motor|Pump)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        ]
        
        # System patterns
        self.system_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+System\b',
            r'\bSystem\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b(ADAS|ABS|ESP|EPS|TCM|ECM|BCM|PCM)\b'
        ]
        
        # Supplier patterns
        self.supplier_patterns = [
            r'(?:Supplier|Manufacturer|Vendor|OEM):\s*([A-Z][a-zA-Z\s&.,]+?)(?:\n|$|,)',
            r'\b(Bosch|Continental|Denso|Delphi|Valeo|ZF|Magna|Aptiv|Visteon|Harman)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:GmbH|Inc\.|Corp\.|Ltd\.|AG|SE)\b'
        ]
        
        # DTC patterns
        self.dtc_patterns = [
            r'\b([BPUC]\d{4})\b',
            r'(?:DTC|Code|Error)\s*:?\s*([BPUC]\d{4})\b'
        ]
        
        # Version patterns
        self.version_patterns = [
            r'(?:Version|Ver\.|v)\s*(\d+\.\d+(?:\.\d+)?)',
            r'(?:Firmware|Software)\s+(\d+\.\d+(?:\.\d+)?)',
            r'\b(v?\d+\.\d+\.\d+)\b'
        ]
        
        # VIN patterns
        self.vin_patterns = [
            r'\b([A-HJ-NPR-Z0-9]{17})\b'
        ]
    
    def _init_keywords(self):
        """Initialize keyword dictionaries for entity classification."""
        self.component_keywords = {
            EntityType.COMPONENT: [
                'sensor', 'actuator', 'module', 'controller', 'ecu', 'unit',
                'motor', 'pump', 'valve', 'switch', 'relay', 'fuse',
                'camera', 'radar', 'lidar', 'antenna', 'display', 'speaker',
                'microphone', 'button', 'knob', 'lever', 'pedal'
            ]
        }
        
        self.system_keywords = {
            EntityType.SYSTEM: [
                'adas', 'abs', 'esp', 'eps', 'tcm', 'ecm', 'bcm', 'pcm',
                'braking', 'steering', 'powertrain', 'infotainment',
                'navigation', 'climate', 'lighting', 'security'
            ]
        }
        
        self.supplier_keywords = {
            EntityType.SUPPLIER: [
                'bosch', 'continental', 'denso', 'delphi', 'valeo', 'zf',
                'magna', 'aptiv', 'visteon', 'harman', 'lear', 'faurecia'
            ]
        }
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract automotive entities from text."""
        entities = []
        
        # Extract different types of entities
        entities.extend(self._extract_components(text))
        entities.extend(self._extract_systems(text))
        entities.extend(self._extract_suppliers(text))
        entities.extend(self._extract_dtc_codes(text))
        entities.extend(self._extract_versions(text))
        entities.extend(self._extract_vins(text))
        
        # Remove duplicates and filter by confidence
        entities = self._deduplicate_entities(entities)
        entities = [e for e in entities if e.confidence >= 0.5]
        
        return entities
    
    def _extract_components(self, text: str) -> List[ExtractedEntity]:
        """Extract component entities from text."""
        entities = []
        
        for pattern in self.component_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if len(name) > 2:  # Filter out very short matches
                    context = self._get_context(text, match.start(), match.end())
                    confidence = self._calculate_component_confidence(name, context)
                    
                    entity = ExtractedEntity(
                        name=name,
                        entity_type=EntityType.COMPONENT,
                        confidence=confidence,
                        context=context,
                        properties=self._extract_component_properties(context),
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_systems(self, text: str) -> List[ExtractedEntity]:
        """Extract system entities from text."""
        entities = []
        
        for pattern in self.system_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if len(name) > 1:
                    context = self._get_context(text, match.start(), match.end())
                    confidence = self._calculate_system_confidence(name, context)
                    
                    entity = ExtractedEntity(
                        name=name,
                        entity_type=EntityType.SYSTEM,
                        confidence=confidence,
                        context=context,
                        properties=self._extract_system_properties(context),
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_suppliers(self, text: str) -> List[ExtractedEntity]:
        """Extract supplier entities from text."""
        entities = []
        
        for pattern in self.supplier_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if len(name) > 2:
                    context = self._get_context(text, match.start(), match.end())
                    confidence = self._calculate_supplier_confidence(name, context)
                    
                    entity = ExtractedEntity(
                        name=name,
                        entity_type=EntityType.SUPPLIER,
                        confidence=confidence,
                        context=context,
                        properties=self._extract_supplier_properties(context),
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        return entities
    
    def _extract_dtc_codes(self, text: str) -> List[ExtractedEntity]:
        """Extract DTC code entities from text."""
        entities = []
        
        for pattern in self.dtc_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).upper()
                context = self._get_context(text, match.start(), match.end())
                
                entity = ExtractedEntity(
                    name=name,
                    entity_type=EntityType.DTC,
                    confidence=0.95,  # High confidence for DTC patterns
                    context=context,
                    properties=self._extract_dtc_properties(name, context),
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        return entities
    
    def _extract_versions(self, text: str) -> List[ExtractedEntity]:
        """Extract version entities from text."""
        entities = []
        
        for pattern in self.version_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1)
                context = self._get_context(text, match.start(), match.end())
                
                entity = ExtractedEntity(
                    name=name,
                    entity_type=EntityType.SOFTWARE_VERSION,
                    confidence=0.9,
                    context=context,
                    properties=self._extract_version_properties(context),
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        return entities
    
    def _extract_vins(self, text: str) -> List[ExtractedEntity]:
        """Extract VIN entities from text."""
        entities = []
        
        for pattern in self.vin_patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1)
                context = self._get_context(text, match.start(), match.end())
                
                entity = ExtractedEntity(
                    name=name,
                    entity_type=EntityType.VIN,
                    confidence=0.95,
                    context=context,
                    properties=self._extract_vin_properties(name),
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        return entities
    
    def _get_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Get context around an entity match."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _calculate_component_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for component entities."""
        confidence = 0.6  # Base confidence
        
        # Boost confidence for known component keywords
        name_lower = name.lower()
        for keyword in self.component_keywords[EntityType.COMPONENT]:
            if keyword in name_lower:
                confidence += 0.2
                break
        
        # Boost confidence for automotive context
        context_lower = context.lower()
        automotive_terms = ['vehicle', 'car', 'automotive', 'ecu', 'can', 'bus']
        for term in automotive_terms:
            if term in context_lower:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    def _calculate_system_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for system entities."""
        confidence = 0.7  # Base confidence
        
        # Boost confidence for known system keywords
        name_lower = name.lower()
        for keyword in self.system_keywords[EntityType.SYSTEM]:
            if keyword in name_lower:
                confidence += 0.2
                break
        
        return min(confidence, 1.0)
    
    def _calculate_supplier_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for supplier entities."""
        confidence = 0.6  # Base confidence
        
        # Boost confidence for known suppliers
        name_lower = name.lower()
        for keyword in self.supplier_keywords[EntityType.SUPPLIER]:
            if keyword in name_lower:
                confidence += 0.3
                break
        
        return min(confidence, 1.0)
    
    def _extract_component_properties(self, context: str) -> Dict[str, Any]:
        """Extract properties for component entities."""
        properties = {}
        
        # Extract part numbers
        part_pattern = r'(?:Part|P/N|PN)\s*:?\s*([A-Z0-9\-]+)'
        part_match = re.search(part_pattern, context, re.IGNORECASE)
        if part_match:
            properties['part_number'] = part_match.group(1)
        
        return properties
    
    def _extract_system_properties(self, context: str) -> Dict[str, Any]:
        """Extract properties for system entities."""
        properties = {}
        
        # Determine vehicle system
        context_lower = context.lower()
        if any(term in context_lower for term in ['brake', 'abs', 'esp']):
            properties['vehicle_system'] = VehicleSystem.BRAKING.value
        elif any(term in context_lower for term in ['steering', 'eps']):
            properties['vehicle_system'] = VehicleSystem.STEERING.value
        elif any(term in context_lower for term in ['adas', 'lane', 'cruise', 'collision']):
            properties['vehicle_system'] = VehicleSystem.ADAS.value
        elif any(term in context_lower for term in ['engine', 'transmission', 'powertrain']):
            properties['vehicle_system'] = VehicleSystem.POWERTRAIN.value
        elif any(term in context_lower for term in ['infotainment', 'navigation', 'audio']):
            properties['vehicle_system'] = VehicleSystem.INFOTAINMENT.value
        
        return properties
    
    def _extract_supplier_properties(self, context: str) -> Dict[str, Any]:
        """Extract properties for supplier entities."""
        return {}
    
    def _extract_dtc_properties(self, name: str, context: str) -> Dict[str, Any]:
        """Extract properties for DTC code entities."""
        properties = {}
        
        # Determine DTC category from first character
        if name.startswith('B'):
            properties['category'] = 'Body'
        elif name.startswith('C'):
            properties['category'] = 'Chassis'
        elif name.startswith('P'):
            properties['category'] = 'Powertrain'
        elif name.startswith('U'):
            properties['category'] = 'Network'
        
        return properties
    
    def _extract_version_properties(self, context: str) -> Dict[str, Any]:
        """Extract properties for version entities."""
        properties = {}
        
        # Determine version type
        context_lower = context.lower()
        if 'firmware' in context_lower:
            properties['version_type'] = 'firmware'
        elif 'software' in context_lower:
            properties['version_type'] = 'software'
        elif 'hardware' in context_lower:
            properties['version_type'] = 'hardware'
        
        return properties
    
    def _extract_vin_properties(self, vin: str) -> Dict[str, Any]:
        """Extract properties from VIN."""
        properties = {}
        
        if len(vin) == 17:
            properties['manufacturer'] = vin[:3]
            properties['model_year_code'] = vin[9]
            properties['plant_code'] = vin[10]
            properties['serial_number'] = vin[11:]
        
        return properties
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping the one with highest confidence."""
        entity_map = {}
        
        for entity in entities:
            key = (entity.name.lower(), entity.entity_type)
            if key not in entity_map or entity.confidence > entity_map[key].confidence:
                entity_map[key] = entity
        
        return list(entity_map.values())

    def extract_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelationship]:
        """Extract relationships between entities."""
        relationships = []

        # Create entity lookup for faster access
        entity_positions = {}
        for entity in entities:
            entity_positions[entity.name.lower()] = entity

        # Extract different types of relationships
        relationships.extend(self._extract_dependency_relationships(text, entities))
        relationships.extend(self._extract_part_of_relationships(text, entities))
        relationships.extend(self._extract_control_relationships(text, entities))
        relationships.extend(self._extract_communication_relationships(text, entities))

        # Remove duplicates
        relationships = self._deduplicate_relationships(relationships)

        return relationships

    def _extract_dependency_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelationship]:
        """Extract dependency relationships."""
        relationships = []

        # Patterns for dependency relationships
        dependency_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:depends on|requires|needs)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:is dependent on|relies on)\s+(\w+(?:\s+\w+)*)',
            r'without\s+(\w+(?:\s+\w+)*),?\s+(\w+(?:\s+\w+)*)\s+(?:cannot|will not|fails)'
        ]

        for pattern in dependency_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()

                # Check if both entities exist in our extracted entities
                if self._entity_exists(source, entities) and self._entity_exists(target, entities):
                    context = self._get_context(text, match.start(), match.end())

                    relationship = ExtractedRelationship(
                        source_entity=source,
                        target_entity=target,
                        relationship_type=RelationshipType.DEPENDS_ON,
                        confidence=0.8,
                        context=context,
                        properties={}
                    )
                    relationships.append(relationship)

        return relationships

    def _extract_part_of_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelationship]:
        """Extract part-of relationships."""
        relationships = []

        # Patterns for part-of relationships
        part_of_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:is part of|belongs to|is in|is within)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:component|module|part)\s+of\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:subsystem|submodule)\s+of\s+(\w+(?:\s+\w+)*)'
        ]

        for pattern in part_of_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()

                if self._entity_exists(source, entities) and self._entity_exists(target, entities):
                    context = self._get_context(text, match.start(), match.end())

                    relationship = ExtractedRelationship(
                        source_entity=source,
                        target_entity=target,
                        relationship_type=RelationshipType.PART_OF,
                        confidence=0.8,
                        context=context,
                        properties={}
                    )
                    relationships.append(relationship)

        return relationships

    def _extract_control_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelationship]:
        """Extract control relationships."""
        relationships = []

        # Patterns for control relationships
        control_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:controls|manages|operates)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:is controlled by|is managed by|is operated by)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:monitors|supervises|oversees)\s+(\w+(?:\s+\w+)*)'
        ]

        for pattern in control_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()

                if self._entity_exists(source, entities) and self._entity_exists(target, entities):
                    context = self._get_context(text, match.start(), match.end())

                    # Determine relationship type based on pattern
                    if 'monitor' in match.group(0).lower():
                        rel_type = RelationshipType.MONITORS
                    else:
                        rel_type = RelationshipType.CONTROLS

                    relationship = ExtractedRelationship(
                        source_entity=source,
                        target_entity=target,
                        relationship_type=rel_type,
                        confidence=0.7,
                        context=context,
                        properties={}
                    )
                    relationships.append(relationship)

        return relationships

    def _extract_communication_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelationship]:
        """Extract communication relationships."""
        relationships = []

        # Patterns for communication relationships
        comm_patterns = [
            r'(\w+(?:\s+\w+)*)\s+(?:communicates with|sends data to|receives data from)\s+(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+(?:and|&)\s+(\w+(?:\s+\w+)*)\s+(?:communicate|exchange data)',
            r'(?:CAN|LIN|FlexRay|Ethernet)\s+(?:bus|network)\s+(?:connects|links)\s+(\w+(?:\s+\w+)*)\s+(?:and|to|with)\s+(\w+(?:\s+\w+)*)'
        ]

        for pattern in comm_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()

                if self._entity_exists(source, entities) and self._entity_exists(target, entities):
                    context = self._get_context(text, match.start(), match.end())

                    relationship = ExtractedRelationship(
                        source_entity=source,
                        target_entity=target,
                        relationship_type=RelationshipType.COMMUNICATES_WITH,
                        confidence=0.7,
                        context=context,
                        properties={}
                    )
                    relationships.append(relationship)

        return relationships

    def _entity_exists(self, entity_name: str, entities: List[ExtractedEntity]) -> bool:
        """Check if an entity exists in the extracted entities list."""
        entity_name_lower = entity_name.lower()
        for entity in entities:
            if entity.name.lower() == entity_name_lower:
                return True
        return False

    def _deduplicate_relationships(self, relationships: List[ExtractedRelationship]) -> List[ExtractedRelationship]:
        """Remove duplicate relationships."""
        relationship_map = {}

        for rel in relationships:
            key = (rel.source_entity.lower(), rel.target_entity.lower(), rel.relationship_type)
            if key not in relationship_map or rel.confidence > relationship_map[key].confidence:
                relationship_map[key] = rel

        return list(relationship_map.values())
