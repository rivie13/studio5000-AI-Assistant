# Tag Vector Database Design

## Overview
Design document for creating a vector database system to handle large Studio 5000 tag CSV exports, enabling semantic search through thousands of I/O points, devices, and system mappings.

## Problem Statement
Studio 5000 tag CSV exports can contain thousands of rows with:
- Tag names, descriptions, data types
- I/O addresses and device mappings  
- Module/rack/slot information
- Aliases and engineering units
- Device-specific metadata

Current challenge: **Finding specific devices/I/O points in massive tag lists is time-consuming and difficult for AI to parse.**

## Proposed Architecture

### 1. CSV Tag Parser (`src/tag_analyzer/csv_tag_parser.py`)
**Purpose**: Parse Studio 5000 tag CSV exports into searchable chunks

**Key Components**:
```python
@dataclass
class TagChunk:
    """Represents a searchable tag entry"""
    id: str                     # Unique identifier
    tag_name: str              # Full tag name
    data_type: str             # BOOL, DINT, REAL, etc.
    description: str           # Human description
    alias: str                 # Alias if exists
    i_o_address: str          # Physical I/O address
    device_info: Dict         # Module/rack/slot details
    engineering_units: str    # Units (RPM, PSI, etc.)
    category: str             # Auto-categorized (motor, sensor, valve, etc.)
    metadata: Dict            # Additional CSV columns

class CSVTagParser:
    def parse_tag_csv(self, csv_path: str) -> List[TagChunk]
    def categorize_tag(self, tag_name: str, description: str) -> str
    def extract_device_info(self, address: str) -> Dict
    def parse_i_o_mapping(self, address: str) -> Dict
```

**Smart Categorization**:
- **Motors**: Keywords like "motor", "drive", "VFD", "run", "start"
- **Sensors**: "sensor", "switch", "PE", "photoeye", "proximity" 
- **Valves**: "valve", "solenoid", "cylinder", "actuator"
- **Safety**: "estop", "emergency", "safety", "guard", "interlock"
- **HMI**: "HMI", "display", "operator", "pushbutton"
- **Analog**: "speed", "pressure", "temperature", "level", "flow"

### 2. Tag Vector Database (`src/tag_analyzer/tag_vector_db.py`)
**Purpose**: Vector database for semantic search of tag data

```python
@dataclass
class TagSearchResult:
    tag_name: str
    description: str
    category: str
    score: float
    i_o_address: str
    device_info: Dict
    related_tags: List[str]

class TagVectorDatabase:
    def __init__(self, cache_dir: str = "tag_vector_cache")
    def build_tag_database(self, tag_chunks: List[TagChunk], force_rebuild: bool = False)
    def search_tags(self, query: str, category_filter: str = None) -> List[TagSearchResult]
    def find_device_by_description(self, description: str) -> List[TagSearchResult]
    def get_tags_by_module(self, rack: int, slot: int) -> List[TagSearchResult]
    def find_related_tags(self, tag_name: str) -> List[TagSearchResult]
    def analyze_i_o_usage(self) -> Dict[str, Any]
```

**Embedding Strategy**:
- **Comprehensive text** for each tag:
  - Tag name + description + category + I/O address
  - Device information and engineering units
  - Related module/rack/slot context
- **Semantic relationships** between similar devices
- **I/O mapping context** for physical location understanding

### 3. Tag MCP Integration (`src/tag_analyzer/tag_mcp_integration.py`)
**Purpose**: MCP server integration for tag analysis tools

```python
class TagMCPTools:
    """Enumeration of available tag analysis MCP tools"""
    INDEX_TAG_CSV = "index_tag_csv"
    SEARCH_TAGS = "search_tags" 
    FIND_DEVICE = "find_device"
    GET_MODULE_TAGS = "get_module_tags"
    FIND_I_O_POINT = "find_i_o_point"
    ANALYZE_I_O_USAGE = "analyze_i_o_usage"
    FIND_RELATED_TAGS = "find_related_tags"
    GET_DEVICE_OVERVIEW = "get_device_overview"

class TagMCPIntegration:
    def __init__(self, vector_db: TagVectorDatabase)
    async def initialize(self, force_rebuild: bool = False)
```

## New MCP Tools

### 1. `index_tag_csv`
**Purpose**: Index Studio 5000 tag CSV export for semantic search
**Parameters**: `csv_path`, `force_rebuild`
**Output**: Indexing status and tag statistics

