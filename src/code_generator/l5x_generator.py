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
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="36.02" TargetName="{project_name}" TargetType="Controller" TargetRevision="36.02" TargetLastEdited="{timestamp}" ContainsContext="true" Owner="Studio5000-AI-Assistant" ExportDate="{timestamp}" ExportOptions="References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans">
    <Controller Use="Context" Name="{project_name}">
        <Description>
            <![CDATA[{description}]]>
        </Description>
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
            {tags}
        </Tags>
        <Programs Use="Context">
            {programs}
        </Programs>
        <Tasks Use="Context">
            <Task Name="MainTask" Type="CONTINUOUS" Priority="10" Watchdog="500" DisableUpdateOutputs="false" InhibitTask="false">
                <ScheduledPrograms>
                    <ScheduledProgram Name="MainProgram"/>
                </ScheduledPrograms>
            </Task>
        </Tasks>
    </Controller>
</RSLogix5000Content>'''
    
    def generate_ladder_rung(self, rung: LadderRung) -> str:
        """Generate XML for a single ladder logic rung"""
        rung_xml = f'''                            <Rung Number="{rung.number}" Type="N">'''
        
        if rung.comment:
            rung_xml += f'''
                                <Comment>
                                    <![CDATA[{rung.comment}]]>
                                </Comment>'''
        
        rung_xml += f'''
                                <Text>
                                    <![CDATA[{rung.logic}]]>
                                </Text>
                            </Rung>'''
        
        return rung_xml
    
    def generate_routine(self, routine: Routine) -> str:
        """Generate XML for a routine (collection of rungs)"""
        rungs_xml = ""
        for rung in routine.rungs:
            rungs_xml += self.generate_ladder_rung(rung)
        
        routine_xml = f'''
                    <Routine Use="Context" Name="{routine.name}" Type="{routine.type}">'''
        
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
        
        # Determine the main routine name (first routine if not specified)
        main_routine_name = program.routines[0].name if program.routines else "MainRoutine"
        
        program_xml = f'''
            <Program Use="Context" Name="{program.name}" TestEdits="false" MainRoutineName="{main_routine_name}" Disabled="false" UseAsFolder="false">'''
        
        if program.description:
            program_xml += f'''
                <Description>
                    <![CDATA[{program.description}]]>
                </Description>'''
        
        program_xml += f'''
                <Tags Use="Context"/>
                <Routines Use="Context">
                    {routines_xml}
                </Routines>
            </Program>'''
        
        return program_xml
    
    def generate_tag(self, tag_spec: Dict) -> str:
        """Generate XML for a tag definition"""
        data_type = tag_spec.get('data_type', 'BOOL')
        radix = tag_spec.get('radix', 'Decimal')
        tag_name = tag_spec['name']
        
        # Structured data types don't use Radix attribute - it causes "Invalid display style" error
        # These include: TIMER, COUNTER, STRING, and User-Defined Types
        structured_types = ['TIMER', 'COUNTER', 'STRING']
        is_structured = data_type in structured_types or data_type.endswith('_UDT')
        
        if is_structured:
            tag_xml = f'''            <Tag Name="{tag_name}" TagType="{tag_spec.get('type', 'Base')}" DataType="{data_type}" Constant="false" ExternalAccess="Read/Write">'''
        else:
            # Basic data types (BOOL, DINT, SINT, BIT, REAL, etc.) need Radix
            tag_xml = f'''            <Tag Name="{tag_name}" TagType="{tag_spec.get('type', 'Base')}" DataType="{data_type}" Radix="{radix}" Constant="false" ExternalAccess="Read/Write">'''
        
        if tag_spec.get('description'):
            tag_xml += f'''
                <Description>
                    <![CDATA[{tag_spec['description']}]]>
                </Description>'''
        
        # Handle different data types with proper structure
        if data_type == 'TIMER':
            # TIMER data type requires special structure matching Studio 5000 format
            preset_value = tag_spec.get('preset_value', 5000)  # Default 5 seconds
            tag_xml += f'''
                <Data Format="L5K">
                    <![CDATA[[{preset_value},0,0]]]>
                </Data>
                <Data Format="Decorated">
                    <Structure DataType="TIMER">
                        <DataValueMember Name="PRE" DataType="DINT" Radix="Decimal" Value="{preset_value}"/>
                        <DataValueMember Name="ACC" DataType="DINT" Radix="Decimal" Value="0"/>
                        <DataValueMember Name="EN" DataType="BOOL" Value="0"/>
                        <DataValueMember Name="TT" DataType="BOOL" Value="0"/>
                        <DataValueMember Name="DN" DataType="BOOL" Value="0"/>
                    </Structure>
                </Data>'''
        elif data_type == 'COUNTER':
            # COUNTER data type similar to TIMER but with CU, CD, DN, OV, UN bits
            preset_value = tag_spec.get('preset_value', 10)
            tag_xml += f'''
                <Data Format="L5K">
                    <![CDATA[[{preset_value},0,0]]]>
                </Data>
                <Data Format="Decorated">
                    <Structure DataType="COUNTER">
                        <DataValueMember Name="PRE" DataType="DINT" Radix="Decimal" Value="{preset_value}"/>
                        <DataValueMember Name="ACC" DataType="DINT" Radix="Decimal" Value="0"/>
                        <DataValueMember Name="CU" DataType="BOOL" Value="0"/>
                        <DataValueMember Name="CD" DataType="BOOL" Value="0"/>
                        <DataValueMember Name="DN" DataType="BOOL" Value="0"/>
                        <DataValueMember Name="OV" DataType="BOOL" Value="0"/>
                        <DataValueMember Name="UN" DataType="BOOL" Value="0"/>
                    </Structure>
                </Data>'''
        elif data_type == 'STRING':
            # STRING data type with default length
            string_length = tag_spec.get('string_length', 82)  # Default STRING length
            string_value = tag_spec.get('value', '')
            tag_xml += f'''
                <Data Format="L5K">
                    <![CDATA['{string_value}']]>
                </Data>
                <Data Format="Decorated">
                    <Structure DataType="STRING">
                        <DataValueMember Name="LEN" DataType="DINT" Radix="Decimal" Value="{len(string_value)}"/>
                        <DataValueMember Name="DATA" DataType="SINT" Radix="ASCII" Dimension="{string_length}">
                            <![CDATA[{string_value}]]>
                        </DataValueMember>
                    </Structure>
                </Data>'''
        elif is_structured:
            # Other structured types (User-defined types) - basic structure
            default_value = tag_spec.get('value', '0')
            tag_xml += f'''
                <Data Format="L5K">
                    <![CDATA[{default_value}]]>
                </Data>
                <Data Format="Decorated">
                    <Structure DataType="{data_type}">
                        <!-- User-defined structure members would go here -->
                    </Structure>
                </Data>'''
        else:
            # Standard basic data types (BOOL, DINT, SINT, BIT, REAL, etc.)
            default_value = tag_spec.get('value', '0')
            tag_xml += f'''
                <Data Format="L5K">
                    <![CDATA[{default_value}]]>
                </Data>
                <Data Format="Decorated">
                    <DataValue DataType="{data_type}" Radix="{radix}" Value="{default_value}"/>
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
    
    def generate_routine_export(self, routine: Routine, controller_name: str = "MTN6_MCM06", 
                               tags: Optional[List[Dict]] = None, 
                               software_revision: str = "36.02") -> str:
        """Generate L5X routine export (not full project) that can be imported into existing ACD"""
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        
        # Generate rungs XML for the routine
        rungs_xml = ""
        for rung in routine.rungs:
            rungs_xml += self.generate_ladder_rung(rung)
        
        # Generate tags XML if provided
        tags_xml = ""
        if tags:
            for tag_spec in tags:
                tags_xml += self.generate_tag(tag_spec)
        
        # Routine export template matching Studio 5000 format
        routine_export_template = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="{software_revision}" TargetName="{routine.name}" TargetType="Routine" TargetSubType="RLL" TargetClass="Standard" ContainsContext="true" ExportDate="{timestamp}" ExportOptions="References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans">
