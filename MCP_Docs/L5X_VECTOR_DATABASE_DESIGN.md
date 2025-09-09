# L5X Vector Database Design

## Overview
Design document for enhancing the Studio 5000 MCP server to handle production-scale L5X files (up to 50,000+ lines) using vector database technology for semantic search and intelligent code insertion.

## Problem Statement
Current MCP tools can generate new L5X projects but cannot efficiently work with massive existing L5X files. Need capability to:
- Find relevant sections in 50k+ line files
- Add/modify code in appropriate locations
- Semantic search within L5X content (routines, tags, UDTs, etc.)

## Proposed Architecture

### 1. L5X Content Parser (`src/l5x_analyzer/l5x_parser.py`)
**Purpose**: Extract semantic chunks from L5X files for indexing

**Key Components**:
```python
@dataclass
class L5XChunk:
    """Represents a searchable chunk of L5X content"""
    id: str                    # Unique identifier
    type: str                  # 'routine', 'udt', 'tag', 'rung', 'program'
    name: str                  # Component name
    content: str               # XML content or ladder logic
    description: str           # Human-readable description
    location: Dict             # Line numbers, parent elements
    dependencies: List[str]    # Related components
    metadata: Dict             # Additional context

class L5XParser:
    def parse_l5x_file(self, file_path: str) -> List[L5XChunk]
    def extract_routines(self, xml_root) -> List[L5XChunk]
    def extract_udts(self, xml_root) -> List[L5XChunk]
    def extract_tags(self, xml_root) -> List[L5XChunk]
    def extract_ladder_rungs(self, routine_element) -> List[L5XChunk]
```

**Chunk Types to Index**:
- **Programs**: Complete program blocks
- **Routines**: Individual routines with all rungs
- **UDTs**: User-defined data types with members
- **Tags**: Individual tags with descriptions
- **Ladder Rungs**: Individual rungs with logic and comments
- **Data Type Members**: UDT members with descriptions

### 2. L5X Vector Database (`src/l5x_analyzer/l5x_vector_db.py`)
**Purpose**: Vector database for semantic search of L5X content

**Following Existing Pattern**:
```python
@dataclass
class L5XSearchResult:
    chunk_id: str
    type: str
    name: str
    description: str
    score: float
    content: str
    location: Dict
    file_path: str

class L5XVectorDatabase:
    def __init__(self, cache_dir: str = "l5x_vector_cache")
    def build_vector_database(self, l5x_chunks: List[L5XChunk], force_rebuild: bool = False)
    def search_l5x_content(self, query: str, limit: int = 20, score_threshold: float = 0.3) -> List[L5XSearchResult]
    def find_insertion_points(self, query: str, routine_name: str = None) -> List[L5XSearchResult]
    def get_related_components(self, chunk_id: str) -> List[L5XSearchResult]
```

**Embedding Strategy**:
- **Comprehensive text creation** for each chunk including:
  - Component type and name
  - Description and comments
  - Related dependencies
  - Ladder logic (for rungs)
  - UDT member details
- **Context-aware chunking** preserving logical boundaries
- **Hierarchical relationships** between programs/routines/rungs

### 3. L5X File Manager (`src/l5x_analyzer/l5x_file_manager.py`)
**Purpose**: Manage multiple L5X files and provide intelligent modification capabilities

```python
class L5XFileManager:
    def __init__(self, vector_db: L5XVectorDatabase)
    def index_l5x_file(self, file_path: str) -> bool
    def index_directory(self, directory_path: str) -> Dict[str, bool]
    def search_across_files(self, query: str) -> List[L5XSearchResult]
    def find_best_insertion_point(self, new_logic: str, target_routine: str = None) -> L5XSearchResult
    def insert_ladder_logic(self, file_path: str, routine_name: str, rung_number: int, logic: str) -> bool
    def modify_routine(self, file_path: str, routine_name: str, modifications: Dict) -> bool
```

### 4. L5X MCP Integration (`src/l5x_analyzer/l5x_mcp_integration.py`)
**Purpose**: MCP server integration for L5X analysis tools

