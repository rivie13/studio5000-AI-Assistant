# L5X Enhanced Architecture Plan - SDK Integration

## 🚀 Revolutionary Hybrid Approach: Vector Database + Studio 5000 SDK

Based on SDK documentation research, we can build a **much more powerful system** that combines semantic search with official Rockwell SDK operations for production-scale L5X file management.

## 🎯 Core Architecture

### Phase 1: SDK-Powered L5X Analyzer
```python
class SDKPoweredL5XAnalyzer:
    """Leverages Studio 5000 SDK for L5X analysis and modification"""
    
    def __init__(self, vector_db: L5XVectorDatabase):
        self.vector_db = vector_db
        self.sdk_project = None
    
    async def open_project(self, acd_path: str):
        """Open ACD/L5K project using SDK"""
        self.sdk_project = await LogixProject.open_logix_project(acd_path, StdOutEventLogger())
    
    async def extract_routine_for_analysis(self, routine_name: str) -> str:
        """Extract specific routine to L5X for vector indexing"""
        xpath = f"Controller/Programs/Program[@Name='MainProgram']/Routines/Routine[@Name='{routine_name}']"
        temp_l5x = f"temp_{routine_name}.L5X"
        await self.sdk_project.partial_export_to_xml_file(xpath, temp_l5x)
        return temp_l5x
    
    async def insert_ladder_logic_surgically(self, routine_name: str, insert_position: int, 
                                           new_logic_l5x: str) -> bool:
        """Use SDK to insert ladder logic at exact position"""
        xpath = f"Controller/Programs/Program[@Name='MainProgram']/Routines/Routine[@Name='{routine_name}']/RLLContent"
        
        await self.sdk_project.partial_import_rungs_from_xml_file(
            xpath, 
            insert_position,  # Exact rung number
            0,               # Don't replace existing rungs
            new_logic_l5x,
            PartialImportOption.IMPORT_OFFLINE
        )
        return True
```

### Phase 2: Enhanced Vector Database with SDK Integration
```python
@dataclass
class L5XChunk:
    """SDK-aware L5X content chunk"""
    id: str
    type: str  # 'routine', 'rung', 'program', 'tag', 'udt'
    name: str
    content: str
    description: str
    location: Dict  # Includes XPath for SDK operations
    sdk_xpath: str  # Direct XPath for SDK operations
    insertion_points: List[int]  # Available rung positions for insertion
    dependencies: List[str]
    metadata: Dict

class L5XVectorDatabase:
    """Vector database with SDK integration for L5X content"""
    
    def __init__(self, cache_dir: str = "l5x_vector_cache"):
        self.cache_dir = Path(cache_dir)
        self.sdk_analyzer = SDKPoweredL5XAnalyzer(self)
        # ... existing vector db setup
    
    async def index_acd_project(self, acd_path: str, extract_routines: List[str] = None):
        """Index ACD project by extracting routines via SDK"""
        await self.sdk_analyzer.open_project(acd_path)
        
        chunks = []
        for routine_name in extract_routines or self._discover_routines():
            # Use SDK to extract each routine
            routine_l5x = await self.sdk_analyzer.extract_routine_for_analysis(routine_name)
            routine_chunks = self._parse_routine_l5x(routine_l5x, routine_name)
            chunks.extend(routine_chunks)
        
        self.build_vector_database(chunks)
    
    def find_optimal_insertion_point(self, query: str, routine_name: str) -> Tuple[int, float]:
        """Find best rung position to insert new logic"""
        # Vector search for similar logic patterns
        similar_chunks = self.search_l5x_content(f"{query} in {routine_name}")
        
        # Analyze insertion points based on semantic similarity
        for chunk in similar_chunks:
            if chunk.type == 'rung' and routine_name in chunk.location.get('routine', ''):
                # Return position after similar logic with confidence score
                return chunk.location.get('rung_number', 0) + 1, chunk.score
        
        return 0, 0.0  # Insert at beginning if no similar logic found
```

### Phase 3: Enhanced MCP Tools with SDK Operations

```python
class L5XSDKMCPIntegration:
    """MCP integration with SDK-powered L5X operations"""
    
    def __init__(self):
        self.vector_db = L5XVectorDatabase()
        self.sdk_analyzer = SDKPoweredL5XAnalyzer(self.vector_db)
    
    async def smart_insert_ladder_logic(self, acd_path: str, routine_name: str, 
                                      logic_description: str) -> Dict:
        """Intelligently insert ladder logic using AI + SDK"""
        
        # 1. Open project via SDK
        await self.sdk_analyzer.open_project(acd_path)
        
        # 2. Find optimal insertion point using vector search
        insertion_point, confidence = self.vector_db.find_optimal_insertion_point(
            logic_description, routine_name
        )
        
        # 3. Generate ladder logic using existing AI assistant
        from ai_assistant.code_assistant import CodeAssistant
        assistant = CodeAssistant()
        generated_logic = assistant.generate_ladder_logic(logic_description)
        
        # 4. Create small L5X fragment with new rungs
        l5x_fragment = self._create_rung_l5x_fragment(generated_logic)
        
        # 5. Use SDK to insert at optimal position
        success = await self.sdk_analyzer.insert_ladder_logic_surgically(
            routine_name, insertion_point, l5x_fragment
        )
        
        # 6. Save project
        await self.sdk_analyzer.sdk_project.save()
        
        return {
            'success': success,
            'insertion_point': insertion_point,
            'confidence': confidence,
            'logic_generated': generated_logic,
            'message': f'Logic inserted at rung {insertion_point} in {routine_name}'
        }
```

