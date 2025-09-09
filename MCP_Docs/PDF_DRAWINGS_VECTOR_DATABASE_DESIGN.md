# PDF Drawings Vector Database Design

## Overview
Design document for integrating technical PDF drawings (P&IDs, electrical schematics, control logic diagrams) into the Studio 5000 MCP server using vector database technology for semantic search and intelligent context retrieval.

## Problem Statement
When writing PLC code, engineers need access to technical drawings for context about:
- Equipment connections and relationships
- Signal flows and control logic paths
- Safety interlocks and equipment tags
- Process flow and system layout
- I/O assignments and wiring details

Current challenge: 57MB PDF with hundreds of pages cannot be efficiently searched or referenced by AI models.

## Proposed Architecture

### 1. PDF Content Parser (`src/drawings_analyzer/pdf_parser.py`)
**Purpose**: Extract searchable content from technical PDF drawings

**Key Components**:
```python
@dataclass
class PDFChunk:
    """Represents a searchable chunk of PDF drawing content"""
    id: str                    # Unique identifier
    type: str                  # 'pid', 'electrical', 'logic', 'io_list', 'layout'
    page_number: int           # Source page in PDF
    drawing_number: str        # Drawing reference number
    title: str                 # Drawing title/description
    content: str               # Extracted text content
    vision_description: str    # AI-generated visual description
    equipment_tags: List[str]  # Referenced equipment tags
    location: Dict             # Page coordinates, zones
    metadata: Dict             # Additional context

class PDFParser:
    def parse_pdf_file(self, file_path: str) -> List[PDFChunk]
    def extract_text_content(self, page) -> str
    def classify_drawing_type(self, content: str, image) -> str
    def extract_equipment_tags(self, content: str) -> List[str]
    def generate_vision_description(self, page_image) -> str
```

**Drawing Types to Index**:
- **P&IDs**: Process flow diagrams with equipment and piping
- **Electrical Schematics**: Motor control, power distribution
- **Control Logic**: Ladder logic, function block diagrams
- **I/O Lists**: Tag assignments and signal types
- **Layout Drawings**: Physical equipment placement
- **Safety Drawings**: Interlock and safety system diagrams

### 2. PDF Vector Database (`src/drawings_analyzer/pdf_vector_db.py`)
**Purpose**: Vector database for semantic search of PDF drawing content

**Following Existing Pattern** (matches L5X/SDK/Tag databases):
```python
@dataclass
class PDFSearchResult:
    chunk_id: str
    drawing_type: str
    page_number: int
    drawing_number: str
    title: str
    description: str
    score: float
    content: str
    equipment_tags: List[str]
    file_path: str

class PDFVectorDatabase:
    def __init__(self, cache_dir: str = "pdf_drawings_cache")
    def build_vector_database(self, pdf_chunks: List[PDFChunk], force_rebuild: bool = False)
    def search_drawings(self, query: str, limit: int = 20, score_threshold: float = 0.3) -> List[PDFSearchResult]
    def find_equipment_references(self, equipment_tag: str) -> List[PDFSearchResult]
    def get_related_drawings(self, drawing_number: str) -> List[PDFSearchResult]
```

**Embedding Strategy** (same as existing DBs):
- **Comprehensive text creation** combining:
  - Drawing title and number
  - Extracted text content
  - AI-generated visual descriptions
  - Equipment tag lists
  - Drawing type and classification
- **Vision AI descriptions** for diagrams and schematics
- **Equipment tag correlation** with existing tag database

### 3. Vision AI Integration (`src/drawings_analyzer/vision_processor.py`)
**Purpose**: Analyze technical drawings using multimodal AI

```python
class VisionProcessor:
    def __init__(self, api_key: str = None)
    def analyze_technical_drawing(self, page_image: bytes, drawing_type: str) -> str
    def extract_equipment_connections(self, page_image: bytes) -> Dict
    def identify_control_logic_flow(self, page_image: bytes) -> str
    def extract_safety_interlocks(self, page_image: bytes) -> List[str]
```

**Vision Analysis Features**:
- **Equipment Identification**: Pumps, motors, valves, sensors
- **Connection Mapping**: Signal flows, piping connections
- **Logic Flow Analysis**: Control sequences and conditions
- **Safety System Recognition**: Interlocks, emergency stops
- **Tag Reading**: Equipment labels and reference numbers

### 4. PDF MCP Integration (`src/drawings_analyzer/pdf_mcp_integration.py`)
**Purpose**: MCP server integration for PDF drawings analysis

```python
class PDFMCPIntegration:
    def __init__(self, vector_db: PDFVectorDatabase, vision_processor: VisionProcessor)
    async def initialize(self, pdf_file_path: str, force_rebuild: bool = False)

class PDFMCPTools:
    """Enumeration of available PDF drawings tools"""
    INDEX_PDF_DRAWINGS = "index_pdf_drawings"
    SEARCH_DRAWINGS = "search_drawings"
    FIND_EQUIPMENT_CONTEXT = "find_equipment_context"
    GET_DRAWING_DETAILS = "get_drawing_details"
    ANALYZE_CONTROL_LOGIC = "analyze_control_logic"
    FIND_SAFETY_INTERLOCKS = "find_safety_interlocks"
```