```python
class L5XMCPIntegration:
    def __init__(self, vector_db: L5XVectorDatabase, file_manager: L5XFileManager)
    async def initialize(self, l5x_directory: str = None, force_rebuild: bool = False)

class L5XMCPTools:
    """Enumeration of available L5X analysis tools"""
    INDEX_L5X_FILE = "index_l5x_file"
    SEARCH_L5X_CONTENT = "search_l5x_content"
    FIND_INSERTION_POINT = "find_insertion_point"
    INSERT_LADDER_LOGIC = "insert_ladder_logic"
    ANALYZE_L5X_STRUCTURE = "analyze_l5x_structure"
    GET_ROUTINE_DETAILS = "get_routine_details"
    FIND_RELATED_COMPONENTS = "find_related_components"
```

## New MCP Tools

### 1. `index_l5x_file`
**Purpose**: Index a large L5X file for semantic search
**Parameters**: `file_path`, `force_rebuild`
**Output**: Indexing status and statistics

### 2. `search_l5x_content`
**Purpose**: Semantic search within indexed L5X files
**Parameters**: `query`, `file_filter`, `component_type`, `limit`
**Output**: Ranked search results with context

### 3. `find_insertion_point`
**Purpose**: Find best location to insert new ladder logic
**Parameters**: `new_logic_description`, `target_routine`, `target_file`
**Output**: Recommended insertion points with confidence scores

### 4. `insert_ladder_logic`
**Purpose**: Intelligently insert new ladder logic at optimal location
**Parameters**: `file_path`, `routine_name`, `logic`, `insertion_mode`
**Output**: Success status and line numbers where inserted

### 5. `analyze_l5x_structure`
**Purpose**: Analyze L5X file structure and provide overview
**Parameters**: `file_path`
**Output**: File statistics, routines list, UDTs, complexity metrics

### 6. `get_routine_details`
**Purpose**: Get detailed information about a specific routine
**Parameters**: `file_path`, `routine_name`
**Output**: Routine content, rungs, dependencies, complexity

### 7. `find_related_components`
**Purpose**: Find components related to a given UDT, tag, or routine
**Parameters**: `component_name`, `file_path`, `relationship_type`
**Output**: Related components with relationship descriptions

## Implementation Priority

### Phase 1: Core Infrastructure ⚡
1. **L5XParser** - Extract chunks from L5X files
2. **L5XVectorDatabase** - Vector indexing and search
3. **Basic MCP integration** - Search tools

### Phase 2: Smart Operations 🧠
4. **L5XFileManager** - File modification capabilities
5. **Advanced MCP tools** - Insertion and analysis
6. **Multi-file indexing** - Directory processing

### Phase 3: Production Features 🏭
7. **Real-time indexing** - Watch for file changes
8. **Advanced insertion logic** - Context-aware placement
9. **Collaboration features** - Team workflow support

## Cache Structure
```
l5x_vector_cache/
├── l5x_index.faiss          # FAISS index for chunks
├── l5x_embeddings.pkl       # Embeddings data
├── l5x_chunks.pkl           # Chunk metadata
├── file_metadata.json       # File indexing status
└── dependency_graph.pkl     # Component relationships
```

## Example Workflows

### Workflow 1: Add Logic to Existing Routine
```
1. User: "Add jam detection logic to R031_SORTER_TRACKING routine"
2. search_l5x_content("jam detection logic", file_filter="R031")
3. find_insertion_point("jam detection", routine="R031_SORTER_TRACKING")
4. insert_ladder_logic(file_path, routine, logic, optimal_location)
```

### Workflow 2: Find Similar Logic Patterns
```
1. User: "Find all conveyor start/stop logic in the system"
2. search_l5x_content("conveyor start stop motor control")
3. Return relevant rungs from multiple files with context
```

### Workflow 3: Analyze Dependencies
```
1. User: "What components use UDT_CTRL_VFD?"
2. find_related_components("UDT_CTRL_VFD", relationship="usage")
3. Return all routines, tags, and programs using this UDT
```

## Benefits
- **Massive File Support**: Handle 50k+ line L5X files efficiently
- **Semantic Search**: Find relevant code by meaning, not just text
- **Smart Insertion**: AI-guided placement of new logic
- **Production Ready**: Built on proven vector database architecture
- **Backward Compatible**: Extends existing MCP server seamlessly
