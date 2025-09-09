#!/usr/bin/env python3
"""
Tag MCP Integration

Integrates the Tag Vector Database with the MCP server, providing tools for semantic search
and analysis of Studio 5000 tag CSV exports.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

from .tag_vector_db import TagVectorDatabase, TagSearchResult
from .csv_tag_parser import CSVTagParser
from .tag_chunk import TagChunk, TagChunkType

logger = logging.getLogger(__name__)

class TagMCPTools(Enum):
    """Enumeration of available tag analysis MCP tools"""
    INDEX_TAG_CSV = "index_tag_csv"
    SEARCH_TAGS = "search_tags"
    FIND_DEVICE = "find_device"
    GET_MODULE_TAGS = "get_module_tags"
    FIND_I_O_POINT = "find_i_o_point"
    ANALYZE_I_O_USAGE = "analyze_i_o_usage"
    FIND_RELATED_TAGS = "find_related_tags"
    GET_DEVICE_OVERVIEW = "get_device_overview"
    GET_SAFETY_TAGS = "get_safety_tags"
    GET_MOTOR_TAGS = "get_motor_tags"
    GET_SENSOR_TAGS = "get_sensor_tags"

class TagMCPIntegration:
    """
    MCP integration for tag analysis tools enabling semantic search
    through Studio 5000 tag CSV exports
    """
    
    def __init__(self, vector_db: TagVectorDatabase = None):
        self.vector_db = vector_db or TagVectorDatabase()
        self.parser = CSVTagParser()
        self.initialized = False
        
        # Index status
        self.indexed_files = {}
    
    async def initialize(self, force_rebuild: bool = False):
        """Initialize the tag analysis system"""
        if self.initialized and not force_rebuild:
            return
        
        try:
            logger.info("Initializing tag MCP integration...")
            
            # Load any cached vector database
            if not force_rebuild:
                self.vector_db._load_from_cache()
            
            self.initialized = True
            logger.info("Tag MCP integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize tag MCP integration: {e}")
            raise
    
    async def index_tag_csv(self, csv_path: str, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Index Studio 5000 tag CSV export for semantic search
        
        Args:
            csv_path: Path to CSV file exported from Studio 5000
            force_rebuild: Force rebuild even if cached
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info(f"Starting indexing of tag CSV: {csv_path}")
            
            if not Path(csv_path).exists():
                return {
                    'success': False,
                    'error': f'CSV file not found: {csv_path}'
                }
            
            # Parse the CSV file
            tag_chunks = self.parser.parse_tag_csv(csv_path)
            
            if not tag_chunks:
                return {
                    'success': False,
                    'error': 'No tags found in CSV file'
                }
            
            # Build vector database
            self.vector_db.build_tag_database(tag_chunks, force_rebuild)
            
            # Get statistics
            stats = self.parser.get_statistics()
            file_name = Path(csv_path).name
            
            # Update indexed files status
            self.indexed_files[file_name] = {
                'path': csv_path,
                'indexed_at': asyncio.get_event_loop().time(),
                'tag_count': len(tag_chunks),
                'statistics': stats
            }
            
            return {
                'success': True,
                'file_name': file_name,
                'tags_indexed': len(tag_chunks),
                'statistics': stats,
                'message': f'Successfully indexed {len(tag_chunks)} tags from {file_name}'
            }
            
        except Exception as e:
            logger.error(f"Error indexing tag CSV {csv_path}: {e}")
            return {
                'success': False,
                'error': f'Indexing failed: {str(e)}'
            }
    
    async def search_tags(self, query: str, category_filter: str = None,
                         chunk_type_filter: str = None, limit: int = 20) -> Dict[str, Any]:
        """
        Semantic search within tag database
        
        Args:
            query: Search query
            category_filter: Filter by device category (VFD, Safety, DI, DO, etc.)
            chunk_type_filter: Filter by chunk type
            limit: Maximum results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Convert chunk_type_filter string to enum if provided
            chunk_type_enum = None
            if chunk_type_filter:
                try:
                    chunk_type_enum = TagChunkType(chunk_type_filter.lower())
                except ValueError:
                    return {
                        'success': False,
                        'error': f'Invalid chunk type: {chunk_type_filter}'
                    }
            
            # Perform search
            results = self.vector_db.search_tags(
                query, limit, 
                category_filter=category_filter,
                chunk_type_filter=chunk_type_enum
            )
            
            # Convert results to serializable format
            search_results = []
            for result in results:
                search_results.append({
                    'tag_name': result.tag_name,
                    'type': result.chunk_type.value,
                    'description': result.description,
                    'function': result.function,
                    'category': result.category,
                    'score': result.score,
                    'device_info': {
                        'module_type': result.device_info.module_type,
                        'rack': result.device_info.rack,
                        'slot': result.device_info.slot,
                        'channel': result.device_info.channel,
                        'local_address': result.device_info.local_address,
                        'device_category': result.device_info.device_category,
                        'connection_type': result.device_info.connection_type
                    },
                    'i_o_address': result.i_o_address,
                    'related_tags': result.related_tags[:5],  # Limit for JSON size
                    'metadata': {k: v for k, v in result.metadata.items() 
                               if isinstance(v, (str, int, float, bool))}
                })
            
            return {
                'success': True,
                'query': query,
                'results_count': len(search_results),
                'results': search_results,
                'filters_applied': {
                    'category': category_filter,
                    'chunk_type': chunk_type_filter
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching tags: {e}")
            return {
                'success': False,
                'error': f'Search failed: {str(e)}'
            }
    
    async def find_device(self, device_description: str, device_type: str = None) -> Dict[str, Any]:
        """
        Find specific devices by description or function
        
        Args:
            device_description: Description of device to find
            device_type: Optional device type filter
            
        Returns:
            Dictionary with matching devices
        """
        try:
            results = self.vector_db.find_device_by_description(device_description, device_type)
            
            devices = []
            for result in results:
                devices.append({
                    'tag_name': result.tag_name,
                    'description': result.description,
                    'function': result.function,
                    'score': result.score,
                    'location': {
                        'rack': result.device_info.rack,
                        'slot': result.device_info.slot,
                        'module_type': result.device_info.module_type
                    },
                    'i_o_address': result.i_o_address,
                    'related_tags': result.related_tags[:3]
                })
            
            return {
                'success': True,
                'device_description': device_description,
                'device_type': device_type,
                'devices_found': len(devices),
                'devices': devices
            }
            
        except Exception as e:
            logger.error(f"Error finding device: {e}")
            return {
                'success': False,
                'error': f'Device search failed: {str(e)}'
            }
    
    async def get_module_tags(self, rack: int, slot: int) -> Dict[str, Any]:
        """
        Get all tags for a specific module (rack/slot)
        
        Args:
            rack: Rack number
            slot: Slot number
            
        Returns:
            Dictionary with module tags
        """
        try:
            results = self.vector_db.get_tags_by_module(rack, slot)
            
            module_tags = []
            module_info = None
            
            for result in results:
                tag_info = {
                    'tag_name': result.tag_name,
                    'description': result.description,
                    'function': result.function,
                    'category': result.category,
                    'i_o_address': result.i_o_address,
                    'connection_type': result.device_info.connection_type
                }
                module_tags.append(tag_info)
                
                # Capture module info from first result
                if module_info is None:
                    module_info = {
                        'rack': rack,
                        'slot': slot,
                        'module_type': result.device_info.module_type,
                        'device_category': result.device_info.device_category
                    }
            
            return {
                'success': True,
                'module_info': module_info,
                'tag_count': len(module_tags),
                'tags': module_tags
            }
            
        except Exception as e:
            logger.error(f"Error getting module tags: {e}")
            return {
                'success': False,
                'error': f'Module query failed: {str(e)}'
            }
    
    async def find_i_o_point(self, address_pattern: str = None, description: str = None) -> Dict[str, Any]:
        """
        Find specific I/O points by address or description
        
        Args:
            address_pattern: I/O address pattern to search for
            description: Description to search for
            
        Returns:
            Dictionary with matching I/O points
        """
        try:
            results = self.vector_db.find_i_o_point(address_pattern, description)
            
            i_o_points = []
            for result in results:
                i_o_points.append({
                    'tag_name': result.tag_name,
                    'description': result.description,
                    'function': result.function,
                    'i_o_address': result.i_o_address,
                    'location': {
                        'rack': result.device_info.rack,
                        'slot': result.device_info.slot,
                        'channel': result.device_info.channel
                    },
                    'device_info': {
                        'module_type': result.device_info.module_type,
                        'device_category': result.device_info.device_category,
                        'connection_type': result.device_info.connection_type
                    }
                })
            
            return {
                'success': True,
                'search_criteria': {
                    'address_pattern': address_pattern,
                    'description': description
                },
                'points_found': len(i_o_points),
                'i_o_points': i_o_points
            }
            
        except Exception as e:
            logger.error(f"Error finding I/O point: {e}")
            return {
                'success': False,
                'error': f'I/O point search failed: {str(e)}'
            }
    
    async def analyze_i_o_usage(self) -> Dict[str, Any]:
        """
        Analyze I/O usage and capacity across the system
        
        Returns:
            Dictionary with I/O usage analysis
        """
        try:
            analysis = self.vector_db.analyze_i_o_usage()
            
            return {
                'success': True,
                'analysis': analysis,
                'summary': {
                    'total_tags': analysis['total_tags'],
                    'safety_tags': analysis['safety_analysis']['total_safety_tags'],
                    'motor_tags': analysis['motor_analysis']['total_motor_tags'],
                    'sensor_tags': analysis['sensor_analysis']['total_sensor_tags'],
                    'modules_in_use': len(analysis['module_utilization']),
                    'device_categories': len(analysis['by_device_category'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing I/O usage: {e}")
            return {
                'success': False,
                'error': f'I/O analysis failed: {str(e)}'
            }
    
    async def find_related_tags(self, tag_name: str, relationship_type: str = "all") -> Dict[str, Any]:
        """
        Find tags related to a given tag
        
        Args:
            tag_name: Tag name to find relationships for
            relationship_type: Type of relationship ('all', 'functional', 'physical')
            
        Returns:
            Dictionary with related tags
        """
        try:
            results = self.vector_db.find_related_tags(tag_name, relationship_type)
            
            related_tags = []
            for result in results:
                related_tags.append({
                    'tag_name': result.tag_name,
                    'description': result.description,
                    'function': result.function,
                    'relationship_score': result.score,
                    'location': {
                        'rack': result.device_info.rack,
                        'slot': result.device_info.slot
                    },
                    'device_category': result.device_info.device_category
                })
            
            return {
                'success': True,
                'source_tag': tag_name,
                'relationship_type': relationship_type,
                'related_count': len(related_tags),
                'related_tags': related_tags
            }
            
        except Exception as e:
            logger.error(f"Error finding related tags: {e}")
            return {
                'success': False,
                'error': f'Related tags search failed: {str(e)}'
            }
    
    async def get_device_overview(self, category_filter: str = None) -> Dict[str, Any]:
        """
        Get comprehensive overview of devices in the system
        
        Args:
            category_filter: Optional category filter
            
        Returns:
            Dictionary with device overview
        """
        try:
            overview = self.vector_db.get_device_overview(category_filter)
            
            return {
                'success': True,
                'category_filter': category_filter,
                'overview': overview
            }
            
        except Exception as e:
            logger.error(f"Error getting device overview: {e}")
            return {
                'success': False,
                'error': f'Device overview failed: {str(e)}'
            }
    
    async def get_safety_tags(self) -> Dict[str, Any]:
        """Get all safety-related tags"""
        return await self.search_tags("safety emergency estop", chunk_type_filter="safety_tag", limit=50)
    
    async def get_motor_tags(self) -> Dict[str, Any]:
        """Get all motor control tags"""
        return await self.search_tags("motor drive vfd conveyor", chunk_type_filter="motor_tag", limit=50)
    
    async def get_sensor_tags(self) -> Dict[str, Any]:
        """Get all sensor tags"""
        return await self.search_tags("sensor photoeye proximity switch", chunk_type_filter="sensor_tag", limit=50)
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available MCP tools"""
        return {
            tool.value: f"Tag analysis tool: {tool.value.replace('_', ' ').title()}"
            for tool in TagMCPTools
        }
    
    def get_indexing_status(self) -> Dict[str, Any]:
        """Get status of indexed files"""
        return {
            'indexed_files': self.indexed_files,
            'total_files': len(self.indexed_files),
            'system_ready': len(self.indexed_files) > 0
        }
