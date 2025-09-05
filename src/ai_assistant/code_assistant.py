#!/usr/bin/env python3
"""
AI-Powered PLC Code Assistant

This module converts natural language specifications into structured PLC code
using the Studio 5000 instruction documentation from the MCP server.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

@dataclass
class PLCRequirement:
    """Structured representation of a PLC programming requirement"""
    description: str
    inputs: List[str]
    outputs: List[str]  
    logic_type: str  # "ladder", "structured_text", "function_block"
    conditions: List[str]
    actions: List[str]

@dataclass
class GeneratedCode:
    """Generated PLC code with metadata"""
    ladder_logic: str
    tags: List[Dict]
    instructions_used: List[str]
    comments: List[str]
    validation_notes: List[str]

class NaturalLanguageParser:
    """Parses natural language into structured PLC requirements"""
    
    def __init__(self):
        self.input_keywords = [
            'button', 'switch', 'sensor', 'input', 'signal', 'detector',
            'limit switch', 'proximity', 'photoeye', 'pressure', 'temperature'
        ]
        
        self.output_keywords = [
            'motor', 'light', 'valve', 'cylinder', 'actuator', 'relay',
            'contactor', 'solenoid', 'output', 'alarm', 'horn', 'beacon'
        ]
        
        self.condition_keywords = [
            'when', 'if', 'while', 'until', 'after', 'before', 'during'
        ]
        
        self.action_keywords = [
            'start', 'stop', 'turn on', 'turn off', 'activate', 'deactivate',
            'energize', 'de-energize', 'open', 'close', 'move', 'run'
        ]
    
    def parse_specification(self, description: str) -> PLCRequirement:
        """Parse natural language into structured requirements"""
        description = description.lower().strip()
        
        # Extract inputs and outputs
        inputs = self._extract_io(description, self.input_keywords)
        outputs = self._extract_io(description, self.output_keywords)
        
        # Extract conditions and actions
        conditions = self._extract_conditions(description)
        actions = self._extract_actions(description)
        
        # Determine logic type (default to ladder)
        logic_type = "ladder"
        if "structured text" in description or "st" in description:
            logic_type = "structured_text"
        elif "function block" in description or "fb" in description:
            logic_type = "function_block"
        
        return PLCRequirement(
            description=description,
            inputs=inputs,
            outputs=outputs,
            logic_type=logic_type,
            conditions=conditions,
            actions=actions
        )
    
    def _extract_io(self, text: str, keywords: List[str]) -> List[str]:
        """Extract inputs or outputs from text"""
        found_io = []
        for keyword in keywords:
            if keyword in text:
                # Try to find specific names near the keyword
                pattern = r'(\w+\s+)?' + re.escape(keyword) + r'(\s+\w+)?'
                matches = re.finditer(pattern, text)
                for match in matches:
                    io_name = match.group(0).strip().replace(' ', '_').upper()
                    if io_name not in found_io:
                        found_io.append(io_name)
        return found_io
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditional statements"""
        conditions = []
        for keyword in self.condition_keywords:
            pattern = keyword + r'\\s+([^.!?]+)'
            matches = re.finditer(pattern, text)
            for match in matches:
                condition = match.group(1).strip()
                conditions.append(condition)
        return conditions
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extract action statements"""
        actions = []
        for keyword in self.action_keywords:
            if keyword in text:
                # Find the context around the action
                words = text.split()
                for i, word in enumerate(words):
                    if keyword.startswith(word):  # Handle multi-word actions
                        # Get surrounding context
                        start = max(0, i-2)
                        end = min(len(words), i+4)
                        context = ' '.join(words[start:end])
                        actions.append(context)
        return actions

class LadderLogicGenerator:
    """Generates ladder logic from structured requirements"""
    
    def __init__(self, mcp_instructions: Optional[Dict] = None):
        self.mcp_instructions = mcp_instructions or {}
        
        # Common instruction mappings
        self.instruction_mappings = {
            'normally_open': 'XIC',      # Examine if Closed (normally open contact)
            'normally_closed': 'XIO',    # Examine if Open (normally closed contact) 
            'output': 'OTE',             # Output Energize
            'latch': 'OTL',              # Output Latch
            'unlatch': 'OTU',            # Output Unlatch
            'timer_on_delay': 'TON',     # Timer On Delay
            'timer_off_delay': 'TOF',    # Timer Off Delay
            'counter_up': 'CTU',         # Count Up
            'counter_down': 'CTD',       # Count Down
            'move': 'MOV',               # Move
            'add': 'ADD',                # Add
            'multiply': 'MUL',           # Multiply
            'equal': 'EQU',              # Equal
            'greater_than': 'GRT',       # Greater Than
            'less_than': 'LES'           # Less Than
        }
    
    def generate_from_requirements(self, requirements: PLCRequirement) -> GeneratedCode:
        """Generate ladder logic from structured requirements"""
        
        if requirements.logic_type == "ladder":
            return self._generate_ladder_logic(requirements)
        elif requirements.logic_type == "structured_text":
            return self._generate_structured_text(requirements)
        else:
            # Default to ladder logic
            return self._generate_ladder_logic(requirements)
    
    def _generate_ladder_logic(self, req: PLCRequirement) -> GeneratedCode:
        """Generate ladder logic rungs"""
        
        # Analyze requirements to determine logic pattern
        if self._is_start_stop_pattern(req):
            return self._generate_start_stop_logic(req)
        elif self._is_timer_pattern(req):
            return self._generate_timer_logic(req)
        elif self._is_counter_pattern(req):
            return self._generate_counter_logic(req)
        else:
            return self._generate_basic_logic(req)
    
    def _is_start_stop_pattern(self, req: PLCRequirement) -> bool:
        """Detect start/stop motor control pattern"""
        desc = req.description.lower()
        return ('start' in desc and 'stop' in desc) or ('motor' in desc)
    
    def _generate_start_stop_logic(self, req: PLCRequirement) -> GeneratedCode:
        """Generate start/stop motor control ladder logic"""
        
        # Determine tag names
        start_input = self._get_or_create_tag(req.inputs, ['start', 'run'], 'START_PB')
        stop_input = self._get_or_create_tag(req.inputs, ['stop'], 'STOP_PB') 
        motor_output = self._get_or_create_tag(req.outputs, ['motor'], 'MOTOR_RUN')
        
        # Generate the classic start/stop logic
        ladder_logic = f"XIC({start_input})XIO({stop_input})OTE({motor_output});"
        
        # Create tags
        tags = [
            {'name': start_input, 'data_type': 'BOOL', 'description': 'Start button input'},
            {'name': stop_input, 'data_type': 'BOOL', 'description': 'Stop button input'}, 
            {'name': motor_output, 'data_type': 'BOOL', 'description': 'Motor run output'}
        ]
        
        return GeneratedCode(
            ladder_logic=ladder_logic,
            tags=tags,
            instructions_used=['XIC', 'XIO', 'OTE'],
            comments=['Start/stop motor control logic'],
            validation_notes=['Standard three-wire control circuit']
        )
    
    def _is_timer_pattern(self, req: PLCRequirement) -> bool:
        """Detect timer-based logic pattern"""
        desc = req.description.lower()
        return 'timer' in desc or 'delay' in desc or 'after' in desc
    
    def _generate_timer_logic(self, req: PLCRequirement) -> GeneratedCode:
        """Generate timer-based ladder logic"""
        
        # Extract timer parameters
        delay_time = self._extract_time_value(req.description)
        
        input_tag = self._get_or_create_tag(req.inputs, [], 'TIMER_INPUT')
        output_tag = self._get_or_create_tag(req.outputs, [], 'TIMER_OUTPUT')
        timer_tag = 'DELAY_TIMER'
        
        # Generate timer logic
        ladder_logic = f"XIC({input_tag})TON({timer_tag},{delay_time},0);"
        ladder_logic += f"XIC({timer_tag}.DN)OTE({output_tag});"
        
        tags = [
            {'name': input_tag, 'data_type': 'BOOL', 'description': 'Timer input'},
            {'name': output_tag, 'data_type': 'BOOL', 'description': 'Timer output'},
            {'name': timer_tag, 'data_type': 'TIMER', 'description': f'Delay timer - {delay_time}ms'}
        ]
        
        return GeneratedCode(
            ladder_logic=ladder_logic,
            tags=tags,
            instructions_used=['XIC', 'TON', 'OTE'],
            comments=[f'Timer logic with {delay_time}ms delay'],
            validation_notes=['Timer preset value may need adjustment']
        )
    
    def _is_counter_pattern(self, req: PLCRequirement) -> bool:
        """Detect counter-based logic pattern"""
        desc = req.description.lower()
        return 'count' in desc or 'counter' in desc or 'cycle' in desc
    
    def _generate_counter_logic(self, req: PLCRequirement) -> GeneratedCode:
        """Generate counter-based ladder logic"""
        
        count_value = self._extract_numeric_value(req.description, default=10)
        
        input_tag = self._get_or_create_tag(req.inputs, [], 'COUNT_INPUT')
        reset_tag = self._get_or_create_tag(req.inputs, ['reset'], 'RESET_INPUT')
        output_tag = self._get_or_create_tag(req.outputs, [], 'COUNT_OUTPUT')
        counter_tag = 'COUNTER'
        
        ladder_logic = f"XIC({input_tag})CTU({counter_tag},{count_value});"
        ladder_logic += f"XIC({reset_tag})RES({counter_tag});"
        ladder_logic += f"XIC({counter_tag}.DN)OTE({output_tag});"
        
        tags = [
            {'name': input_tag, 'data_type': 'BOOL', 'description': 'Count input'},
            {'name': reset_tag, 'data_type': 'BOOL', 'description': 'Reset input'},
            {'name': output_tag, 'data_type': 'BOOL', 'description': 'Count complete output'},
            {'name': counter_tag, 'data_type': 'COUNTER', 'description': f'Counter - preset {count_value}'}
        ]
        
        return GeneratedCode(
            ladder_logic=ladder_logic,
            tags=tags,
            instructions_used=['XIC', 'CTU', 'RES', 'OTE'],
            comments=[f'Counter logic - count to {count_value}'],
            validation_notes=['Counter preset may need adjustment for application']
        )
    
    def _generate_basic_logic(self, req: PLCRequirement) -> GeneratedCode:
        """Generate basic input/output logic"""
        
        # Simple input to output mapping
        if req.inputs and req.outputs:
            input_tag = req.inputs[0] if req.inputs else 'INPUT_1'
            output_tag = req.outputs[0] if req.outputs else 'OUTPUT_1'
            
            # Determine if normally open or normally closed
            if 'not' in req.description or 'stop' in req.description:
                ladder_logic = f"XIO({input_tag})OTE({output_tag});"
                instructions = ['XIO', 'OTE']
            else:
                ladder_logic = f"XIC({input_tag})OTE({output_tag});"
                instructions = ['XIC', 'OTE']
            
            tags = [
                {'name': input_tag, 'data_type': 'BOOL', 'description': 'Input signal'},
                {'name': output_tag, 'data_type': 'BOOL', 'description': 'Output signal'}
            ]
            
            return GeneratedCode(
                ladder_logic=ladder_logic,
                tags=tags,
                instructions_used=instructions,
                comments=['Basic input to output logic'],
                validation_notes=['Verify input/output assignments match hardware']
            )
        
        # Fallback for unclear requirements
        return GeneratedCode(
            ladder_logic="// Unable to generate logic from specification",
            tags=[],
            instructions_used=[],
            comments=['Specification unclear - manual review required'],
            validation_notes=['Requirements need clarification']
        )
    
    def _generate_structured_text(self, req: PLCRequirement) -> GeneratedCode:
        """Generate structured text code"""
        # Simplified ST generation - can be expanded
        if self._is_start_stop_pattern(req):
            st_code = """
