#!/usr/bin/env python3
"""
Tag Content Chunk Data Structures

Defines the data structures for representing searchable chunks of Studio 5000 tag CSV data
including I/O mappings, device information, and physical addressing.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class TagChunkType(Enum):
    """Types of tag chunks for semantic indexing"""
    TAG_DEFINITION = "tag_definition"
    I_O_POINT = "i_o_point"
    DEVICE = "device"
    MODULE = "module"
    SAFETY_TAG = "safety_tag"
    ANALOG_TAG = "analog_tag"
    MOTOR_TAG = "motor_tag"
    SENSOR_TAG = "sensor_tag"
    VALVE_TAG = "valve_tag"
    HMI_TAG = "hmi_tag"
    ALARM_TAG = "alarm_tag"

@dataclass
class DeviceInfo:
    """Physical device and module information"""
    module_type: str = ""           # AB:35_APF_Drive, AB:1756-OB16E, etc.
    rack: Optional[int] = None      # Rack number
    slot: Optional[int] = None      # Slot number  
    channel: Optional[int] = None   # I/O channel
    local_address: str = ""         # Local:x:I.Data.x format
    device_category: str = ""       # VFD, DI, DO, AI, AO, Safety
    connection_type: str = ""       # Input, Output, Safety Input, Safety Output

@dataclass
class TagChunk:
    """Represents a searchable chunk of tag data from Studio 5000 CSV export"""
    
    # Core identification
    id: str                         # Unique identifier
    chunk_type: TagChunkType        # Type of tag chunk
    tag_name: str                   # Full hierarchical tag name
    
    # Description and function
    description: str                # Human-readable description
    function: str                   # Auto-detected function (motor, sensor, valve, etc.)
    category: str                   # Auto-categorized device type
    
    # Data type information
    data_type: str                  # BOOL, DINT, REAL, UDT name
    alias: Optional[str] = None     # Alias tag if exists
    engineering_units: str = ""     # RPM, PSI, °F, etc.
    
    # Physical device information
    device_info: DeviceInfo = None  # Module and I/O address details
    
    # Context and relationships
    related_tags: List[str] = None  # Related tags (same device/function)
    dependencies: List[str] = None  # Tags this depends on
    
    # Additional metadata
    metadata: Dict[str, Any] = None # Additional CSV columns and context
    
    def __post_init__(self):
        if self.related_tags is None:
            self.related_tags = []
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}
        if self.device_info is None:
            self.device_info = DeviceInfo()
    
    @property
    def searchable_text(self) -> str:
        """Generate comprehensive text for vector embedding"""
        parts = [
            f"Tag: {self.tag_name}",
            f"Type: {self.chunk_type.value}",
            f"Description: {self.description}",
            f"Function: {self.function}",
            f"Category: {self.category}",
            f"Data Type: {self.data_type}"
        ]
        
        if self.alias:
            parts.append(f"Alias: {self.alias}")
        
        if self.engineering_units:
            parts.append(f"Units: {self.engineering_units}")
        
        # Add device information
        if self.device_info.module_type:
            parts.append(f"Module: {self.device_info.module_type}")
        
        if self.device_info.local_address:
            parts.append(f"Address: {self.device_info.local_address}")
        
        if self.device_info.rack is not None:
            parts.append(f"Rack: {self.device_info.rack}")
        
        if self.device_info.slot is not None:
            parts.append(f"Slot: {self.device_info.slot}")
        
        if self.device_info.device_category:
            parts.append(f"Device Category: {self.device_info.device_category}")
        
        # Add relationships
        if self.related_tags:
            parts.append(f"Related Tags: {', '.join(self.related_tags[:5])}")
        
        # Add metadata keywords
        for key, value in self.metadata.items():
            if isinstance(value, str) and value:
                parts.append(f"{key}: {value}")
        
        return " | ".join(parts)
    
    @property
    def is_safety_tag(self) -> bool:
        """Check if this is a safety-related tag"""
        return (self.chunk_type == TagChunkType.SAFETY_TAG or 
                'safety' in self.description.lower() or
                'estop' in self.description.lower() or
                'emergency' in self.description.lower())
    
    @property
    def is_motor_control(self) -> bool:
        """Check if this is motor control related"""
        return (self.chunk_type == TagChunkType.MOTOR_TAG or
                'motor' in self.description.lower() or
                'drive' in self.description.lower() or
                'vfd' in self.description.lower())
    
    @property
    def is_sensor(self) -> bool:
        """Check if this is a sensor input"""
        return (self.chunk_type == TagChunkType.SENSOR_TAG or
                'sensor' in self.description.lower() or
                'photoeye' in self.description.lower() or
                'proximity' in self.description.lower())

def categorize_tag_by_name_and_description(tag_name: str, description: str) -> TagChunkType:
    """Auto-categorize tag based on name and description patterns"""
    
    # Combine name and description for analysis
    combined_text = f"{tag_name} {description}".lower()
    
    # Safety tags - highest priority
    safety_keywords = ['estop', 'emergency', 'safety', 'pullcord', 'guard', 'interlock', 'light curtain', 
                      'es_lt', 'stop actuated', 'safety active', 'sto', 'epc', 'safety input']
    if any(keyword in combined_text for keyword in safety_keywords):
        return TagChunkType.SAFETY_TAG
    
    # Motor control tags
    motor_keywords = ['motor', 'drive', 'vfd', 'conveyor', 'run', 'start', 'stop']
    if any(keyword in combined_text for keyword in motor_keywords):
        return TagChunkType.MOTOR_TAG
    
    # Sensor tags
    sensor_keywords = ['sensor', 'photoeye', 'pe', 'proximity', 'switch', 'tracking']
    if any(keyword in combined_text for keyword in sensor_keywords):
        return TagChunkType.SENSOR_TAG
    
    # Valve/actuator tags
    valve_keywords = ['valve', 'solenoid', 'cylinder', 'actuator', 'air']
    if any(keyword in combined_text for keyword in valve_keywords):
        return TagChunkType.VALVE_TAG
    
    # HMI/operator interface tags
    hmi_keywords = ['hmi', 'pushbutton', 'button', 'display', 'operator', 'lamp', 'beacon']
    if any(keyword in combined_text for keyword in hmi_keywords):
        return TagChunkType.HMI_TAG
    
    # I/O Point tags (FIO, SIO, etc.)
    io_keywords = ['fio', 'sio', 'field i/o', 'safety i/o']
    if any(keyword in combined_text for keyword in io_keywords):
        return TagChunkType.I_O_POINT
    
    # Alarm tags
    alarm_keywords = ['alarm', 'fault', 'error', 'warning', 'alert']
    if any(keyword in combined_text for keyword in alarm_keywords):
        return TagChunkType.ALARM_TAG
    
    # Analog tags (by data type)
    if 'real' in tag_name.lower() or 'analog' in combined_text:
        return TagChunkType.ANALOG_TAG
    
    # Default to I/O point for digital I/O
    return TagChunkType.I_O_POINT

def extract_device_info_from_address(tag_name: str, data_type: str, description: str) -> DeviceInfo:
    """Extract device information from tag name and data type"""
    
    device_info = DeviceInfo()
    
    # Parse module type from data type (e.g., "AB:35_APF_Drive:I:1")
    if ':' in data_type:
        parts = data_type.split(':')
        if len(parts) >= 2:
            device_info.module_type = ':'.join(parts[:2])  # "AB:35_APF_Drive"
            
            # Extract I/O direction and slot
            if len(parts) >= 3:
                device_info.connection_type = parts[2]  # "I", "O", "SI", "SO"
            if len(parts) >= 4:
                try:
                    device_info.slot = int(parts[3])
                except ValueError:
                    pass
    
    # Parse Local address format (Local:2:I.Data.5)
    local_match = re.search(r'Local:(\d+):([IO])\.Data\.(\d+)', tag_name)
    if local_match:
        device_info.rack = int(local_match.group(1))
        device_info.connection_type = local_match.group(2)
        device_info.channel = int(local_match.group(3))
        device_info.local_address = local_match.group(0)
    
    # Categorize device type
    if 'drive' in device_info.module_type.lower() or 'vfd' in device_info.module_type.lower():
        device_info.device_category = "VFD"
    elif 'safety' in device_info.connection_type.lower() or device_info.connection_type.startswith('S'):
        device_info.device_category = "Safety"
    elif device_info.connection_type == 'I':
        device_info.device_category = "DI"  # Digital Input
    elif device_info.connection_type == 'O':
        device_info.device_category = "DO"  # Digital Output
    elif 'analog' in device_info.module_type.lower():
        device_info.device_category = "AI" if device_info.connection_type == 'I' else "AO"
    
    return device_info

def detect_function_from_description(description: str, tag_name: str = "") -> str:
    """Detect the primary function of a device from its description and tag name"""
    
    desc_lower = description.lower()
    tag_lower = tag_name.lower()
    
    # Combine description and tag name for analysis
    combined_text = f"{desc_lower} {tag_lower}"
    
    # Remove common prefixes/suffixes to focus on core function
    desc_clean = re.sub(r'\$L.*?\$L', '', combined_text)  # Remove $L...$L markers
    desc_clean = re.sub(r'[_\-\s]+', ' ', desc_clean).strip()
    
    # If description is empty/minimal, focus on tag name patterns
    if len(desc_lower.strip()) < 5:  # Very short/empty description
        if 'sol' in tag_lower:
            return "Solenoid Valve"
        elif 'vfd' in tag_lower:
            return "Vfd Control"
        elif 'bcn' in tag_lower:
            return "Beacon Light"
        elif 'dpm' in tag_lower:
            return "Device Power Module"
        elif 'sio' in tag_lower:
            return "Safety I/O Point"
        elif 'fio' in tag_lower:
            return "Field I/O Point"
    
    # Enhanced function detection patterns
    function_patterns = {
        'emergency_stop': ['estop', 'emergency stop', 'pullcord', 'e-stop', 'es_lt', 'emergency', 'stop actuated'],
        'photoeye': ['photoeye', 'tracking photoeye', 'pe', 'photo eye', 'beam', 'tracking'],
        'proximity_sensor': ['proximity', 'prox sensor', 'prox', 'sensor'],
        'conveyor_motor': ['conveyor motor', 'motor', 'drive', 'conveyor', 'vfd'],
        'beacon_light': ['beacon', 'light', 'lamp', 'bcn', 'red beacon', 'green beacon'],
        'pushbutton': ['pushbutton', 'button', 'pb', 'push button', 'enable', 'start', 'stop'],
        'solenoid_valve': ['solenoid', 'valve', 'sol'],
        'air_cylinder': ['cylinder', 'actuator'],
        'speed_feedback': ['speed', 'encoder', 'feedback'],
        'pressure_sensor': ['pressure', 'psi'],
        'temperature_sensor': ['temperature', 'temp'],
        'flow_sensor': ['flow', 'flow rate'],
        'level_sensor': ['level', 'tank level'],
        'disconnect': ['disconnect', 'disc', 'disconnector'],
        'vfd_control': ['vfd', 'variable frequency drive', 'drive'],
        'safety_input': ['safety input', 'safety', 'sto', 'safety active'],
        'chute_control': ['chute', 'enable', 'chute enable'],
        'safety_io_point': ['sio', 'safety i/o', 'safety io'],
        'field_io_point': ['fio', 'field i/o', 'field io']
    }
    
    # Find best matching function
    for function, keywords in function_patterns.items():
        if any(keyword in desc_clean for keyword in keywords):
            return function.replace('_', ' ').title()
    
    # Default to generic descriptions
    if 'input' in desc_clean:
        return "Digital Input"
    elif 'output' in desc_clean:
        return "Digital Output" 
    else:
        return "Unknown Function"

def create_tag_chunk_from_csv_row(tag_name: str, description: str, data_type: str, 
                                 comment_data: Dict[str, str] = None) -> TagChunk:
    """Factory function to create a tag chunk from CSV row data"""
    
    # Auto-categorize the tag
    chunk_type = categorize_tag_by_name_and_description(tag_name, description)
    
    # Extract device information
    device_info = extract_device_info_from_address(tag_name, data_type, description)
    
    # Determine category
    category = chunk_type.value.replace('_', ' ').title()
    
    # Create unique ID
    chunk_id = f"tag_{tag_name.replace(':', '_').replace('.', '_')}"
    
    # Combine comment data if available
    full_description = description
    if comment_data:
        comment_parts = []
        for comment_key, comment_desc in comment_data.items():
            if comment_desc and comment_desc != description:
                comment_parts.append(comment_desc)
        if comment_parts:
            full_description += " | " + " | ".join(comment_parts)
    
    # Detect primary function AFTER combining all description data
    function = detect_function_from_description(full_description, tag_name)
    
    return TagChunk(
        id=chunk_id,
        chunk_type=chunk_type,
        tag_name=tag_name,
        description=full_description,
        function=function,
        category=category,
        data_type=data_type,
        device_info=device_info,
        metadata={
            'original_description': description,
            'comment_data': comment_data or {}
        }
    )

def find_related_tags(tag_chunks: List[TagChunk], target_chunk: TagChunk) -> List[str]:
    """Find tags related to the target chunk (same device, module, or function)"""
    
    related = []
    target_device = target_chunk.device_info
    
    for chunk in tag_chunks:
        if chunk.id == target_chunk.id:
            continue
        
        chunk_device = chunk.device_info
        
        # Same module/slot relationship
        if (target_device.rack == chunk_device.rack and 
            target_device.slot == chunk_device.slot and
            target_device.rack is not None):
            related.append(chunk.tag_name)
        
        # Same device type and similar function
        elif (target_device.module_type == chunk_device.module_type and
              target_chunk.function == chunk.function):
            related.append(chunk.tag_name)
        
        # Same base tag name (e.g., VFD1:I and VFD1:O)
        elif ':' in target_chunk.tag_name and ':' in chunk.tag_name:
            target_base = target_chunk.tag_name.split(':')[0]
            chunk_base = chunk.tag_name.split(':')[0]
            if target_base == chunk_base:
                related.append(chunk.tag_name)
    
    return related[:10]  # Limit to 10 related tags
