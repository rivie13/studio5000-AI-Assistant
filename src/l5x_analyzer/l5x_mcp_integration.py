#!/usr/bin/env python3
"""
L5X MCP Integration

Integrates the L5X Vector Database and SDK-powered analyzer with the MCP server,
providing tools for semantic search and intelligent modification of large L5X files.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

from .l5x_vector_db import L5XVectorDatabase, L5XSearchResult
from .sdk_powered_analyzer import SDKPoweredL5XAnalyzer
from .l5x_chunk import L5XChunkType

logger = logging.getLogger(__name__)

class L5XMCPTools(Enum):
    """Enumeration of available L5X analysis MCP tools"""
    INDEX_EXPORTED_L5X_FILES = "index_exported_l5x_files"  # NEW: Direct L5X file indexing
    INDEX_ACD_PROJECT = "index_acd_project"  # OLD: Disabled ACD indexing
    SEARCH_L5X_CONTENT = "search_l5x_content"
    FIND_INSERTION_POINT = "find_insertion_point"
    SMART_INSERT_LOGIC = "smart_insert_logic"
    EXTRACT_ROUTINE_CONTENT = "extract_routine_content"
    ANALYZE_ROUTINE_STRUCTURE = "analyze_routine_structure"
    FIND_RELATED_COMPONENTS = "find_related_components"
    GET_PROJECT_OVERVIEW = "get_project_overview"
    BATCH_ROUTINE_ANALYSIS = "batch_routine_analysis"

class L5XSDKMCPIntegration:
    """
    MCP integration for L5X analysis tools combining vector database 
    with SDK-powered operations for production-scale L5X files
    """
    
    def __init__(self, vector_db: L5XVectorDatabase = None):
        self.vector_db = vector_db or L5XVectorDatabase()
        self.sdk_analyzer = SDKPoweredL5XAnalyzer()
        self.initialized = False
        
        # Import AI assistant for logic generation
        self._code_assistant = None
    
    def _get_code_assistant(self):
        """Lazy load code assistant to avoid circular imports"""
        if self._code_assistant is None:
            try:
                from ..ai_assistant.code_assistant import CodeAssistant
                self._code_assistant = CodeAssistant()
            except ImportError:
                logger.warning("Code assistant not available - logic generation disabled")
        return self._code_assistant
    
    async def initialize(self, force_rebuild: bool = False):
        """Initialize the L5X analysis system"""
        if self.initialized and not force_rebuild:
            return
        
        try:
            logger.info("Initializing L5X SDK MCP integration...")
            
            # Load any cached vector database
            if not force_rebuild:
                self.vector_db._load_from_cache()
            
            self.initialized = True
            logger.info("L5X SDK MCP integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize L5X MCP integration: {e}")
            raise
    
    def index_exported_l5x_files(self, l5x_directory: str, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Index EXPORTED L5X files directly (no ACD/SDK opening needed)
        
        Args:
            l5x_directory: Directory containing exported L5X files
            force_rebuild: Force rebuild even if cached
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info(f"Indexing exported L5X files from: {l5x_directory}")
            
            if not Path(l5x_directory).exists():
                return {
                    'success': False,
                    'error': f'L5X directory not found: {l5x_directory}'
                }
            
            # Index the exported L5X files directly
            success = self.vector_db.index_exported_l5x_files(l5x_directory, force_rebuild)
            
            if success:
                # Get indexing statistics
                project_name = Path(l5x_directory).name
                stats = self.vector_db.indexed_projects.get(project_name, {})
                
                return {
                    'success': True,
                    'project_name': project_name,
                    'files_indexed': stats.get('file_count', 0),
                    'chunks_created': stats.get('chunk_count', 0),
                    'message': f'✅ Successfully indexed exported L5X files from {project_name}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to index L5X files - check logs for details'
                }
                
        except Exception as e:
            logger.error(f"Error indexing L5X files from {l5x_directory}: {e}")
            return {
                'success': False,
                'error': f'Exception during L5X indexing: {str(e)}'
            }

    async def index_acd_project(self, acd_path: str, routines_to_index: List[str] = None,
                              force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Index ACD/L5K project for semantic search
        
        Args:
            acd_path: Path to ACD or L5K file
            routines_to_index: Specific routines to index (None for all)
            force_rebuild: Force rebuild even if cached
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info(f"Starting indexing of project: {acd_path}")
            
            if not Path(acd_path).exists():
                return {
                    'success': False,
                    'error': f'Project file not found: {acd_path}'
                }
            
            # Index the project
            success = await self.vector_db.index_acd_project(
                acd_path, routines_to_index, force_rebuild
            )
            
            if success:
                # Get indexing statistics
                project_name = Path(acd_path).stem
                stats = self.vector_db.indexed_projects.get(project_name, {})
                
                return {
                    'success': True,
                    'project_name': project_name,
                    'routines_indexed': stats.get('routine_count', 0),
                    'chunks_created': stats.get('chunk_count', 0),
                    'message': f'Successfully indexed {project_name}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to index project - check logs for details'
                }
                
        except Exception as e:
            logger.error(f"Error indexing project {acd_path}: {e}")
            return {
                'success': False,
                'error': f'Exception during indexing: {str(e)}'
            }
    
    async def search_l5x_content(self, query: str, file_filter: str = None,
                               component_type: str = None, limit: int = 20) -> Dict[str, Any]:
        """
        Semantic search within indexed L5X content
        
        Args:
            query: Search query
            file_filter: Filter by project file name
            component_type: Filter by component type (routine, rung, udt, etc.)
            limit: Maximum results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Convert component_type string to enum if provided
            chunk_types = None
            if component_type:
                try:
                    chunk_types = [L5XChunkType(component_type.lower())]
                except ValueError:
                    return {
                        'success': False,
                        'error': f'Invalid component type: {component_type}'
                    }
            
            # Perform search with lower threshold for broader results
            results = self.vector_db.search_l5x_content(
                query, limit, score_threshold=0.05, chunk_types=chunk_types
            )
            
            # Filter by file if requested
            if file_filter:
                results = [r for r in results if file_filter.lower() in r.file_path.lower()]
            
            # Convert results to serializable format
            search_results = []
            for result in results:
                search_results.append({
                    'chunk_id': result.chunk_id,
                    'type': result.chunk_type.value,
                    'name': result.name,
                    'description': result.description,
                    'score': result.score,
                    'content_preview': result.content[:200] + '...' if len(result.content) > 200 else result.content,
                    'location': {
                        'file_path': result.location.file_path,
                        'xpath': result.location.xpath,
                        'routine': result.location.parent_routine,
                        'program': result.location.parent_program,
                        'rung_number': result.location.rung_number
                    },
                    'insertion_hints': result.insertion_hints
                })
            
            return {
                'success': True,
                'query': query,
                'results_count': len(search_results),
                'results': search_results
            }
            
        except Exception as e:
            logger.error(f"Error searching L5X content: {e}")
            return {
                'success': False,
                'error': f'Search failed: {str(e)}'
            }
    
    async def find_insertion_point(self, new_logic_description: str, target_routine: str,
                                 target_file: str = None) -> Dict[str, Any]:
        """
        Find optimal location to insert new ladder logic
        
        Args:
            new_logic_description: Description of logic to insert
            target_routine: Target routine name
            target_file: Optional target file filter
            
        Returns:
            Dictionary with insertion recommendations
        """
        try:
            # Find optimal insertion point
            position, confidence = self.vector_db.find_optimal_insertion_point(
                new_logic_description, target_routine
            )
            
            # Get related context
            context_search = f"similar to {new_logic_description} in {target_routine}"
            context_results = self.vector_db.search_l5x_content(
                context_search, limit=3, 
                chunk_types=[L5XChunkType.LADDER_RUNG]
            )
            
            # Get routine analysis
            routine_analysis = self.vector_db.get_routine_analysis(target_routine)
            
            return {
                'success': True,
                'recommended_position': position,
                'confidence_score': confidence,
                'target_routine': target_routine,
                'reasoning': f'Insert at rung {position} based on semantic similarity analysis',
                'context_rungs': [
                    {
                        'rung_number': r.location.rung_number,
                        'description': r.description,
                        'similarity_score': r.score
                    }
                    for r in context_results if r.location.parent_routine == target_routine
                ],
                'routine_info': routine_analysis
            }
            
        except Exception as e:
            logger.error(f"Error finding insertion point: {e}")
            return {
                'success': False,
                'error': f'Failed to find insertion point: {str(e)}'
            }
    
    async def smart_insert_logic(self, acd_path: str, routine_name: str, 
                               logic_description: str, program_name: str = "MainProgram",
                               insertion_mode: str = "optimal") -> Dict[str, Any]:
        """
        Generate ladder logic and provide insertion recommendations (analysis only - no file modification)
        
        Args:
            acd_path: Path to ACD/L5K file (for context only)
            routine_name: Target routine name
            logic_description: Description of logic to generate
            program_name: Parent program name
            insertion_mode: 'optimal' or 'end'
            
        Returns:
            Dictionary with logic generation and insertion recommendations
        """
        try:
            logger.info(f"Generating logic analysis for {routine_name}: {logic_description}")
            
            # Find optimal insertion point if requested
            insertion_point = 0
            confidence = 0.0
            
            if insertion_mode == "optimal":
                try:
                    insertion_point, confidence = self.vector_db.find_optimal_insertion_point(
                        logic_description, routine_name
                    )
                except Exception as e:
                    logger.warning(f"Could not find optimal insertion point: {e}")
                    insertion_point = 1  # Default to first rung
                    confidence = 0.0
            else:
                # Insert at end - get routine analysis to find last rung
                try:
                    routine_analysis = self.vector_db.get_routine_analysis(routine_name)
                    if 'rung_range' in routine_analysis and routine_analysis['rung_range'][1] > 0:
                        insertion_point = routine_analysis['rung_range'][1] + 1
                    else:
                        insertion_point = 1
                except Exception as e:
                    logger.warning(f"Could not analyze routine structure: {e}")
                    insertion_point = 1
            
            # Generate ladder logic using AI assistant
            code_assistant = self._get_code_assistant()
            if not code_assistant:
                return {
                    'success': False,
                    'error': 'Code generation not available - AI assistant not loaded'
                }
            
            generated_logic = code_assistant.generate_ladder_logic(logic_description)
            if not generated_logic or 'ladder_logic' not in generated_logic:
                return {
                    'success': False,
                    'error': 'Failed to generate ladder logic - check logic description'
                }
            
            # Create L5X fragment with new logic (for reference)
            logic_text = generated_logic['ladder_logic']
            l5x_fragment = None
            try:
                l5x_fragment = self.sdk_analyzer.create_rung_l5x_fragment(
                    logic_text, f"Generated: {logic_description}"
                )
            except Exception as e:
                logger.warning(f"Could not create L5X fragment: {e}")
            
            # Return analysis results (no actual insertion performed)
            return {
                'success': True,
                'insertion_analysis': {
                    'recommended_position': insertion_point,
                    'confidence_score': confidence,
                    'insertion_mode': insertion_mode
                },
                'generated_content': {
                    'logic_text': logic_text,
                    'tags_referenced': generated_logic.get('tags', []),
                    'l5x_fragment': l5x_fragment if l5x_fragment else 'Could not generate L5X format'
                },
                'target_info': {
                    'routine_name': routine_name,
                    'program_name': program_name,
                    'description': logic_description
                },
                'message': f'✅ Logic generated successfully. Recommended insertion at rung {insertion_point} in {routine_name}',
                'note': 'This is analysis only - no files were modified. Use Studio 5000 to manually insert the generated logic.'
            }
                
        except Exception as e:
            logger.error(f"Error during smart logic generation: {e}")
            return {
                'success': False,
                'error': f'Logic generation failed: {str(e)}'
            }
    
    async def extract_routine_content(self, acd_path: str, routine_name: str,
                                    program_name: str = "MainProgram", 
                                    output_format: str = "summary") -> Dict[str, Any]:
        """
        Extract specific routine content for analysis using vector database
        
        Args:
            acd_path: Path to ACD/L5K file (for context, not opened)
            routine_name: Routine to extract
            program_name: Parent program name  
            output_format: 'summary', 'full', or 'rungs_only'
            
        Returns:
            Dictionary with extracted content
        """
        try:
            logger.info(f"Extracting routine content for {routine_name} using vector database")
            
            # Search for the specific routine in the vector database
            routine_query = f"routine {routine_name}"
            search_results = self.vector_db.search_l5x_content(
                routine_query, limit=50, 
                chunk_types=[L5XChunkType.ROUTINE, L5XChunkType.LADDER_RUNG]
            )
            
            # Filter results to exact routine match
            routine_chunks = []
            rung_chunks = []
            
            for result in search_results:
                # Check if this is the exact routine we want
                if (result.location.parent_routine == routine_name or 
                    result.name == routine_name):
                    
                    if result.chunk_type == L5XChunkType.ROUTINE:
                        routine_chunks.append(result)
                    elif result.chunk_type == L5XChunkType.LADDER_RUNG:
                        rung_chunks.append(result)
            
            if not routine_chunks and not rung_chunks:
                return {
                    'success': False,
                    'error': f'Routine {routine_name} not found in indexed content. Make sure L5X files are indexed first.'
                }
            
            # Sort rungs by rung number
            rung_chunks.sort(key=lambda x: x.location.rung_number or 0)
            
            # Format output based on requested format
            if output_format == "summary":
                return {
                    'success': True,
                    'routine_name': routine_name,
                    'program_name': program_name,
                    'rung_count': len(rung_chunks),
                    'description': routine_chunks[0].description if routine_chunks else 'No description available',
                    'dependencies': list(set().union(*[result.dependencies for result in routine_chunks + rung_chunks if hasattr(result, 'dependencies')])),
                    'complexity_info': {
                        'total_rungs': len(rung_chunks),
                        'has_routine_metadata': len(routine_chunks) > 0
                    },
                    'file_location': routine_chunks[0].location.file_path if routine_chunks else (rung_chunks[0].location.file_path if rung_chunks else 'Unknown')
                }
            
            elif output_format == "rungs_only":
                rungs = []
                
                for result in rung_chunks:
                    rungs.append({
                        'rung_number': result.location.rung_number,
                        'logic': result.content,
                        'comment': result.description,
                        'score': result.score,
                        'file_path': result.location.file_path
                    })
                
                return {
                    'success': True,
                    'routine_name': routine_name,
                    'rungs': rungs,
                    'total_rungs': len(rungs)
                }
            
            else:  # full
                all_chunks = routine_chunks + rung_chunks
                chunks_data = []
                
                for result in all_chunks:
                    chunks_data.append({
                        'id': result.chunk_id,
                        'type': result.chunk_type.value,
                        'name': result.name,
                        'content': result.content,
                        'description': result.description,
                        'score': result.score,
                        'location': {
                            'file_path': result.location.file_path,
                            'xpath': result.location.xpath,
                            'routine': result.location.parent_routine,
                            'program': result.location.parent_program,
                            'rung_number': result.location.rung_number
                        }
                    })
                
                return {
                    'success': True,
                    'routine_name': routine_name,
                    'chunks': chunks_data,
                    'total_chunks': len(chunks_data)
                }
                
        except Exception as e:
            logger.error(f"Error extracting routine content: {e}")
            return {
                'success': False,
                'error': f'Extraction failed: {str(e)}'
            }
    
    async def analyze_routine_structure(self, routine_name: str) -> Dict[str, Any]:
        """
        Analyze structure and complexity of an indexed routine
        
        Args:
            routine_name: Name of routine to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            analysis = self.vector_db.get_routine_analysis(routine_name)
            
            if 'error' in analysis:
                return {
                    'success': False,
                    'error': analysis['error']
                }
            
            return {
                'success': True,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing routine structure: {e}")
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    async def find_related_components(self, component_name: str, project_filter: str = None,
                                    relationship_type: str = "usage") -> Dict[str, Any]:
        """
        Find components related to a given component
        
        Args:
            component_name: Name of component to find relationships for
            project_filter: Optional project file filter
            relationship_type: Type of relationship ('usage', 'dependency', 'similar')
            
        Returns:
            Dictionary with related components
        """
        try:
            # Search for the component first
            component_results = self.vector_db.search_l5x_content(
                component_name, limit=5
            )
            
            if not component_results:
                return {
                    'success': False,
                    'error': f'Component {component_name} not found in indexed content'
                }
            
            # Get the best match
            primary_component = component_results[0]
            
            # Find related components
            related_results = self.vector_db.find_related_components(
                primary_component.chunk_id
            )
            
            # Filter by project if requested
            if project_filter:
                related_results = [r for r in related_results 
                                 if project_filter.lower() in r.file_path.lower()]
            
            # Format results
            related_components = []
            for result in related_results:
                related_components.append({
                    'name': result.name,
                    'type': result.chunk_type.value,
                    'description': result.description,
                    'score': result.score,
                    'location': {
                        'file_path': result.location.file_path,
                        'routine': result.location.parent_routine,
                        'program': result.location.parent_program
                    }
                })
            
            return {
                'success': True,
                'primary_component': {
                    'name': primary_component.name,
                    'type': primary_component.chunk_type.value,
                    'description': primary_component.description
                },
                'related_components': related_components,
                'relationship_type': relationship_type,
                'total_found': len(related_components)
            }
            
        except Exception as e:
            logger.error(f"Error finding related components: {e}")
            return {
                'success': False,
                'error': f'Search for related components failed: {str(e)}'
            }
    
    async def get_project_overview(self, acd_path: str) -> Dict[str, Any]:
        """
        Get project overview from indexed vector database content
        
        Args:
            acd_path: Path to ACD/L5K file (for context only)
            
        Returns:
            Dictionary with project overview from indexed data
        """
        try:
            logger.info(f"Getting project overview from vector database for {acd_path}")
            
            # Get overview from vector database indexed projects
            project_name = Path(acd_path).stem
            indexed_projects = self.vector_db.indexed_projects
            
            # Check if we have data for this project
            if project_name not in indexed_projects:
                # Try to find any indexed project data
                if not indexed_projects:
                    return {
                        'success': False,
                        'error': 'No L5X data indexed. Use index_exported_l5x_files first to analyze project structure.'
                    }
                
                # Use first available indexed project if exact match not found
                project_name = list(indexed_projects.keys())[0]
                logger.info(f"Using indexed project data from: {project_name}")
            
            project_stats = indexed_projects[project_name]
            
            # Get all chunks to analyze structure
            all_chunks = []
            try:
                # Search for all content to get structure overview
                structure_results = self.vector_db.search_l5x_content(
                    "routine program tag", limit=1000  # Get lots of results for overview
                )
                all_chunks = structure_results
            except Exception as e:
                logger.warning(f"Could not retrieve structure details: {e}")
            
            # Analyze the chunks to build overview
            programs = set()
            routines = set()
            udts = set()
            tags = set()
            
            for result in all_chunks:
                if result.location.parent_program:
                    programs.add(result.location.parent_program)
                if result.location.parent_routine:
                    routines.add(result.location.parent_routine)
                if result.chunk_type.value == 'udt':
                    udts.add(result.name)
                # Tags would need additional parsing
            
            return {
                'success': True,
                'project_path': acd_path,
                'project_name': project_name,
                'indexing_stats': {
                    'files_indexed': project_stats.get('file_count', 0),
                    'chunks_created': project_stats.get('chunk_count', 0),
                    'last_indexed': project_stats.get('last_indexed', 'Unknown')
                },
                'overview': {
                    'program_count': len(programs),
                    'routine_count': len(routines),
                    'udt_count': len(udts),
                    'total_chunks': len(all_chunks)
                },
                'programs': list(programs),
                'routines': list(routines),
                'udts': list(udts),
                'note': 'Overview generated from indexed L5X data. Results may vary based on what L5X files were exported and indexed.'
            }
            
        except Exception as e:
            logger.error(f"Error getting project overview: {e}")
            return {
                'success': False,
                'error': f'Failed to get project overview: {str(e)}'
            }
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available MCP tools"""
        return {
            tool.value: f"L5X analysis tool: {tool.value.replace('_', ' ').title()}"
            for tool in L5XMCPTools
        }
