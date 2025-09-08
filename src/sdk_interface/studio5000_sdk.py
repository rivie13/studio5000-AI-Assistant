#!/usr/bin/env python3
"""
Real Studio 5000 SDK Interface

This module provides a Python interface to the actual Studio 5000 SDK
for creating and manipulating real .ACD project files.
"""

import asyncio
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Add Studio 5000 SDK to path - configurable via environment variable
SDK_PATH = os.environ.get(
    'STUDIO5000_SDK_PATH',
    r"C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python"
)
if SDK_PATH not in sys.path:
    sys.path.append(SDK_PATH)

try:
    from logix_designer_sdk import LogixProject, StdOutEventLogger, ImportCollisionOptions
    SDK_AVAILABLE = True
except ImportError as e:
    print(f"Studio 5000 SDK not available: {e}", file=sys.stderr)
    SDK_AVAILABLE = False

class Studio5000SDKInterface:
    """Interface to the real Studio 5000 SDK"""
    
    def __init__(self):
        self.sdk_available = SDK_AVAILABLE
        # Get Python 3.12 path from environment or use default
        self.python312_path = os.environ.get(
            'PYTHON312_PATH',
            r"C:\Users\kontr\AppData\Local\Programs\Python\Python312\python.exe"
        )
    
    async def create_empty_acd_project(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create an EMPTY .ACD project file using Studio 5000 SDK - NO PROGRAMS ADDED"""
        try:
            if not self.sdk_available:
                return {
                    'success': False,
                    'error': 'Studio 5000 SDK not available',
                    'message': 'Please ensure Studio 5000 SDK is properly installed'
                }
            
            # Extract project parameters
            project_name = project_spec.get('name', 'AI_Generated_Project')
            controller_type = project_spec.get('controller_type', '1756-L83E')
            major_revision = project_spec.get('major_revision', 36)
            save_path = project_spec.get('save_path', f'{project_name}.ACD')
            
            # Ensure .ACD extension
            if not save_path.endswith('.ACD'):
                save_path += '.ACD'
            
            # Create full path
            if not os.path.isabs(save_path):
                save_path = os.path.join(os.getcwd(), save_path)
            
            print(f"Creating EMPTY .ACD project: {save_path}", file=sys.stderr)
            print(f"Controller: {controller_type}, Revision: {major_revision}", file=sys.stderr)
            
            # Create the project using Studio 5000 SDK - EMPTY PROJECT ONLY
            project = await LogixProject.create_new_project(
                save_path,
                major_revision,
                controller_type,
                project_name,
                StdOutEventLogger(),
            )
            
            # DON'T ADD ANYTHING - JUST CLOSE THE PROJECT
            # This creates a clean, empty Studio 5000 project
            
            # Get project info
            project_info = {
                'name': project_name,
                'controller_type': controller_type,
                'major_revision': major_revision,
                'file_path': save_path,
                'file_exists': os.path.exists(save_path),
                'file_size': os.path.getsize(save_path) if os.path.exists(save_path) else 0
            }
            
            return {
                'success': True,
                'project_info': project_info,
                'message': f'🎉 SUCCESS! Created EMPTY .ACD project file: {save_path}',
                'sdk_used': True,
                'project_type': 'Empty Studio 5000 Project'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create empty .ACD project using Studio 5000 SDK'
            }
    
    async def create_acd_project_with_programs(self, project_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create .ACD project file WITH MainProgram and MainTask using SDK partial import"""
        try:
            if not self.sdk_available:
                return {
                    'success': False,
                    'error': 'Studio 5000 SDK not available',
                    'message': 'Please ensure Studio 5000 SDK is properly installed'
                }
            
            # Extract project parameters
            project_name = project_spec.get('name', 'AI_Generated_Project')
            controller_type = project_spec.get('controller_type', '1756-L83E')
            major_revision = project_spec.get('major_revision', 36)
            save_path = project_spec.get('save_path', f'{project_name}.ACD')
            ladder_logic = project_spec.get('ladder_logic', '')
            
            # Ensure .ACD extension
            if not save_path.endswith('.ACD'):
                save_path += '.ACD'
            
            # Create full path
            if not os.path.isabs(save_path):
                save_path = os.path.join(os.getcwd(), save_path)
            
            print(f"Creating ACD project WITH programs: {save_path}", file=sys.stderr)
            print(f"Controller: {controller_type}, Revision: {major_revision}", file=sys.stderr)
            
            # Step 1: Create empty project
            project = await LogixProject.create_new_project(
                save_path,
                major_revision,
                controller_type,
                project_name,
                StdOutEventLogger(),
            )
            
            # Step 2: Generate MainProgram L5X XML
            main_program_xml = self._generate_main_program_l5x(project_name, ladder_logic)
            temp_l5x_path = save_path.replace('.ACD', '_MainProgram.L5X')
            
            # Debug: Print the generated XML to see what's wrong
            print("Generated L5X XML:", file=sys.stderr)
            print(main_program_xml[:500] + "..." if len(main_program_xml) > 500 else main_program_xml, file=sys.stderr)
            
            # Save L5X to temporary file
            with open(temp_l5x_path, 'w', encoding='utf-8') as f:
                f.write(main_program_xml)
            
            # Step 3: Import entire Controller section at once
            # This should import both Programs and Tasks together
            await project.partial_import_from_xml_file(
                "/RSLogix5000Content/Controller",
                temp_l5x_path,
                ImportCollisionOptions.OVERWRITE_ON_COLL
            )
            
            # Step 5: Save the project
            await project.save()
            
            # Clean up temporary L5X file
            if os.path.exists(temp_l5x_path):
                os.remove(temp_l5x_path)
            
            # Get project info
            project_info = {
                'name': project_name,
                'controller_type': controller_type,
                'major_revision': major_revision,
                'file_path': save_path,
                'file_exists': os.path.exists(save_path),
                'file_size': os.path.getsize(save_path) if os.path.exists(save_path) else 0,
                'has_main_program': True,
                'has_main_task': True
            }
            
            return {
                'success': True,
                'project_info': project_info,
                'message': f'🎉 SUCCESS! Created ACD project WITH MainProgram and MainTask: {save_path}',
                'sdk_used': True,
                'project_type': 'Complete Studio 5000 Project with Programs',
                'ladder_logic_included': bool(ladder_logic)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create ACD project with programs using Studio 5000 SDK'
            }
    
    def _generate_main_program_l5x(self, project_name: str, ladder_logic: str = '') -> str:
        """Generate L5X XML for MainProgram with MainTask and optional ladder logic"""
        
        # Debug: Print what ladder_logic we received
        print(f"Received ladder_logic: {ladder_logic[:200]}..." if len(ladder_logic) > 200 else f"Received ladder_logic: {ladder_logic}", file=sys.stderr)
        
        # Basic ladder logic if none provided
        if not ladder_logic:
            ladder_logic = '''<Rung Number="0" Type="N">
    <Comment>
        <![CDATA[AI Generated MainRoutine - Add your logic here]]>
    </Comment>
    <Text>
        <![CDATA[NOP();]]>
    </Text>
</Rung>'''
        
        # Check if ladder_logic is already in XML rung format or raw text
        if ladder_logic.strip().startswith('<Rung'):
            # Already in XML format, use as-is
            formatted_ladder_logic = ladder_logic
        else:
            # Raw text format, convert to single rung
            formatted_ladder_logic = f'''<Rung Number="0" Type="N">
    <Comment>
        <![CDATA[AI Generated Conveyor Control Logic]]>
    </Comment>
    <Text>
        <![CDATA[{ladder_logic}]]>
    </Text>
</Rung>'''
        
        # Generate L5X XML with MainProgram and MainTask
        l5x_template = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="36.00" TargetName="{project_name}" TargetType="Controller" TargetRevision="1.0" TargetLastEdited="2024-01-01T00:00:00.000Z" ContainsContext="true" Owner="AI Assistant" ExportDate="Tue Jan 01 00:00:00 2024" ExportOptions="References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans">

    <Controller Use="Context">
        <!-- MainTask Definition -->
        <Tasks>
            <Task Name="MainTask" Type="CONTINUOUS" Priority="10" Watchdog="500" DisableUpdateOutputs="false" InhibitTask="false">
                <ScheduledPrograms>
                    <ScheduledProgram Name="MainProgram"/>
                </ScheduledPrograms>
            </Task>
        </Tasks>
        
        <!-- MainProgram Definition -->
        <Programs>
            <Program Name="MainProgram" TestEdits="false" MainRoutineName="MainRoutine" Disabled="false">
                <Tags/>
                <Routines>
                    <Routine Name="MainRoutine" Type="RLL">
                        <RLLContent>
                            {formatted_ladder_logic}
                        </RLLContent>
                    </Routine>
                </Routines>
            </Program>
        </Programs>
    </Controller>
</RSLogix5000Content>'''
        
        return l5x_template

# Create global instance - handle import failures gracefully
try:
    studio5000_sdk = Studio5000SDKInterface()
except Exception as e:
    print(f"Warning: Studio5000SDKInterface creation failed: {e}", file=sys.stderr)
    # Create a dummy fallback interface
    class DummySDKInterface:
        def __init__(self):
            self.sdk_available = False
        
        async def create_empty_acd_project(self, project_spec):
            return {
                'success': False,
                'error': 'SDK not available - Python version mismatch',
                'message': 'Studio 5000 SDK requires Python 3.12, but MCP server is running on different version'
            }
    
    studio5000_sdk = DummySDKInterface()

# Test function
async def test_sdk_interface():
    """Test the SDK interface"""
    test_spec = {
        'name': 'SDK_Test_Empty_Project',
        'controller_type': '1756-L83E',
        'save_path': 'SDK_Test_Empty.ACD'
    }
    
    result = await studio5000_sdk.create_empty_acd_project(test_spec)
    print(f"SDK Test Result: {result}")
    return result

if __name__ == "__main__":
    print("Testing Studio 5000 SDK Interface...")
    asyncio.run(test_sdk_interface())
