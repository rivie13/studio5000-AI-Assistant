#!/usr/bin/env python3
"""
PDF Chunk Data Structures

Defines data structures for representing searchable chunks of PDF drawing content.
Follows the same patterns as L5XChunk and TagChunk for consistency.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class PDFChunkType(Enum):
    """Types of PDF drawing content chunks"""
    TITLE_BLOCK = "title_block"          # Drawing title and metadata
    ELECTRICAL = "electrical"           # Electrical schematics and wiring
    PID = "pid"                        # Process and instrumentation diagrams  
    CONTROL_LOGIC = "control_logic"    # Control logic diagrams
    IO_LIST = "io_list"               # I/O assignment lists
    EQUIPMENT_LIST = "equipment_list"  # Equipment and tag lists
    NOTES = "notes"                   # Drawing notes and specifications
    LAYOUT = "layout"                 # Physical layout drawings
    SAFETY = "safety"                 # Safety system diagrams
    GENERAL = "general"               # General drawing content

@dataclass
class PDFLocation:
    """Location information for PDF content"""
    page_number: int
    drawing_number: Optional[str] = None
    zone: Optional[str] = None           # Drawing zone (A1, B2, etc.)
    coordinates: Optional[Dict] = None    # X,Y coordinates on page
    
@dataclass 
class PDFChunk:
    """Represents a searchable chunk of PDF drawing content"""
    id: str                              # Unique identifier
    chunk_type: PDFChunkType            # Type of drawing content
    page_number: int                    # Source page number
    drawing_number: Optional[str]       # Drawing reference number
    title: Optional[str]                # Drawing/section title
    content: str                        # Extracted text content
    vision_description: str             # AI-generated visual description
    equipment_tags: List[str]           # Referenced equipment tags
    location: PDFLocation              # Location within PDF
    metadata: Dict[str, Any]           # Additional context
    
    # Computed properties
    @property
    def searchable_text(self) -> str:
        """Create comprehensive searchable text for embedding"""
        parts = []
        
        # Add basic identifiers
        if self.drawing_number:
            parts.append(f"Drawing: {self.drawing_number}")
        if self.title:
            parts.append(f"Title: {self.title}")
        parts.append(f"Type: {self.chunk_type.value}")
        parts.append(f"Page: {self.page_number}")
        
        # Add content
        if self.content.strip():
            parts.append(f"Content: {self.content}")
        
        # Add vision description
        if self.vision_description.strip():
            parts.append(f"Visual: {self.vision_description}")
        
        # Add equipment tags
        if self.equipment_tags:
            parts.append(f"Equipment: {', '.join(self.equipment_tags)}")
        
        # Add metadata
        for key, value in self.metadata.items():
            if value and str(value).strip():
                parts.append(f"{key}: {value}")
        
        return " | ".join(parts)
    
    @property
    def display_name(self) -> str:
        """User-friendly display name"""
        if self.drawing_number and self.title:
            return f"{self.drawing_number}: {self.title}"
        elif self.drawing_number:
            return self.drawing_number
        elif self.title:
            return self.title
        else:
            return f"Page {self.page_number} - {self.chunk_type.value}"
