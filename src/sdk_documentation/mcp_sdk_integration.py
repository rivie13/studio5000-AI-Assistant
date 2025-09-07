#!/usr/bin/env python3
"""
MCP Server Integration for SDK Documentation

Integrates SDK documentation vector database with the MCP server,
adding new tools for SDK operation search and discovery.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .sdk_doc_parser import SDKDocumentationParser
from .sdk_vector_db import SDKVectorDatabase

logger = logging.getLogger(__name__)

class SDKMCPIntegration:
    """Integration layer between SDK documentation and MCP server"""
    
    def __init__(self, sdk_doc_root: str = None):
        # Default SDK documentation path
        if sdk_doc_root is None:
            sdk_doc_root = r"C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\Documentation"
        
        self.sdk_doc_root = sdk_doc_root
        self.parser = SDKDocumentationParser(sdk_doc_root)
        self.vector_db = SDKVectorDatabase()
        self.initialized = False
    
    async def initialize(self, force_rebuild: bool = False):
        """Initialize the SDK documentation system"""
        if self.initialized and not force_rebuild:
            return
        
        try:
            logger.info("Initializing SDK documentation system...")
            
            # Parse SDK documentation
            parsed_data = self.parser.parse_all_documentation()
            operations = self.parser.get_all_sdk_operations()
            
            if not operations:
                logger.warning("No SDK operations found - check documentation path")
                return
            
            # Build vector database
            self.vector_db.build_vector_database(operations, force_rebuild=force_rebuild)
            
            self.initialized = True
            logger.info(f"SDK documentation system initialized with {len(operations)} operations")
            
        except Exception as e:
            logger.error(f"Failed to initialize SDK documentation: {e}")
            raise
    
    async def search_sdk_operations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search SDK operations using natural language query"""
        if not self.initialized:
            await self.initialize()
        
        try:
            results = self.vector_db.search_sdk_operations(query, limit=limit)
            
            # Convert to MCP-friendly format
            formatted_results = []
            for result in results:
                formatted_result = {
                    'name': result.name,
                    'type': result.type,
                    'description': result.description,
                    'category': result.category,
                    'score': result.score,
                    'details': self._format_operation_details(result.details)
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"SDK search error: {e}")
            return []
    
    async def get_sdk_operation_details(self, name: str, operation_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific SDK operation"""
        if not self.initialized:
            await self.initialize()
        
        try:
            operation = self.vector_db.get_operation_by_name(name, operation_type)
            if operation:
                return self._format_operation_details(operation)
            return None
            
        except Exception as e:
            logger.error(f"Error getting SDK operation details: {e}")
            return None
    
    async def get_sdk_categories(self) -> List[str]:
        """Get all SDK operation categories"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return self.vector_db.get_all_categories()
        except Exception as e:
            logger.error(f"Error getting SDK categories: {e}")
            return []
    
    async def get_sdk_operations_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all SDK operations in a specific category"""
        if not self.initialized:
            await self.initialize()
        
        try:
            operations = self.vector_db.get_operations_by_category(category)
            return [self._format_operation_summary(op) for op in operations]
        except Exception as e:
            logger.error(f"Error getting operations by category: {e}")
            return []
    
    async def get_sdk_methods_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Get all methods for a specific SDK class"""
        if not self.initialized:
            await self.initialize()
        
        try:
            methods = self.vector_db.get_methods_by_class(class_name)
            return [self._format_operation_summary(method) for method in methods]
        except Exception as e:
            logger.error(f"Error getting methods by class: {e}")
            return []
    
    async def get_sdk_statistics(self) -> Dict[str, Any]:
        """Get statistics about the SDK documentation"""
        if not self.initialized:
            await self.initialize()
        
        try:
            return self.vector_db.get_statistics()
        except Exception as e:
            logger.error(f"Error getting SDK statistics: {e}")
            return {}
    
    async def suggest_sdk_operations(self, context: str) -> List[Dict[str, Any]]:
        """Suggest relevant SDK operations based on context"""
        if not self.initialized:
            await self.initialize()
        
        # Create enhanced query based on context
        suggestions = []
        
        # Different suggestion strategies based on context
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['create', 'new', 'project']):
            suggestions.extend(await self.search_sdk_operations("create new project", limit=3))
        
        if any(word in context_lower for word in ['tag', 'value', 'read', 'write']):
            suggestions.extend(await self.search_sdk_operations("tag operations get set value", limit=3))
        
        if any(word in context_lower for word in ['download', 'upload', 'controller']):
            suggestions.extend(await self.search_sdk_operations("controller operations download upload", limit=3))
        
        if any(word in context_lower for word in ['import', 'export', 'l5x']):
            suggestions.extend(await self.search_sdk_operations("import export L5X components", limit=3))
        
        if any(word in context_lower for word in ['online', 'offline', 'communication']):
            suggestions.extend(await self.search_sdk_operations("communication online offline", limit=3))
        
        # Remove duplicates and limit results
        seen_names = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion['name'] not in seen_names:
                seen_names.add(suggestion['name'])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:10]
    
    def _format_operation_details(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Format operation details for MCP response"""
        op_type = operation.get('type', 'unknown')
        
        if op_type == 'method':
            return {
                'type': 'method',
                'name': operation.get('name', ''),
                'class_name': operation.get('class_name', ''),
                'description': operation.get('description', ''),
                'category': operation.get('category', ''),
                'signature': operation.get('signature', ''),
                'is_async': operation.get('is_async', False),
                'return_type': operation.get('return_type', ''),
                'parameters': operation.get('parameters', []),
                'namespace': operation.get('namespace', ''),
                'usage_example': self._generate_usage_example(operation)
            }
        
        elif op_type == 'class':
            return {
                'type': 'class',
                'name': operation.get('name', ''),
                'description': operation.get('description', ''),
                'category': operation.get('category', ''),
                'namespace': operation.get('namespace', ''),
                'methods': operation.get('methods', []),
                'inheritance': operation.get('inheritance', [])
            }
        
        elif op_type == 'enum':
            return {
                'type': 'enum',
                'name': operation.get('name', ''),
                'description': operation.get('description', ''),
                'category': operation.get('category', ''),
                'namespace': operation.get('namespace', ''),
                'values': operation.get('values', [])
            }
        
        elif op_type == 'example':
            return {
                'type': 'example',
                'title': operation.get('title', ''),
                'description': operation.get('description', ''),
                'category': operation.get('category', ''),
                'code': operation.get('code', ''),
                'related_methods': operation.get('related_methods', [])
            }
        
        else:
            return operation
    
    def _format_operation_summary(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Format operation summary for lists"""
        return {
            'name': operation.get('name', operation.get('title', '')),
            'type': operation.get('type', ''),
            'description': operation.get('description', ''),
            'category': operation.get('category', '')
        }
    
    def _generate_usage_example(self, method_operation: Dict[str, Any]) -> str:
        """Generate a usage example for a method"""
        name = method_operation.get('name', '')
        class_name = method_operation.get('class_name', '')
        is_async = method_operation.get('is_async', False)
        params = method_operation.get('parameters', [])
        
        if not name:
            return ""
        
        # Generate parameter list
        param_list = []
        for param in params:
            param_name = param.get('name', '')
            param_type = param.get('type', '')
            if param_name and param_name != 'self':
                if param_type in ['str', 'string']:
                    param_list.append(f'"{param_name}_value"')
                elif param_type in ['int', 'integer']:
                    param_list.append('0')
                elif param_type in ['bool', 'boolean']:
                    param_list.append('True')
                else:
                    param_list.append(f'{param_name}_value')
        
        param_str = ', '.join(param_list)
        
        # Generate example
        if class_name == 'LogixProject':
            if is_async:
                example = f"# Assuming you have an open LogixProject instance\nresult = await project.{name}({param_str})"
            else:
                example = f"# Assuming you have an open LogixProject instance\nresult = project.{name}({param_str})"
        else:
            if is_async:
                example = f"result = await {class_name}.{name}({param_str})"
            else:
                example = f"result = {class_name}.{name}({param_str})"
        
        return example


# MCP tool implementations for SDK documentation
class SDKMCPTools:
    """MCP tools for SDK documentation search"""
    
    def __init__(self, sdk_integration: SDKMCPIntegration):
        self.sdk = sdk_integration
    
    async def search_sdk_documentation(self, query: str, limit: Optional[int] = 10) -> Dict[str, Any]:
        """Search SDK documentation using natural language"""
        try:
            results = await self.sdk.search_sdk_operations(query, limit or 10)
            return {
                'success': True,
                'query': query,
                'results': results,
                'total_found': len(results)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    async def get_sdk_operation_info(self, name: str, operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a specific SDK operation"""
        try:
            details = await self.sdk.get_sdk_operation_details(name, operation_type)
            if details:
                return {
                    'success': True,
                    'operation': details
                }
            else:
                return {
                    'success': False,
                    'error': f'SDK operation not found: {name}',
                    'name': name
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'name': name
            }
    
    async def list_sdk_categories(self) -> Dict[str, Any]:
        """List all SDK operation categories"""
        try:
            categories = await self.sdk.get_sdk_categories()
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
    
    async def get_sdk_operations_by_category(self, category: str) -> Dict[str, Any]:
        """Get all SDK operations in a category"""
        try:
            operations = await self.sdk.get_sdk_operations_by_category(category)
            return {
                'success': True,
                'category': category,
                'operations': operations,
                'total': len(operations)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'category': category
            }
    
    async def get_logix_project_methods(self, method_category: Optional[str] = None) -> Dict[str, Any]:
        """Get LogixProject methods, optionally filtered by category"""
        try:
            all_methods = await self.sdk.get_sdk_methods_by_class('LogixProject')
            
            if method_category:
                filtered_methods = [m for m in all_methods if m.get('category', '').lower() == method_category.lower()]
                return {
                    'success': True,
                    'class_name': 'LogixProject',
                    'category_filter': method_category,
                    'methods': filtered_methods,
                    'total': len(filtered_methods)
                }
            else:
                return {
                    'success': True,
                    'class_name': 'LogixProject',
                    'methods': all_methods,
                    'total': len(all_methods)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'class_name': 'LogixProject'
            }
    
    async def suggest_sdk_operations(self, context: str) -> Dict[str, Any]:
        """Suggest relevant SDK operations based on context"""
        try:
            suggestions = await self.sdk.suggest_sdk_operations(context)
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
    
    async def get_sdk_statistics(self) -> Dict[str, Any]:
        """Get SDK documentation statistics"""
        try:
            stats = await self.sdk.get_sdk_statistics()
            return {
                'success': True,
                'statistics': stats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
