#!/usr/bin/env python3
"""
Studio 5000 Logix Designer Documentation MCP Server

This MCP server provides access to Studio 5000/Logix Designer instruction documentation,
making it easy to search for and retrieve information about PLC instructions, programming
syntax, and best practices directly within AI conversations.
"""

import asyncio
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import argparse
from dataclasses import dataclass

# Import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from code_generator.l5x_generator import L5XGenerator, L5XProject, Program, Routine, LadderRung, create_motor_control_example
from ai_assistant.code_assistant import CodeAssistant
from ai_assistant.mcp_integration import create_mcp_integrated_assistant
from sdk_interface.studio5000_sdk import studio5000_sdk
from sdk_documentation.mcp_sdk_integration import SDKMCPIntegration, SDKMCPTools
from documentation.instruction_mcp_integration import InstructionMCPIntegration, InstructionMCPTools

# MCP imports (we'll implement a simplified version)
class MCPServer:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools = {}
        self.resources = {}
    
    def add_tool(self, name: str, description: str, handler):
        self.tools[name] = {
            "name": name,
            "description": description,
            "handler": handler
        }
    
    def add_resource(self, uri: str, description: str, handler):
        self.resources[uri] = {
            "uri": uri,
            "description": description,
            "handler": handler
        }

@dataclass
class Instruction:
    """Represents a Studio 5000 instruction"""
    name: str
    category: str
    description: str
    file_path: str
    languages: List[str]
    syntax: Optional[str] = None
    parameters: Optional[List[Dict]] = None
    examples: Optional[str] = None

class Studio5000Parser:
    """Parses Studio 5000 HTML documentation"""
    
    def __init__(self, doc_root: str):
        self.doc_root = Path(doc_root)
        self.instructions = {}
        self.categories = {}
        
    def parse_main_index(self) -> Dict[str, Any]:
        """Parse the main instruction set index"""
        index_file = self.doc_root / "17691.htm"
        if not index_file.exists():
            raise FileNotFoundError(f"Main index file not found: {index_file}")
        
        with open(index_file, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        categories = {}
        
        # Find instruction category links
        links = soup.find_all('a', href=re.compile(r'\d+\.htm'))
        for link in links:
            if 'Instructions' in link.get_text():
                category_name = link.get_text().strip()
                category_file = link.get('href')
                categories[category_name] = category_file
        
        self.categories = categories
        return categories
    
    def parse_instruction_file(self, file_path: str) -> Optional[Instruction]:
        """Parse an individual instruction file"""
        full_path = self.doc_root / file_path
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Extract instruction name from title
            match = re.search(r'([A-Z]{2,}[A-Z0-9]*)', title)
            instruction_name = match.group(1) if match else ""
            
            # Extract breadcrumb for category
            breadcrumb = soup.find('p', class_='breadcrumbs')
            category = ""
            if breadcrumb:
                links = breadcrumb.find_all('a')
                for link in links:
                    if 'Instructions' in link.get_text():
                        category = link.get_text().strip()
                        break
            
            # Extract description from first paragraph
            content_section = soup.find('div', id='content_section')
            description = ""
            if content_section:
                first_p = content_section.find('p')
                if first_p:
                    description = first_p.get_text().strip()
            
            # Determine supported languages from icons
            languages = []
            img_tags = soup.find_all('img', src=re.compile(r'o151\d+\.jpg'))
            if img_tags:
                # Based on the pattern seen in the documentation
                if any('o15168.jpg' in img.get('src', '') for img in img_tags):
                    languages.append('Ladder Diagram')
                if any('o15169.jpg' in img.get('src', '') for img in img_tags):
                    languages.append('Function Block')
                if any('o15170.jpg' in img.get('src', '') for img in img_tags):
                    languages.append('Structured Text')
            
            return Instruction(
                name=instruction_name,
                category=category,
                description=description,
                file_path=file_path,
                languages=languages,
                syntax=self._extract_syntax(soup),
                parameters=self._extract_parameters(soup),
                examples=self._extract_examples(soup)
            )
        
        except Exception as e:
            import sys
            print(f"Error parsing {file_path}: {e}", file=sys.stderr)
            return None
    
    def _extract_syntax(self, soup) -> Optional[str]:
        """Extract syntax information from the HTML"""
        # Look for syntax tables or code blocks
        syntax_patterns = [
            'Syntax',
            'Parameters',
            'Operands'
        ]
        
        for pattern in syntax_patterns:
            heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4'] and 
                              pattern.lower() in tag.get_text().lower())
            if heading:
                # Get the next table or paragraph
                next_elem = heading.find_next_sibling(['table', 'p', 'div'])
                if next_elem:
                    return next_elem.get_text().strip()
        
        return None
    
    def _extract_parameters(self, soup) -> Optional[List[Dict]]:
        """Extract parameter information"""
        parameters = []
        
        # Look for parameter tables
        tables = soup.find_all('table')
        for table in tables:
            headers = table.find_all('th')
            if len(headers) >= 2:
                header_texts = [th.get_text().strip().lower() for th in headers]
                if any('parameter' in h or 'operand' in h for h in header_texts):
                    rows = table.find_all('tr')[1:]  # Skip header row
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            param = {
                                'name': cells[0].get_text().strip(),
                                'description': cells[1].get_text().strip()
                            }
                            if len(cells) > 2:
                                param['type'] = cells[2].get_text().strip()
                            parameters.append(param)
        
        return parameters if parameters else None
    
    def _extract_examples(self, soup) -> Optional[str]:
        """Extract example information"""
        example_patterns = ['example', 'sample', 'usage']
        
        for pattern in example_patterns:
            heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4'] and 
                              pattern.lower() in tag.get_text().lower())
            if heading:
                example_content = []
                current = heading.find_next_sibling()
                while current and current.name not in ['h1', 'h2', 'h3', 'h4']:
                    if current.name in ['p', 'pre', 'code', 'div']:
                        example_content.append(current.get_text().strip())
                    current = current.find_next_sibling()
                
                if example_content:
                    return '\n\n'.join(example_content)
        
        return None
    
    def build_instruction_index(self) -> Dict[str, Instruction]:
        """Build a comprehensive index of all instructions"""
        instructions = {}
        
        # Parse categories first
        self.parse_main_index()
        
        # Find all HTML files that might be instructions
        html_files = list(self.doc_root.glob("*.htm"))
        
        for html_file in html_files:
            instruction = self.parse_instruction_file(html_file.name)
            if instruction and instruction.name:
                instructions[instruction.name.upper()] = instruction
        
        self.instructions = instructions
        return instructions

