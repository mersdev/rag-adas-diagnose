"""
Document processing utilities for ADAS Diagnostics Co-pilot.

This module handles file parsing, text extraction, and semantic chunking
for various automotive document types including PDFs, markdown, and text files.
"""

import hashlib
import logging
import mimetypes
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import pypdf
from markdown import markdown
from bs4 import BeautifulSoup

from agent.models import (
    DocumentCreate, ChunkCreate, ContentType, VehicleSystem, SeverityLevel,
    ProcessingStatus
)
from agent.config import get_settings

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a processed document chunk."""
    
    def __init__(
        self,
        content: str,
        chunk_index: int,
        start_char: int = 0,
        end_char: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.chunk_index = chunk_index
        self.start_char = start_char
        self.end_char = end_char
        self.metadata = metadata or {}
        
        # Automotive-specific flags
        self.contains_dtc_codes = self._detect_dtc_codes()
        self.contains_version_info = self._detect_version_info()
        self.contains_component_info = self._detect_component_info()
    
    def _detect_dtc_codes(self) -> bool:
        """Detect if chunk contains diagnostic trouble codes."""
        dtc_pattern = r'\b[BPUC]\d{4}\b'
        return bool(re.search(dtc_pattern, self.content, re.IGNORECASE))
    
    def _detect_version_info(self) -> bool:
        """Detect if chunk contains version information."""
        version_patterns = [
            r'v\d+\.\d+\.\d+',
            r'version\s+\d+\.\d+',
            r'firmware\s+\d+\.\d+',
            r'software\s+\d+\.\d+'
        ]
        for pattern in version_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                return True
        return False
    
    def _detect_component_info(self) -> bool:
        """Detect if chunk contains component information."""
        component_keywords = [
            'sensor', 'module', 'controller', 'ecu', 'actuator',
            'camera', 'radar', 'lidar', 'brake', 'steering',
            'engine', 'transmission', 'battery', 'motor'
        ]
        content_lower = self.content.lower()
        return any(keyword in content_lower for keyword in component_keywords)
    
    def get_content_hash(self) -> str:
        """Generate hash for chunk content."""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()


class AutomotiveDocumentProcessor:
    """Processor for automotive documents with domain-specific parsing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supported_extensions = self.settings.automotive.supported_file_types
        self.max_file_size = self.settings.automotive.max_file_size_mb * 1024 * 1024
        
        # Automotive-specific patterns
        self.ota_version_pattern = re.compile(self.settings.automotive.ota_version_pattern)
        self.dtc_code_pattern = re.compile(self.settings.automotive.dtc_code_pattern)
    
    def can_process(self, file_path: Path) -> bool:
        """Check if file can be processed."""
        if not file_path.exists():
            return False
        
        if file_path.stat().st_size > self.max_file_size:
            logger.warning(f"File {file_path} exceeds maximum size limit")
            return False
        
        return file_path.suffix.lower() in self.supported_extensions
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text content from file."""
        try:
            suffix = file_path.suffix.lower()
            
            if suffix == '.pdf':
                return self._extract_pdf_text(file_path)
            elif suffix in ['.md', '.markdown']:
                return self._extract_markdown_text(file_path)
            elif suffix in ['.txt', '.log']:
                return self._extract_plain_text(file_path)
            elif suffix == '.csv':
                return self._extract_csv_text(file_path)
            elif suffix == '.json':
                return self._extract_json_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {suffix}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return ""
    
    def _extract_markdown_text(self, file_path: Path) -> str:
        """Extract text from Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_content = file.read()
            
            # Convert markdown to HTML then extract text
            html = markdown(markdown_content)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(separator='\n').strip()
        except Exception as e:
            logger.error(f"Failed to extract Markdown text: {e}")
            return ""
    
    def _extract_plain_text(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read().strip()
            except Exception as e:
                logger.error(f"Failed to extract plain text: {e}")
                return ""
    
    def _extract_csv_text(self, file_path: Path) -> str:
        """Extract text from CSV file."""
        try:
            import csv
            text_lines = []
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    text_lines.append(' | '.join(row))
            return '\n'.join(text_lines)
        except Exception as e:
            logger.error(f"Failed to extract CSV text: {e}")
            return ""
    
    def _extract_json_text(self, file_path: Path) -> str:
        """Extract text from JSON file."""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert JSON to readable text
            def json_to_text(obj, prefix=""):
                if isinstance(obj, dict):
                    lines = []
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            lines.append(f"{prefix}{key}:")
                            lines.extend(json_to_text(value, prefix + "  "))
                        else:
                            lines.append(f"{prefix}{key}: {value}")
                    return lines
                elif isinstance(obj, list):
                    lines = []
                    for i, item in enumerate(obj):
                        lines.append(f"{prefix}[{i}]:")
                        lines.extend(json_to_text(item, prefix + "  "))
                    return lines
                else:
                    return [f"{prefix}{obj}"]
            
            return '\n'.join(json_to_text(data))
        except Exception as e:
            logger.error(f"Failed to extract JSON text: {e}")
            return ""
    
    def detect_content_type(self, file_path: Path, content: str) -> ContentType:
        """Detect automotive content type from file and content."""
        filename_lower = file_path.name.lower()
        content_lower = content.lower()
        
        # OTA Update detection
        if any(keyword in filename_lower for keyword in ['ota', 'update', 'release', 'firmware']):
            return ContentType.OTA_UPDATE
        if any(keyword in content_lower for keyword in ['over-the-air', 'software update', 'firmware update']):
            return ContentType.OTA_UPDATE
        
        # Hardware specification detection
        if any(keyword in filename_lower for keyword in ['spec', 'datasheet', 'hardware']):
            return ContentType.HARDWARE_SPEC
        if any(keyword in content_lower for keyword in ['specifications', 'datasheet', 'pin configuration']):
            return ContentType.HARDWARE_SPEC
        
        # Diagnostic log detection
        if any(keyword in filename_lower for keyword in ['log', 'diagnostic', 'dtc']):
            return ContentType.DIAGNOSTIC_LOG
        if self.dtc_code_pattern.search(content):
            return ContentType.DIAGNOSTIC_LOG
        
        # Repair note detection
        if any(keyword in filename_lower for keyword in ['repair', 'fix', 'solution', 'troubleshoot']):
            return ContentType.REPAIR_NOTE
        if any(keyword in content_lower for keyword in ['repair procedure', 'troubleshooting', 'solution']):
            return ContentType.REPAIR_NOTE
        
        # Supplier documentation detection
        if any(keyword in filename_lower for keyword in ['supplier', 'vendor', 'manufacturer']):
            return ContentType.SUPPLIER_DOC
        
        # Default to system architecture
        return ContentType.SYSTEM_ARCHITECTURE
    
    def detect_vehicle_system(self, content: str) -> Optional[VehicleSystem]:
        """Detect vehicle system from content."""
        content_lower = content.lower()
        
        # ADAS system detection
        adas_keywords = ['adas', 'advanced driver', 'lane keep', 'adaptive cruise', 'collision', 'autonomous']
        if any(keyword in content_lower for keyword in adas_keywords):
            return VehicleSystem.ADAS
        
        # Braking system detection
        braking_keywords = ['brake', 'abs', 'esp', 'stability control']
        if any(keyword in content_lower for keyword in braking_keywords):
            return VehicleSystem.BRAKING
        
        # Steering system detection
        steering_keywords = ['steering', 'power steering', 'eps']
        if any(keyword in content_lower for keyword in steering_keywords):
            return VehicleSystem.STEERING
        
        # Powertrain detection
        powertrain_keywords = ['engine', 'transmission', 'powertrain', 'drivetrain']
        if any(keyword in content_lower for keyword in powertrain_keywords):
            return VehicleSystem.POWERTRAIN
        
        # Infotainment detection
        infotainment_keywords = ['infotainment', 'navigation', 'audio', 'display']
        if any(keyword in content_lower for keyword in infotainment_keywords):
            return VehicleSystem.INFOTAINMENT
        
        return None
    
    def detect_severity_level(self, content: str) -> Optional[SeverityLevel]:
        """Detect severity level from content."""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['critical', 'safety', 'recall', 'urgent']):
            return SeverityLevel.CRITICAL
        elif any(keyword in content_lower for keyword in ['high', 'important', 'significant']):
            return SeverityLevel.HIGH
        elif any(keyword in content_lower for keyword in ['medium', 'moderate']):
            return SeverityLevel.MEDIUM
        elif any(keyword in content_lower for keyword in ['low', 'minor', 'cosmetic']):
            return SeverityLevel.LOW
        
        return None
    
    def extract_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract automotive-specific metadata from document."""
        metadata = {}
        
        # Extract VIN patterns
        vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
        vins = re.findall(vin_pattern, content)
        if vins:
            metadata['vin_patterns'] = list(set(vins))
        
        # Extract component names
        component_pattern = r'\b(?:ECU|Module|Controller|Sensor|Actuator)\s+([A-Z][A-Za-z\s]+)'
        components = re.findall(component_pattern, content, re.IGNORECASE)
        if components:
            metadata['components'] = list(set(comp.strip() for comp in components))
        
        # Extract supplier information
        supplier_pattern = r'(?:Supplier|Manufacturer|Vendor):\s*([A-Za-z\s]+)'
        suppliers = re.findall(supplier_pattern, content, re.IGNORECASE)
        if suppliers:
            metadata['suppliers'] = list(set(sup.strip() for sup in suppliers))
        
        # Extract model years
        year_pattern = r'\b(20\d{2})\b'
        years = [int(year) for year in re.findall(year_pattern, content)]
        if years:
            metadata['model_years'] = sorted(list(set(years)))
        
        return metadata

    def chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
        """
        Split document content into semantic chunks.

        Uses a combination of sentence boundaries and size limits to create
        meaningful chunks for automotive documents.
        """
        if not content.strip():
            return []

        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If adding this paragraph would exceed chunk size, finalize current chunk
            if current_chunk and len(current_chunk) + len(paragraph) > chunk_size:
                # Create chunk
                chunk_end = current_start + len(current_chunk)
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=chunk_end
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + paragraph
                current_start = chunk_end - len(overlap_text)
                chunk_index += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk if there's content
        if current_chunk.strip():
            chunk_end = current_start + len(current_chunk)
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end
            )
            chunks.append(chunk)

        return chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= overlap_size:
            return text

        # Try to break at sentence boundary
        sentences = text.split('. ')
        if len(sentences) > 1:
            # Take last few sentences that fit in overlap
            overlap_text = ""
            for sentence in reversed(sentences):
                test_text = sentence + ". " + overlap_text if overlap_text else sentence
                if len(test_text) <= overlap_size:
                    overlap_text = test_text
                else:
                    break
            return overlap_text

        # Fallback to character-based overlap
        return text[-overlap_size:]

    def process_document(self, file_path: Path) -> Tuple[DocumentCreate, List[DocumentChunk]]:
        """
        Process a document file and return document metadata and chunks.

        Returns:
            Tuple of (DocumentCreate object, list of DocumentChunk objects)
        """
        if not self.can_process(file_path):
            raise ValueError(f"Cannot process file: {file_path}")

        # Extract text content
        content = self.extract_text(file_path)
        if not content:
            raise ValueError(f"No content extracted from file: {file_path}")

        # Generate file hash
        file_hash = self._calculate_file_hash(file_path)

        # Detect automotive metadata
        content_type = self.detect_content_type(file_path, content)
        vehicle_system = self.detect_vehicle_system(content)
        severity_level = self.detect_severity_level(content)
        metadata = self.extract_metadata(file_path, content)

        # Create document metadata
        document = DocumentCreate(
            filename=file_path.name,
            title=self._extract_title(content),
            content_type=content_type,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            file_hash=file_hash,
            vehicle_system=vehicle_system,
            component_name=metadata.get('components', [None])[0] if metadata.get('components') else None,
            supplier=metadata.get('suppliers', [None])[0] if metadata.get('suppliers') else None,
            model_years=metadata.get('model_years'),
            vin_patterns=metadata.get('vin_patterns'),
            severity_level=severity_level,
            processing_status=ProcessingStatus.PROCESSING
        )

        # Create chunks
        chunks = self.chunk_document(content)

        return document, chunks

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from document content."""
        lines = content.split('\n')

        # Look for markdown-style headers
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()

        # Look for title-like patterns
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 100 and not line.endswith('.'):
                # Likely a title
                return line

        return None
