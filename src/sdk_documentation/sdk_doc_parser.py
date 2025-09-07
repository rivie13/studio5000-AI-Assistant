#!/usr/bin/env python3
"""
Studio 5000 SDK Documentation Parser

Parses the official Studio 5000 SDK HTML documentation to create a searchable
vector database of all SDK capabilities, methods, classes, and examples.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SDKMethod:
    """Represents an SDK method or function"""
    name: str
    class_name: str
    description: str
    parameters: List[Dict[str, str]]
    return_type: str
    is_async: bool
    examples: List[str]
    file_path: str
    namespace: str
    category: str
    signature: str

@dataclass
class SDKClass:
    """Represents an SDK class"""
    name: str
    description: str
    namespace: str
    methods: List[str]  # Method names
    file_path: str
    inheritance: List[str]
    category: str

@dataclass
class SDKEnum:
    """Represents an SDK enum"""
    name: str
    description: str
    values: List[Dict[str, str]]
    namespace: str
    file_path: str
    category: str

@dataclass
class SDKExample:
    """Represents an SDK code example"""
    title: str
    description: str
    code: str
    file_path: str
    category: str
    related_methods: List[str]

class SDKDocumentationParser:
    """Parser for Studio 5000 SDK HTML documentation"""
    
    def __init__(self, doc_root: str):
        self.doc_root = Path(doc_root)
        self.methods: Dict[str, SDKMethod] = {}
        self.classes: Dict[str, SDKClass] = {}
        self.enums: Dict[str, SDKEnum] = {}
        self.examples: Dict[str, SDKExample] = {}
        
        # Category mappings
        self.categories = {
            'logix_project': 'Project Management',
            'enums': 'Enumerations',
            'exceptions': 'Exception Handling',
            'getting_started': 'Getting Started',
            'examples': 'Code Examples'
        }
        
    def parse_all_documentation(self) -> Dict[str, Any]:
        """Parse all SDK documentation files"""
        logger.info(f"Starting SDK documentation parsing from: {self.doc_root}")
        
        if not self.doc_root.exists():
            raise FileNotFoundError(f"SDK documentation directory not found: {self.doc_root}")
        
        # Parse different types of documentation
        self._parse_class_files()
        self._parse_enum_files()
        self._parse_example_files()
        self._parse_overview_files()
        
        logger.info(f"Parsing complete:")
        logger.info(f"  - Methods: {len(self.methods)}")
        logger.info(f"  - Classes: {len(self.classes)}")
        logger.info(f"  - Enums: {len(self.enums)}")
        logger.info(f"  - Examples: {len(self.examples)}")
        
        return {
            'methods': self.methods,
            'classes': self.classes,
            'enums': self.enums,
            'examples': self.examples
        }
    
    def _parse_class_files(self):
        """Parse class documentation files"""
        # Look for LogixProject class documentation
        logix_project_file = self.doc_root / "classlogix__designer__sdk_1_1logix__project_1_1LogixProject.html"
        if logix_project_file.exists():
            self._parse_logix_project_class(logix_project_file)
        
        # CRITICAL FIX: Parse the LogixProject members file which contains ALL methods
        logix_project_members_file = self.doc_root / "classlogix__designer__sdk_1_1logix__project_1_1LogixProject-members.html"
        if logix_project_members_file.exists():
            self._parse_logix_project_members(logix_project_members_file)
        
        # Parse other class files
        class_pattern = "class*.html"
        for class_file in self.doc_root.glob(class_pattern):
            if "LogixProject" not in class_file.name:
                self._parse_generic_class_file(class_file)
    
    def _parse_logix_project_members(self, file_path: Path):
        """Parse the LogixProject members file which contains the complete method list"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            logger.info(f"Parsing LogixProject members file: {file_path}")
            
            # Find the directory table with all members
            directory_table = soup.find('table', class_='directory')
            if not directory_table:
                logger.warning("No directory table found in members file")
                return
            
            methods_found = 0
            
            # Parse each table row for method information
            for row in directory_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # First cell contains the method signature and link
                    method_cell = cells[0]
                    class_cell = cells[1]
                    
                    # Extract method signature from the full text (not just the link)
                    method_signature = method_cell.get_text().strip()
                    
                    # Extract method name from signature
                    method_name = self._extract_method_name_from_signature(method_signature)
                    
                    if method_name and method_name not in self.methods:
                            # Extract parameters from signature
                            parameters = self._extract_parameters_from_signature(method_signature)
                            
                            # Determine if method is async (most SDK methods are async)
                            is_async = True  # Default for SDK methods
                            
                            # Get return type from signature
                            return_type = self._extract_return_type_from_signature(method_signature)
                            
                            # Create method object
                            method = SDKMethod(
                                name=method_name,
                                class_name='LogixProject',
                                description=f'LogixProject method: {method_signature}',
                                parameters=parameters,
                                return_type=return_type,
                                is_async=is_async,
                                examples=[],
                                file_path=str(file_path),
                                namespace='logix_designer_sdk.logix_project',
                                category=self._categorize_method(method_name, method_signature),
                                signature=method_signature
                            )
                            
                            self.methods[method_name] = method
                            methods_found += 1
            
            logger.info(f"Found {methods_found} methods in LogixProject members file")
            
        except Exception as e:
            logger.error(f"Error parsing LogixProject members file {file_path}: {e}")
    
    def _extract_method_name_from_signature(self, signature: str) -> Optional[str]:
        """Extract method name from a method signature"""
        # Handle various signature formats:
        # "method_name(params)" -> "method_name"  
        # "return_type method_name(params)" -> "method_name"
        import re
        
        # Look for method name pattern before parentheses
        match = re.search(r'(\w+)\s*\(', signature)
        if match:
            return match.group(1)
        return None
    
    def _extract_parameters_from_signature(self, signature: str) -> List[Dict[str, str]]:
        """Extract parameters from method signature"""
        import re
        
        # Extract content between parentheses
        match = re.search(r'\((.*?)\)', signature)
        if not match:
            return []
        
        params_str = match.group(1).strip()
        if not params_str or params_str == 'self':
            return []
        
        # Split parameters (basic parsing)
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if param and param != 'self':
                # Try to split type and name
                parts = param.split()
                if len(parts) >= 2:
                    param_type = ' '.join(parts[:-1])
                    param_name = parts[-1]
                else:
                    param_type = 'any'
                    param_name = param
                
                params.append({
                    'name': param_name,
                    'type': param_type,
                    'description': f'Parameter: {param_name}'
                })
        
        return params
    
    def _extract_return_type_from_signature(self, signature: str) -> str:
        """Extract return type from method signature"""
        # Look for return type at the beginning before method name
        import re
        
        # Pattern: "ReturnType methodName(" 
        match = re.match(r'^(\w+(?:\s*\|\s*\w+)*)\s+\w+\s*\(', signature)
        if match:
            return match.group(1)
        
        # Default return type for SDK methods
        return 'Any'
    
    def _parse_generic_class_file(self, file_path: Path):
        """Parse a generic class documentation file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract class name from title or filename
            title = soup.find('title')
            class_name = self._extract_class_name_from_title(title.get_text() if title else file_path.name)
            
            if class_name:
                description = self._extract_class_description(soup)
                namespace = self._extract_namespace_from_title(title.get_text() if title else "")
                
                self.classes[class_name] = SDKClass(
                    name=class_name,
                    description=description,
                    namespace=namespace,
                    methods=[],  # Could be enhanced to parse methods
                    file_path=str(file_path),
                    inheritance=[],
                    category=self._categorize_class(class_name)
                )
                
        except Exception as e:
            logger.debug(f"Error parsing generic class file {file_path}: {e}")
    
    def _extract_class_name_from_title(self, title_text: str) -> Optional[str]:
        """Extract class name from title text"""
        # Look for patterns like "logix_designer_sdk.enums.ControllerMode"
        match = re.search(r'([A-Z][a-zA-Z_]+)(?:\s+Class|\s+Reference)?', title_text)
        return match.group(1) if match else None
    
    def _extract_namespace_from_title(self, title_text: str) -> str:
        """Extract namespace from title text"""
        # Look for patterns like "logix_designer_sdk.enums"
        match = re.search(r'(logix_designer_sdk\.[a-z_]+)', title_text)
        return match.group(1) if match else "logix_designer_sdk"
    
    def _categorize_class(self, class_name: str) -> str:
        """Categorize a class based on its name"""
        name_lower = class_name.lower()
        
        if 'enum' in name_lower or class_name in ['ControllerMode', 'ConnectedState', 'OperationMode']:
            return 'Enumerations'
        elif 'exception' in name_lower or 'error' in name_lower:
            return 'Exception Handling'
        else:
            return 'SDK Classes'
    
    def _parse_logix_project_class(self, file_path: Path):
        """Parse the main LogixProject class documentation"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract class info
            class_name = "LogixProject"
            namespace = "logix_designer_sdk.logix_project"
            
            # Get class description
            description = self._extract_class_description(soup)
            
            # Parse all methods in the class
            methods = self._parse_class_methods(soup, class_name, namespace, str(file_path))
            
            # Store class info
            self.classes[class_name] = SDKClass(
                name=class_name,
                description=description,
                namespace=namespace,
                methods=list(methods.keys()),
                file_path=str(file_path),
                inheritance=[],
                category="Project Management"
            )
            
            # Store methods
            self.methods.update(methods)
            
        except Exception as e:
            logger.error(f"Error parsing LogixProject class: {e}")
    
    def _extract_class_description(self, soup) -> str:
        """Extract class description from HTML"""
        # Look for class description in various locations
        descriptions = []
        
        # Check for detailed description
        content_div = soup.find('div', class_='textblock')
        if content_div:
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short text
                    descriptions.append(text)
        
        # Fallback to title or brief
        if not descriptions:
            title = soup.find('title')
            if title:
                descriptions.append(title.get_text().strip())
        
        return ' '.join(descriptions[:3])  # Limit to first 3 paragraphs
    
    def _parse_class_methods(self, soup, class_name: str, namespace: str, file_path: str) -> Dict[str, SDKMethod]:
        """Parse all methods from a class documentation page"""
        methods = {}
        
        # Find method definitions
        method_tables = soup.find_all('table', class_='memberdecls')
        for table in method_tables:
            rows = table.find_all('tr', class_=['memitem', 'memitem:'])
            
            for row in rows:
                method_info = self._parse_method_row(row, class_name, namespace, file_path)
                if method_info:
                    methods[method_info.name] = method_info
        
        # Also look for detailed method descriptions
        self._enhance_methods_with_details(soup, methods, file_path)
        
        return methods
    
    def _parse_method_row(self, row, class_name: str, namespace: str, file_path: str) -> Optional[SDKMethod]:
        """Parse a single method row from HTML table"""
        try:
            # Extract method signature
            right_cell = row.find('td', class_='memItemRight')
            if not right_cell:
                return None
            
            # Get method link and name
            method_link = right_cell.find('a')
            if not method_link:
                return None
            
            method_name = method_link.get_text().strip()
            if not method_name or method_name in ['', ' ']:
                return None
            
            # Extract return type
            left_cell = row.find('td', class_='memItemLeft')
            return_type = left_cell.get_text().strip() if left_cell else "None"
            
            # Get full signature
            signature = right_cell.get_text().strip()
            
            # Extract parameters from signature
            parameters = self._parse_parameters_from_signature(signature)
            
            # Get description from next row
            next_row = row.find_next_sibling('tr', class_=['memdesc', 'memdesc:'])
            description = ""
            if next_row:
                desc_cell = next_row.find('td', class_='mdescRight')
                if desc_cell:
                    description = desc_cell.get_text().strip()
            
            # Determine if method is async
            is_async = 'async' in signature.lower() or 'await' in description.lower()
            
            # Categorize method
            category = self._categorize_method(method_name, description)
            
            return SDKMethod(
                name=method_name,
                class_name=class_name,
                description=description,
                parameters=parameters,
                return_type=return_type,
                is_async=is_async,
                examples=[],  # Will be populated later
                file_path=file_path,
                namespace=namespace,
                category=category,
                signature=signature
            )
            
        except Exception as e:
            logger.debug(f"Error parsing method row: {e}")
            return None
    
    def _parse_parameters_from_signature(self, signature: str) -> List[Dict[str, str]]:
        """Extract parameters from method signature"""
        parameters = []
        
        # Simple parameter extraction (can be enhanced)
        if '(' in signature and ')' in signature:
            param_section = signature[signature.find('(') + 1:signature.rfind(')')]
            if param_section.strip():
                # Split by comma and parse each parameter
                param_parts = [p.strip() for p in param_section.split(',')]
                for param in param_parts:
                    if param and param != 'self':
                        # Extract type and name
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = parts[0]
                            param_name = parts[1]
                            parameters.append({
                                'name': param_name,
                                'type': param_type,
                                'description': ''
                            })
                        else:
                            parameters.append({
                                'name': param,
                                'type': 'unknown',
                                'description': ''
                            })
        
        return parameters
    
    def _categorize_method(self, method_name: str, description: str) -> str:
        """Categorize a method based on its name and description"""
        name_lower = method_name.lower()
        desc_lower = description.lower()
        
        # Project operations
        if any(word in name_lower for word in ['save', 'open', 'create', 'close', 'build']):
            return 'Project Management'
        
        # Controller operations
        elif any(word in name_lower for word in ['download', 'upload', 'online', 'offline', 'controller']):
            return 'Controller Operations'
        
        # Tag operations
        elif any(word in name_lower for word in ['tag', 'get_tag', 'set_tag']):
            return 'Tag Operations'
        
        # Communication operations
        elif any(word in name_lower for word in ['comm', 'path', 'connect']):
            return 'Communication'
        
        # Import/Export operations
        elif any(word in name_lower for word in ['import', 'export', 'partial']):
            return 'Import/Export'
        
        # Safety operations
        elif any(word in name_lower for word in ['safety', 'signature', 'lock']):
            return 'Safety Operations'
        
        # SD Card operations
        elif any(word in name_lower for word in ['sd', 'card', 'deployment']):
            return 'SD Card Operations'
        
        else:
            return 'General'
    
    def _enhance_methods_with_details(self, soup, methods: Dict[str, SDKMethod], file_path: str):
        """Add detailed information to methods by parsing full page content"""
        # This could be enhanced to find detailed method descriptions,
        # parameter details, examples, etc.
        pass
    
    def _parse_enum_files(self):
        """Parse enumeration documentation files"""
        enum_files = list(self.doc_root.glob("*enums*.html"))
        for enum_file in enum_files:
            self._parse_enum_file(enum_file)
    
    def _parse_enum_file(self, file_path: Path):
        """Parse a single enum file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract enum name from title or filename
            title = soup.find('title')
            enum_name = self._extract_enum_name(title.get_text() if title else file_path.name)
            
            if enum_name:
                description = self._extract_class_description(soup)
                values = self._extract_enum_values(soup)
                
                self.enums[enum_name] = SDKEnum(
                    name=enum_name,
                    description=description,
                    values=values,
                    namespace="logix_designer_sdk.enums",
                    file_path=str(file_path),
                    category="Enumerations"
                )
                
        except Exception as e:
            logger.error(f"Error parsing enum file {file_path}: {e}")
    
    def _extract_enum_name(self, title_text: str) -> Optional[str]:
        """Extract enum name from title"""
        # Look for patterns like "ControllerMode" or "RequestedControllerMode"
        match = re.search(r'([A-Z][a-zA-Z]+(?:Mode|State|Type|Options|Event))', title_text)
        return match.group(1) if match else None
    
    def _extract_enum_values(self, soup) -> List[Dict[str, str]]:
        """Extract enum values from HTML"""
        values = []
        # Implementation would depend on the HTML structure of enum documentation
        return values
    
    def _parse_example_files(self):
        """Parse example documentation files AND Python example files"""
        # Parse HTML example files from documentation
        example_files = list(self.doc_root.glob("*Example*.html"))
        for example_file in example_files:
            self._parse_html_example_file(example_file)
            
        # CRITICAL: Parse Python example files from Examples directory
        examples_dir = self.doc_root.parent / "Examples"
        if examples_dir.exists():
            self._parse_python_example_files(examples_dir)
        
        # Parse getting started examples
        getting_started = self.doc_root / "PythonGettingStarted.html"
        if getting_started.exists():
            self._parse_getting_started_examples(getting_started)
        
        # Look for other example content
        for html_file in self.doc_root.glob("*.html"):
            if 'example' in html_file.name.lower():
                self._parse_example_file(html_file)
    
    def _parse_html_example_file(self, file_path: Path):
        """Parse HTML example files"""
        # Placeholder for HTML example parsing
        pass
    
    def _parse_python_example_files(self, examples_dir: Path):
        """Parse Python example files to extract real SDK usage patterns"""
        logger.info(f"Parsing Python examples from: {examples_dir}")
        
        for py_file in examples_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract title and description from docstring
                title = py_file.stem.replace('_', ' ').title()
                description = self._extract_python_docstring(content)
                
                # Extract related methods used in the example
                related_methods = self._extract_sdk_methods_from_python(content)
                
                # Clean up the code (remove comments, format nicely)
                clean_code = self._clean_python_example_code(content)
                
                example = SDKExample(
                    title=f"Python Example: {title}",
                    description=description or f"Example showing how to use {title}",
                    code=clean_code,
                    file_path=str(py_file),
                    category="Python Examples",
                    related_methods=related_methods
                )
                
                self.examples[f"py_{py_file.stem}"] = example
                logger.debug(f"Added Python example: {title}")
                
            except Exception as e:
                logger.error(f"Error parsing Python example {py_file}: {e}")
        
        logger.info(f"Parsed {len([k for k in self.examples.keys() if k.startswith('py_')])} Python examples")
    
    def _extract_python_docstring(self, content: str) -> str:
        """Extract the module docstring from Python code"""
        import re
        
        # Look for docstring at the beginning
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for single-line docstring  
        match = re.search(r'"([^"]{20,})"', content)
        if match:
            return match.group(1).strip()
            
        return ""
    
    def _extract_sdk_methods_from_python(self, content: str) -> List[str]:
        """Extract SDK methods used in Python example code"""
        import re
        
        methods = []
        
        # Look for await project.method_name( patterns
        matches = re.findall(r'await\s+\w*[pP]roject\.(\w+)\s*\(', content)
        methods.extend(matches)
        
        # Look for LogixProject.method_name( patterns 
        matches = re.findall(r'LogixProject\.(\w+)\s*\(', content)
        methods.extend(matches)
        
        # Remove duplicates and return
        return list(set(methods))
    
    def _clean_python_example_code(self, content: str) -> str:
        """Clean up Python example code for display"""
        lines = content.split('\n')
        cleaned_lines = []
        
        in_docstring = False
        docstring_quotes = None
        
        for line in lines:
            stripped = line.strip()
            
            # Skip shebang and pylint comments
            if stripped.startswith('#!') or 'pylint:' in stripped:
                continue
                
            # Handle docstrings
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    docstring_quotes = '"""' if '"""' in stripped else "'''"
                    in_docstring = True
                    continue
                elif docstring_quotes in stripped:
                    in_docstring = False
                    continue
            
            if in_docstring:
                continue
                
            # Keep the line if it's not empty or just a comment
            if stripped and not stripped.startswith('#'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _parse_getting_started_examples(self, file_path: Path):
        """Parse examples from getting started documentation"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Find code fragments
            code_blocks = soup.find_all('div', class_='fragment')
            for i, block in enumerate(code_blocks):
                lines = block.find_all('div', class_='line')
                if lines:
                    code = '\n'.join([line.get_text() for line in lines])
                    
                    # Find related description
                    prev_element = block.find_previous(['p', 'h1', 'h2', 'h3'])
                    description = prev_element.get_text().strip() if prev_element else "SDK Example"
                    
                    example_id = f"getting_started_{i}"
                    self.examples[example_id] = SDKExample(
                        title=f"Getting Started Example {i+1}",
                        description=description,
                        code=code,
                        file_path=str(file_path),
                        category="Getting Started",
                        related_methods=self._extract_methods_from_code(code)
                    )
                    
        except Exception as e:
            logger.error(f"Error parsing getting started examples: {e}")
    
    def _parse_example_file(self, file_path: Path):
        """Parse a general example file"""
        # Implementation for parsing other example files
        pass
    
    def _extract_methods_from_code(self, code: str) -> List[str]:
        """Extract method names referenced in code"""
        methods = []
        # Find patterns like "await project.method_name(" or "project.method_name("
        patterns = [
            r'await\s+\w+\.(\w+)\s*\(',
            r'\w+\.(\w+)\s*\(',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            methods.extend(matches)
        
        return list(set(methods))  # Remove duplicates
    
    def _parse_overview_files(self):
        """Parse overview and general documentation files"""
        overview_files = [
            "index.html",
            "LogixProjectPage.html",
            "Logix.html"
        ]
        
        for filename in overview_files:
            file_path = self.doc_root / filename
            if file_path.exists():
                self._parse_overview_file(file_path)
    
    def _parse_overview_file(self, file_path: Path):
        """Parse an overview documentation file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract key information and add as a special "example"
            title = soup.find('title')
            title_text = title.get_text().strip() if title else file_path.name
            
            content = self._extract_class_description(soup)
            
            if content and len(content) > 50:  # Only store substantial content
                example_id = f"overview_{file_path.stem}"
                self.examples[example_id] = SDKExample(
                    title=title_text,
                    description="SDK Overview Documentation",
                    code=content,  # Store as text content, not code
                    file_path=str(file_path),
                    category="Documentation",
                    related_methods=[]
                )
                
        except Exception as e:
            logger.error(f"Error parsing overview file {file_path}: {e}")
    
    def get_all_sdk_operations(self) -> List[Dict[str, Any]]:
        """Get a comprehensive list of all SDK operations for searching"""
        operations = []
        
        # Add methods
        for method in self.methods.values():
            operations.append({
                'type': 'method',
                'name': method.name,
                'class_name': method.class_name,
                'description': method.description,
                'category': method.category,
                'signature': method.signature,
                'is_async': method.is_async,
                'parameters': method.parameters,
                'namespace': method.namespace,
                'searchable_text': f"{method.name} {method.description} {method.category} {' '.join([p['name'] for p in method.parameters])}"
            })
        
        # Add classes
        for cls in self.classes.values():
            operations.append({
                'type': 'class',
                'name': cls.name,
                'description': cls.description,
                'category': cls.category,
                'namespace': cls.namespace,
                'methods': cls.methods,
                'searchable_text': f"{cls.name} {cls.description} {cls.category}"
            })
        
        # Add enums
        for enum in self.enums.values():
            operations.append({
                'type': 'enum',
                'name': enum.name,
                'description': enum.description,
                'category': enum.category,
                'values': enum.values,
                'searchable_text': f"{enum.name} {enum.description} {' '.join([v.get('name', '') for v in enum.values])}"
            })
        
        # Add examples
        for example in self.examples.values():
            operations.append({
                'type': 'example',
                'title': example.title,
                'description': example.description,
                'category': example.category,
                'code': example.code[:500],  # Truncate long code
                'related_methods': example.related_methods,
                'searchable_text': f"{example.title} {example.description} {' '.join(example.related_methods)}"
            })
        
        return operations
    
    def save_parsed_data(self, output_file: Path):
        """Save parsed data to JSON file"""
        data = {
            'methods': {k: asdict(v) for k, v in self.methods.items()},
            'classes': {k: asdict(v) for k, v in self.classes.items()},
            'enums': {k: asdict(v) for k, v in self.enums.items()},
            'examples': {k: asdict(v) for k, v in self.examples.items()}
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Parsed SDK documentation saved to: {output_file}")


def main():
    """Test the SDK documentation parser"""
    doc_root = r"C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\Documentation"
    
    parser = SDKDocumentationParser(doc_root)
    parsed_data = parser.parse_all_documentation()
    
    # Save parsed data
    output_file = Path("sdk_documentation_parsed.json")
    parser.save_parsed_data(output_file)
    
    # Display summary
    operations = parser.get_all_sdk_operations()
    print(f"\n🎉 SDK Documentation Parsing Complete!")
    print(f"📊 Found {len(operations)} total operations:")
    
    by_type = {}
    for op in operations:
        op_type = op.get('type', 'unknown')
        by_type[op_type] = by_type.get(op_type, 0) + 1
    
    for op_type, count in by_type.items():
        print(f"  - {op_type.title()}: {count}")


if __name__ == "__main__":
    main()