<Controller Use="Context" Name="{controller_name}">
<DataTypes Use="Context">
</DataTypes>
<Tags Use="Context">
{tags_xml}
</Tags>
<Programs Use="Context">
<Program Use="Context" Name="MainProgram" Class="Standard">
<Tags Use="Context">
</Tags>
<Routines Use="Context">
<Routine Use="Target" Name="{routine.name}" Type="RLL">
<Description>
<![CDATA[{routine.description or "Generated by Studio5000-AI-Assistant"}]]>
</Description>
<RLLContent>
{rungs_xml}
</RLLContent>
</Routine>
</Routines>
</Program>
</Programs>
</Controller>
</RSLogix5000Content>'''
        
        # Pretty print the XML
        try:
            root = ET.fromstring(routine_export_template)
            rough_string = ET.tostring(root, 'unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception as e:
            # If pretty printing fails, return raw XML
            return routine_export_template
    
    def save_routine_export(self, routine: Routine, file_path: str, controller_name: str = "MTN6_MCM06", 
                           tags: Optional[List[Dict]] = None, software_revision: str = "36.02") -> bool:
        """Save routine export L5X file"""
        try:
            l5x_content = self.generate_routine_export(routine, controller_name, tags, software_revision)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(l5x_content)
            return True
        except Exception as e:
            print(f"Error saving routine export L5X file: {e}")
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