## 🛠️ New MCP Tools Leveraging SDK

### 1. `index_acd_project`
**Purpose**: Index large ACD/L5K project using SDK extraction
**Parameters**: `acd_path`, `routines_to_index`, `force_rebuild`
**SDK Methods**: `open_logix_project`, `partial_export_to_xml_file`

### 2. `smart_insert_logic`
**Purpose**: AI-guided logic insertion at optimal location
**Parameters**: `acd_path`, `routine_name`, `logic_description`, `insert_mode`
**SDK Methods**: `partial_import_rungs_from_xml_file`

### 3. `extract_routine_content`
**Purpose**: Extract specific routine content for analysis
**Parameters**: `acd_path`, `routine_name`, `output_format`
**SDK Methods**: `partial_export_to_xml_file`

### 4. `search_project_content`
**Purpose**: Semantic search across indexed project content
**Parameters**: `query`, `project_filter`, `component_type`
**Integration**: Vector DB + SDK XPath navigation

### 5. `analyze_insertion_points`
**Purpose**: Analyze best locations for new logic in a routine
**Parameters**: `acd_path`, `routine_name`, `logic_type`
**Integration**: Vector similarity + rung analysis

### 6. `batch_modify_routines`
**Purpose**: Apply similar modifications across multiple routines
**Parameters**: `acd_path`, `routine_pattern`, `modification_spec`
**SDK Methods**: Multiple `partial_import_rungs_from_xml_file` calls

## 🎯 Example Workflows

### Workflow 1: Smart Logic Insertion
```
User: "Add jam detection logic to R031_SORTER_TRACKING routine"

1. vector_db.search_l5x_content("jam detection conveyor logic") 
   → Find similar patterns in other routines

2. find_optimal_insertion_point("jam detection", "R031_SORTER_TRACKING")
   → Determine best rung position (e.g., rung 45 after conveyor start logic)

3. CodeAssistant.generate_ladder_logic("jam detection with timer and alarm")
   → Generate appropriate ladder logic

4. sdk.partial_import_rungs_from_xml_file(xpath, 45, 0, logic_l5x, IMPORT_OFFLINE)
   → Insert at exact position using SDK

5. sdk.save() → Save project with changes
```

### Workflow 2: Cross-Routine Analysis
```
User: "Find all routines that use UDT_CTRL_VFD and add new status bit"

1. vector_db.search_l5x_content("UDT_CTRL_VFD usage patterns")
   → Find all routines using this UDT

2. For each routine:
   - sdk.partial_export_to_xml_file() → Extract for analysis
   - find_optimal_insertion_point() → Find best location for new logic
   - sdk.partial_import_rungs_from_xml_file() → Add status bit logic
```

## 💡 Key Advantages

### Technical Benefits:
- **Official SDK Integration**: All modifications via Rockwell APIs
- **Surgical Precision**: Insert at exact rung positions
- **Large File Support**: Extract only needed sections for analysis
- **XPath Navigation**: Precise project structure targeting

### Production Benefits:
- **Safe Operations**: No manual XML manipulation
- **Audit Trail**: SDK operations provide proper logging
- **Studio 5000 Compatibility**: Changes open normally in Studio 5000
- **Rollback Capability**: Save versions before modifications

### AI-Enhanced Benefits:
- **Semantic Discovery**: Find relevant code by meaning
- **Pattern Recognition**: Learn from existing project patterns
- **Context-Aware Insertion**: Place logic in optimal locations
- **Cross-Project Learning**: Apply patterns from other projects

## 🚀 Implementation Timeline

### Week 1: SDK Integration Foundation
- SDKPoweredL5XAnalyzer class
- Basic project opening and routine extraction
- XPath navigation utilities

### Week 2: Vector Database Enhancement
- L5X content parsing with SDK extraction
- Vector indexing of routine content
- Insertion point analysis algorithms

### Week 3: MCP Tool Integration
- Enhanced MCP tools with SDK operations
- Smart insertion workflow implementation
- Testing with production L5X files

### Week 4: Production Testing
- Test with actual 50k line files from MCM_06_Real
- Performance optimization
- Error handling and edge cases

This approach gives us the **best of both worlds**: AI-powered semantic analysis combined with official SDK precision for production-ready L5X file enhancement!
