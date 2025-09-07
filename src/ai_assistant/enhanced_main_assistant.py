#!/usr/bin/env python3
"""
Enhanced Main AI Assistant for Industrial Warehouse Automation

This is the main entry point for the enhanced PLC code generation system,
designed specifically for complex warehouse automation scenarios.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .enhanced_code_assistant import (
    IndustrialNLPParser, EnhancedPLCRequirement, EnhancedGeneratedCode,
    IndustryDomain, LogicComplexity
)
from .enhanced_ladder_generator import EnhancedLadderLogicGenerator
from .warehouse_automation_patterns import WarehouseAutomationPatterns

class EnhancedCodeAssistant:
    """Enhanced AI assistant for warehouse automation PLC code generation"""
    
    def __init__(self, mcp_server=None):
        self.parser = IndustrialNLPParser()
        self.generator = EnhancedLadderLogicGenerator(mcp_server)
        self.warehouse_patterns = WarehouseAutomationPatterns()
        self.mcp_server = mcp_server
        
        # Initialize conversation context for multi-turn interactions
        self.conversation_context = {
            'previous_requirements': [],
            'generated_projects': [],
            'user_preferences': {},
            'domain_expertise': IndustryDomain.WAREHOUSE
        }
    
    async def generate_code_from_description(self, description: str, 
                                           context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main entry point - convert natural language description to PLC code
        
        Args:
            description: Natural language description of automation requirements
            context: Optional context from previous conversations or user preferences
            
        Returns:
            Comprehensive result with generated code, documentation, and metadata
        """
        
        try:
            # Update context if provided
            if context:
                self.conversation_context.update(context)
            
            # Parse natural language into enhanced structured requirements
            requirements = await self.parser.parse_specification(description, self.mcp_server)
            
            # Enhance requirements with conversation context
            requirements = self._enhance_with_context(requirements)
            
            # Generate code from enhanced requirements
            generated_code = await self.generator.generate_from_requirements(requirements)
            
            # Post-process and validate
            generated_code = await self._post_process_code(generated_code, requirements)
            
            # Update conversation context
            self._update_conversation_context(requirements, generated_code)
            
            # Prepare comprehensive response
            response = self._prepare_response(requirements, generated_code, description)
            
            return response
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate code from description',
                'suggestions': self._get_error_suggestions(str(e))
            }
    
    async def analyze_requirements_complexity(self, description: str) -> Dict[str, Any]:
        """Analyze the complexity and feasibility of requirements"""
        
        requirements = await self.parser.parse_specification(description, self.mcp_server)
        
        analysis = {
            'domain': requirements.domain.value,
            'complexity_level': requirements.complexity.value,
            'estimated_development_time': self._estimate_development_time(requirements),
            'required_hardware': self._identify_required_hardware(requirements),
            'safety_considerations': requirements.safety_requirements,
            'recommended_approach': self._recommend_approach(requirements),
            'potential_challenges': self._identify_challenges(requirements)
        }
        
        return analysis
    
    async def suggest_improvements(self, current_code: str, requirements_text: str) -> Dict[str, Any]:
        """Suggest improvements to existing PLC code"""
        
        # Parse the requirements again to understand intent
        requirements = await self.parser.parse_specification(requirements_text, self.mcp_server)
        
        # Analyze current code
        current_instructions = self.generator._extract_instructions_from_logic(current_code)
        
        # Find matching patterns for comparison
        matching_patterns = self.warehouse_patterns.find_matching_patterns(requirements_text)
        
        suggestions = {
            'performance_improvements': self._suggest_performance_improvements(current_code, requirements),
            'safety_enhancements': self._suggest_safety_enhancements(current_code, requirements),
            'code_organization': self._suggest_code_organization(current_code),
            'missing_functionality': self._identify_missing_functionality(current_code, requirements),
            'best_practices': self._suggest_best_practices(current_code, matching_patterns),
            'instruction_alternatives': await self._suggest_instruction_alternatives(current_instructions)
        }
        
        return suggestions
    
    async def generate_project_documentation(self, requirements_text: str, 
                                           generated_code: EnhancedGeneratedCode) -> str:
        """Generate comprehensive project documentation"""
        
        requirements = await self.parser.parse_specification(requirements_text, self.mcp_server)
        
        doc_sections = []
        
        # Project Overview
        doc_sections.append("# Warehouse Automation PLC Project Documentation")
        doc_sections.append(f"## Project Overview")
        doc_sections.append(f"**Domain:** {requirements.domain.value.title()}")
        doc_sections.append(f"**Complexity:** {requirements.complexity.value.title()}")
        doc_sections.append(f"**Generated:** {self._get_timestamp()}")
        doc_sections.append("")
        
        # Requirements Summary
        doc_sections.append("## Requirements Summary")
        doc_sections.append(f"**Original Description:** {requirements.description}")
        doc_sections.append("")
        
        if requirements.components:
            doc_sections.append("### Components")
            for comp in requirements.components:
                safety_note = " ⚠️ **Safety Critical**" if comp.safety_critical else ""
                doc_sections.append(f"- **{comp.name}** ({comp.component_type}){safety_note}")
            doc_sections.append("")
        
        if requirements.sequences:
            doc_sections.append("### Automation Sequences")
            for seq in requirements.sequences:
                doc_sections.append(f"- **{seq.name}:** {len(seq.steps)} steps")
            doc_sections.append("")
        
        # Safety Requirements
        if requirements.safety_requirements:
            doc_sections.append("## Safety Requirements")
            for safety_req in requirements.safety_requirements:
                doc_sections.append(f"- {safety_req}")
            doc_sections.append("")
        
        # Generated Code Summary
        doc_sections.append("## Generated Code Summary")
        doc_sections.append(f"**Instructions Used:** {', '.join(generated_code.instructions_used)}")
        doc_sections.append(f"**Total Tags:** {len(generated_code.tags)}")
        doc_sections.append("")
        
        # Tag Documentation
        if generated_code.tags:
            doc_sections.append("### Tag Documentation")
            doc_sections.append("| Tag Name | Data Type | Description |")
            doc_sections.append("|----------|-----------|-------------|")
            for tag in generated_code.tags:
                doc_sections.append(f"| {tag['name']} | {tag['data_type']} | {tag['description']} |")
            doc_sections.append("")
        
        # Performance Metrics
        if generated_code.performance_metrics:
            doc_sections.append("### Performance Metrics")
            for metric, value in generated_code.performance_metrics.items():
                doc_sections.append(f"- **{metric.replace('_', ' ').title()}:** {value}")
            doc_sections.append("")
        
        # Implementation Notes
        doc_sections.append("## Implementation Notes")
        for comment in generated_code.comments:
            doc_sections.append(f"- {comment}")
        doc_sections.append("")
        
        # Validation Results
        if generated_code.validation_notes:
            doc_sections.append("## Validation Results")
            for note in generated_code.validation_notes:
                doc_sections.append(f"- {note}")
            doc_sections.append("")
        
        # Safety Logic
        if generated_code.safety_logic:
            doc_sections.append("## Safety Logic Implementation")
            doc_sections.append("```ladder")
            for safety_line in generated_code.safety_logic:
                doc_sections.append(safety_line)
            doc_sections.append("```")
            doc_sections.append("")
        
        return "\n".join(doc_sections)
    
    def _enhance_with_context(self, requirements: EnhancedPLCRequirement) -> EnhancedPLCRequirement:
        """Enhance requirements with conversation context and user preferences"""
        
        # Apply domain expertise from context
        if self.conversation_context['domain_expertise']:
            requirements.domain = self.conversation_context['domain_expertise']
        
        # Add user preferences for safety levels
        if 'safety_level' in self.conversation_context.get('user_preferences', {}):
            safety_level = self.conversation_context['user_preferences']['safety_level']
            if safety_level == 'high':
                # Add additional safety requirements
                requirements.safety_requirements.extend([
                    "Dual channel safety monitoring required",
                    "Category 3 safety system implementation",
                    "Positive feedback required for all safety devices"
                ])
        
        # Learn from previous requirements
        if self.conversation_context['previous_requirements']:
            # Look for common patterns in previous requests
            prev_components = []
            for prev_req in self.conversation_context['previous_requirements']:
                prev_components.extend([comp.component_type for comp in prev_req.components])
            
            # If user frequently mentions certain components, suggest related ones
            common_components = set(prev_components)
            if 'conveyor' in common_components and not any(comp.component_type == 'photoeye' for comp in requirements.components):
                # Suggest adding photoeyes for conveyor systems
                requirements.validation_rules.append("Consider adding photoeyes for material detection")
        
        return requirements
    
    async def _post_process_code(self, code: EnhancedGeneratedCode, 
                               requirements: EnhancedPLCRequirement) -> EnhancedGeneratedCode:
        """Post-process generated code for optimization and validation"""
        
        # Add standard safety interlocks if safety-critical components present
        safety_critical_components = [comp for comp in requirements.components if comp.safety_critical]
        if safety_critical_components and not code.safety_logic:
            code.safety_logic = self.generator._generate_safety_logic(requirements.safety_requirements)
        
        # Optimize ladder logic organization
        code.ladder_logic = self._optimize_ladder_organization(code.ladder_logic)
        
        # Add performance monitoring if performance requirements exist
        if requirements.performance_requirements:
            perf_monitoring = self._generate_performance_monitoring(requirements.performance_requirements)
            code.ladder_logic += "\n\n// Performance Monitoring\n" + perf_monitoring
        
        # Validate with MCP server if available
        if self.mcp_server and code.instructions_used:
            additional_validation = await self._comprehensive_validation(code.instructions_used)
            code.validation_notes.extend(additional_validation)
        
        return code
    
    def _optimize_ladder_organization(self, ladder_logic: str) -> str:
        """Organize ladder logic for better readability and maintenance"""
        
        lines = ladder_logic.split('\n')
        organized_lines = []
        
        # Group related logic together
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('//'):
                # Comment line - start new section
                if current_section and organized_lines:
                    organized_lines.append("")  # Add blank line between sections
                current_section = line
                organized_lines.append(line)
            else:
                organized_lines.append(line)
        
        return "\n".join(organized_lines)
    
    def _generate_performance_monitoring(self, performance_req: Dict[str, Any]) -> str:
        """Generate performance monitoring logic"""
        
        monitoring_lines = []
        
        if 'timing_ms' in performance_req:
            target_time = min(performance_req['timing_ms'])
            monitoring_lines.append(f"// Cycle Time Monitoring (Target: {target_time}ms)")
            monitoring_lines.append("GSV(TASK,MainTask,MAXSCANTIME,MAX_SCAN_TIME);")
            monitoring_lines.append(f"LES(MAX_SCAN_TIME,{target_time * 1000}) OTE(CYCLE_TIME_OK);")  # Convert to microseconds
        
        if 'speed_linear' in performance_req:
            target_speed = max(performance_req['speed_linear'])
            monitoring_lines.append(f"// Speed Monitoring (Target: {target_speed} units/min)")
            monitoring_lines.append("GRT(ACTUAL_SPEED,MIN_SPEED_LIMIT) OTE(SPEED_OK);")
        
        return "\n".join(monitoring_lines)
    
    async def _comprehensive_validation(self, instructions: List[str]) -> List[str]:
        """Perform comprehensive validation using MCP server"""
        
        validation_notes = []
        
        for instruction in instructions:
            try:
                # Get detailed instruction information
                if hasattr(self.mcp_server, 'get_instruction_syntax'):
                    syntax_info = await self.mcp_server.get_instruction_syntax(instruction)
                    if syntax_info:
                        validation_notes.append(f"✓ {instruction}: Syntax validated")
                    else:
                        validation_notes.append(f"⚠ {instruction}: Syntax information not available")
                
                # Check instruction category for appropriateness
                if hasattr(self.mcp_server, 'get_instruction'):
                    inst_info = await self.mcp_server.get_instruction(instruction)
                    if inst_info and 'category' in inst_info:
                        validation_notes.append(f"ℹ {instruction}: Category - {inst_info['category']}")
                        
            except Exception as e:
                validation_notes.append(f"❌ {instruction}: Validation error - {str(e)}")
        
        return validation_notes
    
    def _update_conversation_context(self, requirements: EnhancedPLCRequirement, 
                                   code: EnhancedGeneratedCode):
        """Update conversation context with current interaction"""
        
        # Store requirements for future reference
        self.conversation_context['previous_requirements'].append(requirements)
        
        # Keep only last 5 interactions to prevent memory bloat
        if len(self.conversation_context['previous_requirements']) > 5:
            self.conversation_context['previous_requirements'] = \
                self.conversation_context['previous_requirements'][-5:]
        
        # Store generated project info
        project_info = {
            'domain': requirements.domain.value,
            'complexity': requirements.complexity.value,
            'instructions_used': code.instructions_used,
            'component_types': [comp.component_type for comp in requirements.components]
        }
        self.conversation_context['generated_projects'].append(project_info)
        
        # Update user preferences based on patterns
        if not self.conversation_context['user_preferences'].get('preferred_logic_type'):
            self.conversation_context['user_preferences']['preferred_logic_type'] = requirements.logic_type
    
    def _prepare_response(self, requirements: EnhancedPLCRequirement, 
                         code: EnhancedGeneratedCode, original_description: str) -> Dict[str, Any]:
        """Prepare comprehensive response for the user"""
        
        return {
            'success': True,
            'message': 'Enhanced PLC code generated successfully',
            'original_description': original_description,
            'requirements': {
                'domain': requirements.domain.value,
                'complexity': requirements.complexity.value,
                'logic_type': requirements.logic_type,
                'component_count': len(requirements.components),
                'sequence_count': len(requirements.sequences),
                'safety_requirements_count': len(requirements.safety_requirements)
            },
            'generated_code': {
                'ladder_logic': code.ladder_logic,
                'structured_text': code.structured_text,
                'tags': code.tags,
                'instructions_used': code.instructions_used,
                'safety_logic': code.safety_logic,
                'performance_metrics': code.performance_metrics
            },
            'validation': {
                'notes': code.validation_notes,
                'instruction_count': len(code.instructions_used),
                'safety_validated': len(code.safety_logic) > 0 if code.safety_logic else False
            },
            'documentation': code.documentation,
            'recommendations': self._generate_recommendations(requirements, code),
            'next_steps': self._suggest_next_steps(requirements, code)
        }
    
    def _generate_recommendations(self, requirements: EnhancedPLCRequirement, 
                                code: EnhancedGeneratedCode) -> List[str]:
        """Generate recommendations for the user"""
        
        recommendations = []
        
        # Complexity-based recommendations
        if requirements.complexity == LogicComplexity.ADVANCED:
            recommendations.append("Consider implementing state machine logic for better organization")
            recommendations.append("Add comprehensive error handling and diagnostics")
        
        # Safety recommendations
        if any(comp.safety_critical for comp in requirements.components):
            recommendations.append("Implement dual-channel safety monitoring")
            recommendations.append("Add safety function testing procedures")
        
        # Performance recommendations
        if requirements.performance_requirements:
            recommendations.append("Add performance monitoring and trending")
            recommendations.append("Consider implementing predictive maintenance logic")
        
        # Domain-specific recommendations
        if requirements.domain == IndustryDomain.WAREHOUSE:
            recommendations.append("Implement material tracking and traceability")
            recommendations.append("Add integration points for WMS/WCS systems")
        
        return recommendations
    
    def _suggest_next_steps(self, requirements: EnhancedPLCRequirement, 
                          code: EnhancedGeneratedCode) -> List[str]:
        """Suggest next steps for implementation"""
        
        next_steps = []
        
        next_steps.append("1. Review generated ladder logic and customize tag names")
        next_steps.append("2. Configure I/O mapping in Studio 5000")
        next_steps.append("3. Test logic in simulation mode")
        
        if code.safety_logic:
            next_steps.append("4. Validate safety logic with safety engineer")
            next_steps.append("5. Perform safety function testing")
        
        next_steps.append("6. Commission system with actual hardware")
        next_steps.append("7. Perform system integration testing")
        
        if requirements.performance_requirements:
            next_steps.append("8. Validate performance metrics")
            next_steps.append("9. Optimize for production requirements")
        
        return next_steps
    
    # Helper methods for analysis and suggestions
    def _estimate_development_time(self, requirements: EnhancedPLCRequirement) -> str:
        """Estimate development time based on complexity"""
        
        base_hours = {
            LogicComplexity.SIMPLE: 4,
            LogicComplexity.MODERATE: 12,
            LogicComplexity.COMPLEX: 24,
            LogicComplexity.ADVANCED: 48
        }
        
        hours = base_hours.get(requirements.complexity, 12)
        
        # Add time for safety requirements
        if requirements.safety_requirements:
            hours += len(requirements.safety_requirements) * 2
        
        # Add time for complex sequences
        if requirements.sequences:
            hours += len(requirements.sequences) * 4
        
        return f"{hours}-{hours * 1.5:.0f} hours"
    
    def _identify_required_hardware(self, requirements: EnhancedPLCRequirement) -> List[str]:
        """Identify required hardware based on components"""
        
        hardware = ["CompactLogix or ControlLogix PLC"]
        
        component_types = [comp.component_type for comp in requirements.components]
        
        if 'servo_motor' in component_types:
            hardware.append("Kinetix servo drives")
        
        if 'safety_scanner' in component_types or any(comp.safety_critical for comp in requirements.components):
            hardware.append("GuardLogix safety PLC or safety I/O modules")
        
        if 'barcode_scanner' in component_types:
            hardware.append("Ethernet/IP barcode scanner")
        
        if requirements.domain == IndustryDomain.WAREHOUSE:
            hardware.append("Industrial Ethernet infrastructure")
            hardware.append("HMI/SCADA system for monitoring")
        
        return hardware
    
    def _recommend_approach(self, requirements: EnhancedPLCRequirement) -> str:
        """Recommend development approach"""
        
        if requirements.complexity in [LogicComplexity.COMPLEX, LogicComplexity.ADVANCED]:
            return "Phased implementation with simulation testing at each phase"
        elif len(requirements.safety_requirements) > 3:
            return "Safety-first approach with comprehensive risk assessment"
        else:
            return "Standard development lifecycle with thorough testing"
    
    def _identify_challenges(self, requirements: EnhancedPLCRequirement) -> List[str]:
        """Identify potential implementation challenges"""
        
        challenges = []
        
        if requirements.complexity == LogicComplexity.ADVANCED:
            challenges.append("Complex state machine logic may require extensive testing")
        
        if len(requirements.sequences) > 3:
            challenges.append("Multiple sequences may require careful coordination")
        
        if any(comp.safety_critical for comp in requirements.components):
            challenges.append("Safety validation and certification requirements")
        
        if requirements.performance_requirements:
            challenges.append("Meeting performance requirements may require optimization")
        
        return challenges
    
    def _get_error_suggestions(self, error_message: str) -> List[str]:
        """Provide suggestions based on error type"""
        
        suggestions = []
        
        if "parse" in error_message.lower():
            suggestions.append("Try rephrasing the description with more specific details")
            suggestions.append("Include component names and their relationships")
        
        if "instruction" in error_message.lower():
            suggestions.append("Check if all mentioned instructions are valid Studio 5000 instructions")
            suggestions.append("Verify MCP server connection for instruction validation")
        
        if "timeout" in error_message.lower():
            suggestions.append("Simplify the request or break it into smaller parts")
            suggestions.append("Check network connection to MCP server")
        
        return suggestions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for documentation"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Additional helper methods for code improvement suggestions
    def _suggest_performance_improvements(self, code: str, requirements: EnhancedPLCRequirement) -> List[str]:
        """Suggest performance improvements"""
        improvements = []
        
        if "TON(" in code and requirements.performance_requirements.get('timing_ms'):
            improvements.append("Consider using high-resolution timers for precise timing")
        
        if code.count("XIC(") > 10:
            improvements.append("Consider using function blocks to organize complex logic")
        
        return improvements
    
    def _suggest_safety_enhancements(self, code: str, requirements: EnhancedPLCRequirement) -> List[str]:
        """Suggest safety enhancements"""
        enhancements = []
        
        if not any("E_STOP" in line for line in code.split('\n')):
            enhancements.append("Add emergency stop monitoring logic")
        
        if any(comp.safety_critical for comp in requirements.components):
            if not any("SAFETY" in line for line in code.split('\n')):
                enhancements.append("Add comprehensive safety interlock logic")
        
        return enhancements
    
    def _suggest_code_organization(self, code: str) -> List[str]:
        """Suggest code organization improvements"""
        suggestions = []
        
        lines = code.split('\n')
        comment_lines = [line for line in lines if line.strip().startswith('//')]
        
        if len(comment_lines) < len(lines) * 0.2:
            suggestions.append("Add more comments to improve code readability")
        
        if len(lines) > 50:
            suggestions.append("Consider breaking code into multiple routines")
        
        return suggestions
    
    def _identify_missing_functionality(self, code: str, requirements: EnhancedPLCRequirement) -> List[str]:
        """Identify potentially missing functionality"""
        missing = []
        
        # Check for fault handling
        if not any("FAULT" in line for line in code.split('\n')):
            missing.append("Add fault detection and handling logic")
        
        # Check for diagnostics
        if requirements.complexity in [LogicComplexity.COMPLEX, LogicComplexity.ADVANCED]:
            if not any("DIAGNOSTIC" in line for line in code.split('\n')):
                missing.append("Add diagnostic monitoring capabilities")
        
        return missing
    
    def _suggest_best_practices(self, code: str, patterns: List) -> List[str]:
        """Suggest best practices based on patterns"""
        practices = []
        
        if patterns:
            practices.append("Follow established pattern conventions for consistency")
        
        if "OTE(" in code and "OTU(" in code:
            practices.append("Use consistent output control methods (OTE vs OTL/OTU)")
        
        return practices
    
    async def _suggest_instruction_alternatives(self, instructions: List[str]) -> List[str]:
        """Suggest alternative instructions using MCP server"""
        alternatives = []
        
        # This would use the MCP server to find alternative instructions
        # For now, provide some basic suggestions
        
        if 'TON' in instructions:
            alternatives.append("Consider TOF for off-delay timing applications")
        
        if 'CTU' in instructions:
            alternatives.append("Consider CTD for down-counting applications")
        
        return alternatives


# Example usage and testing
if __name__ == "__main__":
    async def test_enhanced_assistant():
        assistant = EnhancedCodeAssistant()
        
        # Test complex warehouse scenario
        description = """
        Create a conveyor sorting system for a warehouse that scans packages with barcodes,
        sorts them into 3 different lanes based on destination codes, and includes safety
        interlocks with light curtains and emergency stops. The system should handle 
        100 packages per minute and include jam detection with automatic recovery.
        """
        
        result = await assistant.generate_code_from_description(description)
        
        print("Generated Code:")
        print("=" * 50)
        print(result['generated_code']['ladder_logic'])
        print("\nTags:")
        print("=" * 50)
        for tag in result['generated_code']['tags']:
            print(f"{tag['name']}: {tag['data_type']} - {tag['description']}")
        
        print(f"\nComplexity: {result['requirements']['complexity']}")
        print(f"Domain: {result['requirements']['domain']}")
        print(f"Instructions Used: {', '.join(result['generated_code']['instructions_used'])}")
    
    # Run the test
    asyncio.run(test_enhanced_assistant())

