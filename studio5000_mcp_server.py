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
        self.server = MCPServer("studio5000-docs", "1.0.0")
        self.instructions = {}
        
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
                "name": "studio5000-docs",
                "version": "1.0.0"
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
    parser = argparse.ArgumentParser(description='Studio 5000 Documentation MCP Server')
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
        
        print(f"\nServer initialized successfully with {len(mcp_server.instructions)} instructions!")
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