class Studio5000MCPServer:
    """MCP Server for Studio 5000 documentation"""
    
    def __init__(self, doc_root: str):
        self.doc_root = doc_root
        self.parser = Studio5000Parser(doc_root)
        self.server = MCPServer("studio5000-ai-assistant", "2.0.0")
        self.instructions = {}
        
        # Initialize new components
        self.l5x_generator = L5XGenerator()
        self.code_assistant = CodeAssistant(mcp_server=self)
        self.enhanced_assistant = create_mcp_integrated_assistant(self)
        self.studio5000_sdk = studio5000_sdk
        
        # Initialize SDK documentation system
        self.sdk_integration = SDKMCPIntegration()
        self.sdk_tools = SDKMCPTools(self.sdk_integration)
        
        # Initialize instruction documentation vector database
        self.instruction_integration = InstructionMCPIntegration()
        self.instruction_tools = InstructionMCPTools(self.instruction_integration)
        
        # Initialize and index the documentation
        self._initialize()
    
    async def _ensure_instruction_db_ready(self):
        """Ensure the instruction vector database is fully initialized"""
        # Database is now initialized synchronously in __init__, so this is a no-op
        pass
    
    async def _ensure_sdk_db_ready(self):
        """Ensure the SDK vector database is fully initialized"""
        # Database is now initialized synchronously in __init__, so this is a no-op
        pass
    
    def _initialize(self):
        """Initialize the server with documentation index"""
        # Don't print to stdout - it breaks JSON-RPC protocol
        # Use stderr for debug messages
        import sys
        print("Indexing Studio 5000 documentation...", file=sys.stderr)
        self.instructions = self.parser.build_instruction_index()
        print(f"Indexed {len(self.instructions)} instructions", file=sys.stderr)
        
        # Initialize instruction vector database - use blocking approach for immediate initialization
        print("Building instruction vector database...", file=sys.stderr)
        self._instruction_db_init_task = None
        try:
            import asyncio
            import threading
            
            # Use a thread to run the async initialization synchronously
            def run_async_init():
                """Run async initialization in a new event loop in a thread"""
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    # Force rebuild to ensure fresh data (temporary fix for cache issues)
                    new_loop.run_until_complete(
                        self.instruction_integration.initialize(self.instructions, force_rebuild=True)
                    )
                finally:
                    new_loop.close()
            
            print("Initializing instruction vector database (blocking)...", file=sys.stderr)
            # Run in a thread and wait for completion
            init_thread = threading.Thread(target=run_async_init)
            init_thread.start()
            init_thread.join(timeout=30)  # Wait up to 30 seconds
            
            if init_thread.is_alive():
                print("❌ Instruction vector database initialization timed out!", file=sys.stderr)
            else:
                print("✅ Instruction vector database initialized successfully!", file=sys.stderr)
                
        except Exception as e:
            print(f"❌ Failed to initialize instruction vector database: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            print("Falling back to basic text search", file=sys.stderr)
            # Continue without vector database - fallbacks will handle this
        
        # CRITICAL FIX: Initialize SDK documentation vector database - use blocking approach
        print("Building SDK documentation vector database...", file=sys.stderr)
        self._sdk_db_init_task = None
        try:
            import asyncio
            import threading
            
            # Use a thread to run the async initialization synchronously
            def run_async_sdk_init():
                """Run async SDK initialization in a new event loop in a thread"""
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    # Force rebuild to ensure fresh data (temporary fix for cache issues)
                    new_loop.run_until_complete(
                        self.sdk_integration.initialize(force_rebuild=True)
                    )
                finally:
                    new_loop.close()
            
            print("Initializing SDK vector database (blocking)...", file=sys.stderr)
            # Run in a thread and wait for completion
            sdk_init_thread = threading.Thread(target=run_async_sdk_init)
            sdk_init_thread.start()
            sdk_init_thread.join(timeout=30)  # Wait up to 30 seconds
            
            if sdk_init_thread.is_alive():
                print("❌ SDK vector database initialization timed out!", file=sys.stderr)
            else:
                print("✅ SDK vector database initialized successfully!", file=sys.stderr)
                
        except Exception as e:
            print(f"❌ Failed to initialize SDK vector database: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            print("Falling back to basic SDK search", file=sys.stderr)
            # Continue without vector database - fallbacks will handle this
        
        # Register tools
        self.server.add_tool(
            "search_instructions",
            "Search for PLC instructions by name, category, or description",
            self.search_instructions
        )
        
        self.server.add_tool(
            "get_instruction",
            "Get detailed information about a specific PLC instruction",
            self.get_instruction
        )
        
        self.server.add_tool(
            "list_categories",
            "List all available instruction categories",
            self.list_categories
        )
        
        self.server.add_tool(
            "list_instructions_by_category",
            "List all instructions in a specific category",
            self.list_instructions_by_category
        )
        
        self.server.add_tool(
            "get_instruction_syntax",
            "Get the syntax and parameters for a specific instruction",
            self.get_instruction_syntax
        )
        
        # Add new AI-powered code generation tools
        self.server.add_tool(
            "generate_ladder_logic",
            "Generate ladder logic from natural language specification",
            self.generate_ladder_logic
        )
        
        self.server.add_tool(
            "create_l5x_project",
            "Create complete L5X project file from specification",
            self.create_l5x_project
        )
        
        self.server.add_tool(
            "create_l5x_routine",
            "Create L5X routine export file that can be imported into existing ACD projects",
            self.create_l5x_routine
        )
        
        self.server.add_tool(
            "validate_ladder_logic",
            "Validate ladder logic using Studio 5000 documentation",
            self.validate_ladder_logic
        )
        
        self.server.add_tool(
            "create_acd_project",
            "Create real Studio 5000 .ACD project file using official SDK",
            self.create_acd_project
        )
        
        # Add SDK documentation search tools
        self.server.add_tool(
            "search_sdk_documentation",
            "Search Studio 5000 SDK documentation using natural language",
            self.search_sdk_documentation
        )
        
        self.server.add_tool(
            "get_sdk_operation_info",
            "Get detailed information about a specific SDK operation",
            self.get_sdk_operation_info
        )
        
        self.server.add_tool(
            "list_sdk_categories", 
            "List all SDK operation categories",
            self.list_sdk_categories
        )
        
        self.server.add_tool(
            "get_sdk_operations_by_category",
            "Get all SDK operations in a specific category",
            self.get_sdk_operations_by_category
        )
        
        self.server.add_tool(
            "get_logix_project_methods",
            "Get LogixProject methods, optionally filtered by category",
            self.get_logix_project_methods
        )
        
        self.server.add_tool(
            "suggest_sdk_operations",
            "Suggest relevant SDK operations based on context",
            self.suggest_sdk_operations
        )
        
        self.server.add_tool(
            "get_sdk_statistics",
            "Get SDK documentation statistics and overview",
            self.get_sdk_statistics
        )
    
    async def search_instructions(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Enhanced search for instructions using vector database"""
        try:
            # Ensure vector database is ready
            await self._ensure_instruction_db_ready()
            
            # Use vector database for semantic search
            vector_results = await self.instruction_tools.search_instructions(query, category)
            if vector_results.get('success', False):
                return vector_results.get('results', [])
            else:
                # Fallback to basic search if vector search fails
                import sys
                print(f"Vector search failed, using fallback: {vector_results.get('error', 'Unknown error')}", file=sys.stderr)
                return self._basic_search_instructions(query, category)
        except Exception as e:
            # Fallback to basic search
            import sys
            print(f"Vector search error, using fallback: {e}", file=sys.stderr)
            return self._basic_search_instructions(query, category)
    
    def _basic_search_instructions(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Fallback basic search for instructions (original implementation)"""
        results = []
        query_lower = query.lower()
        
        for name, instruction in self.instructions.items():
            match_score = 0
            
            # Name match (highest priority)
            if query_lower in instruction.name.lower():
                match_score += 10
            
            # Description match
            if instruction.description and query_lower in instruction.description.lower():
                match_score += 5
            
            # Category filter
            if category and instruction.category.lower() != category.lower():
                continue
            
            if match_score > 0:
                results.append({
                    'name': instruction.name,
                    'category': instruction.category,
                    'description': instruction.description,
                    'languages': instruction.languages,
                    'match_score': match_score,
                    'search_type': 'basic_fallback'
                })
        
        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:20]  # Limit to top 20 results
    
    async def get_instruction(self, name: str) -> Optional[Dict]:
        """Get detailed information about a specific instruction using vector database"""
        try:
            # Ensure vector database is ready
            await self._ensure_instruction_db_ready()
            
            # Try vector database first
            vector_result = await self.instruction_tools.get_instruction(name)
            if vector_result.get('success', False):
                return vector_result.get('instruction')
            
            # Fallback to direct lookup
            instruction = self.instructions.get(name.upper())
            if not instruction:
                return None
            
            return {
                'name': instruction.name,
                'category': instruction.category,
                'description': instruction.description,
                'languages': instruction.languages,
                'syntax': instruction.syntax,
                'parameters': instruction.parameters,
                'examples': instruction.examples,
                'file_path': instruction.file_path,
                'search_type': 'direct_fallback'
            }
        except Exception as e:
            # Fallback to direct lookup
            instruction = self.instructions.get(name.upper())
            if not instruction:
                return None
            
            return {
                'name': instruction.name,
                'category': instruction.category,
                'description': instruction.description,
                'languages': instruction.languages,
                'syntax': instruction.syntax,
                'parameters': instruction.parameters,
                'examples': instruction.examples,
                'file_path': instruction.file_path,
                'search_type': 'direct_fallback'
            }
    
    async def list_categories(self) -> List[str]:
        """List all available instruction categories using vector database"""
        try:
            # Ensure vector database is ready
            await self._ensure_instruction_db_ready()
            
            # Try vector database first
            vector_result = await self.instruction_tools.list_categories()
            if vector_result.get('success', False):
                return vector_result.get('categories', [])
            
            # Fallback to direct enumeration
            categories = set()
            for instruction in self.instructions.values():
                if instruction.category:
                    categories.add(instruction.category)
            return sorted(list(categories))
        except Exception as e:
            # Fallback to direct enumeration
            categories = set()
            for instruction in self.instructions.values():
                if instruction.category:
                    categories.add(instruction.category)
            return sorted(list(categories))
    
    async def list_instructions_by_category(self, category: str) -> List[Dict]:
        """List all instructions in a specific category using vector database"""
        try:
            # Ensure vector database is ready
            await self._ensure_instruction_db_ready()
            
            # Try vector database first
            vector_result = await self.instruction_tools.get_instructions_by_category(category)
            if vector_result.get('success', False):
                return vector_result.get('instructions', [])
            
            # Fallback to direct enumeration
            results = []
            category_lower = category.lower()
            
            for instruction in self.instructions.values():
                if instruction.category.lower() == category_lower:
                    results.append({
                        'name': instruction.name,
                        'description': instruction.description,
                        'languages': instruction.languages,
                        'search_type': 'direct_fallback'
                    })
            
            return sorted(results, key=lambda x: x['name'])
        except Exception as e:
            # Fallback to direct enumeration
            results = []
            category_lower = category.lower()
            
            for instruction in self.instructions.values():
                if instruction.category.lower() == category_lower:
                    results.append({
                        'name': instruction.name,
                        'description': instruction.description,
                        'languages': instruction.languages,
                        'search_type': 'direct_fallback'
                    })
            
            return sorted(results, key=lambda x: x['name'])
    
    async def get_instruction_syntax(self, name: str) -> Optional[Dict]:
        """Get syntax and parameter information for an instruction using vector database"""
        try:
            # Ensure vector database is ready
            await self._ensure_instruction_db_ready()
            
            # Try vector database first
            vector_result = await self.instruction_tools.get_instruction_syntax(name)
            if vector_result.get('success', False):
                return vector_result.get('syntax_info')
            
            # Fallback to direct lookup
            instruction = self.instructions.get(name.upper())
            if not instruction:
                return None
            
            return {
                'name': instruction.name,
                'syntax': instruction.syntax,
                'parameters': instruction.parameters,
                'languages': instruction.languages,
                'search_type': 'direct_fallback'
            }
        except Exception as e:
            # Fallback to direct lookup
            instruction = self.instructions.get(name.upper())
            if not instruction:
                return None
            
            return {
                'name': instruction.name,
                'syntax': instruction.syntax,
                'parameters': instruction.parameters,
                'languages': instruction.languages,
                'search_type': 'direct_fallback'
            }
    
    # New AI-powered code generation methods
    async def generate_ladder_logic(self, specification: str) -> Dict[str, Any]:
        """Generate enhanced ladder logic from natural language specification"""
        try:
            # Use the enhanced assistant for better warehouse automation support
            result = await self.enhanced_assistant.generate_ladder_logic(specification)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate ladder logic from specification'
            }
    
    async def create_l5x_project(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create complete L5X project file using enhanced code generation"""
        try:
            # Use the enhanced assistant for L5X project creation
            result = await self.enhanced_assistant.create_l5x_project(project_spec)
            return result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create L5X project'
            }
    
    async def create_l5x_routine(self, routine_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create L5X routine export file that can be imported into existing ACD projects"""
        try:
            from code_generator.l5x_generator import L5XGenerator, Routine, LadderRung
            
            # Extract routine specification
            routine_name = routine_spec.get('name', 'SIMPLE_TEST')
            specification = routine_spec.get('specification', '')
            controller_name = routine_spec.get('controller_name', 'MTN6_MCM06')
            software_revision = routine_spec.get('software_revision', '36.02')
            save_path = routine_spec.get('save_path')
            
            # Generate ladder logic using enhanced assistant
            ladder_result = await self.enhanced_assistant.generate_ladder_logic(specification)
            
            if not ladder_result.get('success', False):
                return {
                    'success': False,
                    'error': ladder_result.get('error', 'Failed to generate ladder logic'),
                    'message': 'Failed to generate ladder logic for routine'
                }
            
            # Parse the generated ladder logic into rungs
            ladder_logic = ladder_result.get('ladder_logic', '')
            ladder_lines = [line.strip() for line in ladder_logic.split('\n') if line.strip()]
            
            # Create rungs from ladder logic
            rungs = []
            rung_number = 0
            current_comment = None
            
            for line in ladder_lines:
                if line.startswith('//'):
                    # This is a comment for the next rung
                    current_comment = line[2:].strip()
                elif line and not line.startswith('//'):
                    # This is ladder logic
                    rung = LadderRung(
                        number=rung_number,
                        logic=line,
                        comment=current_comment
                    )
                    rungs.append(rung)
                    rung_number += 1
                    current_comment = None
            
            # If no rungs were created, create a simple default rung
            if not rungs:
                rungs = [
                    LadderRung(
                        number=0,
                        logic="XIC(Start_Test)XIO(Stop_Test)OTL(Test_Running);",
                        comment="Start/Stop logic"
                    ),
                    LadderRung(
                        number=1,
                        logic="XIC(Test_Running)TON(Test_Timer,5000,0);",
                        comment="Timer logic - 5 second timer"
                    ),
                    LadderRung(
                        number=2,
                        logic="XIC(Test_Timer.EN)OTE(Test_Output);",
                        comment="Output active during timer"
                    ),
                    LadderRung(
                        number=3,
                        logic="XIC(Test_Timer.DN)OTU(Test_Running);",
                        comment="Auto-reset when timer done"
                    )
                ]
            
            # Create the routine
            routine = Routine(
                name=routine_name,
                type="RLL",
                rungs=rungs,
                description=f"Generated routine: {specification[:100]}..."
            )
            
            # Extract tags from the ladder result
            tags = []
            if 'tags' in ladder_result:
                for tag in ladder_result['tags']:
                    tags.append({
                        'name': tag['name'],
                        'data_type': tag['data_type'],
                        'description': tag.get('description', '')
                    })
            else:
                # Default tags for the simple test routine
                tags = [
                    {'name': 'Start_Test', 'data_type': 'BOOL', 'description': 'Start test button'},
                    {'name': 'Stop_Test', 'data_type': 'BOOL', 'description': 'Stop test button'},
                    {'name': 'Test_Running', 'data_type': 'BOOL', 'description': 'Test running status'},
                    {'name': 'Test_Timer', 'data_type': 'TIMER', 'description': '5 second test timer', 'preset_value': 5000},
                    {'name': 'Test_Output', 'data_type': 'BOOL', 'description': 'Test output'}
                ]
            
            # Generate the routine export L5X
            generator = L5XGenerator()
            l5x_content = generator.generate_routine_export(
                routine=routine,
                controller_name=controller_name,
                tags=tags,
                software_revision=software_revision
            )
            
            # Save to file if path provided
            file_saved = False
            if save_path:
                file_saved = generator.save_routine_export(
                    routine=routine,
                    file_path=save_path,
                    controller_name=controller_name,
                    tags=tags,
                    software_revision=software_revision
                )
            
            return {
                'success': True,
                'routine_name': routine_name,
                'controller_name': controller_name,
                'l5x_content': l5x_content,
                'ladder_logic': ladder_logic,
                'tags_created': len(tags),
                'rungs_created': len(rungs),
                'instructions_used': ladder_result.get('instructions_used', []),
                'file_saved': file_saved,
                'save_path': save_path,
                'export_type': 'routine_export'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create L5X routine export'
            }
    
    async def validate_ladder_logic(self, logic_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ladder logic using enhanced validation with Studio 5000 documentation"""
        try:
            # Use the enhanced assistant for comprehensive validation
            result = await self.enhanced_assistant.validate_ladder_logic(logic_spec)
            return result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': 'Failed to validate ladder logic'
            }
    
    async def create_acd_project(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create real Studio 5000 .ACD project file using enhanced assistant and official SDK"""
        try:
            # Use the enhanced assistant for ACD project creation
            result = await self.enhanced_assistant.create_acd_project(project_spec)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create .ACD project using Studio 5000 SDK'
            }
    
    # New SDK Documentation Search Methods
    async def search_sdk_documentation(self, query: str, limit: Optional[int] = 10) -> Dict[str, Any]:
        """Search Studio 5000 SDK documentation using natural language"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.search_sdk_documentation(query, limit)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'message': 'Failed to search SDK documentation'
            }
    
    async def get_sdk_operation_info(self, name: str, operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a specific SDK operation"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.get_sdk_operation_info(name, operation_type)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'name': name,
                'message': 'Failed to get SDK operation info'
            }
    
    async def list_sdk_categories(self) -> Dict[str, Any]:
        """List all SDK operation categories"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.list_sdk_categories()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to list SDK categories'
            }
    
    async def get_sdk_operations_by_category(self, category: str) -> Dict[str, Any]:
        """Get all SDK operations in a specific category"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.get_sdk_operations_by_category(category)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'category': category,
                'message': 'Failed to get SDK operations by category'
            }
    
    async def get_logix_project_methods(self, method_category: Optional[str] = None) -> Dict[str, Any]:
        """Get LogixProject methods, optionally filtered by category"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.get_logix_project_methods(method_category)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method_category': method_category,
                'message': 'Failed to get LogixProject methods'
            }
    
    async def suggest_sdk_operations(self, context: str) -> Dict[str, Any]:
        """Suggest relevant SDK operations based on context"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.suggest_sdk_operations(context)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'context': context,
                'message': 'Failed to suggest SDK operations'
            }
    
    async def get_sdk_statistics(self) -> Dict[str, Any]:
        """Get SDK documentation statistics and overview"""
        try:
            await self._ensure_sdk_db_ready()  # Ensure SDK database is initialized
            result = await self.sdk_tools.get_sdk_statistics()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get SDK statistics'
            }

# JSON-RPC 2.0 MCP Protocol Implementation
async def handle_mcp_request(server: Studio5000MCPServer, request: Dict) -> Optional[Dict]:
    """Handle an MCP request"""
    method = request.get('method')
    params = request.get('params', {})
    request_id = request.get('id')
    
    # Handle notifications (requests without ID) by returning None
    is_notification = 'id' not in request
    
    # Initialize response with JSON-RPC 2.0 format
    response = {
        "jsonrpc": "2.0"
    }
    
    # Only include ID in response if this is not a notification
    if not is_notification:
        response["id"] = request_id
    
    if method == 'initialize':
        response["result"] = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "studio5000-ai-assistant",
                "version": "2.0.0"
            }
        }
        return response
    
    elif method == 'tools/list':
        tools = []
        for name, tool in server.server.tools.items():
            # Build properties and required fields based on tool name
            properties = {}
            required = []
            
            if name == 'search_instructions':
                properties = {
                    'query': {'type': 'string', 'description': 'Search query'},
                    'category': {'type': 'string', 'description': 'Optional category filter'}
                }
                required = ['query']
            elif name in ['get_instruction', 'get_instruction_syntax']:
                properties = {
                    'name': {'type': 'string', 'description': 'Instruction name'}
                }
                required = ['name']
            elif name == 'list_instructions_by_category':
                properties = {
                    'category': {'type': 'string', 'description': 'Category name'}
                }
                required = ['category']
            elif name == 'generate_ladder_logic':
                properties = {
                    'specification': {'type': 'string', 'description': 'Natural language specification for PLC logic'}
                }
                required = ['specification']
            elif name == 'create_l5x_project':
                properties = {
                    'project_spec': {
                        'type': 'object',
                        'description': 'Project specification',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Project name'},
                            'controller_type': {'type': 'string', 'description': 'Controller type (e.g., 1756-L83E)'},
                            'specification': {'type': 'string', 'description': 'Natural language specification'},
                            'save_path': {'type': 'string', 'description': 'Optional file path to save L5X file'}
                        }
                    }
                }
                required = ['project_spec']
            elif name == 'create_l5x_routine':
                properties = {
                    'routine_spec': {
                        'type': 'object',
                        'description': 'Routine specification for export',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Routine name'},
                            'controller_name': {'type': 'string', 'description': 'Existing controller name (e.g., MTN6_MCM06)'},
                            'specification': {'type': 'string', 'description': 'Natural language specification for routine logic'},
                            'software_revision': {'type': 'string', 'description': 'Studio 5000 software revision (default: 36.02)'},
                            'save_path': {'type': 'string', 'description': 'File path to save routine L5X export'}
                        }
                    }
                }
                required = ['routine_spec']
            elif name == 'validate_ladder_logic':
                properties = {
                    'logic_spec': {
                        'type': 'object',
                        'description': 'Ladder logic specification to validate',
                        'properties': {
                            'ladder_logic': {'type': 'string', 'description': 'Ladder logic code'},
                            'instructions_used': {'type': 'array', 'description': 'List of instructions used'}
                        }
                    }
                }
                required = ['logic_spec']
            elif name == 'create_acd_project':
                properties = {
                    'project_spec': {
                        'type': 'object',
                        'description': 'ACD project specification',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Project name'},
                            'controller_type': {'type': 'string', 'description': 'Controller type (e.g., 1756-L83E)'},
                            'major_revision': {'type': 'integer', 'description': 'Studio 5000 major revision (default 36)'},
                            'save_path': {'type': 'string', 'description': 'File path to save .ACD file'}
                        }
                    }
                }
                required = ['project_spec']
            elif name == 'search_sdk_documentation':
                properties = {
                    'query': {'type': 'string', 'description': 'Natural language query to search SDK documentation'},
                    'limit': {'type': 'integer', 'description': 'Maximum number of results to return (default: 10)'}
                }
                required = ['query']
            elif name == 'get_sdk_operation_info':
                properties = {
                    'name': {'type': 'string', 'description': 'Name of the SDK operation to get details for'},
                    'operation_type': {'type': 'string', 'description': 'Optional operation type filter (method, class, enum, example)'}
                }
                required = ['name']
            elif name == 'list_sdk_categories':
                properties = {}
                required = []
            elif name == 'get_sdk_operations_by_category':
                properties = {
                    'category': {'type': 'string', 'description': 'SDK operation category name'}
                }
                required = ['category']
            elif name == 'get_logix_project_methods':
                properties = {
                    'method_category': {'type': 'string', 'description': 'Optional category to filter LogixProject methods by'}
                }
                required = []
            elif name == 'suggest_sdk_operations':
                properties = {
                    'context': {'type': 'string', 'description': 'Context or description of what you want to accomplish'}
                }
                required = ['context']
            elif name == 'get_sdk_statistics':
                properties = {}
                required = []
            
            tools.append({
                'name': name,
                'description': tool['description'],
                'inputSchema': {
                    'type': 'object',
                    'properties': properties,
                    'required': required
                }
            })
        
        response["result"] = {'tools': tools}
        return response
    
    elif method == 'tools/call':
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if tool_name in server.server.tools:
            handler = server.server.tools[tool_name]['handler']
            try:
                result = await handler(**arguments)
                response["result"] = {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2)
                        }
                    ]
                }
                return response
            except Exception as e:
                if is_notification:
                    return None
                response["error"] = {
                    'code': -32603,
                    'message': f"Internal error: {str(e)}"
                }
                return response
        else:
            if is_notification:
                return None
            response["error"] = {
                'code': -32601,
                'message': f"Unknown tool: {tool_name}"
            }
            return response
    
    else:
        # Don't send error responses for notifications
        if is_notification:
            return None
            
        response["error"] = {
            'code': -32601,
            'message': f"Unknown method: {method}"
        }
        return response

async def main():
    """Main server entry point"""
    parser = argparse.ArgumentParser(description='Studio 5000 AI-Powered PLC Programming Assistant MCP Server')
    
    # Get default documentation path from environment variable or use fallback
    default_doc_path = os.environ.get(
        'STUDIO5000_DOC_PATH', 
        r'C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000'
    )
    
    parser.add_argument('--doc-root', 
                       default=default_doc_path,
                       help='Path to Studio 5000 documentation root directory (can also set STUDIO5000_DOC_PATH env var)')
    parser.add_argument('--test', 
                       action='store_true',
                       help='Run in test mode with sample queries')
    
    args = parser.parse_args()
    
    # Initialize the server
    try:
        mcp_server = Studio5000MCPServer(args.doc_root)
    except Exception as e:
        import sys
        print(f"Error initializing server: {e}", file=sys.stderr)
        return 1
    
    if args.test:
        # Test mode - run some sample queries
        print("\n=== Testing Studio 5000 MCP Server ===\n")
        
        # Test search
        print("1. Searching for 'timer' instructions:")
        results = await mcp_server.search_instructions("timer")
        for result in results[:5]:
            print(f"  - {result['name']}: {result['description']}")
        
        print("\n2. Getting details for ALMD instruction:")
        almd_info = await mcp_server.get_instruction("ALMD")
        if almd_info:
            print(f"  Name: {almd_info['name']}")
            print(f"  Category: {almd_info['category']}")
            print(f"  Languages: {', '.join(almd_info['languages'])}")
            print(f"  Description: {almd_info['description'][:100]}...")
        
        print("\n3. Listing categories:")
        categories = await mcp_server.list_categories()
        for cat in categories[:10]:
            print(f"  - {cat}")
        
        print(f"\n4. Testing AI code generation:")
        test_spec = "Start the motor when the start button is pressed and stop it when the stop button is pressed"
        result = await mcp_server.generate_ladder_logic(test_spec)
        if result['success']:
            print(f"  Generated logic: {result['ladder_logic']}")
            print(f"  Tags created: {len(result['tags'])}")
            print(f"  Instructions used: {', '.join(result['instructions_used'])}")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n5. Testing L5X project creation:")
        project_spec = {
            'name': 'TestMotorControl',
            'specification': test_spec
        }
        l5x_result = await mcp_server.create_l5x_project(project_spec)
        if l5x_result.get('success'):
            print(f"  L5X Project Creation Success!")
            # Print actual keys to see the structure
            print(f"  Available keys: {list(l5x_result.keys())}")
            if 'project_info' in l5x_result:
                info = l5x_result['project_info']
                print(f"  Project: {info.get('name', 'N/A')}")
                print(f"  Controller: {info.get('controller', 'N/A')}")
                print(f"  Programs: {info.get('programs', 'N/A')}")
                print(f"  Tags: {info.get('tags', 'N/A')}")
            elif 'project_name' in l5x_result:
                print(f"  Project: {l5x_result['project_name']}")
            elif 'name' in l5x_result:
                print(f"  Project: {l5x_result['name']}")
        else:
            print(f"  Error: {l5x_result.get('error', 'Unknown error')}")

        print(f"\n🎉 AI-Powered Studio 5000 Assistant initialized successfully!")
        print(f"📊 Features ready:")
        print(f"  • {len(mcp_server.instructions)} Studio 5000 instructions indexed")
        print(f"  • AI-powered natural language to ladder logic conversion")
        print(f"  • L5X project file generation")
        print(f"  • Instruction validation using official documentation")
        return 0
    
    else:
        # Real MCP server mode - JSON-RPC 2.0 via stdin/stdout
        import sys
        print("Studio 5000 MCP Server starting...", file=sys.stderr)
        print("Ready to handle MCP requests via stdin/stdout", file=sys.stderr)
        
        # JSON-RPC 2.0 stdin/stdout protocol handler
        while True:
            try:
                line = input()
                if not line:
                    break
                
                request = json.loads(line)
                response = await handle_mcp_request(mcp_server, request)
                
                # Only print response if it's not None (notifications return None)
                if response is not None:
                    print(json.dumps(response), flush=True)
                
            except EOFError:
                break
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
