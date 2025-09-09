#!/usr/bin/env python3
"""
PDF Drawings MCP Integration

Integrates the PDF Drawings Vector Database with the MCP server,
providing tools for semantic search and equipment context retrieval from technical drawings.

Follows the exact same patterns as L5X, SDK, and Tag MCP integrations.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

from .pdf_vector_db import PDFVectorDatabase, PDFSearchResult
from .pdf_chunk import PDFChunkType

logger = logging.getLogger(__name__)

class PDFMCPTools(Enum):
    """Enumeration of available PDF drawings MCP tools"""
    INDEX_PDF_DRAWINGS = "index_pdf_drawings"
    SEARCH_DRAWINGS = "search_drawings"
    FIND_EQUIPMENT_CONTEXT = "find_equipment_context"
    GET_DRAWING_DETAILS = "get_drawing_details"
    ANALYZE_CONTROL_LOGIC = "analyze_control_logic"
    FIND_SAFETY_INTERLOCKS = "find_safety_interlocks"
    GET_EQUIPMENT_CONNECTIONS = "get_equipment_connections"

class PDFMCPIntegration:
    """
    MCP integration for PDF technical drawings analysis tools
    following the exact same pattern as L5X/SDK/Tag integrations
    """
    
    def __init__(self, vector_db: PDFVectorDatabase = None):
        self.vector_db = vector_db or PDFVectorDatabase()
        self.initialized = False
        
    async def initialize(self, pdf_file_path: str = None, force_rebuild: bool = False):
        """Initialize the PDF drawings database"""
        try:
            logger.info("Initializing PDF drawings MCP integration...")
            
            # First, try to load any existing cache (following L5X pattern)
            if not force_rebuild:
                try:
                    logger.info("Attempting to load existing PDF cache...")
                    self.vector_db._load_from_cache()
                    if self.vector_db.chunks_data:
                        self.initialized = True
                        logger.info(f"PDF drawings database loaded from cache with {len(self.vector_db.chunks_data)} chunks")
                        return  # Cache loaded successfully, no need to reindex
                except Exception as e:
                    logger.info(f"No existing cache found or cache invalid: {e}")
            
            # If no cache or force_rebuild, index new PDF file
            if pdf_file_path and Path(pdf_file_path).exists():
                logger.info(f"Indexing PDF file: {pdf_file_path}")
                success = self.vector_db.index_pdf_file(pdf_file_path, force_rebuild=force_rebuild)
                if success:
                    self.initialized = True
                    logger.info("PDF drawings database initialized successfully")
                else:
                    logger.warning("PDF indexing failed")
            else:
                logger.warning("No PDF file provided and no cache available")
                    
        except Exception as e:
            logger.error(f"Failed to initialize PDF drawings database: {e}")
            self.initialized = False
    
    async def index_pdf_drawings(self, pdf_file_path: str, force_rebuild: bool = False, 
                               use_vision_ai: bool = False, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        MCP Tool: Index PDF technical drawings file
        
        Args:
            pdf_file_path: Path to PDF file containing technical drawings
            force_rebuild: Force re-indexing even if cached
            use_vision_ai: Enable advanced vision AI analysis (future feature)
            max_pages: Limit processing to first N pages (for testing)
        """
        try:
            if not Path(pdf_file_path).exists():
                return {
                    "success": False,
                    "error": f"PDF file not found: {pdf_file_path}",
                    "pages_indexed": 0,
                    "chunks_created": 0
                }
            
            logger.info(f"Indexing PDF drawings: {pdf_file_path}")
            success = self.vector_db.index_pdf_file(
                pdf_file_path, 
                force_rebuild=force_rebuild,
                use_vision_ai=use_vision_ai,
                max_pages=max_pages
            )
            
            if success:
                self.initialized = True
                return {
                    "success": True,
                    "message": "PDF drawings indexed successfully",
                    "total_chunks": len(self.vector_db.chunks_data),
                    "indexed_files": len(self.vector_db.indexed_files),
                    "cache_location": str(self.vector_db.cache_dir)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to index PDF drawings",
                    "total_chunks": 0
                }
                
        except Exception as e:
            logger.error(f"PDF indexing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_chunks": 0
            }
    
    async def search_drawings(self, query: str, limit: int = 10, score_threshold: float = 0.3,
                            drawing_type_filter: Optional[str] = None, 
                            equipment_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        MCP Tool: Search technical drawings using semantic similarity
        
        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0.0 to 1.0)
            drawing_type_filter: Filter by drawing type (electrical, pid, layout, etc.)
            equipment_filter: Filter by equipment tag
        """
        try:
            if not self.initialized:
                return {
                    "success": False,
                    "error": "PDF drawings database not initialized",
                    "results": []
                }
            
            # Convert string filter to enum if provided
            type_filter = None
            if drawing_type_filter:
                try:
                    type_filter = PDFChunkType(drawing_type_filter.lower())
                except ValueError:
                    logger.warning(f"Invalid drawing type filter: {drawing_type_filter}")
            
            results = self.vector_db.search_drawings(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                drawing_type_filter=type_filter,
                equipment_filter=equipment_filter
            )
            
            # Convert results to serializable format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "chunk_id": result.chunk_id,
                    "drawing_type": result.chunk_type.value,
                    "page_number": result.page_number,
                    "drawing_number": result.drawing_number,
                    "title": result.title,
                    "description": result.description,
                    "relevance_score": round(result.score, 3),
                    "equipment_tags": result.equipment_tags,
                    "content_preview": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "file_path": result.file_path
                })
            
            return {
                "success": True,
                "query": query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "search_parameters": {
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "drawing_type_filter": drawing_type_filter,
                    "equipment_filter": equipment_filter
                }
            }
            
        except Exception as e:
            logger.error(f"Drawings search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def find_equipment_context(self, equipment_tag: str, context_type: Optional[str] = None) -> Dict[str, Any]:
        """
        MCP Tool: Find all drawings and context related to specific equipment
        
        Args:
            equipment_tag: Equipment identifier (e.g., "MCM01", "PDP01", "M001")
            context_type: Type of context (electrical, process, safety, control)
        """
        try:
            if not self.initialized:
                return {
                    "success": False,
                    "error": "PDF drawings database not initialized",
                    "contexts": []
                }
            
            results = self.vector_db.find_equipment_context(equipment_tag, context_type)
            
            # Group results by drawing type for better organization
            context_by_type = {}
            for result in results:
                drawing_type = result.chunk_type.value
                if drawing_type not in context_by_type:
                    context_by_type[drawing_type] = []
                
                context_by_type[drawing_type].append({
                    "page_number": result.page_number,
                    "drawing_number": result.drawing_number,
                    "title": result.title,
                    "relevance_score": round(result.score, 3),
                    "equipment_tags": result.equipment_tags,
                    "content_preview": result.content[:150] + "..." if len(result.content) > 150 else result.content
                })
            
            return {
                "success": True,
                "equipment_tag": equipment_tag,
                "context_type": context_type,
                "total_contexts": len(results),
                "contexts_by_type": context_by_type,
                "related_equipment": list(set([tag for result in results for tag in result.equipment_tags if tag != equipment_tag.upper()]))
            }
            
        except Exception as e:
            logger.error(f"Equipment context search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "contexts": []
            }
    
    async def get_drawing_details(self, drawing_number: Optional[str] = None, 
                                page_number: Optional[int] = None) -> Dict[str, Any]:
        """
        MCP Tool: Get detailed information about a specific drawing
        
        Args:
            drawing_number: Drawing reference number
            page_number: Page number to retrieve details for
        """
        try:
            if not self.initialized:
                return {
                    "success": False,
                    "error": "PDF drawings database not initialized",
                    "drawing_details": {}
                }
            
            if not drawing_number and not page_number:
                return {
                    "success": False,
                    "error": "Either drawing_number or page_number must be provided",
                    "drawing_details": {}
                }
            
            results = self.vector_db.get_drawing_details(drawing_number, page_number)
            
            if not results:
                return {
                    "success": False,
                    "error": f"No drawing found for number='{drawing_number}' page='{page_number}'",
                    "drawing_details": {}
                }
            
            # Use the first result as main drawing details
            main_result = results[0]
            
            return {
                "success": True,
                "drawing_details": {
                    "drawing_number": main_result.drawing_number,
                    "title": main_result.title,
                    "page_number": main_result.page_number,
                    "drawing_type": main_result.chunk_type.value,
                    "equipment_tags": main_result.equipment_tags,
                    "content": main_result.content,
                    "file_path": main_result.file_path
                },
                "related_pages": len(results) if len(results) > 1 else 0,
                "all_equipment_on_drawing": list(set([tag for result in results for tag in result.equipment_tags]))
            }
            
        except Exception as e:
            logger.error(f"Drawing details error: {e}")
            return {
                "success": False,
                "error": str(e),
                "drawing_details": {}
            }
    
    async def get_equipment_connections(self, equipment_tag: str) -> Dict[str, Any]:
        """
        MCP Tool: Get electrical connections and wiring info for equipment
        
        Args:
            equipment_tag: Equipment identifier to find connections for
        """
        try:
            # Search specifically for electrical connections
            electrical_query = f"{equipment_tag} electrical connections wiring motor control power"
            electrical_results = self.vector_db.search_drawings(
                electrical_query, 
                limit=10, 
                drawing_type_filter=PDFChunkType.ELECTRICAL
            )
            
            # Search for I/O and control connections
            control_query = f"{equipment_tag} input output control signal plc"
            control_results = self.vector_db.search_drawings(
                control_query,
                limit=10,
                drawing_type_filter=PDFChunkType.CONTROL_LOGIC
            )
            
            # Combine and format results
            all_connections = []
            
            for result in electrical_results + control_results:
                all_connections.append({
                    "connection_type": "electrical" if result.chunk_type == PDFChunkType.ELECTRICAL else "control",
                    "page_number": result.page_number,
                    "drawing_number": result.drawing_number,
                    "relevance_score": round(result.score, 3),
                    "description": result.description,
                    "related_equipment": [tag for tag in result.equipment_tags if tag != equipment_tag.upper()]
                })
            
            return {
                "success": True,
                "equipment_tag": equipment_tag,
                "total_connections": len(all_connections),
                "connections": all_connections,
                "search_queries_used": [electrical_query, control_query]
            }
            
        except Exception as e:
            logger.error(f"Equipment connections error: {e}")
            return {
                "success": False,
                "error": str(e),
                "connections": []
            }
    
    # Tool registration mapping (following existing pattern)
    def get_available_tools(self) -> Dict[str, Any]:
        """Return available MCP tools for registration"""
        return {
            PDFMCPTools.INDEX_PDF_DRAWINGS.value: {
                "description": "Index PDF technical drawings file for semantic search",
                "parameters": {
                    "pdf_file_path": {"type": "string", "description": "Path to PDF file"},
                    "force_rebuild": {"type": "boolean", "description": "Force re-indexing", "default": False},
                    "use_vision_ai": {"type": "boolean", "description": "Enable vision AI analysis", "default": False},
                    "max_pages": {"type": "integer", "description": "Limit pages (for testing)", "default": None}
                }
            },
            PDFMCPTools.SEARCH_DRAWINGS.value: {
                "description": "Search technical drawings using natural language",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                    "score_threshold": {"type": "number", "description": "Min relevance score", "default": 0.3},
                    "drawing_type_filter": {"type": "string", "description": "Filter by type", "default": None},
                    "equipment_filter": {"type": "string", "description": "Filter by equipment", "default": None}
                }
            },
            PDFMCPTools.FIND_EQUIPMENT_CONTEXT.value: {
                "description": "Find all drawings referencing specific equipment",
                "parameters": {
                    "equipment_tag": {"type": "string", "description": "Equipment identifier"},
                    "context_type": {"type": "string", "description": "Context type", "default": None}
                }
            },
            PDFMCPTools.GET_DRAWING_DETAILS.value: {
                "description": "Get detailed information about a specific drawing",
                "parameters": {
                    "drawing_number": {"type": "string", "description": "Drawing number", "default": None},
                    "page_number": {"type": "integer", "description": "Page number", "default": None}
                }
            },
            PDFMCPTools.GET_EQUIPMENT_CONNECTIONS.value: {
                "description": "Get electrical connections and wiring info for equipment",
                "parameters": {
                    "equipment_tag": {"type": "string", "description": "Equipment identifier"}
                }
            }
        }
