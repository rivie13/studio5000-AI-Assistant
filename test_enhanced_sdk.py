#!/usr/bin/env python3
"""
Test the Enhanced SDK Interface with MainProgram and MainTask creation
"""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path('.') / 'src'))

from sdk_interface.studio5000_sdk import Studio5000SDKInterface

async def test_enhanced_sdk():
    print('🚀 Testing Enhanced SDK Interface...')
    print('=' * 50)
    
    sdk = Studio5000SDKInterface()
    
    # Test 1: Empty ACD creation (existing functionality)
    print('\n📁 Test 1: Empty ACD Creation...')
    empty_spec = {
        'name': 'Enhanced_SDK_Test_Empty',
        'controller_type': '1756-L83E',
        'save_path': 'enhanced_test_empty.ACD'
    }
    
    result1 = await sdk.create_empty_acd_project(empty_spec)
    if result1['success']:
        print('✅ Empty ACD creation: WORKS')
        print(f'   Size: {result1["project_info"]["file_size"]} bytes')
    else:
        print(f'❌ Empty ACD creation: FAILED - {result1["error"]}')
    
    # Test 2: Complete ACD creation with MainProgram (NEW functionality)
    print('\n🎯 Test 2: Complete ACD with MainProgram and MainTask...')
    complete_spec = {
        'name': 'Enhanced_SDK_Test_Complete',
        'controller_type': '1756-L83E',
        'save_path': 'enhanced_test_complete.ACD',
        'ladder_logic': '''<Rung Number="0" Type="N">
    <Comment>
        <![CDATA[AI Generated Motor Control Logic]]>
    </Comment>
    <Text>
        <![CDATA[XIC(START_BUTTON)XIO(STOP_BUTTON)OTE(MOTOR_RUN);]]>
    </Text>
</Rung>
<Rung Number="1" Type="N">
    <Comment>
        <![CDATA[Motor Status Indicator]]>
    </Comment>
    <Text>
        <![CDATA[XIC(MOTOR_RUN)OTE(MOTOR_STATUS_LED);]]>
    </Text>
</Rung>'''
    }
    
    try:
        result2 = await sdk.create_acd_project_with_programs(complete_spec)
        if result2['success']:
            print('🎉 Complete ACD creation: SUCCESS!')
            print(f'   File: {result2["project_info"]["file_path"]}')
            print(f'   Size: {result2["project_info"]["file_size"]} bytes')
            print(f'   Has MainProgram: {result2["project_info"]["has_main_program"]}')
            print(f'   Has MainTask: {result2["project_info"]["has_main_task"]}')
            print(f'   Ladder Logic: {result2["ladder_logic_included"]}')
            print('\n🎯 THIS SOLVES THE ORIGINAL PROBLEM!')
            print('   You can now create ACD files with MainProgram + MainTask!')
        else:
            print(f'❌ Complete ACD creation: FAILED - {result2["error"]}')
    except Exception as e:
        print(f'❌ Complete ACD creation: ERROR - {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_sdk())
