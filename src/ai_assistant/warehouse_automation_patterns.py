#!/usr/bin/env python3
"""
Warehouse Automation Pattern Library

This module contains pre-built automation patterns specifically designed
for warehouse and material handling applications.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .enhanced_code_assistant import EnhancedGeneratedCode, AutomationSequence, IndustrialComponent

@dataclass(frozen=True)
class WarehousePattern:
    """Represents a reusable warehouse automation pattern"""
    name: str
    description: str
    components: tuple  # Changed from List[str] to tuple for hashability
    ladder_logic_template: str
    structured_text_template: Optional[str] = None
    required_tags: Optional[tuple] = None  # Changed from List[Dict] to tuple for hashability
    safety_considerations: Optional[tuple] = None  # Changed from List[str] to tuple for hashability
    performance_notes: Optional[tuple] = None  # Changed from List[str] to tuple for hashability

class WarehouseAutomationPatterns:
    """Library of common warehouse automation patterns"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, WarehousePattern]:
        """Initialize the library of warehouse automation patterns"""
        
        patterns = {}
        
        # Conveyor Control Pattern
        patterns['conveyor_control'] = WarehousePattern(
            name="Conveyor Control System",
            description="Basic conveyor with start/stop, jam detection, and speed control",
            components=('motor_starter', 'photoeye_upstream', 'photoeye_downstream', 'jam_timer', 'speed_reference'),
            ladder_logic_template="""
// Conveyor Start/Stop Logic
XIC(CONV_START_PB) XIO(CONV_STOP_PB) XIO(CONV_JAM) XIO(CONV_FAULT) OTE(CONV_RUN);
XIC(CONV_RUN) OTE(CONV_MOTOR);

// Jam Detection Logic  
XIC(CONV_RUN) XIC(PHOTO_UPSTREAM) XIO(PHOTO_DOWNSTREAM) TON(JAM_TIMER,5000,0);
XIC(JAM_TIMER.DN) OTE(CONV_JAM);

// Reset Logic
XIC(CONV_RESET_PB) OTU(CONV_JAM);
XIC(CONV_RESET_PB) RES(JAM_TIMER);

// Speed Control (if VFD present)
XIC(CONV_RUN) MOV(CONV_SPEED_REF,VFD_SPEED_CMD);
""",
            required_tags=(
                {'name': 'CONV_START_PB', 'data_type': 'BOOL', 'description': 'Conveyor start pushbutton'},
                {'name': 'CONV_STOP_PB', 'data_type': 'BOOL', 'description': 'Conveyor stop pushbutton'},
                {'name': 'CONV_RESET_PB', 'data_type': 'BOOL', 'description': 'Conveyor reset pushbutton'},
                {'name': 'CONV_RUN', 'data_type': 'BOOL', 'description': 'Conveyor run command'},
                {'name': 'CONV_MOTOR', 'data_type': 'BOOL', 'description': 'Conveyor motor output'},
                {'name': 'CONV_JAM', 'data_type': 'BOOL', 'description': 'Conveyor jam alarm'},
                {'name': 'CONV_FAULT', 'data_type': 'BOOL', 'description': 'Conveyor fault status'},
                {'name': 'PHOTO_UPSTREAM', 'data_type': 'BOOL', 'description': 'Upstream photoeye'},
                {'name': 'PHOTO_DOWNSTREAM', 'data_type': 'BOOL', 'description': 'Downstream photoeye'},
                {'name': 'JAM_TIMER', 'data_type': 'TIMER', 'description': 'Jam detection timer'},
                {'name': 'CONV_SPEED_REF', 'data_type': 'REAL', 'description': 'Conveyor speed reference'},
                {'name': 'VFD_SPEED_CMD', 'data_type': 'REAL', 'description': 'VFD speed command'}
            ),
            safety_considerations=(
                "Emergency stop must immediately stop conveyor",
                "Jam detection prevents material damage",
                "Guard switches should interlock motor operation"
            )
        )
        
        # Sorting System Pattern
        patterns['sorting_system'] = WarehousePattern(
            name="Package Sorting System",
            description="Automated sorting with barcode scanning and diverter control",
            components=('barcode_scanner', 'diverter_cylinder', 'confirmation_photoeye', 'reject_chute'),
            ladder_logic_template="""
// Scan Trigger Logic
XIC(SCAN_PHOTO) OSR(SCAN_TRIGGER);
XIC(SCAN_TRIGGER) OTE(SCANNER_TRIGGER);

// Sort Decision Logic (from scanner data)
XIC(SORT_DECISION_READY) EQU(SORT_CODE,LANE_1_CODE) OTE(DIVERT_LANE_1);
XIC(SORT_DECISION_READY) EQU(SORT_CODE,LANE_2_CODE) OTE(DIVERT_LANE_2);
XIC(SORT_DECISION_READY) EQU(SORT_CODE,REJECT_CODE) OTE(DIVERT_REJECT);

// Diverter Control with Timing
XIC(DIVERT_LANE_1) XIC(DIVERT_PHOTO) TON(DIVERT_TIMER_1,500,0);
XIC(DIVERT_TIMER_1.DN) OTE(DIVERTER_1_EXTEND);

// Diverter Retract Logic
XIC(DIVERTER_1_EXTEND) TON(RETRACT_TIMER_1,1000,0);
XIC(RETRACT_TIMER_1.DN) OTU(DIVERTER_1_EXTEND);
XIC(RETRACT_TIMER_1.DN) RES(DIVERT_TIMER_1);
XIC(RETRACT_TIMER_1.DN) RES(RETRACT_TIMER_1);

// Sort Confirmation
XIC(CONFIRM_PHOTO_1) CTU(LANE_1_COUNT,9999);
XIC(CONFIRM_PHOTO_2) CTU(LANE_2_COUNT,9999);
""",
            required_tags=(
                {'name': 'SCAN_PHOTO', 'data_type': 'BOOL', 'description': 'Scan trigger photoeye'},
                {'name': 'SCAN_TRIGGER', 'data_type': 'BOOL', 'description': 'Scanner trigger one-shot'},
                {'name': 'SCANNER_TRIGGER', 'data_type': 'BOOL', 'description': 'Scanner trigger output'},
                {'name': 'SORT_DECISION_READY', 'data_type': 'BOOL', 'description': 'Sort decision available'},
                {'name': 'SORT_CODE', 'data_type': 'DINT', 'description': 'Scanned sort code'},
                {'name': 'LANE_1_CODE', 'data_type': 'DINT', 'description': 'Lane 1 destination code'},
                {'name': 'LANE_2_CODE', 'data_type': 'DINT', 'description': 'Lane 2 destination code'},
                {'name': 'REJECT_CODE', 'data_type': 'DINT', 'description': 'Reject destination code'},
                {'name': 'DIVERT_LANE_1', 'data_type': 'BOOL', 'description': 'Divert to lane 1 command'},
                {'name': 'DIVERT_LANE_2', 'data_type': 'BOOL', 'description': 'Divert to lane 2 command'},
                {'name': 'DIVERT_REJECT', 'data_type': 'BOOL', 'description': 'Divert to reject command'},
                {'name': 'DIVERT_PHOTO', 'data_type': 'BOOL', 'description': 'Divert position photoeye'},
                {'name': 'DIVERTER_1_EXTEND', 'data_type': 'BOOL', 'description': 'Diverter 1 extend output'},
                {'name': 'DIVERT_TIMER_1', 'data_type': 'TIMER', 'description': 'Divert activation timer'},
                {'name': 'RETRACT_TIMER_1', 'data_type': 'TIMER', 'description': 'Diverter retract timer'},
                {'name': 'LANE_1_COUNT', 'data_type': 'COUNTER', 'description': 'Lane 1 package counter'},
                {'name': 'LANE_2_COUNT', 'data_type': 'COUNTER', 'description': 'Lane 2 package counter'}
            )
        )
        
        # Palletizing System Pattern
        patterns['palletizing_system'] = WarehousePattern(
            name="Robotic Palletizing System",
            description="Automated palletizing with layer pattern control and safety interlocks",
            components=('robot_controller', 'gripper', 'pallet_station', 'layer_counter', 'safety_scanner'),
            ladder_logic_template="""
// System Ready Conditions
XIC(ROBOT_READY) XIC(GRIPPER_READY) XIC(PALLET_PRESENT) XIC(SAFETY_OK) OTE(SYSTEM_READY);

// Palletizing Sequence Control
XIC(SYSTEM_READY) XIC(PACKAGE_READY) XIC(CYCLE_START) OTE(START_PALLETIZE);

// Pick Sequence
XIC(START_PALLETIZE) XIC(ROBOT_AT_PICK) OTE(GRIPPER_CLOSE);
XIC(GRIPPER_CLOSED_FB) TON(GRIP_DELAY,500,0);
XIC(GRIP_DELAY.DN) OTE(MOVE_TO_PLACE);

// Place Sequence  
XIC(MOVE_TO_PLACE) XIC(ROBOT_AT_PLACE) OTE(GRIPPER_OPEN);
XIC(GRIPPER_OPENED_FB) OTE(PACKAGE_PLACED);

// Layer and Pallet Counting
XIC(PACKAGE_PLACED) OSR(COUNT_TRIGGER);
XIC(COUNT_TRIGGER) CTU(LAYER_COUNT,PACKAGES_PER_LAYER);
XIC(LAYER_COUNT.DN) CTU(PALLET_COUNT,LAYERS_PER_PALLET);
XIC(LAYER_COUNT.DN) RES(LAYER_COUNT);

// Pallet Complete Logic
XIC(PALLET_COUNT.DN) OTE(PALLET_COMPLETE);
XIC(PALLET_COMPLETE) OTE(REQUEST_NEW_PALLET);
XIC(NEW_PALLET_READY) RES(PALLET_COUNT);

// Safety Interlock
XIO(SAFETY_SCANNER) XIO(LIGHT_CURTAIN) OTE(SAFETY_FAULT);
XIC(SAFETY_FAULT) OTU(SYSTEM_READY);
""",
            required_tags=(
                {'name': 'ROBOT_READY', 'data_type': 'BOOL', 'description': 'Robot system ready'},
                {'name': 'GRIPPER_READY', 'data_type': 'BOOL', 'description': 'Gripper system ready'},
                {'name': 'PALLET_PRESENT', 'data_type': 'BOOL', 'description': 'Pallet in position'},
                {'name': 'SAFETY_OK', 'data_type': 'BOOL', 'description': 'All safety systems OK'},
                {'name': 'SYSTEM_READY', 'data_type': 'BOOL', 'description': 'System ready for operation'},
                {'name': 'PACKAGE_READY', 'data_type': 'BOOL', 'description': 'Package ready for pickup'},
                {'name': 'CYCLE_START', 'data_type': 'BOOL', 'description': 'Cycle start command'},
                {'name': 'PACKAGES_PER_LAYER', 'data_type': 'DINT', 'description': 'Packages per layer setpoint'},
                {'name': 'LAYERS_PER_PALLET', 'data_type': 'DINT', 'description': 'Layers per pallet setpoint'},
                {'name': 'LAYER_COUNT', 'data_type': 'COUNTER', 'description': 'Current layer package count'},
                {'name': 'PALLET_COUNT', 'data_type': 'COUNTER', 'description': 'Current pallet layer count'}
            ),
            safety_considerations=(
                "Safety scanner must stop robot motion immediately",
                "Light curtains protect operator access areas", 
                "Gripper must have positive feedback for open/closed states",
                "Emergency stop accessible from all operator positions"
            )
        )
        
        # AGV Integration Pattern
        patterns['agv_integration'] = WarehousePattern(
            name="AGV Integration System",
            description="Automated Guided Vehicle integration with warehouse systems",
            components=('agv_controller', 'docking_station', 'load_sensors', 'traffic_control'),
            ladder_logic_template="""
// AGV Request Handling
XIC(AGV_REQUEST) XIC(STATION_AVAILABLE) OTE(AGV_APPROVED);
XIC(AGV_APPROVED) OTE(STATION_RESERVED);

// Docking Sequence
XIC(AGV_AT_STATION) XIC(DOCKING_SENSORS_OK) OTE(AGV_DOCKED);
XIC(AGV_DOCKED) TON(SETTLE_TIMER,2000,0);
XIC(SETTLE_TIMER.DN) OTE(DOCKING_COMPLETE);

// Load Transfer Logic
XIC(DOCKING_COMPLETE) XIC(LOAD_TRANSFER_CMD) OTE(TRANSFER_ACTIVE);
XIC(TRANSFER_ACTIVE) XIC(CONVEYOR_TO_AGV) OTE(CONV_TO_AGV_RUN);
XIC(TRANSFER_ACTIVE) XIC(AGV_TO_CONVEYOR) OTE(AGV_TO_CONV_RUN);

// Load Confirmation
XIC(LOAD_SENSORS_AGV) XIO(LOAD_SENSORS_CONV) OTE(LOAD_ON_AGV);
XIO(LOAD_SENSORS_AGV) XIC(LOAD_SENSORS_CONV) OTE(LOAD_ON_CONV);

// Transfer Complete Logic
XIC(LOAD_ON_AGV) XIC(CONVEYOR_TO_AGV) OTE(TRANSFER_TO_AGV_COMPLETE);
XIC(LOAD_ON_CONV) XIC(AGV_TO_CONVEYOR) OTE(TRANSFER_TO_CONV_COMPLETE);

// AGV Release Logic
XIC(TRANSFER_TO_AGV_COMPLETE) XIC(AGV_READY_TO_LEAVE) OTE(RELEASE_AGV);
XIC(TRANSFER_TO_CONV_COMPLETE) XIC(AGV_READY_TO_LEAVE) OTE(RELEASE_AGV);
XIC(RELEASE_AGV) OTU(STATION_RESERVED);

// Traffic Control
XIC(AGV_IN_ZONE_1) OTE(ZONE_1_OCCUPIED);
XIC(ZONE_1_OCCUPIED) OTU(ZONE_1_CLEAR_FOR_ENTRY);
""",
            required_tags=(
                {'name': 'AGV_REQUEST', 'data_type': 'BOOL', 'description': 'AGV requests station access'},
                {'name': 'STATION_AVAILABLE', 'data_type': 'BOOL', 'description': 'Station available for AGV'},
                {'name': 'AGV_APPROVED', 'data_type': 'BOOL', 'description': 'AGV access approved'},
                {'name': 'STATION_RESERVED', 'data_type': 'BOOL', 'description': 'Station reserved for AGV'},
                {'name': 'AGV_AT_STATION', 'data_type': 'BOOL', 'description': 'AGV positioned at station'},
                {'name': 'DOCKING_SENSORS_OK', 'data_type': 'BOOL', 'description': 'AGV properly positioned'},
                {'name': 'LOAD_TRANSFER_CMD', 'data_type': 'BOOL', 'description': 'Load transfer command'},
                {'name': 'CONVEYOR_TO_AGV', 'data_type': 'BOOL', 'description': 'Transfer direction: conv to AGV'},
                {'name': 'AGV_TO_CONVEYOR', 'data_type': 'BOOL', 'description': 'Transfer direction: AGV to conv'},
                {'name': 'LOAD_SENSORS_AGV', 'data_type': 'BOOL', 'description': 'Load present on AGV'},
                {'name': 'LOAD_SENSORS_CONV', 'data_type': 'BOOL', 'description': 'Load present on conveyor'}
            )
        )
        
        # Safety Interlock Pattern
        patterns['safety_interlock'] = WarehousePattern(
            name="Comprehensive Safety Interlock System",
            description="Multi-level safety system with emergency stops, light curtains, and guard monitoring",
            components=('emergency_stops', 'light_curtains', 'guard_switches', 'safety_relays'),
            ladder_logic_template="""
// Emergency Stop Chain (Category 3/4 Safety)
XIC(E_STOP_1_OK) XIC(E_STOP_2_OK) XIC(E_STOP_3_OK) XIC(E_STOP_RESET) OTE(E_STOP_CHAIN_OK);

// Guard Switch Monitoring
XIC(GUARD_1_CLOSED) XIC(GUARD_2_CLOSED) XIC(GUARD_3_CLOSED) OTE(GUARDS_OK);

// Light Curtain Safety
XIC(LIGHT_CURTAIN_1_OK) XIC(LIGHT_CURTAIN_2_OK) XIO(LC_MUTE_ACTIVE) OTE(LIGHT_CURTAINS_OK);

// Safety Mat Monitoring
XIO(SAFETY_MAT_1) XIO(SAFETY_MAT_2) OTE(SAFETY_MATS_OK);

// Master Safety Logic
XIC(E_STOP_CHAIN_OK) XIC(GUARDS_OK) XIC(LIGHT_CURTAINS_OK) XIC(SAFETY_MATS_OK) OTE(SAFETY_OK);

// Safety Fault Detection
XIO(SAFETY_OK) OSR(SAFETY_FAULT_TRIGGER);
XIC(SAFETY_FAULT_TRIGGER) OTE(SAFETY_FAULT_LATCH);

// Fault Reset Logic (requires manual reset)
XIC(SAFETY_RESET_PB) XIC(SAFETY_OK) OTU(SAFETY_FAULT_LATCH);

// Equipment Interlock (all equipment must check this)
XIC(SAFETY_OK) XIO(SAFETY_FAULT_LATCH) OTE(EQUIPMENT_ENABLE);

// Diagnostic Monitoring
XIC(E_STOP_1_FAULT) XIC(E_STOP_2_FAULT) XIC(E_STOP_3_FAULT) OTE(E_STOP_DIAGNOSTIC_FAULT);
XIC(GUARD_1_FAULT) XIC(GUARD_2_FAULT) XIC(GUARD_3_FAULT) OTE(GUARD_DIAGNOSTIC_FAULT);
""",
            required_tags=(
                {'name': 'E_STOP_1_OK', 'data_type': 'BOOL', 'description': 'Emergency stop 1 OK status'},
                {'name': 'E_STOP_2_OK', 'data_type': 'BOOL', 'description': 'Emergency stop 2 OK status'},
                {'name': 'E_STOP_3_OK', 'data_type': 'BOOL', 'description': 'Emergency stop 3 OK status'},
                {'name': 'E_STOP_RESET', 'data_type': 'BOOL', 'description': 'Emergency stop reset button'},
                {'name': 'GUARD_1_CLOSED', 'data_type': 'BOOL', 'description': 'Guard switch 1 closed'},
                {'name': 'GUARD_2_CLOSED', 'data_type': 'BOOL', 'description': 'Guard switch 2 closed'},
                {'name': 'GUARD_3_CLOSED', 'data_type': 'BOOL', 'description': 'Guard switch 3 closed'},
                {'name': 'LIGHT_CURTAIN_1_OK', 'data_type': 'BOOL', 'description': 'Light curtain 1 OK'},
                {'name': 'LIGHT_CURTAIN_2_OK', 'data_type': 'BOOL', 'description': 'Light curtain 2 OK'},
                {'name': 'SAFETY_MAT_1', 'data_type': 'BOOL', 'description': 'Safety mat 1 activated'},
                {'name': 'SAFETY_MAT_2', 'data_type': 'BOOL', 'description': 'Safety mat 2 activated'},
                {'name': 'SAFETY_OK', 'data_type': 'BOOL', 'description': 'Master safety OK status'},
                {'name': 'EQUIPMENT_ENABLE', 'data_type': 'BOOL', 'description': 'Equipment operation enable'}
            ),
            safety_considerations=(
                "Complies with ISO 13849 Category 3/4 requirements",
                "Dual channel monitoring for critical functions",
                "Positive feedback required for all safety devices",
                "Manual reset required after safety fault",
                "Diagnostic monitoring for safety device health"
            )
        )
        
        return patterns
    
    def get_pattern(self, pattern_name: str) -> Optional[WarehousePattern]:
        """Get a specific automation pattern"""
        return self.patterns.get(pattern_name)
    
    def find_matching_patterns(self, description: str) -> List[WarehousePattern]:
        """Find patterns that match the given description"""
        description_lower = description.lower()
        matching_patterns = []
        
        pattern_keywords = {
            'conveyor_control': ['conveyor', 'belt', 'transport', 'jam'],
            'sorting_system': ['sort', 'divert', 'scanner', 'barcode'],
            'palletizing_system': ['pallet', 'robot', 'stack', 'layer'],
            'agv_integration': ['agv', 'automated guided vehicle', 'docking'],
            'safety_interlock': ['safety', 'interlock', 'e-stop', 'guard', 'light curtain']
        }
        
        for pattern_name, keywords in pattern_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                pattern = self.get_pattern(pattern_name)
                if pattern:
                    matching_patterns.append(pattern)
        
        return matching_patterns
    
    def get_all_patterns(self) -> List[WarehousePattern]:
        """Get all available patterns"""
        return list(self.patterns.values())

