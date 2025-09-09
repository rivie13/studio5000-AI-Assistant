#!/usr/bin/env python3
"""
CSV Tag Parser

Parses Studio 5000 tag CSV exports into searchable chunks with device information,
I/O mappings, and semantic categorization.
"""

import csv
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .tag_chunk import (
    TagChunk, TagChunkType, DeviceInfo, 
    create_tag_chunk_from_csv_row, find_related_tags
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVTagParser:
    """
    Parses Studio 5000 tag CSV exports into semantic chunks for vector database indexing
    """
    
    def __init__(self):
        self.tag_chunks = []
        self.comment_map = {}  # Maps tag names to their comment descriptions
        self.statistics = {
            'total_rows': 0,
            'tags_parsed': 0,
            'comments_parsed': 0,
            'device_categories': {},
            'chunk_types': {}
        }
    
    def parse_tag_csv(self, csv_path: str) -> List[TagChunk]:
        """
        Parse Studio 5000 tag CSV export into searchable chunks
        
        Args:
            csv_path: Path to the CSV file exported from Studio 5000
            
        Returns:
            List of TagChunk objects ready for vector database indexing
        """
        
        logger.info(f"Parsing tag CSV file: {csv_path}")
        
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Reset statistics
        self.tag_chunks = []
        self.comment_map = {}
        self.statistics = {
            'total_rows': 0,
            'tags_parsed': 0,
            'comments_parsed': 0,
            'device_categories': {},
            'chunk_types': {}
        }
        
        try:
            # Read the file and find the header line
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Find the header line and keep content from there
            lines = content.split('\n')
            header_index = None
            
            for i, line in enumerate(lines):
                if line.startswith('TYPE,SCOPE,NAME'):
                    header_index = i
                    break
            
            if header_index is None:
                raise ValueError("No CSV header line found (TYPE,SCOPE,NAME)")
            
            # Create CSV content from header onwards
            csv_content = '\n'.join(lines[header_index:])
            
            # Parse the CSV content
            import io
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            for row in reader:
                self.statistics['total_rows'] += 1
                self._process_csv_row(row)
            
            # Post-process to find related tags
            self._find_all_related_tags()
            
            logger.info(f"Successfully parsed {len(self.tag_chunks)} tag chunks")
            self._log_statistics()
            
            return self.tag_chunks
            
        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            raise
    
    
    def _process_csv_row(self, row: Dict[str, str]):
        """Process a single CSV row"""
        
        # Handle None values from CSV parsing
        row_type = (row.get('TYPE') or '').strip()
        tag_name = (row.get('NAME') or '').strip()
        description = (row.get('DESCRIPTION') or '').strip()
        data_type = (row.get('DATATYPE') or '').strip()
        
        if row_type == 'TAG' and tag_name:
            self._process_tag_row(tag_name, description, data_type, row)
        elif row_type == 'COMMENT' and tag_name:
            self._process_comment_row(tag_name, description, row)
    
    def _process_tag_row(self, tag_name: str, description: str, data_type: str, row: Dict[str, str]):
        """Process a TAG row from the CSV"""
        
        try:
            # Create tag chunk
            tag_chunk = create_tag_chunk_from_csv_row(tag_name, description, data_type)
            
            # Add additional metadata from CSV row
            tag_chunk.metadata.update({
                'scope': row.get('SCOPE', ''),
                'specifier': row.get('SPECIFIER', ''),
                'attributes': row.get('ATTRIBUTES', ''),
                'csv_row_type': 'TAG'
            })
            
            self.tag_chunks.append(tag_chunk)
            self.statistics['tags_parsed'] += 1
            
            # Update statistics
            category = tag_chunk.device_info.device_category
            if category:
                self.statistics['device_categories'][category] = (
                    self.statistics['device_categories'].get(category, 0) + 1
                )
            
            chunk_type = tag_chunk.chunk_type.value
            self.statistics['chunk_types'][chunk_type] = (
                self.statistics['chunk_types'].get(chunk_type, 0) + 1
            )
            
        except Exception as e:
            logger.warning(f"Failed to process tag {tag_name}: {e}")
    
    def _process_comment_row(self, tag_name: str, description: str, row: Dict[str, str]):
        """Process a COMMENT row from the CSV"""
        
        # Comments provide additional context for specific I/O points
        # They often have the format: tag_base_name with description for tag_base_name.member
        
        self.statistics['comments_parsed'] += 1
        
        # Store comment data for later association with tags
        if tag_name not in self.comment_map:
            self.comment_map[tag_name] = {}
        
        # Get the specific I/O point this comment refers to
        specifier = row.get('SPECIFIER', '').strip()
        if specifier:
            self.comment_map[tag_name][specifier] = description
        else:
            self.comment_map[tag_name]['general'] = description
    
    def _find_all_related_tags(self):
        """Find related tags for all chunks after parsing is complete"""
        
        logger.info("Finding related tags...")
        
        for chunk in self.tag_chunks:
            related_tags = find_related_tags(self.tag_chunks, chunk)
            chunk.related_tags = related_tags
            
            # Also enhance description with comment data if available
            if chunk.tag_name in self.comment_map:
                comment_data = self.comment_map[chunk.tag_name]
                self._enhance_chunk_with_comments(chunk, comment_data)
    
    def _enhance_chunk_with_comments(self, chunk: TagChunk, comment_data: Dict[str, str]):
        """Enhance a tag chunk with additional comment information"""
        
        # Add comment descriptions to the chunk for better searchability
        comment_descriptions = []
        
        for comment_key, comment_desc in comment_data.items():
            if comment_desc and comment_desc.strip():
                # Clean up comment description (remove $L markers)
                clean_desc = re.sub(r'\$L(.*?)\$L', r'\1', comment_desc).strip()
                if clean_desc and clean_desc != chunk.description:
                    comment_descriptions.append(clean_desc)
        
        if comment_descriptions:
            # Add to searchable content
            chunk.metadata['comment_descriptions'] = comment_descriptions
            
            # Enhance the main description
            original_desc = chunk.description
            enhanced_desc = original_desc
            
            if comment_descriptions:
                enhanced_desc += " | I/O Points: " + " | ".join(comment_descriptions[:5])
            
            chunk.description = enhanced_desc
            
            # Re-run function detection with the enhanced description
            from .tag_chunk import detect_function_from_description
            chunk.function = detect_function_from_description(enhanced_desc, chunk.tag_name)
    
    def _log_statistics(self):
        """Log parsing statistics"""
        
        stats = self.statistics
        logger.info(f"CSV Parsing Statistics:")
        logger.info(f"  Total rows processed: {stats['total_rows']}")
        logger.info(f"  Tags parsed: {stats['tags_parsed']}")
        logger.info(f"  Comments processed: {stats['comments_parsed']}")
        
        if stats['device_categories']:
            logger.info(f"  Device categories found:")
            for category, count in stats['device_categories'].items():
                logger.info(f"    {category}: {count}")
        
        if stats['chunk_types']:
            logger.info(f"  Chunk types created:")
            for chunk_type, count in stats['chunk_types'].items():
                logger.info(f"    {chunk_type}: {count}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        return self.statistics.copy()
    
    def get_tags_by_category(self, category: str) -> List[TagChunk]:
        """Get all tags of a specific device category"""
        return [chunk for chunk in self.tag_chunks 
                if chunk.device_info.device_category.lower() == category.lower()]
    
    def get_tags_by_chunk_type(self, chunk_type: TagChunkType) -> List[TagChunk]:
        """Get all tags of a specific chunk type"""
        return [chunk for chunk in self.tag_chunks if chunk.chunk_type == chunk_type]
    
    def get_tags_by_module(self, rack: int, slot: int) -> List[TagChunk]:
        """Get all tags for a specific module (rack/slot)"""
        return [chunk for chunk in self.tag_chunks
                if (chunk.device_info.rack == rack and 
                    chunk.device_info.slot == slot)]
    
    def get_safety_tags(self) -> List[TagChunk]:
        """Get all safety-related tags"""
        return [chunk for chunk in self.tag_chunks if chunk.is_safety_tag]
    
    def get_motor_control_tags(self) -> List[TagChunk]:
        """Get all motor control tags"""
        return [chunk for chunk in self.tag_chunks if chunk.is_motor_control]
    
    def get_sensor_tags(self) -> List[TagChunk]:
        """Get all sensor tags"""
        return [chunk for chunk in self.tag_chunks if chunk.is_sensor]
    
    def search_tags_by_text(self, search_text: str) -> List[TagChunk]:
        """Simple text-based search through tags (fallback for vector search)"""
        
        search_lower = search_text.lower()
        matches = []
        
        for chunk in self.tag_chunks:
            # Search in tag name, description, and function
            searchable_content = f"{chunk.tag_name} {chunk.description} {chunk.function}".lower()
            
            if search_lower in searchable_content:
                matches.append(chunk)
        
        return matches
    
    def analyze_i_o_usage(self) -> Dict[str, Any]:
        """Analyze I/O usage across the system"""
        
        analysis = {
            'total_tags': len(self.tag_chunks),
            'by_device_category': {},
            'by_chunk_type': {},
            'by_rack_slot': {},
            'safety_tags': 0,
            'motor_tags': 0,
            'sensor_tags': 0
        }
        
        rack_slot_usage = {}
        
        for chunk in self.tag_chunks:
            # Device category analysis
            category = chunk.device_info.device_category
            if category:
                analysis['by_device_category'][category] = (
                    analysis['by_device_category'].get(category, 0) + 1
                )
            
            # Chunk type analysis
            chunk_type = chunk.chunk_type.value
            analysis['by_chunk_type'][chunk_type] = (
                analysis['by_chunk_type'].get(chunk_type, 0) + 1
            )
            
            # Rack/slot analysis
            if chunk.device_info.rack is not None and chunk.device_info.slot is not None:
                rack_slot_key = f"Rack{chunk.device_info.rack}_Slot{chunk.device_info.slot}"
                if rack_slot_key not in rack_slot_usage:
                    rack_slot_usage[rack_slot_key] = {
                        'count': 0,
                        'module_type': chunk.device_info.module_type,
                        'device_category': chunk.device_info.device_category
                    }
                rack_slot_usage[rack_slot_key]['count'] += 1
            
            # Special category counts
            if chunk.is_safety_tag:
                analysis['safety_tags'] += 1
            if chunk.is_motor_control:
                analysis['motor_tags'] += 1
            if chunk.is_sensor:
                analysis['sensor_tags'] += 1
        
        analysis['by_rack_slot'] = rack_slot_usage
        
        return analysis
