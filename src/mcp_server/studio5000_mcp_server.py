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

# Import our new modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from code_generator.l5x_generator import L5XGenerator, L5XProject, Program, Routine, LadderRung, create_motor_control_example
from ai_assistant.code_assistant import CodeAssistant

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
        
        # Initialize and index the documentation
        self._initialize()
        
    def _initialize(self):
        """Initialize the server with documentation index"""
        # Don't print to stdout - it breaks JSON-RPC protocol
        # Use stderr for debug messages
        import sys
        print("Indexing Studio 5000 documentation...", file=sys.stderr)
        self.instructions = self.parser.build_instruction_index()
        print(f"Indexed {len(self.instructions)} instructions", file=sys.stderr)
        
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
            "validate_ladder_logic",
            "Validate ladder logic using Studio 5000 documentation",
            self.validate_ladder_logic
        )
    
    async def search_instructions(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search for instructions matching the query"""
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
                    'match_score': match_score
                })
        
        # Sort by match score
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:20]  # Limit to top 20 results
    
    async def get_instruction(self, name: str) -> Optional[Dict]:
        """Get detailed information about a specific instruction"""
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
            'file_path': instruction.file_path
        }
    
    async def list_categories(self) -> List[str]:
        """List all available instruction categories"""
        categories = set()
        for instruction in self.instructions.values():
            if instruction.category:
                categories.add(instruction.category)
        return sorted(list(categories))
    
    async def list_instructions_by_category(self, category: str) -> List[Dict]:
        """List all instructions in a specific category"""
        results = []
        category_lower = category.lower()
        
        for instruction in self.instructions.values():
            if instruction.category.lower() == category_lower:
                results.append({
                    'name': instruction.name,
                    'description': instruction.description,
                    'languages': instruction.languages
                })
        
        return sorted(results, key=lambda x: x['name'])
    
    async def get_instruction_syntax(self, name: str) -> Optional[Dict]:
        """Get syntax and parameter information for an instruction"""
        instruction = self.instructions.get(name.upper())
        if not instruction:
            return None
        
        return {
            'name': instruction.name,
            'syntax': instruction.syntax,
            'parameters': instruction.parameters,
            'languages': instruction.languages
        }
    
    # New AI-powered code generation methods
    async def generate_ladder_logic(self, specification: str) -> Dict[str, Any]:
        """Generate ladder logic from natural language specification"""
        try:
            result = await self.code_assistant.generate_code_from_description(specification)
            return {
                'success': True,
                'ladder_logic': result['generated_code'].ladder_logic,
                'tags': result['generated_code'].tags,
                'instructions_used': result['generated_code'].instructions_used,
                'comments': result['generated_code'].comments,
                'validation_notes': result['generated_code'].validation_notes,
                'requirements_parsed': {
                    'inputs': result['requirements'].inputs,
                    'outputs': result['requirements'].outputs,
                    'logic_type': result['requirements'].logic_type
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate ladder logic from specification'
            }
    
    async def create_l5x_project(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create complete L5X project file from specification"""
        try:
            project_name = project_spec.get('name', 'GeneratedProject')
            controller_type = project_spec.get('controller_type', '1756-L83E')
            description = project_spec.get('description', 'Generated by Studio5000-AI-Assistant')
            
            # If specification contains natural language, generate code first
            if 'specification' in project_spec:
                code_result = await self.generate_ladder_logic(project_spec['specification'])
                if not code_result['success']:
                    return code_result
                
                # Create L5X project from generated code
                rungs = [LadderRung(0, code_result['ladder_logic'], 'Generated logic')]
                routine = Routine('MainRoutine', 'RLL', rungs, 'Main control routine')
                program = Program('MainProgram', [routine], 'Main program')
                
                project = L5XProject(
                    name=project_name,
                    controller_type=controller_type,
                    programs=[program],
                    tags=code_result['tags'],
                    description=description
                )
            else:
                # Use example project for now
                project = create_motor_control_example()
                project.name = project_name
                project.controller_type = controller_type
                project.description = description
            
            # Generate L5X content
            l5x_content = self.l5x_generator.generate_l5x_project(project)
            
            # Save to file if path specified
            file_path = project_spec.get('save_path')
            if file_path:
                success = self.l5x_generator.save_l5x_file(project, file_path)
                return {
                    'success': success,
                    'file_path': file_path if success else None,
                    'l5x_content': l5x_content[:500] + '...' if len(l5x_content) > 500 else l5x_content,
                    'project_info': {
                        'name': project.name,
                        'controller': project.controller_type,
                        'programs': len(project.programs),
                        'tags': len(project.tags) if project.tags else 0
                    }
                }
            else:
                return {
                    'success': True,
                    'l5x_content': l5x_content,
                    'project_info': {
                        'name': project.name,
                        'controller': project.controller_type,
                        'programs': len(project.programs),
                        'tags': len(project.tags) if project.tags else 0
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create L5X project'
            }
    
    async def validate_ladder_logic(self, logic_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ladder logic using Studio 5000 documentation"""
        try:
            ladder_logic = logic_spec.get('ladder_logic', '')
            instructions_used = logic_spec.get('instructions_used', [])
            
            validation_results = []
            warnings = []
            errors = []
            
            # Validate each instruction against our documentation
            for instruction in instructions_used:
                instruction_info = await self.get_instruction(instruction)
                if instruction_info:
                    validation_results.append(f"✓ {instruction} - Valid instruction")
                    
                    # Check if instruction supports ladder logic
                    if 'Ladder Diagram' not in instruction_info.get('languages', []):
                        warnings.append(f"⚠ {instruction} - May not support Ladder Diagram")
                else:
                    errors.append(f"✗ {instruction} - Unknown instruction")
            
            # Basic syntax validation
            if ladder_logic:
                # Check for basic ladder logic syntax patterns
                if not ladder_logic.strip().endswith(';'):
                    warnings.append("⚠ Ladder logic should end with semicolon")
                
                # Check for balanced parentheses
                if ladder_logic.count('(') != ladder_logic.count(')'):
                    errors.append("✗ Unbalanced parentheses in ladder logic")
            
            is_valid = len(errors) == 0
            
            return {
                'valid': is_valid,
                'validation_results': validation_results,
                'warnings': warnings,
                'errors': errors,
                'instructions_validated': len(instructions_used),
                'summary': f"Validated {len(instructions_used)} instructions - {'PASS' if is_valid else 'FAIL'}"
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': 'Validation failed due to internal error'
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
    parser.add_argument('--doc-root', 
                       default='.',
                       help='Path to Studio 5000 documentation root directory')
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
        if l5x_result['success']:
            print(f"  Project created: {l5x_result['project_info']['name']}")
            print(f"  Controller: {l5x_result['project_info']['controller']}")
            print(f"  Programs: {l5x_result['project_info']['programs']}")
            print(f"  Tags: {l5x_result['project_info']['tags']}")
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