## New MCP Tools

### 1. `index_pdf_drawings`
**Purpose**: Process and index the technical drawings PDF
**Parameters**: `pdf_file_path`, `force_rebuild`, `use_vision_ai`
**Output**: Indexing status, page count, drawing types found

### 2. `search_drawings`
**Purpose**: Semantic search within indexed PDF drawings
**Parameters**: `query`, `drawing_type_filter`, `equipment_filter`, `limit`
**Output**: Ranked search results with drawing context

### 3. `find_equipment_context`
**Purpose**: Find all drawings referencing specific equipment
**Parameters**: `equipment_tag`, `context_type`
**Output**: Related drawings with equipment connections and control logic

### 4. `get_drawing_details`
**Purpose**: Get detailed information about a specific drawing
**Parameters**: `drawing_number` or `page_number`
**Output**: Full drawing analysis, equipment list, connections

### 5. `analyze_control_logic`
**Purpose**: Extract control logic patterns from drawings
**Parameters**: `equipment_system`, `logic_type`
**Output**: Control sequences, interlocks, logic descriptions

### 6. `find_safety_interlocks`
**Purpose**: Find safety systems and interlocks for equipment
**Parameters**: `equipment_tag`, `safety_type`
**Output**: Safety requirements, interlock logic, emergency procedures

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1) ⚡
1. **PDFParser** - Extract text and images from PDF
2. **PDFVectorDatabase** - Vector indexing following existing pattern
3. **Basic MCP integration** - Search tools

### Phase 2: Vision AI Enhancement (Week 2) 🧠
4. **VisionProcessor** - AI analysis of technical drawings
5. **Enhanced embeddings** - Combine text + vision descriptions
6. **Equipment correlation** - Link with existing tag database

### Phase 3: Advanced Features (Week 3) 🏭
7. **Advanced MCP tools** - Context-aware searches
8. **Cross-database queries** - Connect drawings with L5X/tags
9. **Smart context injection** - Auto-provide drawing context

## Cache Structure
```
pdf_drawings_cache/
├── pdf_index.faiss              # FAISS index for chunks
├── pdf_embeddings.pkl           # Embeddings data
├── pdf_chunks.pkl               # Chunk metadata
├── drawing_metadata.json        # Drawing indexing status
├── vision_cache/                # Cached vision AI results
│   ├── page_001_analysis.json
│   ├── page_002_analysis.json
│   └── ...
└── equipment_references.pkl     # Equipment cross-references
```

## Integration with Existing Databases

### Cross-Database Queries:
- **Tags + Drawings**: "Show me drawings for conveyor_01 and its control logic"
- **L5X + Drawings**: "Find drawings referenced in routine R031_CONVEYOR"
- **SDK + Drawings**: "Show electrical drawings for VFD control implementation"

### Enhanced AI Context:
When user asks: *"Add jam detection to conveyor R031"*
1. Search L5X database for R031 routine
2. **Search drawings database for R031 equipment context**
3. **Auto-include drawing references in AI prompt**
4. Generate code with proper equipment understanding

## Example Workflows

### Workflow 1: Equipment Context Lookup
```
User: "Add motor start logic for M001"
1. find_equipment_context("M001", "electrical")
2. Return: electrical schemematic page 47, control logic page 23
3. AI writes motor control code with proper I/O and safety interlocks
```

### Workflow 2: Safety System Analysis
```
User: "What safety interlocks does conveyor CV-001 have?"
1. search_drawings("CV-001 safety interlocks")
2. find_safety_interlocks("CV-001")
3. Return: E-stop locations, guard switches, safety PLC logic
```

### Workflow 3: Cross-Reference Validation
```
User: "Verify the I/O assignments in my conveyor routine"
1. Extract equipment tags from L5X routine
2. find_equipment_context(tags, "io_assignments")  
3. Cross-reference with tag database
4. Return: validation results with drawing references
```

## Benefits

- **Seamless Integration**: Follows existing vector database patterns
- **Production Ready**: Built on proven infrastructure
- **Enhanced AI Context**: Drawings provide missing context automatically
- **Cross-Database Correlation**: Links drawings with L5X/tags/SDK
- **Vision AI Powered**: Understands visual technical content
- **Scalable**: Can handle multiple large PDF files
- **Backward Compatible**: Extends existing MCP server without changes

## Technical Considerations

### Performance:
- **PDF Processing**: ~2-5 minutes for 57MB file (one-time)
- **Search Performance**: Same as existing DBs (~6-20ms)
- **Vision AI**: Optional, can be cached and run incrementally

### Storage:
- **Vector Cache**: ~100-200MB for processed 57MB PDF
- **Vision Cache**: ~500MB for detailed visual analysis
- **Total Impact**: <1GB additional storage

### Dependencies:
- **PDF Processing**: PyMuPDF, pdfplumber
- **Vision AI**: OpenAI GPT-4V, Anthropic Claude Vision, or local models
- **Existing Stack**: sentence-transformers, FAISS (already installed)
