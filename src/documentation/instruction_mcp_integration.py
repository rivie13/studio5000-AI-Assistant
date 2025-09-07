#!/usr/bin/env python3
"""
MCP Server Integration for Instruction Documentation

Integrates instruction documentation vector database with the MCP server,
replacing the basic text search with semantic vector search capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .instruction_vector_db import InstructionVectorDatabase, InstructionSearchResult

logger = logging.getLogger(__name__)

class InstructionMCPIntegration:
    """Integration layer between instruction documentation and MCP server"""
    
    def __init__(self):
        self.vector_db = InstructionVectorDatabase()
        self.initialized = False
        self.instruction_data = {}
    
    async def initialize(self, instructions_dict: Dict[str, Any], force_rebuild: bool = False):
        """Initialize the instruction documentation system with parsed instruction data"""
        if self.initialized and not force_rebuild:
            return
        
        try:
            logger.info("Initializing instruction documentation vector database...")
            
            if not instructions_dict:
                logger.warning("No instructions provided for vector database")
                return
            
            self.instruction_data = instructions_dict
            
            # Build vector database from instruction data
            self.vector_db.build_vector_database(instructions_dict, force_rebuild=force_rebuild)
            
            self.initialized = True
            logger.info(f"Instruction documentation system initialized with {len(instructions_dict)} instructions")
            
        except Exception as e:
            logger.error(f"Failed to initialize instruction documentation: {e}")
            raise
    
    async def search_instructions(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search instructions using vector database with optional category filter"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return []
        
        try:
            # Use vector database search
            results = self.vector_db.search_instructions(query, limit=limit)
            
            # Apply category filter if specified
            if category:
                results = [r for r in results if r.category.lower() == category.lower()]
            
            # Convert to MCP-friendly format
            formatted_results = []
            for result in results:
                formatted_result = {
                    'name': result.name,
                    'category': result.category,
                    'description': result.description,
                    'languages': result.languages,
                    'match_score': result.score,
                    'search_type': 'vector_semantic'
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Instruction search error: {e}")
            return []
    
    async def get_instruction(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific instruction"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return None
        
        try:
            result = self.vector_db.get_instruction_by_name(name)
            if result:
                return {
                    'name': result.name,
                    'category': result.category,
                    'description': result.description,
                    'languages': result.languages,
                    'syntax': result.syntax,
                    'parameters': result.parameters,
                    'examples': result.examples,
                    'search_type': 'exact_match'
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting instruction details: {e}")
            return None
    
    async def list_categories(self) -> List[str]:
        """Get all instruction categories"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return []
        
        try:
            return self.vector_db.get_categories()
        except Exception as e:
            logger.error(f"Error getting instruction categories: {e}")
            return []
    
    async def get_instructions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all instructions in a specific category"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return []
        
        try:
            results = self.vector_db.get_instructions_by_category(category)
            
            formatted_results = []
            for result in results:
                formatted_result = {
                    'name': result.name,
                    'description': result.description,
                    'languages': result.languages,
                    'category': result.category
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error getting instructions by category: {e}")
            return []
    
    async def get_instruction_syntax(self, name: str) -> Optional[Dict[str, Any]]:
        """Get syntax and parameter information for an instruction"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return None
        
        try:
            result = self.vector_db.get_instruction_by_name(name)
            if result:
                return {
                    'name': result.name,
                    'syntax': result.syntax,
                    'parameters': result.parameters,
                    'languages': result.languages,
                    'category': result.category
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting instruction syntax: {e}")
            return None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the instruction documentation"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return {'initialized': False}
        
        try:
            stats = self.vector_db.get_statistics()
            stats['initialized'] = True
            return stats
        except Exception as e:
            logger.error(f"Error getting instruction statistics: {e}")
            return {'initialized': False, 'error': str(e)}
    
    async def suggest_instructions(self, context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Suggest relevant instructions based on context"""
        if not self.initialized:
            logger.warning("Instruction vector database not initialized")
            return []
        
        # Create enhanced queries based on context
        suggestions = []
        context_lower = context.lower()
        
        try:
            # Different suggestion strategies based on context
            if any(word in context_lower for word in ['timer', 'delay', 'wait', 'time']):
                timer_results = await self.search_instructions("timer delay timing", limit=3)
                suggestions.extend(timer_results)
            
            if any(word in context_lower for word in ['count', 'counter', 'pulse', 'increment']):
                counter_results = await self.search_instructions("counter counting increment", limit=3)
                suggestions.extend(counter_results)
            
            if any(word in context_lower for word in ['math', 'calculate', 'add', 'subtract', 'multiply']):
                math_results = await self.search_instructions("mathematical operations arithmetic", limit=3)
                suggestions.extend(math_results)
            
            if any(word in context_lower for word in ['compare', 'equal', 'greater', 'less', 'limit']):
                compare_results = await self.search_instructions("comparison equal greater less", limit=3)
                suggestions.extend(compare_results)
            
            if any(word in context_lower for word in ['motion', 'move', 'servo', 'axis', 'position']):
                motion_results = await self.search_instructions("motion control servo positioning", limit=3)
                suggestions.extend(motion_results)
            
            if any(word in context_lower for word in ['safety', 'emergency', 'interlock', 'guard']):
                safety_results = await self.search_instructions("safety emergency interlock", limit=3)
                suggestions.extend(safety_results)
            
            if any(word in context_lower for word in ['communication', 'message', 'network', 'ethernet']):
                comm_results = await self.search_instructions("communication networking message", limit=3)
                suggestions.extend(comm_results)
            
            if any(word in context_lower for word in ['array', 'file', 'data', 'copy', 'move']):
                array_results = await self.search_instructions("array file operations data manipulation", limit=3)
                suggestions.extend(array_results)
            
            # If no specific context matches, do a general search
            if not suggestions:
                general_results = await self.search_instructions(context, limit=limit)
                suggestions.extend(general_results)
            
            # Remove duplicates and limit results
            seen_names = set()
            unique_suggestions = []
            for suggestion in suggestions:
                if suggestion['name'] not in seen_names:
                    seen_names.add(suggestion['name'])
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error generating instruction suggestions: {e}")
            return []


# MCP tool implementations for instruction documentation
class InstructionMCPTools:
    """Enhanced MCP tools for instruction documentation search with vector database"""
    
    def __init__(self, instruction_integration: InstructionMCPIntegration):
        self.instruction_db = instruction_integration
    
    async def search_instructions(self, query: str, category: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Enhanced search for instructions using vector database"""
        try:
            results = await self.instruction_db.search_instructions(query, category, limit)
            return {
                'success': True,
                'query': query,
                'category_filter': category,
                'results': results,
                'total_found': len(results),
                'search_method': 'vector_semantic'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'category_filter': category
            }
    
    async def get_instruction(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific instruction"""
        try:
            details = await self.instruction_db.get_instruction(name)
            if details:
                return {
                    'success': True,
                    'instruction': details
                }
            else:
                return {
                    'success': False,
                    'error': f'Instruction not found: {name}',
                    'name': name
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'name': name
            }
    
    async def list_categories(self) -> Dict[str, Any]:
        """List all instruction categories"""
        try:
            categories = await self.instruction_db.list_categories()
            return {
                'success': True,
                'categories': categories,
                'total': len(categories)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_instructions_by_category(self, category: str) -> Dict[str, Any]:
        """Get all instructions in a category"""
        try:
            instructions = await self.instruction_db.get_instructions_by_category(category)
            return {
                'success': True,
                'category': category,
                'instructions': instructions,
                'total': len(instructions)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'category': category
            }
    
    async def get_instruction_syntax(self, name: str) -> Dict[str, Any]:
        """Get syntax and parameter information for an instruction"""
        try:
            syntax_info = await self.instruction_db.get_instruction_syntax(name)
            if syntax_info:
                return {
                    'success': True,
                    'instruction': name,
                    'syntax_info': syntax_info
                }
            else:
                return {
                    'success': False,
                    'error': f'Instruction syntax not found: {name}',
                    'name': name
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'name': name
            }
    
    async def suggest_instructions(self, context: str, limit: int = 10) -> Dict[str, Any]:
        """Suggest relevant instructions based on context"""
        try:
            suggestions = await self.instruction_db.suggest_instructions(context, limit)
            return {
                'success': True,
                'context': context,
                'suggestions': suggestions,
                'total': len(suggestions)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'context': context
            }
    
    async def get_instruction_statistics(self) -> Dict[str, Any]:
        """Get instruction documentation statistics"""
        try:
            stats = await self.instruction_db.get_statistics()
            return {
                'success': True,
                'statistics': stats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
