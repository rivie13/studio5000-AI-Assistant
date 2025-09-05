#!/usr/bin/env python3
"""
L5X Project File Generator

This module generates Studio 5000 L5X project files from specifications.
L5X files are XML-based project files that can be imported into Studio 5000.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class LadderRung:
    """Represents a single rung in ladder logic"""
    number: int
    logic: str
    comment: Optional[str] = None

@dataclass
class Routine:
    """Represents a Studio 5000 routine"""
    name: str
    type: str  # "RLL" for ladder logic, "ST" for structured text, etc.
    rungs: List[LadderRung]
    description: Optional[str] = None

@dataclass
class Program:
    """Represents a Studio 5000 program"""
    name: str
    routines: List[Routine]
    description: Optional[str] = None

@dataclass
class L5XProject:
    """Represents a complete L5X project"""
    name: str
    controller_type: str
    programs: List[Program]
    tags: List[Dict] = None
    description: Optional[str] = None

class L5XGenerator:
    """Generates L5X XML files from project specifications"""
    
    def __init__(self):
        self.project_template = self._load_project_template()
    
    def _load_project_template(self) -> str:
        """Load the base L5X project template"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="36.00" TargetName="{controller_type}" TargetType="Controller" TargetRevision="36.00" TargetLastEdited="{timestamp}" ContainsContext="true" Owner="Studio5000-AI-Assistant" ExportDate="{timestamp}" ExportOptions="References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans">
    <Controller Use="Context" Name="{project_name}">
        <Description>
            <![CDATA[{description}]]>
        </Description>
        <Programs>
            {programs}
        </Programs>
        <Tags>
            {tags}
        </Tags>
    </Controller>
