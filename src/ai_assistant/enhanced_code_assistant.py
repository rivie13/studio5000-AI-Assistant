#!/usr/bin/env python3
"""
Enhanced AI-Powered PLC Code Assistant for Industrial Warehouse Automation

This module provides advanced natural language processing and code generation
capabilities specifically designed for complex warehouse automation scenarios.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio

class IndustryDomain(Enum):
    """Supported industrial domains"""
    WAREHOUSE = "warehouse"
    MANUFACTURING = "manufacturing"
    PACKAGING = "packaging"
    MATERIAL_HANDLING = "material_handling"
    SAFETY_SYSTEMS = "safety_systems"

class LogicComplexity(Enum):
    """Logic complexity levels"""
    SIMPLE = "simple"          # Single input/output
    MODERATE = "moderate"      # Multiple I/O, basic conditions
    COMPLEX = "complex"        # Multi-step sequences, interlocks
    ADVANCED = "advanced"      # State machines, coordinated motion

@dataclass
class IndustrialComponent:
    """Represents an industrial component with its properties"""
    name: str
    component_type: str  # 'sensor', 'actuator', 'motor', 'valve', etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    safety_critical: bool = False
    interlock_requirements: List[str] = field(default_factory=list)

@dataclass
class AutomationSequence:
    """Represents a sequence of automation steps"""
    name: str
    steps: List[Dict[str, Any]]
    conditions: List[str]
    safety_checks: List[str]
    timeout_ms: Optional[int] = None

@dataclass
class EnhancedPLCRequirement:
    """Enhanced structured representation of PLC requirements"""
    description: str
    domain: IndustryDomain
    complexity: LogicComplexity
    components: List[IndustrialComponent]
    sequences: List[AutomationSequence]
    safety_requirements: List[str]
    performance_requirements: Dict[str, Any]
    logic_type: str = "ladder"
    validation_rules: List[str] = field(default_factory=list)

@dataclass
class EnhancedGeneratedCode:
    """Enhanced generated PLC code with comprehensive metadata"""
    ladder_logic: str
    structured_text: Optional[str] = None
    function_blocks: List[Dict] = field(default_factory=list)
    tags: List[Dict] = field(default_factory=list)
    user_defined_types: List[Dict] = field(default_factory=list)
    instructions_used: List[str] = field(default_factory=list)
    safety_logic: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    validation_notes: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    documentation: str = ""

class IndustrialNLPParser:
    """Advanced natural language parser for industrial automation"""
    
    def __init__(self):
        self._initialize_industrial_vocabularies()
        self._initialize_pattern_recognizers()
        self._initialize_safety_keywords()
    
    def _initialize_industrial_vocabularies(self):
        """Initialize comprehensive industrial vocabularies"""
        
        # Warehouse-specific components
        self.warehouse_components = {
            'conveyors': ['conveyor', 'belt', 'roller', 'chain conveyor', 'belt conveyor', 'accumulation conveyor'],
            'sensors': ['photoeye', 'photoelectric', 'proximity', 'ultrasonic', 'laser scanner', 'barcode scanner', 
                       'weight scale', 'load cell', 'encoder', 'resolver', 'limit switch'],
            'actuators': ['pusher', 'diverter', 'gate', 'stop blade', 'lift table', 'transfer unit', 
                         'sorter', 'picker', 'robot arm', 'gripper'],
            'motors': ['servo motor', 'stepper motor', 'VFD', 'variable frequency drive', 'AC motor', 'DC motor'],
            'safety': ['light curtain', 'safety mat', 'e-stop', 'emergency stop', 'safety relay', 'guard switch',
                      'safety scanner', 'safety PLC', 'lockout', 'tagout'],
            'material_handling': ['crane', 'hoist', 'lift', 'elevator', 'shuttle', 'AGV', 'automated guided vehicle',
                                'palletizer', 'depalletizer', 'wrapper', 'strapper']
        }
        
        # Motion and positioning terms
        self.motion_terms = {
            'movements': ['move', 'position', 'rotate', 'extend', 'retract', 'lift', 'lower', 'advance', 'return'],
            'motion_types': ['absolute', 'relative', 'incremental', 'continuous', 'indexed', 'synchronized'],
            'motion_params': ['velocity', 'acceleration', 'deceleration', 'jerk', 'position', 'distance', 'angle']
        }
        
        # Process control terms
        self.process_terms = {
            'control_modes': ['manual', 'automatic', 'semi-automatic', 'maintenance', 'setup'],
            'states': ['idle', 'running', 'stopped', 'fault', 'alarm', 'warning', 'ready', 'busy'],
            'operations': ['start', 'stop', 'pause', 'resume', 'reset', 'abort', 'home', 'initialize']
        }
        
        # Timing and sequencing
        self.timing_terms = {
            'delays': ['delay', 'wait', 'pause', 'hold', 'dwell', 'timeout'],
            'sequences': ['sequence', 'step', 'stage', 'phase', 'cycle', 'routine', 'procedure'],
            'conditions': ['when', 'if', 'after', 'before', 'until', 'while', 'during', 'upon']
        }
    
    def _initialize_pattern_recognizers(self):
        """Initialize pattern recognition for common automation scenarios"""
        
        self.automation_patterns = {
            'conveyor_control': {
                'keywords': ['conveyor', 'belt', 'transport', 'move material'],
                'components': ['motor', 'photoeye', 'encoder', 'VFD'],
                'typical_logic': ['start/stop', 'speed control', 'jam detection', 'material tracking']
            },
            'sorting_system': {
                'keywords': ['sort', 'divert', 'route', 'separate', 'classify'],
                'components': ['diverter', 'pusher', 'scanner', 'decision logic'],
                'typical_logic': ['scan code', 'decision matrix', 'actuate diverter', 'confirm sort']
            },
            'material_handling': {
                'keywords': ['pick', 'place', 'transfer', 'load', 'unload', 'stack'],
                'components': ['robot', 'gripper', 'servo', 'vision system'],
                'typical_logic': ['position verification', 'grip confirmation', 'collision avoidance']
            },
            'safety_interlock': {
                'keywords': ['safety', 'interlock', 'guard', 'e-stop', 'lockout'],
                'components': ['safety relay', 'light curtain', 'guard switch', 'e-stop button'],
                'typical_logic': ['safety chain', 'fault detection', 'safe state', 'reset sequence']
            },
            'batch_processing': {
                'keywords': ['batch', 'recipe', 'formula', 'sequence', 'procedure'],
                'components': ['valves', 'pumps', 'mixers', 'sensors'],
                'typical_logic': ['recipe execution', 'ingredient dosing', 'process monitoring']
            }
        }
    
    def _initialize_safety_keywords(self):
        """Initialize safety-related keywords and requirements"""
        
        self.safety_keywords = {
            'emergency': ['emergency', 'e-stop', 'estop', 'emergency stop', 'panic', 'abort'],
            'protection': ['guard', 'barrier', 'fence', 'shield', 'cover', 'protection'],
            'detection': ['light curtain', 'safety mat', 'pressure mat', 'safety scanner', 'area scanner'],
            'control': ['safety relay', 'safety PLC', 'safety controller', 'safety module'],
            'standards': ['category 3', 'category 4', 'SIL 2', 'SIL 3', 'PLd', 'PLe', 'ISO 13849']
        }
    
    async def parse_specification(self, description: str, mcp_server=None) -> EnhancedPLCRequirement:
        """Parse natural language into enhanced structured requirements"""
        
        # Normalize input
        description = description.strip()
        description_lower = description.lower()
        
        # Determine industry domain
        domain = self._identify_domain(description_lower)
        
        # Assess complexity
        complexity = self._assess_complexity(description_lower)
        
        # Extract components
        components = await self._extract_components(description_lower, mcp_server)
        
        # Extract sequences and workflows
        sequences = self._extract_sequences(description_lower)
        
        # Identify safety requirements
        safety_requirements = self._extract_safety_requirements(description_lower)
        
        # Extract performance requirements
        performance_requirements = self._extract_performance_requirements(description_lower)
        
        # Determine logic type
        logic_type = self._determine_logic_type(description_lower, complexity)
        
        return EnhancedPLCRequirement(
            description=description,
            domain=domain,
            complexity=complexity,
            components=components,
            sequences=sequences,
            safety_requirements=safety_requirements,
            performance_requirements=performance_requirements,
            logic_type=logic_type
        )
    
    def _identify_domain(self, text: str) -> IndustryDomain:
        """Identify the industrial domain from the description"""
        
        domain_indicators = {
            IndustryDomain.WAREHOUSE: ['warehouse', 'distribution', 'shipping', 'receiving', 'storage', 
                                     'conveyor', 'sorting', 'picking', 'packing'],
            IndustryDomain.MANUFACTURING: ['manufacturing', 'assembly', 'production', 'machining', 
                                         'fabrication', 'welding', 'cutting'],
            IndustryDomain.PACKAGING: ['packaging', 'wrapping', 'labeling', 'sealing', 'filling', 'capping'],
            IndustryDomain.MATERIAL_HANDLING: ['crane', 'hoist', 'lift', 'robot', 'palletizer', 'AGV'],
            IndustryDomain.SAFETY_SYSTEMS: ['safety', 'interlock', 'guard', 'e-stop', 'lockout']
        }
        
        domain_scores = {}
        for domain, keywords in domain_indicators.items():
            score = sum(1 for keyword in keywords if keyword in text)
            domain_scores[domain] = score
        
        # Return domain with highest score, default to warehouse
        return max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else IndustryDomain.WAREHOUSE
    
    def _assess_complexity(self, text: str) -> LogicComplexity:
        """Assess the complexity level of the automation requirement"""
        
        complexity_indicators = {
            LogicComplexity.SIMPLE: ['simple', 'basic', 'single', 'one'],
            LogicComplexity.MODERATE: ['multiple', 'several', 'sequence', 'timer', 'counter'],
            LogicComplexity.COMPLEX: ['interlock', 'coordinate', 'synchronize', 'multi-step', 'conditional'],
            LogicComplexity.ADVANCED: ['state machine', 'recipe', 'batch', 'coordinated motion', 'advanced']
        }
        
        # Count indicators for each complexity level
        scores = {}
        for complexity, indicators in complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text)
            scores[complexity] = score
        
        # Additional complexity factors
        if len(re.findall(r'\band\b|\bor\b|\bif\b|\bthen\b|\bwhen\b', text)) > 3:
            scores[LogicComplexity.COMPLEX] += 2
        
        if len(re.findall(r'\d+', text)) > 2:  # Multiple numeric values suggest complexity
            scores[LogicComplexity.MODERATE] += 1
        
        # Return highest scoring complexity, default to moderate
        return max(scores, key=scores.get) if max(scores.values()) > 0 else LogicComplexity.MODERATE
    
    async def _extract_components(self, text: str, mcp_server=None) -> List[IndustrialComponent]:
        """Extract industrial components from the description"""
        
        components = []
        
        # Search through all component categories
        for category, component_list in self.warehouse_components.items():
            for component_name in component_list:
                if component_name in text:
                    # Extract specific instance names if possible
                    pattern = rf'(\w+\s+)?{re.escape(component_name)}(\s+\w+)?'
                    matches = re.finditer(pattern, text)
                    
                    for match in matches:
                        full_name = match.group(0).strip()
                        
                        # Determine if safety critical
                        safety_critical = any(safety_word in text for safety_word in self.safety_keywords['emergency'] + 
                                            self.safety_keywords['protection'])
                        
                        component = IndustrialComponent(
                            name=full_name.replace(' ', '_').upper(),
                            component_type=category.rstrip('s'),  # Remove plural 's'
                            safety_critical=safety_critical
                        )
                        
                        components.append(component)
        
        return components
    
    def _extract_sequences(self, text: str) -> List[AutomationSequence]:
        """Extract automation sequences from the description"""
        
        sequences = []
        
        # Look for sequence indicators
        sequence_patterns = [
            r'first\s+(.+?),?\s+then\s+(.+?)(?:\.|,|$)',
            r'when\s+(.+?),?\s+then\s+(.+?)(?:\.|,|$)',
            r'after\s+(.+?),?\s+(.+?)(?:\.|,|$)',
            r'step\s+\d+[:\s]+(.+?)(?:\.|,|step|\n|$)'
        ]
        
        for pattern in sequence_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                steps = []
                for i, group in enumerate(match.groups(), 1):
                    if group:
                        steps.append({
                            'step_number': i,
                            'description': group.strip(),
                            'type': 'condition' if i == 1 else 'action'
                        })
                
                if steps:
                    sequence = AutomationSequence(
                        name=f"Sequence_{len(sequences) + 1}",
                        steps=steps,
                        conditions=[],
                        safety_checks=[]
                    )
                    sequences.append(sequence)
        
        return sequences
    
    def _extract_safety_requirements(self, text: str) -> List[str]:
        """Extract safety requirements from the description"""
        
        safety_requirements = []
        
        # Check for safety keywords and extract context
        for category, keywords in self.safety_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    # Extract surrounding context
                    pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        context = match.group(0).strip()
                        safety_requirements.append(f"{category.title()}: {context}")
        
        return list(set(safety_requirements))  # Remove duplicates
    
    def _extract_performance_requirements(self, text: str) -> Dict[str, Any]:
        """Extract performance requirements like timing, speed, accuracy"""
        
        performance = {}
        
        # Extract timing requirements
        time_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(?:milli)?seconds?', 'timing_ms'),
            (r'(\d+(?:\.\d+)?)\s*minutes?', 'timing_min'),
            (r'(\d+(?:\.\d+)?)\s*hours?', 'timing_hr')
        ]
        
        for pattern, key in time_patterns:
            matches = re.findall(pattern, text)
            if matches:
                performance[key] = [float(match) for match in matches]
        
        # Extract speed requirements
        speed_patterns = [
            (r'(\d+(?:\.\d+)?)\s*(?:ft|feet|m|meters?)/(?:min|minute)', 'speed_linear'),
            (r'(\d+(?:\.\d+)?)\s*rpm', 'speed_rotational'),
            (r'(\d+(?:\.\d+)?)\s*hz', 'frequency')
        ]
        
        for pattern, key in speed_patterns:
            matches = re.findall(pattern, text)
            if matches:
                performance[key] = [float(match) for match in matches]
        
        return performance
    
    def _determine_logic_type(self, text: str, complexity: LogicComplexity) -> str:
        """Determine the most appropriate logic type"""
        
        if "structured text" in text or "st" in text:
            return "structured_text"
        elif "function block" in text or "fb" in text:
            return "function_block"
        elif complexity in [LogicComplexity.COMPLEX, LogicComplexity.ADVANCED]:
            return "mixed"  # Use combination of ladder and ST
        else:
            return "ladder"

class IndustrialInstructionMapper:
    """Maps industrial requirements to Studio 5000 instructions"""
    
    def __init__(self, mcp_server=None):
        self.mcp_server = mcp_server
        self._initialize_comprehensive_mappings()
    
    async def _initialize_comprehensive_mappings(self):
        """Initialize comprehensive instruction mappings"""
        
        # Basic I/O and Logic
        self.basic_instructions = {
            'examine_if_closed': 'XIC',
            'examine_if_open': 'XIO', 
            'output_energize': 'OTE',
            'output_latch': 'OTL',
            'output_unlatch': 'OTU',
            'one_shot_rising': 'OSR',
            'one_shot_falling': 'OSF'
        }
        
        # Timer Instructions
        self.timer_instructions = {
            'timer_on_delay': 'TON',
            'timer_off_delay': 'TOF',
            'retentive_timer': 'RTO',
            'reset_timer': 'RES'
        }
        
        # Counter Instructions  
        self.counter_instructions = {
            'count_up': 'CTU',
            'count_down': 'CTD',
            'reset_counter': 'RES'
        }
        
        # Math Instructions
        self.math_instructions = {
            'add': 'ADD',
            'subtract': 'SUB', 
            'multiply': 'MUL',
            'divide': 'DIV',
            'square_root': 'SQR',
            'negate': 'NEG',
            'absolute_value': 'ABS',
            'scale': 'SCL',
            'scale_with_parameters': 'SCP'
        }
        
        # Comparison Instructions
        self.compare_instructions = {
            'equal': 'EQU',
            'not_equal': 'NEQ', 
            'less_than': 'LES',
            'less_equal': 'LEQ',
            'greater_than': 'GRT',
            'greater_equal': 'GEQ',
            'limit_test': 'LIM',
            'masked_equal': 'MEQ'
        }
        
        # Move and Logical Instructions
        self.move_logical_instructions = {
            'move': 'MOV',
            'masked_move': 'MVM',
            'and': 'AND',
            'or': 'OR',
            'exclusive_or': 'XOR',
            'not': 'NOT',
            'clear': 'CLR'
        }
        
        # Motion Instructions (for warehouse automation)
        self.motion_instructions = {
            'motion_axis_home': 'MAH',
            'motion_axis_jog': 'MAJ', 
            'motion_axis_move': 'MAM',
            'motion_axis_stop': 'MAS',
            'motion_coordinated_path': 'MCCP',
            'motion_change_dynamics': 'MCD',
            'motion_servo_on': 'MSO',
            'motion_servo_off': 'MSF'
        }
        
        # Process Control Instructions
        self.process_instructions = {
            'pid': 'PID',
            'enhanced_pid': 'PIDE', 
            'deadtime': 'DEDT',
            'lead_lag': 'LDLG',
            'ramp_soak': 'RMPS'
        }
        
        # Safety Instructions
        self.safety_instructions = {
            'safety_function': 'SAFEF',
            'safety_input': 'SAFEI',
            'safety_output': 'SAFEO'
        }
        
        # Communication Instructions
        self.comm_instructions = {
            'message': 'MSG',
            'produce': 'PRODUCE',
            'consume': 'CONSUME',
            'get_system_value': 'GSV',
            'set_system_value': 'SSV'
        }
        
        # Array and File Instructions
        self.array_instructions = {
            'file_arithmetic_logic': 'FAL',
            'file_copy': 'COP',
            'file_fill': 'FLL',
            'bit_shift_left': 'BSL',
            'bit_shift_right': 'BSR',
            'fifo_load': 'FFL',
            'fifo_unload': 'FFU',
            'lifo_load': 'LFL',
            'lifo_unload': 'LFU'
        }
        
        # Combine all mappings
        self.all_instructions = {
            **self.basic_instructions,
            **self.timer_instructions,
            **self.counter_instructions,
            **self.math_instructions,
            **self.compare_instructions,
            **self.move_logical_instructions,
            **self.motion_instructions,
            **self.process_instructions,
            **self.safety_instructions,
            **self.comm_instructions,
            **self.array_instructions
        }
    
    async def get_instruction_for_operation(self, operation: str, context: str = "") -> Optional[str]:
        """Get the appropriate instruction for a given operation"""
        
        operation_lower = operation.lower()
        context_lower = context.lower()
        
        # Direct mapping lookup
        if operation_lower in self.all_instructions:
            return self.all_instructions[operation_lower]
        
        # Fuzzy matching for common operations
        fuzzy_mappings = {
            'start': 'OTE',
            'stop': 'OTU', 
            'turn on': 'OTE',
            'turn off': 'OTU',
            'enable': 'OTE',
            'disable': 'OTU',
            'delay': 'TON',
            'wait': 'TON',
            'count': 'CTU',
            'compare': 'EQU',
            'check': 'XIC',
            'monitor': 'XIC',
            'move': 'MAM' if 'motion' in context_lower else 'MOV',
            'position': 'MAM',
            'home': 'MAH',
            'jog': 'MAJ'
        }
        
        for key, instruction in fuzzy_mappings.items():
            if key in operation_lower:
                return instruction
        
        # Use MCP server to search for instruction if available
        if self.mcp_server:
            try:
                search_results = await self.mcp_server.search_instructions(operation)
                if search_results:
                    return search_results[0].get('name')
            except:
                pass
        
        return None

# This is just the beginning - we need to continue with the enhanced generator classes
# The file is getting long, so I'll create additional files for the other components