### 2. `search_tags`
**Purpose**: Semantic search through tag database
**Parameters**: `query`, `category_filter`, `limit`
**Output**: Ranked tag results with device context

### 3. `find_device`
**Purpose**: Find specific devices by description or function
**Parameters**: `device_description`, `device_type`
**Output**: Matching devices with I/O addresses and context

### 4. `get_module_tags`
**Purpose**: Get all tags for a specific module/rack/slot
**Parameters**: `rack`, `slot`, `module_type`
**Output**: Complete tag listing for physical module

### 5. `find_i_o_point`
**Purpose**: Find specific I/O points by address or description
**Parameters**: `address_pattern`, `description`
**Output**: Matching I/O points with context

### 6. `analyze_i_o_usage`
**Purpose**: Analyze I/O usage and capacity across the system
**Parameters**: None
**Output**: Usage statistics, available points, module analysis

### 7. `find_related_tags`
**Purpose**: Find tags related to a given tag (same device, module, function)
**Parameters**: `tag_name`, `relationship_type`
**Output**: Related tags with relationship descriptions

### 8. `get_device_overview`
**Purpose**: Get comprehensive overview of devices in the system
**Parameters**: `category_filter`
**Output**: Device breakdown by type, location, status

## Example Workflows

### Workflow 1: Find Motor Control I/O
```
User: "Find the conveyor motor start and stop buttons"

1. search_tags("conveyor motor start stop button")
   → Finds relevant motor control tags

2. find_related_tags("CONV_01_START") 
   → Discovers related tags (stop, run feedback, VFD)

3. get_module_tags(rack=2, slot=3)
   → Shows all I/O on the motor control module
```

### Workflow 2: Locate Device by Function  
```
User: "Where is the photoeye for the packaging line?"

1. find_device("packaging line photoeye sensor")
   → Finds PE tags with descriptions

2. Returns: I/O address, module location, related logic
```

### Workflow 3: Analyze I/O Capacity
```
User: "How much I/O capacity do we have left?"

1. analyze_i_o_usage()
   → Returns usage by module, available points, recommendations
```

### Workflow 4: Troubleshoot Device Issues
```
User: "What's connected to rack 3 slot 5?"

1. get_module_tags(rack=3, slot=5)
   → Lists all tags for that module
   
2. Shows device types, I/O usage, potential issues
```

## Integration with L5X Analyzer

### **Combined Power**:
- **L5X Analyzer**: Understands ladder logic and routines
- **Tag Database**: Understands physical devices and I/O mapping
- **Together**: Complete system understanding!

### **Cross-Reference Capabilities**:
```python
# Find where a tag is used in logic
l5x_results = l5x_integration.search_l5x_content(f"uses {tag_name}")

# Find the physical device for a tag
tag_results = tag_integration.find_device(tag_name)

# Complete picture: Logic + Physical device + I/O address
```

## CSV Format Support

### **Standard Studio 5000 Export Columns**:
- **Tag Name**: Full hierarchical tag name
- **Data Type**: BOOL, DINT, REAL, STRING, UDT names
- **Description**: Human-readable description  
- **Alias**: Alias tag if exists
- **Address**: I/O address (Local:x:I.Data.x format)
- **Engineering Units**: RPM, PSI, °F, etc.
- **Min/Max Values**: Scaling information
- **Comments**: Additional notes

### **Smart Parsing Features**:
- **Auto-detect column formats** from different Studio 5000 versions
- **Extract rack/slot/channel** from I/O addresses
- **Categorize by naming conventions** (your specific patterns)
- **Cross-reference aliases** with base tags
- **Parse UDT members** for complex data types

## Benefits

### **For Engineers**:
- **"Find the estop for line 3"** → Instant results with I/O address
- **"What sensors are on rack 2?"** → Complete module inventory
- **"Where is the speed feedback?"** → Find analog input with context

### **For Troubleshooting**:
- **Physical to logical mapping** → Tag to ladder logic cross-reference
- **Module diagnostics** → I/O usage and capacity analysis
- **Device relationships** → Find all related I/O for a machine

### **For System Design**:
- **I/O planning** → Available points and capacity analysis
- **Device inventory** → Complete system overview by category
- **Naming consistency** → Find tags with similar functions

This system would make your MCM_06_Real CSV tag file as searchable and analyzable as your L5X files!
