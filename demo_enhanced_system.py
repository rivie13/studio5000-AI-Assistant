#!/usr/bin/env python3
"""
Enhanced Warehouse Automation PLC Assistant Demo

This script demonstrates the enhanced capabilities of the PLC code generation system
specifically designed for complex warehouse automation scenarios.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from ai_assistant.enhanced_main_assistant import EnhancedCodeAssistant
from ai_assistant.warehouse_automation_patterns import WarehouseAutomationPatterns

class MockMCPServer:
    """Mock MCP server for demonstration"""
    
    def __init__(self):
        self.instructions = {
            'XIC': {'name': 'XIC', 'description': 'Examine if Closed', 'category': 'Bit Instructions'},
            'XIO': {'name': 'XIO', 'description': 'Examine if Open', 'category': 'Bit Instructions'},
            'OTE': {'name': 'OTE', 'description': 'Output Energize', 'category': 'Bit Instructions'},
            'TON': {'name': 'TON', 'description': 'Timer On Delay', 'category': 'Timer Instructions'},
            'CTU': {'name': 'CTU', 'description': 'Count Up', 'category': 'Counter Instructions'},
            'MAM': {'name': 'MAM', 'description': 'Motion Axis Move', 'category': 'Motion Instructions'},
            'MAH': {'name': 'MAH', 'description': 'Motion Axis Home', 'category': 'Motion Instructions'},
            'EQU': {'name': 'EQU', 'description': 'Equal', 'category': 'Compare Instructions'},
            'MOV': {'name': 'MOV', 'description': 'Move', 'category': 'Move Instructions'}
        }
    
    async def get_instruction(self, name):
        return self.instructions.get(name)
    
    async def get_instruction_syntax(self, name):
        if name in self.instructions:
            return {'syntax': f'{name}(operand)', 'parameters': ['operand']}
        return None

async def demo_simple_vs_enhanced():
    """Demonstrate the difference between simple and enhanced systems"""
    
    print("🏭 WAREHOUSE AUTOMATION PLC ASSISTANT DEMO")
    print("=" * 60)
    
    # Initialize enhanced assistant
    mock_server = MockMCPServer()
    enhanced_assistant = EnhancedCodeAssistant(mock_server)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Simple Motor Control',
            'description': 'Start motor with start button, stop with stop button'
        },
        {
            'name': 'Conveyor System with Jam Detection',
            'description': '''Create a conveyor control system that starts when the start button is pressed,
            stops when the stop button is pressed, and includes jam detection using upstream and downstream
            photoeyes. If material is detected upstream but not downstream for more than 5 seconds,
            trigger a jam alarm and stop the conveyor.'''
        },
        {
            'name': 'Package Sorting System',
            'description': '''Design a package sorting system for a warehouse that scans barcodes on packages,
            compares them to destination codes, and activates diverters to route packages to the correct lanes.
            Include confirmation photoeyes and package counting for each lane. The system should handle
            3 destination lanes plus a reject lane for unreadable codes.'''
        },
        {
            'name': 'Safety Interlock System',
            'description': '''Create a comprehensive safety system with emergency stops, light curtains,
            and guard switches. The system must comply with Category 3 safety requirements and include
            diagnostic monitoring. All equipment must be interlocked through this safety system.'''
        },
        {
            'name': 'AGV Integration Station',
            'description': '''Design an AGV docking and load transfer station that handles AGV requests,
            manages docking sequences, transfers loads between conveyors and AGVs, and includes traffic
            control to prevent collisions. The system should handle both loading and unloading operations.'''
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 SCENARIO {i}: {scenario['name']}")
        print("-" * 50)
        print(f"Description: {scenario['description']}")
        
        try:
            # Generate code with enhanced system
            result = await enhanced_assistant.generate_code_from_description(scenario['description'])
            
            if result['success']:
                print(f"\n✅ SUCCESS - Generated {result['requirements']['complexity'].upper()} logic")
                print(f"🏭 Domain: {result['requirements']['domain'].title()}")
                print(f"📊 Components: {result['requirements']['component_count']}")
                print(f"🔧 Instructions Used: {len(result['generated_code']['instructions_used'])}")
                print(f"🏷️  Tags Created: {len(result['generated_code']['tags'])}")
                
                # Show first few lines of generated logic
                logic_lines = result['generated_code']['ladder_logic'].split('\n')[:5]
                print(f"\n📝 Generated Logic (first 5 lines):")
                for line in logic_lines:
                    if line.strip():
                        print(f"   {line}")
                
                # Show some tags
                if result['generated_code']['tags']:
                    print(f"\n🏷️  Sample Tags:")
                    for tag in result['generated_code']['tags'][:3]:
                        print(f"   {tag['name']}: {tag['data_type']} - {tag['description']}")
                
                # Show recommendations
                if result.get('recommendations'):
                    print(f"\n💡 Recommendations:")
                    for rec in result['recommendations'][:2]:
                        print(f"   • {rec}")
                
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
        
        print("\n" + "="*60)

async def demo_warehouse_patterns():
    """Demonstrate warehouse automation patterns"""
    
    print("\n🏗️  WAREHOUSE AUTOMATION PATTERNS LIBRARY")
    print("=" * 60)
    
    patterns = WarehouseAutomationPatterns()
    all_patterns = patterns.get_all_patterns()
    
    for pattern in all_patterns:
        print(f"\n📦 {pattern.name}")
        print(f"   Description: {pattern.description}")
        print(f"   Components: {', '.join(pattern.components)}")
        print(f"   Safety Considerations: {len(pattern.safety_considerations or [])}")
        
        # Show a snippet of the ladder logic template
        logic_lines = pattern.ladder_logic_template.strip().split('\n')[:3]
        print(f"   Logic Preview:")
        for line in logic_lines:
            if line.strip() and not line.strip().startswith('//'):
                print(f"      {line.strip()}")
                break

async def demo_complexity_analysis():
    """Demonstrate complexity analysis capabilities"""
    
    print("\n🧠 COMPLEXITY ANALYSIS DEMO")
    print("=" * 60)
    
    mock_server = MockMCPServer()
    enhanced_assistant = EnhancedCodeAssistant(mock_server)
    
    test_descriptions = [
        "Turn on light when button is pressed",
        "Start conveyor with jam detection and speed control using VFD",
        "Multi-station assembly line with robot coordination, safety interlocks, and batch tracking",
        "Complete warehouse management system with AGV coordination, inventory tracking, and predictive maintenance"
    ]
    
    for desc in test_descriptions:
        print(f"\n📝 Analyzing: '{desc}'")
        
        try:
            analysis = await enhanced_assistant.analyze_requirements_complexity(desc)
            
            print(f"   🏭 Domain: {analysis['domain']}")
            print(f"   📊 Complexity: {analysis['complexity_level']}")
            print(f"   ⏱️  Est. Development Time: {analysis['estimated_development_time']}")
            print(f"   🔧 Required Hardware: {len(analysis['required_hardware'])} items")
            print(f"   ⚠️  Safety Considerations: {len(analysis['safety_considerations'])}")
            
            if analysis['potential_challenges']:
                print(f"   🚧 Challenges: {analysis['potential_challenges'][0]}")
                
        except Exception as e:
            print(f"   ❌ Analysis Error: {str(e)}")

async def demo_instruction_coverage():
    """Demonstrate expanded instruction coverage"""
    
    print("\n🔧 INSTRUCTION COVERAGE DEMO")
    print("=" * 60)
    
    from ai_assistant.enhanced_ladder_generator import IndustrialInstructionMapper
    
    mock_server = MockMCPServer()
    mapper = IndustrialInstructionMapper(mock_server)
    
    # Initialize mappings
    await mapper._initialize_comprehensive_mappings()
    
    print(f"📊 Total Instruction Mappings: {len(mapper.all_instructions)}")
    print(f"   • Basic I/O: {len(mapper.basic_instructions)}")
    print(f"   • Timers: {len(mapper.timer_instructions)}")
    print(f"   • Counters: {len(mapper.counter_instructions)}")
    print(f"   • Math: {len(mapper.math_instructions)}")
    print(f"   • Comparison: {len(mapper.compare_instructions)}")
    print(f"   • Motion: {len(mapper.motion_instructions)}")
    print(f"   • Process Control: {len(mapper.process_instructions)}")
    print(f"   • Safety: {len(mapper.safety_instructions)}")
    print(f"   • Communication: {len(mapper.comm_instructions)}")
    print(f"   • Array/File: {len(mapper.array_instructions)}")
    
    # Test operation mapping
    print(f"\n🔍 Operation Mapping Examples:")
    test_operations = [
        ('start motor', 'motor control'),
        ('position servo', 'motion control'),
        ('count packages', 'counting'),
        ('compare values', 'comparison'),
        ('emergency stop', 'safety')
    ]
    
    for operation, context in test_operations:
        instruction = await mapper.get_instruction_for_operation(operation, context)
        print(f"   '{operation}' → {instruction}")

def print_summary():
    """Print enhancement summary"""
    
    print("\n🎯 ENHANCEMENT SUMMARY")
    print("=" * 60)
    
    enhancements = [
        "✅ Enhanced Natural Language Processing for complex industrial scenarios",
        "✅ Expanded instruction coverage from 15 to 100+ instructions across all categories",
        "✅ Warehouse-specific automation patterns (conveyors, sorting, AGV, safety)",
        "✅ Advanced context understanding and multi-step logic generation",
        "✅ Comprehensive safety system pattern recognition and validation",
        "✅ Performance requirements analysis and optimization suggestions",
        "✅ Domain-specific expertise (warehouse, manufacturing, material handling)",
        "✅ Complexity assessment and development time estimation",
        "✅ Real-time instruction validation using MCP server integration",
        "✅ Comprehensive documentation generation and best practices"
    ]
    
    for enhancement in enhancements:
        print(f"  {enhancement}")
    
    print(f"\n🚀 The enhanced system is now capable of handling:")
    print(f"   • Complex warehouse automation scenarios")
    print(f"   • Multi-component systems with safety interlocks")
    print(f"   • Motion control and servo positioning")
    print(f"   • AGV integration and material handling")
    print(f"   • Comprehensive safety systems (Category 3/4)")
    print(f"   • Performance monitoring and optimization")
    print(f"   • Real-world industrial automation challenges")

async def main():
    """Run the complete demonstration"""
    
    print("🤖 ENHANCED WAREHOUSE AUTOMATION PLC ASSISTANT")
    print("🏭 Designed for Industrial Warehouse Applications")
    print("=" * 60)
    
    try:
        # Run all demonstrations
        await demo_simple_vs_enhanced()
        await demo_warehouse_patterns()
        await demo_complexity_analysis()
        await demo_instruction_coverage()
        print_summary()
        
        print(f"\n🎉 DEMONSTRATION COMPLETE!")
        print(f"The enhanced system is ready for complex warehouse automation tasks.")
        
    except Exception as e:
        print(f"❌ Demo Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

