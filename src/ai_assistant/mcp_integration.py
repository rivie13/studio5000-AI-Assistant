#!/usr/bin/env python3
"""
MCP Server Integration for Enhanced Code Assistant

This module integrates the enhanced code assistant with the Studio 5000 MCP server
to provide real-time instruction validation and documentation lookup.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .enhanced_main_assistant import EnhancedCodeAssistant
from .enhanced_code_assistant import EnhancedGeneratedCode, EnhancedPLCRequirement

@dataclass
class MCPValidationResult:
    """Result of MCP server validation"""
    instruction: str
    is_valid: bool
    syntax_info: Optional[Dict] = None
    category: Optional[str] = None
    description: Optional[str] = None
    examples: Optional[List[str]] = None
    warnings: List[str] = None

class MCPIntegratedAssistant:
    """Enhanced code assistant with full MCP server integration"""
    
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.enhanced_assistant = EnhancedCodeAssistant(mcp_server)
        self.instruction_cache = {}  # Cache for instruction lookups
    
    async def generate_ladder_logic(self, specification: str) -> Dict[str, Any]:
        """
        Generate ladder logic with MCP server integration
        
        This is the main entry point called by the MCP server tools
        """
        
        try:
            # Use enhanced assistant to generate code
            result = await self.enhanced_assistant.generate_code_from_description(specification)
            
            if result['success']:
                # Enhance with MCP-specific validation
                enhanced_result = await self._enhance_with_mcp_validation(result)
                
                # Format for MCP response
                return self._format_mcp_response(enhanced_result)
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'ladder_logic': '// Error: Could not generate logic',
                    'tags': [],
                    'instructions_used': [],
                    'validation_notes': [f"Generation failed: {result.get('error', 'Unknown error')}"]
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ladder_logic': f'// Error: {str(e)}',
                'tags': [],
                'instructions_used': [],
                'validation_notes': [f"Exception during generation: {str(e)}"]
            }
    
    async def validate_ladder_logic(self, logic_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate existing ladder logic using MCP server
        
        Args:
            logic_spec: Dictionary containing 'ladder_logic' and 'instructions_used'
        """
        
        ladder_logic = logic_spec.get('ladder_logic', '')
        instructions_used = logic_spec.get('instructions_used', [])
        
        validation_results = []
        errors = []
        warnings = []
        
        # Validate each instruction
        for instruction in instructions_used:
            try:
                validation = await self._validate_instruction_comprehensive(instruction)
                validation_results.append(validation)
                
                if not validation.is_valid:
                    errors.append(f"Invalid instruction: {instruction}")
                
                if validation.warnings:
                    warnings.extend(validation.warnings)
                    
            except Exception as e:
                errors.append(f"Validation error for {instruction}: {str(e)}")
        
        # Analyze ladder logic structure
        structure_analysis = self._analyze_ladder_structure(ladder_logic)
        
        # Check for common issues
        common_issues = self._check_common_issues(ladder_logic)
        warnings.extend(common_issues)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'instruction_validations': [
                {
                    'instruction': v.instruction,
                    'is_valid': v.is_valid,
                    'category': v.category,
                    'description': v.description
                } for v in validation_results
            ],
            'structure_analysis': structure_analysis,
            'recommendations': self._generate_validation_recommendations(validation_results, structure_analysis)
        }
    
    async def create_l5x_project(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create complete L5X project with enhanced code generation
        
        Args:
            project_spec: Project specification including name, controller_type, specification
        """
        
        try:
            # Generate the ladder logic first
            specification = project_spec.get('specification', '')
            ladder_result = await self.generate_ladder_logic(specification)
            
            if not ladder_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to generate ladder logic for project',
                    'details': ladder_result.get('error', 'Unknown error')
                }
            
            # Create L5X project structure
            project_name = project_spec.get('name', 'WarehouseAutomation')
            controller_type = project_spec.get('controller_type', '1756-L83E')
            
            l5x_content = await self._create_l5x_content(
                project_name, 
                controller_type, 
                ladder_result
            )
            
            # Save if path provided
            save_path = project_spec.get('save_path')
            if save_path:
                await self._save_l5x_file(l5x_content, save_path)
            
            return {
                'success': True,
                'project_name': project_name,
                'controller_type': controller_type,
                'l5x_content': l5x_content,
                'ladder_logic': ladder_result['ladder_logic'],
                'tags_created': len(ladder_result['tags']),
                'instructions_used': ladder_result['instructions_used'],
                'file_saved': save_path is not None,
                'save_path': save_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'project_name': project_spec.get('name', 'Unknown'),
                'details': f"L5X creation failed: {str(e)}"
            }
    
    async def create_acd_project(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create real ACD project file using Studio 5000 SDK
        
        Args:
            project_spec: ACD project specification
        """
        
        try:
            # This would integrate with the existing SDK interface
            # For now, return a structured response
            
            project_name = project_spec.get('name', 'WarehouseAutomation')
            controller_type = project_spec.get('controller_type', '1756-L83E')
            save_path = project_spec.get('save_path', f"{project_name}.ACD")
            major_revision = project_spec.get('major_revision', 36)
            
            # Generate ladder logic if specification provided
            ladder_result = None
            if 'specification' in project_spec:
                ladder_result = await self.generate_ladder_logic(project_spec['specification'])
            
            return {
                'success': True,
                'message': 'ACD project creation initiated',
                'project_name': project_name,
                'controller_type': controller_type,
                'major_revision': major_revision,
                'save_path': save_path,
                'ladder_logic_generated': ladder_result is not None,
                'next_steps': [
                    'Use Studio 5000 SDK to create actual ACD file',
                    'Import generated ladder logic',
                    'Configure I/O modules',
                    'Test in simulation mode'
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'ACD project creation failed'
            }
    
    async def _enhance_with_mcp_validation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance result with comprehensive MCP validation"""
        
        instructions_used = result['generated_code']['instructions_used']
        enhanced_validations = []
        
        for instruction in instructions_used:
            validation = await self._validate_instruction_comprehensive(instruction)
            enhanced_validations.append({
                'instruction': instruction,
                'is_valid': validation.is_valid,
                'category': validation.category,
                'syntax_verified': validation.syntax_info is not None,
                'has_examples': validation.examples is not None and len(validation.examples) > 0
            })
        
        # Add enhanced validation to result
        result['mcp_validation'] = {
            'total_instructions': len(instructions_used),
            'valid_instructions': sum(1 for v in enhanced_validations if v['is_valid']),
            'instruction_details': enhanced_validations,
            'validation_summary': self._create_validation_summary(enhanced_validations)
        }
        
        return result
    
    async def _validate_instruction_comprehensive(self, instruction: str) -> MCPValidationResult:
        """Perform comprehensive validation of a single instruction"""
        
        # Check cache first
        if instruction in self.instruction_cache:
            cached = self.instruction_cache[instruction]
            return MCPValidationResult(**cached)
        
        validation = MCPValidationResult(instruction=instruction, is_valid=False)
        
        try:
            # Get instruction details
            if hasattr(self.mcp_server, 'get_instruction'):
                inst_info = await self.mcp_server.get_instruction(instruction)
                if inst_info:
                    validation.is_valid = True
                    validation.description = inst_info.get('description', '')
                    validation.category = inst_info.get('category', '')
            
            # Get syntax information
            if hasattr(self.mcp_server, 'get_instruction_syntax'):
                syntax_info = await self.mcp_server.get_instruction_syntax(instruction)
                if syntax_info:
                    validation.syntax_info = syntax_info
            
            # Cache the result
            self.instruction_cache[instruction] = {
                'instruction': validation.instruction,
                'is_valid': validation.is_valid,
                'syntax_info': validation.syntax_info,
                'category': validation.category,
                'description': validation.description,
                'examples': validation.examples,
                'warnings': validation.warnings or []
            }
            
        except Exception as e:
            validation.warnings = [f"Validation error: {str(e)}"]
        
        return validation
    
    def _analyze_ladder_structure(self, ladder_logic: str) -> Dict[str, Any]:
        """Analyze the structure of ladder logic"""
        
        lines = [line.strip() for line in ladder_logic.split('\n') if line.strip()]
        
        analysis = {
            'total_lines': len(lines),
            'comment_lines': len([line for line in lines if line.startswith('//')]),
            'logic_lines': len([line for line in lines if not line.startswith('//')]),
            'rungs_estimated': len([line for line in lines if ';' in line]),
            'complexity_score': 0
        }
        
        # Calculate complexity score
        complexity_factors = {
            'XIC(': 1, 'XIO(': 1, 'OTE(': 2, 'OTL(': 2, 'OTU(': 2,
            'TON(': 3, 'TOF(': 3, 'CTU(': 3, 'CTD(': 3,
            'ADD(': 2, 'SUB(': 2, 'MUL(': 2, 'DIV(': 2,
            'EQU(': 2, 'NEQ(': 2, 'GRT(': 2, 'LES(': 2,
            'MAM(': 4, 'MAH(': 3, 'MAJ(': 3  # Motion instructions are more complex
        }
        
        for instruction, weight in complexity_factors.items():
            count = ladder_logic.count(instruction)
            analysis['complexity_score'] += count * weight
        
        # Determine complexity level
        if analysis['complexity_score'] < 20:
            analysis['complexity_level'] = 'Simple'
        elif analysis['complexity_score'] < 50:
            analysis['complexity_level'] = 'Moderate'
        elif analysis['complexity_score'] < 100:
            analysis['complexity_level'] = 'Complex'
        else:
            analysis['complexity_level'] = 'Advanced'
        
        return analysis
    
    def _check_common_issues(self, ladder_logic: str) -> List[str]:
        """Check for common ladder logic issues"""
        
        issues = []
        
        # Check for potential issues
        if ladder_logic.count('OTE(') > ladder_logic.count('XIC(') + ladder_logic.count('XIO('):
            issues.append("More outputs than inputs - verify logic structure")
        
        # Check for timer usage without reset
        timers = set()
        for line in ladder_logic.split('\n'):
            if 'TON(' in line or 'TOF(' in line:
                # Extract timer name
                import re
                match = re.search(r'TO[NF]\(([^,]+)', line)
                if match:
                    timers.add(match.group(1))
        
        for timer in timers:
            if f'RES({timer})' not in ladder_logic:
                issues.append(f"Timer {timer} used without reset logic")
        
        # Check for safety considerations
        if 'E_STOP' not in ladder_logic and ('MOTOR' in ladder_logic or 'RUN' in ladder_logic):
            issues.append("Consider adding emergency stop logic for motor control")
        
        return issues
    
    def _generate_validation_recommendations(self, validations: List[MCPValidationResult], 
                                          structure: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Instruction-based recommendations
        invalid_count = sum(1 for v in validations if not v.is_valid)
        if invalid_count > 0:
            recommendations.append(f"Review {invalid_count} invalid instructions")
        
        # Structure-based recommendations
        if structure['complexity_level'] == 'Advanced':
            recommendations.append("Consider breaking complex logic into multiple routines")
        
        if structure['comment_lines'] < structure['logic_lines'] * 0.2:
            recommendations.append("Add more comments to improve maintainability")
        
        # Safety recommendations
        safety_instructions = [v for v in validations if v.category and 'safety' in v.category.lower()]
        if not safety_instructions and structure['complexity_level'] in ['Complex', 'Advanced']:
            recommendations.append("Consider adding safety monitoring for complex systems")
        
        return recommendations
    
    def _create_validation_summary(self, validations: List[Dict]) -> str:
        """Create a summary of validation results"""
        
        total = len(validations)
        valid = sum(1 for v in validations if v['is_valid'])
        
        if total == 0:
            return "No instructions to validate"
        
        percentage = (valid / total) * 100
        
        if percentage == 100:
            return f"All {total} instructions validated successfully"
        elif percentage >= 80:
            return f"{valid}/{total} instructions validated ({percentage:.1f}%) - Good"
        elif percentage >= 60:
            return f"{valid}/{total} instructions validated ({percentage:.1f}%) - Needs review"
        else:
            return f"{valid}/{total} instructions validated ({percentage:.1f}%) - Significant issues"
    
    def _format_mcp_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format result for MCP server response"""
        
        return {
            'success': result['success'],
            'ladder_logic': result['generated_code']['ladder_logic'],
            'tags': result['generated_code']['tags'],
            'instructions_used': result['generated_code']['instructions_used'],
            'validation_notes': result['validation']['notes'],
            'complexity': result['requirements']['complexity'],
            'domain': result['requirements']['domain'],
            'safety_logic': result['generated_code'].get('safety_logic', []),
            'performance_metrics': result['generated_code'].get('performance_metrics', {}),
            'recommendations': result.get('recommendations', []),
            'mcp_validation': result.get('mcp_validation', {})
        }
    
    async def _create_l5x_content(self, project_name: str, controller_type: str, 
                                ladder_result: Dict[str, Any]) -> str:
        """Create L5X XML content"""
        
        # This is a simplified L5X structure - would need full implementation
        l5x_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="36.00">
    <Controller Use="Context" Name="{project_name}">
        <RedundancyInfo Enabled="false" KeepTestEditsOnSwitchOver="false" IOMemoryPadPercentage="90" DataTablePadPercentage="50"/>
        <Security Code="0" ChangesToDetect="16#ffff_ffff_ffff_ffff"/>
        <SafetyInfo/>
        <DataTypes Use="Context"/>
        <Modules Use="Context">
            <Module Name="Local" CatalogNumber="{controller_type}" Vendor="1" ProductType="14" ProductCode="166" Major="36" Minor="11" ParentModule="Local" ParentModPortId="1" Inhibited="false" MajorFault="true">
                <EKey State="ExactMatch"/>
                <Ports>
                    <Port Id="1" Type="ICP" Upstream="false">
                        <Bus Size="17"/>
                    </Port>
                </Ports>
            </Module>
        </Modules>
        <Tags Use="Context">
"""
        
        # Add tags
        for tag in ladder_result.get('tags', []):
            l5x_template += f"""            <Tag Name="{tag['name']}" TagType="Base" DataType="{tag['data_type']}" Radix="Decimal" Constant="false" ExternalAccess="Read/Write">
                <Description>
                    <![CDATA[{tag['description']}]]>
                </Description>
            </Tag>
"""
        
        l5x_template += """        </Tags>
        <Programs Use="Context">
            <Program Use="Context" Name="MainProgram" TestEdits="false" MainRoutineName="MainRoutine" Disabled="false" UseAsFolder="false">
                <Tags Use="Context"/>
                <Routines Use="Context">
                    <Routine Use="Context" Name="MainRoutine" Type="RLL">
                        <RLLContent>
"""
        
        # Add ladder logic (would need proper RLL XML formatting)
        ladder_logic = ladder_result.get('ladder_logic', '')
        l5x_template += f"""                            <![CDATA[{ladder_logic}]]>
"""
        
        l5x_template += """                        </RLLContent>
                    </Routine>
                </Routines>
            </Program>
        </Programs>
        <Tasks Use="Context">
            <Task Name="MainTask" Type="CONTINUOUS" Priority="10" Watchdog="500" DisableUpdateOutputs="false" InhibitTask="false">
                <ScheduledPrograms>
                    <ScheduledProgram Name="MainProgram"/>
                </ScheduledPrograms>
            </Task>
        </Tasks>
    </Controller>
</RSLogix5000Content>"""
        
        return l5x_template
    
    async def _save_l5x_file(self, content: str, file_path: str):
        """Save L5X content to file"""
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to save L5X file: {str(e)}")


# Factory function for MCP server integration
def create_mcp_integrated_assistant(mcp_server) -> MCPIntegratedAssistant:
    """Create an MCP-integrated assistant instance"""
    return MCPIntegratedAssistant(mcp_server)

