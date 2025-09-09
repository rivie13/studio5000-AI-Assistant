#!/usr/bin/env python3
"""
L5X Content Chunk Data Structures

Defines the data structures for representing searchable chunks of L5X content
extracted from Studio 5000 projects using the SDK.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class L5XChunkType(Enum):
    """Types of L5X content chunks for semantic indexing"""
    PROGRAM = "program"
    ROUTINE = "routine"
    LADDER_RUNG = "ladder_rung"
    STRUCTURED_TEXT = "structured_text"
    UDT = "udt"
    UDT_MEMBER = "udt_member"
    TAG = "tag"
    TAG_COMMENT = "tag_comment"
    MODULE = "module"
    TASK = "task"
    MOTION_GROUP = "motion_group"
    DATA_TYPE = "data_type"
    ALARM = "alarm"

@dataclass
class L5XLocation:
    """Precise location information for L5X content"""
    file_path: str                  # Source ACD/L5K file path
    xpath: str                      # SDK XPath for direct navigation
    line_start: Optional[int] = None    # Line number in extracted L5X
    line_end: Optional[int] = None      # End line number
    parent_program: Optional[str] = None  # Parent program name
    parent_routine: Optional[str] = None  # Parent routine name
    rung_number: Optional[int] = None     # Rung number for ladder logic
    insertion_points: List[int] = None    # Available positions for new content

    def __post_init__(self):
        if self.insertion_points is None:
            self.insertion_points = []

@dataclass 
class L5XChunk:
    """Represents a searchable chunk of L5X content with SDK integration"""
    
    # Core identification
    id: str                         # Unique identifier
    chunk_type: L5XChunkType        # Type of content
    name: str                       # Component name
    
    # Content and description
    content: str                    # Raw L5X content or ladder logic
    description: str                # Human-readable description
    comment: Optional[str] = None   # Original comment from L5X
    
    # Location and navigation
    location: L5XLocation = None    # Location information with XPath
    
    # Relationships and dependencies
    dependencies: List[str] = None  # Related components (tags, UDTs, etc.)
    references: List[str] = None    # Components that reference this chunk
    
    # Metadata for enhanced search
    metadata: Dict[str, Any] = None # Additional context information
    
    # SDK-specific information
    sdk_extractable: bool = True    # Can be extracted via SDK
    sdk_modifiable: bool = True     # Can be modified via SDK
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.references is None:
            self.references = []
        if self.metadata is None:
            self.metadata = {}
        if self.location is None:
            self.location = L5XLocation("", "")
    
    @property
    def searchable_text(self) -> str:
        """Generate comprehensive text for vector embedding"""
        parts = [
            f"Type: {self.chunk_type.value}",
            f"Name: {self.name}",
            f"Description: {self.description}"
        ]
        
        if self.comment:
            parts.append(f"Comment: {self.comment}")
        
        if self.location.parent_program:
            parts.append(f"Program: {self.location.parent_program}")
        
        if self.location.parent_routine:
            parts.append(f"Routine: {self.location.parent_routine}")
        
        if self.dependencies:
            parts.append(f"Dependencies: {', '.join(self.dependencies)}")
        
        # Add content if it's not too long
        if len(self.content) < 500:
            parts.append(f"Content: {self.content}")
        else:
            # For long content, add just a snippet
            parts.append(f"Content preview: {self.content[:200]}...")
        
        # Add metadata
        for key, value in self.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                parts.append(f"{key}: {value}")
        
        return " | ".join(parts)
    
    @property
    def is_ladder_logic(self) -> bool:
        """Check if this chunk contains ladder logic"""
        return self.chunk_type == L5XChunkType.LADDER_RUNG
    
    @property
    def is_routine(self) -> bool:
        """Check if this chunk is a complete routine"""
        return self.chunk_type == L5XChunkType.ROUTINE
    
    @property
    def insertion_xpath(self) -> str:
        """Generate XPath for inserting content after this chunk"""
        if self.chunk_type == L5XChunkType.LADDER_RUNG and self.location.parent_routine:
            return f"Controller/Programs/Program[@Name='{self.location.parent_program}']/Routines/Routine[@Name='{self.location.parent_routine}']/RLLContent"
        elif self.chunk_type == L5XChunkType.ROUTINE and self.location.parent_program:
            return f"Controller/Programs/Program[@Name='{self.location.parent_program}']/Routines"
        else:
            return self.location.xpath

def create_ladder_rung_chunk(routine_name: str, program_name: str, rung_number: int, 
                           rung_content: str, rung_comment: str = None, 
                           file_path: str = "") -> L5XChunk:
    """Factory function to create a ladder rung chunk"""
    
    # Generate XPath for this specific rung
    xpath = f"Controller/Programs/Program[@Name='{program_name}']/Routines/Routine[@Name='{routine_name}']/RLLContent/Rung[@Number='{rung_number}']"
    
    location = L5XLocation(
        file_path=file_path,
        xpath=xpath,
        parent_program=program_name,
        parent_routine=routine_name,
        rung_number=rung_number,
        insertion_points=[rung_number + 1]  # Can insert after this rung
    )
    
    # Extract tags from ladder logic for dependencies
    dependencies = extract_tags_from_ladder_logic(rung_content)
    
    return L5XChunk(
        id=f"{routine_name}_rung_{rung_number}",
        chunk_type=L5XChunkType.LADDER_RUNG,
        name=f"Rung {rung_number}",
        content=rung_content,
        description=rung_comment or f"Ladder logic rung {rung_number} in routine {routine_name}",
        comment=rung_comment,
        location=location,
        dependencies=dependencies,
        metadata={
            'rung_number': rung_number,
            'routine_name': routine_name,
            'program_name': program_name,
            'instruction_count': len(rung_content.split())
        }
    )

def create_routine_chunk(routine_name: str, program_name: str, routine_type: str,
                        routine_content: str, routine_description: str = None,
                        file_path: str = "") -> L5XChunk:
    """Factory function to create a routine chunk"""
    
    xpath = f"Controller/Programs/Program[@Name='{program_name}']/Routines/Routine[@Name='{routine_name}']"
    
    location = L5XLocation(
        file_path=file_path,
        xpath=xpath,
        parent_program=program_name,
        parent_routine=routine_name
    )
    
    return L5XChunk(
        id=f"{program_name}_{routine_name}",
        chunk_type=L5XChunkType.ROUTINE,
        name=routine_name,
        content=routine_content,
        description=routine_description or f"{routine_type} routine {routine_name} in program {program_name}",
        location=location,
        metadata={
            'routine_type': routine_type,
            'program_name': program_name,
            'content_length': len(routine_content)
        }
    )

def create_udt_chunk(udt_name: str, udt_content: str, udt_description: str = None,
                    file_path: str = "") -> L5XChunk:
    """Factory function to create a UDT chunk"""
    
    xpath = f"Controller/DataTypes/DataType[@Name='{udt_name}']"
    
    location = L5XLocation(
        file_path=file_path,
        xpath=xpath
    )
    
    # Extract member names for dependencies
    dependencies = extract_udt_dependencies(udt_content)
    
    return L5XChunk(
        id=f"udt_{udt_name}",
        chunk_type=L5XChunkType.UDT,
        name=udt_name,
        content=udt_content,
        description=udt_description or f"User-defined data type {udt_name}",
        location=location,
        dependencies=dependencies,
        metadata={
            'udt_name': udt_name,
            'member_count': udt_content.count('<Member Name=')
        }
    )

def extract_tags_from_ladder_logic(ladder_logic: str) -> List[str]:
    """Extract tag names from ladder logic content"""
    import re
    
    # Common ladder logic tag patterns
    patterns = [
        r'XIC\(([^)]+)\)',  # XIC(tag_name)
        r'XIO\(([^)]+)\)',  # XIO(tag_name)  
        r'OTE\(([^)]+)\)',  # OTE(tag_name)
        r'OTL\(([^)]+)\)',  # OTL(tag_name)
        r'OTU\(([^)]+)\)',  # OTU(tag_name)
        r'TON\(([^,)]+)',   # TON(timer_tag, ...
        r'TOF\(([^,)]+)',   # TOF(timer_tag, ...
        r'RTO\(([^,)]+)',   # RTO(timer_tag, ...
        r'CTU\(([^,)]+)',   # CTU(counter_tag, ...
        r'CTD\(([^,)]+)',   # CTD(counter_tag, ...
        r'MOV\([^,]+,([^)]+)\)',  # MOV(source, dest)
        r'ADD\([^,]+,[^,]+,([^)]+)\)',  # ADD(A, B, dest)
    ]
    
    tags = set()
    for pattern in patterns:
        matches = re.findall(pattern, ladder_logic)
        tags.update(matches)
    
    # Clean up tag names (remove quotes, trim whitespace)
    cleaned_tags = []
    for tag in tags:
        cleaned = tag.strip().strip('"\'')
        if cleaned and not cleaned.isdigit():  # Skip numeric constants
            cleaned_tags.append(cleaned)
    
    return list(set(cleaned_tags))

def extract_udt_dependencies(udt_content: str) -> List[str]:
    """Extract dependencies from UDT XML content"""
    import re
    
    # Extract DataType references
    pattern = r'DataType="([^"]+)"'
    matches = re.findall(pattern, udt_content)
    
    # Filter out basic data types
    basic_types = {'BOOL', 'SINT', 'INT', 'DINT', 'REAL', 'STRING', 'TIMER', 'COUNTER'}
    dependencies = [match for match in matches if match not in basic_types]
    
    return list(set(dependencies))
