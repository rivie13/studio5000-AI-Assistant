#!/usr/bin/env python3
"""
Enhanced Ladder Logic Generator for Industrial Warehouse Automation

This module generates sophisticated ladder logic for complex warehouse automation
scenarios using pattern matching and intelligent instruction selection.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from .enhanced_code_assistant import (
    EnhancedPLCRequirement, EnhancedGeneratedCode, IndustrialComponent, 
    AutomationSequence, LogicComplexity, IndustryDomain
)
from .warehouse_automation_patterns import WarehouseAutomationPatterns, WarehousePattern

class EnhancedLadderLogicGenerator:
    """Advanced ladder logic generator for warehouse automation"""
    
    def __init__(self, mcp_server=None):
        self.mcp_server = mcp_server
        self.warehouse_patterns = WarehouseAutomationPatterns()
        self._initialize_advanced_mappings()
    
    def _initialize_advanced_mappings(self):
        """Initialize advanced instruction mappings for warehouse automation"""
        
        # Motion control mappings for warehouse equipment
        self.motion_mappings = {
            'conveyor_control': {
                'start': 'OTE',
                'stop': 'OTU', 
                'speed_control': 'MOV',
                'position_control': 'MAM',
                'home': 'MAH'
            },
            'servo_positioning': {
                'absolute_move': 'MAM',
                'relative_move': 'MAM', 
                'jog': 'MAJ',
                'stop': 'MAS',
                'home': 'MAH',
                'gear': 'MAG'
            },
            'robot_control': {
                'move_joint': 'MAM',
                'move_linear': 'MAM',
                'gripper_close': 'OTE',
                'gripper_open': 'OTU'
            }
        }
        
        # Safety system mappings
        self.safety_mappings = {
            'emergency_stop': 'XIO',  # Normally closed contact
            'light_curtain': 'XIC',   # Normally open when clear
            'guard_switch': 'XIC',    # Normally open when closed
            'safety_mat': 'XIO',      # Normally closed when not activated
            'safety_relay': 'XIC'     # Normally open when energized
        }
        
        # Process control mappings for warehouse operations
        self.process_mappings = {
            'weighing': 'SCL',        # Scale weight values
            'counting': 'CTU',        # Count packages
            'sorting': 'EQU',         # Compare sort codes
            'tracking': 'MOV',        # Move tracking data
            'batching': 'ADD'         # Accumulate batch quantities
        }
        
        # Communication mappings for warehouse systems
        self.comm_mappings = {
            'barcode_scanner': 'MSG',     # Message instruction for scanner comm
            'wms_interface': 'PRODUCE',   # Produce data to WMS
            'hmi_update': 'CONSUME',      # Consume HMI commands
            'plc_to_plc': 'MSG'          # Inter-PLC communication
        }
    
    async def generate_from_requirements(self, requirements: EnhancedPLCRequirement) -> EnhancedGeneratedCode:
        """Generate enhanced ladder logic from structured requirements"""
        
        # Find matching warehouse patterns
        matching_patterns = self.warehouse_patterns.find_matching_patterns(requirements.description)
        
        if matching_patterns:
            return await self._generate_from_patterns(requirements, matching_patterns)
        else:
            return await self._generate_custom_logic(requirements)
    
    async def _generate_from_patterns(self, requirements: EnhancedPLCRequirement, 
                                    patterns: List[WarehousePattern]) -> EnhancedGeneratedCode:
        """Generate logic using warehouse automation patterns"""
        
        # Select the best matching pattern
        best_pattern = self._select_best_pattern(requirements, patterns)
        
        # Customize the pattern for specific requirements
        customized_logic = await self._customize_pattern(best_pattern, requirements)
        
        # Add safety logic if required
        if requirements.safety_requirements:
            safety_logic = self._generate_safety_logic(requirements.safety_requirements)
            customized_logic.safety_logic = safety_logic
        
        # Add performance optimizations
        if requirements.performance_requirements:
            self._optimize_for_performance(customized_logic, requirements.performance_requirements)
        
        return customized_logic
    
    def _select_best_pattern(self, requirements: EnhancedPLCRequirement, 
                           patterns: List[WarehousePattern]) -> WarehousePattern:
        """Select the best matching pattern based on requirements"""
        
        if len(patterns) == 1:
            return patterns[0]
        
        # Score patterns based on component matches
        pattern_scores = {}
        req_components = [comp.name.lower() for comp in requirements.components]
        
        for pattern in patterns:
            score = 0
            for pattern_comp in pattern.components:
                if any(pattern_comp.lower() in req_comp for req_comp in req_components):
                    score += 1
            pattern_scores[pattern] = score
        
        # Return highest scoring pattern
        return max(pattern_scores, key=pattern_scores.get)
    
    async def _customize_pattern(self, pattern: WarehousePattern, 
                               requirements: EnhancedPLCRequirement) -> EnhancedGeneratedCode:
        """Customize a warehouse pattern for specific requirements"""
        
        # Start with the pattern template
        ladder_logic = pattern.ladder_logic_template
        tags = pattern.required_tags.copy() if pattern.required_tags else []
        
        # Customize tag names based on requirements
        tag_mapping = self._create_tag_mapping(requirements, pattern)
        
        # Apply tag name customizations
        for old_tag, new_tag in tag_mapping.items():
            ladder_logic = ladder_logic.replace(old_tag, new_tag)
            # Update tag definitions
            for tag in tags:
                if tag['name'] == old_tag:
                    tag['name'] = new_tag
        
        # Add component-specific logic
        additional_logic = await self._generate_component_logic(requirements.components)
        if additional_logic:
            ladder_logic += "\n\n// Additional Component Logic\n" + additional_logic
        
        # Add sequence logic if present
        sequence_logic = self._generate_sequence_logic(requirements.sequences)
        if sequence_logic:
            ladder_logic += "\n\n// Sequence Control Logic\n" + sequence_logic
        
        # Validate instructions with MCP server
        instructions_used = self._extract_instructions_from_logic(ladder_logic)
        validation_notes = []
        if self.mcp_server:
            validation_notes = await self._validate_instructions(instructions_used)
        
        return EnhancedGeneratedCode(
            ladder_logic=ladder_logic,
            tags=tags,
            instructions_used=instructions_used,
            comments=[f"Generated from {pattern.name} pattern"],
            validation_notes=validation_notes,
            documentation=self._generate_documentation(pattern, requirements)
        )
    
    def _create_tag_mapping(self, requirements: EnhancedPLCRequirement, 
                          pattern: WarehousePattern) -> Dict[str, str]:
        """Create mapping from generic pattern tags to specific requirement tags"""
        
        tag_mapping = {}
        
        # Map component names to pattern tags
        for component in requirements.components:
            comp_name = component.name.upper()
            comp_type = component.component_type.lower()
            
            # Look for matching pattern components
            if comp_type == 'motor' and 'MOTOR' in pattern.ladder_logic_template:
                tag_mapping['CONV_MOTOR'] = f"{comp_name}_MOTOR"
                tag_mapping['CONV_RUN'] = f"{comp_name}_RUN"
            elif comp_type == 'sensor' and 'PHOTO' in pattern.ladder_logic_template:
                if 'upstream' in component.name.lower():
                    tag_mapping['PHOTO_UPSTREAM'] = comp_name
                elif 'downstream' in component.name.lower():
                    tag_mapping['PHOTO_DOWNSTREAM'] = comp_name
        
        return tag_mapping
    
    async def _generate_component_logic(self, components: List[IndustrialComponent]) -> str:
        """Generate logic specific to individual components"""
        
        logic_lines = []
        
        for component in components:
            comp_type = component.component_type.lower()
            comp_name = component.name.upper()
            
            if comp_type == 'servo_motor':
                # Add servo control logic
                logic_lines.append(f"// {comp_name} Servo Control")
                logic_lines.append(f"XIC({comp_name}_ENABLE) MAH({comp_name}_AXIS);")
                logic_lines.append(f"XIC({comp_name}_HOME_COMPLETE) OTE({comp_name}_READY);")
                
            elif comp_type == 'vfd':
                # Add VFD control logic
                logic_lines.append(f"// {comp_name} VFD Control")
                logic_lines.append(f"XIC({comp_name}_RUN_CMD) OTE({comp_name}_START);")
                logic_lines.append(f"MOV({comp_name}_SPEED_REF,{comp_name}_SPEED_CMD);")
                
            elif comp_type == 'safety_scanner':
                # Add safety scanner logic
                logic_lines.append(f"// {comp_name} Safety Scanner")
                logic_lines.append(f"XIC({comp_name}_FIELD_ON) XIO({comp_name}_WARNING) OTE({comp_name}_SAFE);")
                
            elif component.safety_critical:
                # Add safety-critical component monitoring
                logic_lines.append(f"// {comp_name} Safety Monitoring")
                logic_lines.append(f"XIC({comp_name}_OK) XIO({comp_name}_FAULT) OTE({comp_name}_SAFE);")
        
        return "\n".join(logic_lines) if logic_lines else ""
    
    def _generate_sequence_logic(self, sequences: List[AutomationSequence]) -> str:
        """Generate ladder logic for automation sequences"""
        
        if not sequences:
            return ""
        
        logic_lines = []
        
        for seq_idx, sequence in enumerate(sequences):
            seq_name = sequence.name.upper().replace(' ', '_')
            
            logic_lines.append(f"// {sequence.name} Sequence Control")
            
            # Generate step control logic
            for step_idx, step in enumerate(sequence.steps):
                step_num = step_idx + 1
                step_tag = f"{seq_name}_STEP_{step_num}"
                
                if step['type'] == 'condition':
                    # Condition step - wait for condition to be true
                    condition = self._parse_step_condition(step['description'])
                    logic_lines.append(f"XIC({seq_name}_ACTIVE) XIC({condition}) OTE({step_tag}_ACTIVE);")
                    
                elif step['type'] == 'action':
                    # Action step - perform action
                    action = self._parse_step_action(step['description'])
                    prev_step_tag = f"{seq_name}_STEP_{step_num-1}" if step_num > 1 else f"{seq_name}_START"
                    logic_lines.append(f"XIC({prev_step_tag}_ACTIVE) OTE({action});")
                    logic_lines.append(f"XIC({action}) TON({step_tag}_TIMER,1000,0);")
                    logic_lines.append(f"XIC({step_tag}_TIMER.DN) OTE({step_tag}_COMPLETE);")
            
            # Sequence completion logic
            last_step = len(sequence.steps)
            logic_lines.append(f"XIC({seq_name}_STEP_{last_step}_COMPLETE) OTE({seq_name}_COMPLETE);")
            logic_lines.append(f"XIC({seq_name}_COMPLETE) OTU({seq_name}_ACTIVE);")
            
            logic_lines.append("")  # Add blank line between sequences
        
        return "\n".join(logic_lines)
    
    def _parse_step_condition(self, description: str) -> str:
        """Parse step description to extract condition tag"""
        # Simple parsing - can be enhanced with NLP
        description_upper = description.upper().replace(' ', '_')
        return f"{description_upper}_OK"
    
    def _parse_step_action(self, description: str) -> str:
        """Parse step description to extract action tag"""
        # Simple parsing - can be enhanced with NLP
        description_upper = description.upper().replace(' ', '_')
        return f"{description_upper}_CMD"
    
    async def _generate_custom_logic(self, requirements: EnhancedPLCRequirement) -> EnhancedGeneratedCode:
        """Generate custom logic when no patterns match"""
        
        logic_lines = []
        tags = []
        instructions_used = []
        
        # Generate basic I/O logic
        if requirements.components:
            inputs = [comp for comp in requirements.components if comp.component_type in ['sensor', 'button', 'switch']]
            outputs = [comp for comp in requirements.components if comp.component_type in ['motor', 'valve', 'actuator']]
            
            if inputs and outputs:
                input_tag = inputs[0].name
                output_tag = outputs[0].name
                
                logic_lines.append(f"// Basic Input/Output Control")
                logic_lines.append(f"XIC({input_tag}) OTE({output_tag});")
                
                tags.extend([
                    {'name': input_tag, 'data_type': 'BOOL', 'description': f'{inputs[0].component_type} input'},
                    {'name': output_tag, 'data_type': 'BOOL', 'description': f'{outputs[0].component_type} output'}
                ])
                
                instructions_used.extend(['XIC', 'OTE'])
        
        # Add complexity-based enhancements
        if requirements.complexity in [LogicComplexity.COMPLEX, LogicComplexity.ADVANCED]:
            # Add state machine logic for complex requirements
            state_logic = self._generate_state_machine_logic(requirements)
            if state_logic:
                logic_lines.append("\n// State Machine Control")
                logic_lines.append(state_logic)
        
        ladder_logic = "\n".join(logic_lines) if logic_lines else "// No logic generated - requirements unclear"
        
        return EnhancedGeneratedCode(
            ladder_logic=ladder_logic,
            tags=tags,
            instructions_used=instructions_used,
            comments=["Custom generated logic"],
            validation_notes=["Manual review recommended for custom logic"]
        )
    
    def _generate_state_machine_logic(self, requirements: EnhancedPLCRequirement) -> str:
        """Generate state machine logic for complex requirements"""
        
        logic_lines = []
        
        # Define common states for warehouse operations
        states = ['IDLE', 'RUNNING', 'STOPPING', 'FAULT', 'MAINTENANCE']
        
        logic_lines.append("// State Machine Logic")
        logic_lines.append("// State Definitions: 0=IDLE, 1=RUNNING, 2=STOPPING, 3=FAULT, 4=MAINTENANCE")
        
        # State transition logic
        logic_lines.append("XIC(START_CMD) EQU(CURRENT_STATE,0) MOV(1,CURRENT_STATE);  // IDLE to RUNNING")
        logic_lines.append("XIC(STOP_CMD) EQU(CURRENT_STATE,1) MOV(2,CURRENT_STATE);   // RUNNING to STOPPING")
        logic_lines.append("XIC(FAULT_DETECTED) MOV(3,CURRENT_STATE);                  // Any state to FAULT")
        logic_lines.append("XIC(MAINT_MODE) MOV(4,CURRENT_STATE);                      // Any state to MAINTENANCE")
        
        # State-based outputs
        logic_lines.append("EQU(CURRENT_STATE,1) OTE(SYSTEM_RUNNING);                  // Running state output")
        logic_lines.append("EQU(CURRENT_STATE,3) OTE(FAULT_ALARM);                     // Fault state output")
        
        return "\n".join(logic_lines)
    
    def _generate_safety_logic(self, safety_requirements: List[str]) -> List[str]:
        """Generate comprehensive safety logic"""
        
        safety_logic = []
        
        # Emergency stop logic
        if any('emergency' in req.lower() for req in safety_requirements):
            safety_logic.append("XIC(E_STOP_1_OK) XIC(E_STOP_2_OK) OTE(E_STOP_CHAIN_OK);")
        
        # Light curtain logic
        if any('light curtain' in req.lower() for req in safety_requirements):
            safety_logic.append("XIC(LIGHT_CURTAIN_CLEAR) XIO(LC_BYPASS) OTE(LC_SAFE);")
        
        # Guard monitoring
        if any('guard' in req.lower() for req in safety_requirements):
            safety_logic.append("XIC(GUARD_CLOSED) XIC(GUARD_LOCKED) OTE(GUARD_SAFE);")
        
        # Master safety enable
        safety_logic.append("XIC(E_STOP_CHAIN_OK) XIC(LC_SAFE) XIC(GUARD_SAFE) OTE(SAFETY_OK);")
        
        return safety_logic
    
    def _optimize_for_performance(self, code: EnhancedGeneratedCode, 
                                performance_req: Dict[str, Any]):
        """Optimize generated code for performance requirements"""
        
        # Add performance monitoring
        if 'timing_ms' in performance_req:
            timing_values = performance_req['timing_ms']
            code.performance_metrics['cycle_time_target'] = min(timing_values)
        
        if 'speed_linear' in performance_req:
            speed_values = performance_req['speed_linear']
            code.performance_metrics['max_speed'] = max(speed_values)
        
        # Add performance-related tags
        perf_tags = [
            {'name': 'CYCLE_TIME', 'data_type': 'DINT', 'description': 'Current cycle time in ms'},
            {'name': 'PERFORMANCE_OK', 'data_type': 'BOOL', 'description': 'Performance within limits'}
        ]
        code.tags.extend(perf_tags)
    
    def _extract_instructions_from_logic(self, ladder_logic: str) -> List[str]:
        """Extract PLC instructions from ladder logic"""
        
        # Common Studio 5000 instruction patterns
        instruction_pattern = r'\b([A-Z]{2,4})\b'
        matches = re.findall(instruction_pattern, ladder_logic)
        
        # Filter to known instructions only
        known_instructions = {
            'XIC', 'XIO', 'OTE', 'OTL', 'OTU', 'OSR', 'OSF',
            'TON', 'TOF', 'RTO', 'RES', 'CTU', 'CTD',
            'ADD', 'SUB', 'MUL', 'DIV', 'MOV', 'COP',
            'EQU', 'NEQ', 'LES', 'LEQ', 'GRT', 'GEQ',
            'MAH', 'MAJ', 'MAM', 'MAS', 'MSG', 'GSV', 'SSV'
        }
        
        return list(set(match for match in matches if match in known_instructions))
    
    async def _validate_instructions(self, instructions: List[str]) -> List[str]:
        """Validate instructions using MCP server"""
        
        validation_notes = []
        
        for instruction in instructions:
            try:
                # Check if instruction exists in MCP database
                if hasattr(self.mcp_server, 'get_instruction'):
                    instruction_info = await self.mcp_server.get_instruction(instruction)
                    if instruction_info:
                        validation_notes.append(f"✓ {instruction} instruction validated")
                    else:
                        validation_notes.append(f"⚠ {instruction} instruction not found in documentation")
            except Exception as e:
                validation_notes.append(f"Validation error for {instruction}: {str(e)}")
        
        return validation_notes
    
    def _generate_documentation(self, pattern: WarehousePattern, 
                             requirements: EnhancedPLCRequirement) -> str:
        """Generate comprehensive documentation for the generated code"""
        
        doc_lines = []
        
        doc_lines.append(f"# {pattern.name}")
        doc_lines.append(f"## Description")
        doc_lines.append(pattern.description)
        doc_lines.append("")
        
        doc_lines.append("## Requirements")
        doc_lines.append(f"- Domain: {requirements.domain.value}")
        doc_lines.append(f"- Complexity: {requirements.complexity.value}")
        doc_lines.append(f"- Logic Type: {requirements.logic_type}")
        doc_lines.append("")
        
        if requirements.components:
            doc_lines.append("## Components")
            for comp in requirements.components:
                safety_note = " (Safety Critical)" if comp.safety_critical else ""
                doc_lines.append(f"- {comp.name}: {comp.component_type}{safety_note}")
            doc_lines.append("")
        
        if pattern.safety_considerations:
            doc_lines.append("## Safety Considerations")
            for consideration in pattern.safety_considerations:
                doc_lines.append(f"- {consideration}")
            doc_lines.append("")
        
        if requirements.performance_requirements:
            doc_lines.append("## Performance Requirements")
            for key, value in requirements.performance_requirements.items():
                doc_lines.append(f"- {key}: {value}")
        
        return "\n".join(doc_lines)