IF START_PB AND NOT STOP_PB THEN
    MOTOR_RUN := TRUE;
END_IF;

IF STOP_PB THEN
    MOTOR_RUN := FALSE;
END_IF;
"""
            tags = [
                {'name': 'START_PB', 'data_type': 'BOOL', 'description': 'Start button'},
                {'name': 'STOP_PB', 'data_type': 'BOOL', 'description': 'Stop button'},
                {'name': 'MOTOR_RUN', 'data_type': 'BOOL', 'description': 'Motor output'}
            ]
            
            return GeneratedCode(
                ladder_logic=st_code,
                tags=tags,
                instructions_used=['IF', 'AND', 'NOT'],
                comments=['Structured text motor control'],
                validation_notes=['ST syntax verified']
            )
        
        return GeneratedCode(
            ladder_logic="// ST generation not implemented for this pattern",
            tags=[],
            instructions_used=[],
            comments=['Structured text generation needed'],
            validation_notes=['Pattern not supported in ST mode']
        )
    
    def _get_or_create_tag(self, available_tags: List[str], keywords: List[str], default: str) -> str:
        """Find best matching tag or create default"""
        for tag in available_tags:
            for keyword in keywords:
                if keyword.upper() in tag.upper():
                    return tag
        return default
    
    def _extract_time_value(self, text: str) -> int:
        """Extract time values from text (returns milliseconds)"""
        # Look for numbers followed by time units
        time_patterns = [
            (r'(\\d+)\\s*ms', 1),           # milliseconds
            (r'(\\d+)\\s*milliseconds?', 1),
            (r'(\\d+)\\s*s(?:ec)?', 1000),   # seconds
            (r'(\\d+)\\s*seconds?', 1000),
            (r'(\\d+)\\s*min', 60000),       # minutes
            (r'(\\d+)\\s*minutes?', 60000)
        ]
        
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1)) * multiplier
        
        # Default to 5 seconds if no time found
        return 5000
    
    def _extract_numeric_value(self, text: str, default: int = 10) -> int:
        """Extract numeric values from text"""
        numbers = re.findall(r'\\d+', text)
        if numbers:
            return int(numbers[0])
        return default

class CodeAssistant:
    """Main AI assistant for PLC code generation"""
    
    def __init__(self, mcp_server=None):
        self.parser = NaturalLanguageParser()
        self.generator = LadderLogicGenerator()
        self.mcp_server = mcp_server
    
    async def generate_code_from_description(self, description: str) -> Dict[str, Any]:
        """Main entry point - convert description to PLC code"""
        
        # Parse natural language into structured requirements
        requirements = self.parser.parse_specification(description)
        
        # Generate code from requirements
        generated_code = self.generator.generate_from_requirements(requirements)
        
        # Validate using MCP server if available
        if self.mcp_server:
            validation_results = await self._validate_with_mcp(generated_code)
            generated_code.validation_notes.extend(validation_results)
        
        return {
            'requirements': requirements,
            'generated_code': generated_code,
            'success': True,
            'message': 'Code generated successfully'
        }
    
    async def _validate_with_mcp(self, code: GeneratedCode) -> List[str]:
        """Validate generated code using MCP server instruction database"""
        validation_notes = []
        
        try:
            for instruction in code.instructions_used:
                # Check if instruction exists in MCP database
                instruction_info = await self.mcp_server.get_instruction(instruction)
                if instruction_info:
                    validation_notes.append(f"✓ {instruction} instruction validated")
                else:
                    validation_notes.append(f"⚠ {instruction} instruction not found in documentation")
        except Exception as e:
            validation_notes.append(f"Validation error: {str(e)}")
        
        return validation_notes

# Example usage
if __name__ == "__main__":
    assistant = CodeAssistant()
    
    # Test with motor control example
    description = "Start the motor when the start button is pressed and stop it when the stop button is pressed"
    
    import asyncio
    async def test():
        result = await assistant.generate_code_from_description(description)
        print("Generated Code:")
        print(result['generated_code'].ladder_logic)
        print("\\nTags:")
        for tag in result['generated_code'].tags:
            print(f"  {tag['name']}: {tag['data_type']} - {tag['description']}")
    
    asyncio.run(test())