</RSLogix5000Content>'''
    
    def generate_ladder_rung(self, rung: LadderRung) -> str:
        """Generate XML for a single ladder logic rung"""
        rung_xml = f'''
        <Rung Number="{rung.number}" Type="N">
            <Text><![CDATA[{rung.logic}]]></Text>'''
        
        if rung.comment:
            rung_xml += f'''
            <Comment>
                <![CDATA[{rung.comment}]]>
            </Comment>'''
        
        rung_xml += '''
        </Rung>'''
        
        return rung_xml
    
    def generate_routine(self, routine: Routine) -> str:
        """Generate XML for a routine (collection of rungs)"""
        rungs_xml = ""
        for rung in routine.rungs:
            rungs_xml += self.generate_ladder_rung(rung)
        
        routine_xml = f'''
        <Routine Name="{routine.name}" Type="{routine.type}">'''
        
        if routine.description:
            routine_xml += f'''
            <Description>
                <![CDATA[{routine.description}]]>
            </Description>'''
        
        if routine.type == "RLL":  # Ladder Logic
            routine_xml += f'''
            <RLLContent>
                {rungs_xml}
            </RLLContent>'''
        elif routine.type == "ST":  # Structured Text
            # For structured text, combine all rung logic
            st_code = "\\n".join([rung.logic for rung in routine.rungs])
            routine_xml += f'''
            <STContent>
                <Line Number="0">
                    <![CDATA[{st_code}]]>
                </Line>
            </STContent>'''
        
        routine_xml += '''
        </Routine>'''
        
        return routine_xml
    
    def generate_program(self, program: Program) -> str:
        """Generate XML for a program (collection of routines)"""
        routines_xml = ""
        for routine in program.routines:
            routines_xml += self.generate_routine(routine)
        
        program_xml = f'''
        <Program Name="{program.name}" Type="Normal" Use="Context">'''
        
        if program.description:
            program_xml += f'''
            <Description>
                <![CDATA[{program.description}]]>
            </Description>'''
        
        program_xml += f'''
            <Tags>
            </Tags>
            <Routines>
                {routines_xml}
            </Routines>
        </Program>'''
        
        return program_xml
    
    def generate_tag(self, tag_spec: Dict) -> str:
        """Generate XML for a tag definition"""
        tag_xml = f'''
        <Tag Name="{tag_spec['name']}" TagType="{tag_spec.get('type', 'Base')}" DataType="{tag_spec.get('data_type', 'BOOL')}" Radix="{tag_spec.get('radix', 'Decimal')}" Constant="false" ExternalAccess="Read/Write">'''
        
        if tag_spec.get('description'):
            tag_xml += f'''
            <Description>
                <![CDATA[{tag_spec['description']}]]>
            </Description>'''
        
        if tag_spec.get('value') is not None:
            tag_xml += f'''
            <Data Format="L5K">
                <![CDATA[{tag_spec['value']}]]>
            </Data>'''
        
        tag_xml += '''
        </Tag>'''
        
        return tag_xml
    
    def generate_l5x_project(self, project: L5XProject) -> str:
        """Generate complete L5X XML from project specification"""
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        
        # Generate programs XML
        programs_xml = ""
        for program in project.programs:
            programs_xml += self.generate_program(program)
        
        # Generate tags XML
        tags_xml = ""
        if project.tags:
            for tag_spec in project.tags:
                tags_xml += self.generate_tag(tag_spec)
        
        # Fill in the template
        l5x_content = self.project_template.format(
            controller_type=project.controller_type,
            project_name=project.name,
            description=project.description or "Generated by Studio5000-AI-Assistant",
            timestamp=timestamp,
            programs=programs_xml,
            tags=tags_xml
        )
        
        # Pretty print the XML
        try:
            root = ET.fromstring(l5x_content)
            rough_string = ET.tostring(root, 'unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception as e:
            # If pretty printing fails, return raw XML
            return l5x_content
    
    def save_l5x_file(self, project: L5XProject, file_path: str) -> bool:
        """Save L5X project to file"""
        try:
            l5x_content = self.generate_l5x_project(project)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(l5x_content)
            return True
        except Exception as e:
            print(f"Error saving L5X file: {e}")
            return False

# Example usage and templates
def create_motor_control_example() -> L5XProject:
    """Create a simple motor control L5X project example"""
    
    # Define ladder logic rungs
    start_stop_rung = LadderRung(
        number=0,
        logic="XIC(START_PB)XIO(STOP_PB)OTE(MOTOR_RUN);",
        comment="Start/Stop motor control logic"
    )
    
    indicator_rung = LadderRung(
        number=1, 
        logic="XIC(MOTOR_RUN)OTE(RUN_LIGHT);",
        comment="Turn on indicator light when motor is running"
    )
    
    # Create routine
    main_routine = Routine(
        name="MainRoutine",
        type="RLL",
        rungs=[start_stop_rung, indicator_rung],
        description="Main motor control routine"
    )
    
    # Create program  
    main_program = Program(
        name="MainProgram",
        routines=[main_routine],
        description="Motor control program"
    )
    
    # Define tags
    project_tags = [
        {
            'name': 'START_PB',
            'data_type': 'BOOL',
            'description': 'Start push button input'
        },
        {
            'name': 'STOP_PB', 
            'data_type': 'BOOL',
            'description': 'Stop push button input'
        },
        {
            'name': 'MOTOR_RUN',
            'data_type': 'BOOL', 
            'description': 'Motor run output'
        },
        {
            'name': 'RUN_LIGHT',
            'data_type': 'BOOL',
            'description': 'Run indicator light output'
        }
    ]
    
    # Create project
    project = L5XProject(
        name="MotorControl",
        controller_type="1756-L83E",
        programs=[main_program],
        tags=project_tags,
        description="Simple motor start/stop control system"
    )
    
    return project

if __name__ == "__main__":
    # Test the L5X generator
    generator = L5XGenerator()
    example_project = create_motor_control_example()
    
    l5x_content = generator.generate_l5x_project(example_project)
    print("Generated L5X Content:")
    print(l5x_content[:500] + "...")
    
    # Save to file
    if generator.save_l5x_file(example_project, "test_motor_control.L5X"):
        print("\\nL5X file saved successfully!")
