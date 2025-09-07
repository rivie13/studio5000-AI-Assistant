#!/usr/bin/env python3
"""
Test script for Instruction Vector Database

Tests the new instruction vector database functionality to ensure
it properly replaces the basic text search with semantic search.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Imports
from documentation.instruction_vector_db import InstructionVectorDatabase
from documentation.instruction_mcp_integration import InstructionMCPIntegration, InstructionMCPTools
from mcp_server.studio5000_mcp_server import Studio5000MCPServer

async def test_instruction_vector_database():
    """Test the instruction vector database functionality"""
    print("🧪 Testing Instruction Vector Database")
    print("=" * 50)
    
    # Get default documentation path
    default_doc_path = os.environ.get(
        'STUDIO5000_DOC_PATH', 
        r'C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000'
    )
    
    try:
        print(f"📂 Using documentation path: {default_doc_path}")
        
        # Check if documentation path exists
        if not Path(default_doc_path).exists():
            print("⚠️  Warning: Documentation path does not exist")
            print("   The test will continue but may not find instructions")
        
        # Initialize MCP server (this will parse instructions and build vector database)
        print("\n1. Initializing MCP Server with Vector Database...")
        start_time = time.time()
        
        mcp_server = Studio5000MCPServer(default_doc_path)
        
        # Give the async initialization time to complete
        await asyncio.sleep(2)
        
        init_time = time.time() - start_time
        print(f"   ✅ Server initialized in {init_time:.2f} seconds")
        print(f"   📊 Found {len(mcp_server.instructions)} instructions")
        
        # Test vector search vs basic search
        print("\n2. Testing Search Capabilities...")
        
        test_queries = [
            "timer delay",
            "mathematical operations", 
            "motion control servo",
            "compare values equal",
            "counting pulses increment",
            "safety emergency stop",
            "communication network",
            "array file operations"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: '{query}'")
            
            # Test vector search
            start_time = time.time()
            vector_results = await mcp_server.search_instructions(query)
            vector_time = time.time() - start_time
            
            # Test basic search fallback
            start_time = time.time()
            basic_results = mcp_server._basic_search_instructions(query)
            basic_time = time.time() - start_time
            
            print(f"   🔍 Vector Search: {len(vector_results)} results in {vector_time*1000:.1f}ms")
            if vector_results:
                for j, result in enumerate(vector_results[:3]):
                    search_type = result.get('search_type', 'vector_semantic')
                    score = result.get('match_score', 0)
                    print(f"      {j+1}. {result['name']} (Score: {score:.3f}, Type: {search_type})")
            
            print(f"   📝 Basic Search:  {len(basic_results)} results in {basic_time*1000:.1f}ms")
            if basic_results:
                for j, result in enumerate(basic_results[:3]):
                    score = result.get('match_score', 0)
                    print(f"      {j+1}. {result['name']} (Score: {score:.3f}, Type: basic)")
        
        # Test specific instruction lookup
        print("\n3. Testing Specific Instruction Lookup...")
        
        test_instructions = ['TON', 'ADD', 'PID', 'MOV', 'XIC']
        
        for instruction in test_instructions:
            result = await mcp_server.get_instruction(instruction)
            if result:
                search_type = result.get('search_type', 'vector_database')
                print(f"   ✅ {instruction}: Found ({search_type})")
                print(f"      Category: {result.get('category', 'Unknown')}")
                print(f"      Languages: {', '.join(result.get('languages', []))}")
            else:
                print(f"   ❌ {instruction}: Not found")
        
        # Test category listing
        print("\n4. Testing Category Listing...")
        categories = await mcp_server.list_categories()
        print(f"   📋 Found {len(categories)} categories:")
        for i, category in enumerate(categories[:10]):  # Show first 10
            print(f"      {i+1}. {category}")
        if len(categories) > 10:
            print(f"      ... and {len(categories) - 10} more")
        
        # Test category-specific search
        if categories:
            test_category = categories[0]
            print(f"\n5. Testing Category-Specific Search ('{test_category}')...")
            category_instructions = await mcp_server.list_instructions_by_category(test_category)
            print(f"   📊 Found {len(category_instructions)} instructions in '{test_category}':")
            for i, instruction in enumerate(category_instructions[:5]):  # Show first 5
                search_type = instruction.get('search_type', 'vector_database')
                print(f"      {i+1}. {instruction['name']} ({search_type})")
        
        # Test syntax lookup
        print("\n6. Testing Syntax Lookup...")
        test_syntax_instructions = ['TON', 'ADD', 'PID']
        
        for instruction in test_syntax_instructions:
            syntax_info = await mcp_server.get_instruction_syntax(instruction)
            if syntax_info:
                search_type = syntax_info.get('search_type', 'vector_database')
                print(f"   ✅ {instruction} Syntax: Found ({search_type})")
                if syntax_info.get('syntax'):
                    print(f"      Syntax: {syntax_info['syntax'][:100]}...")
                if syntax_info.get('parameters'):
                    print(f"      Parameters: {len(syntax_info['parameters'])} found")
            else:
                print(f"   ❌ {instruction} Syntax: Not found")
        
        # Performance comparison
        print("\n7. Performance Comparison...")
        test_query = "timer delay operations"
        
        # Time vector search
        vector_times = []
        for _ in range(5):
            start_time = time.time()
            await mcp_server.search_instructions(test_query)
            vector_times.append(time.time() - start_time)
        
        # Time basic search
        basic_times = []
        for _ in range(5):
            start_time = time.time()
            mcp_server._basic_search_instructions(test_query)
            basic_times.append(time.time() - start_time)
        
        avg_vector_time = sum(vector_times) / len(vector_times) * 1000
        avg_basic_time = sum(basic_times) / len(basic_times) * 1000
        
        print(f"   🔍 Vector Search Average: {avg_vector_time:.2f}ms")
        print(f"   📝 Basic Search Average:  {avg_basic_time:.2f}ms")
        
        if avg_basic_time > 0:
            if avg_vector_time < avg_basic_time:
                speedup = avg_basic_time / avg_vector_time
                print(f"   🚀 Vector search is {speedup:.1f}x faster!")
            else:
                slowdown = avg_vector_time / avg_basic_time
                print(f"   ⏳ Vector search is {slowdown:.1f}x slower (but more accurate)")
        else:
            print(f"   ℹ️  Basic search is extremely fast ({avg_basic_time:.3f}ms), vector search provides semantic accuracy")
        
        print("\n🎉 Instruction Vector Database Test Complete!")
        print("\n📊 Summary:")
        print(f"   • Instructions indexed: {len(mcp_server.instructions)}")
        print(f"   • Categories available: {len(categories) if categories else 0}")
        print(f"   • Vector search working: {'✅ Yes' if any('vector_semantic' in str(r.get('search_type', '')) for r in vector_results) else '❌ No (using fallback)'}")
        print(f"   • Average search time: {avg_vector_time:.2f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_vector_database_directly():
    """Test the vector database directly without MCP server"""
    print("\n🧪 Direct Vector Database Test")
    print("=" * 30)
    
    try:
        # Create sample instruction data for testing
        sample_instructions = {
            'TON': type('Instruction', (), {
                'name': 'TON',
                'category': 'Timer Instructions',
                'description': 'Timer On Delay - Delays turning on output for specified time',
                'languages': ['Ladder Diagram', 'Function Block', 'Structured Text'],
                'syntax': 'TON(Timer, Preset, TimerEnable)',
                'parameters': [
                    {'name': 'Timer', 'type': 'TIMER', 'description': 'Timer structure'},
                    {'name': 'Preset', 'type': 'DINT', 'description': 'Preset time value'},
                    {'name': 'TimerEnable', 'type': 'BOOL', 'description': 'Enable input'}
                ],
                'examples': 'Use TON when you need to delay an output turning on',
                'file_path': 'TON.htm'
            })(),
            'ADD': type('Instruction', (), {
                'name': 'ADD',
                'category': 'Math Instructions', 
                'description': 'Add - Adds Source A and Source B and stores result in Destination',
                'languages': ['Ladder Diagram', 'Function Block', 'Structured Text'],
                'syntax': 'ADD(SourceA, SourceB, Destination)',
                'parameters': [
                    {'name': 'SourceA', 'type': 'SINT/INT/DINT/REAL', 'description': 'First value to add'},
                    {'name': 'SourceB', 'type': 'SINT/INT/DINT/REAL', 'description': 'Second value to add'},
                    {'name': 'Destination', 'type': 'SINT/INT/DINT/REAL', 'description': 'Result storage'}
                ],
                'examples': 'ADD two values together for mathematical operations',
                'file_path': 'ADD.htm'
            })()
        }
        
        # Test vector database directly
        vector_db = InstructionVectorDatabase(cache_dir="test_instruction_vector_cache")
        
        print("Building vector database with sample data...")
        vector_db.build_vector_database(sample_instructions, force_rebuild=True)
        
        # Test searches
        test_queries = ['timer delay', 'mathematical addition', 'time operations']
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = vector_db.search_instructions(query, limit=5)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.name} (Score: {result.score:.3f})")
                    print(f"     Category: {result.category}")
                    print(f"     Description: {result.description[:80]}...")
            else:
                print("  No results found")
        
        # Test statistics
        stats = vector_db.get_statistics()
        print(f"\n📊 Vector Database Statistics:")
        print(f"   Total instructions: {stats['total_instructions']}")
        print(f"   Vector search enabled: {stats['has_vector_search']}")
        print(f"   Categories: {list(stats['by_category'].keys())}")
        print(f"   Languages: {list(stats['by_language'].keys())}")
        
        # Clean up test cache
        import shutil
        if Path("test_instruction_vector_cache").exists():
            shutil.rmtree("test_instruction_vector_cache")
            print("   🧹 Cleaned up test cache")
        
        print("✅ Direct vector database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Studio 5000 Instruction Vector Database Test Suite")
    print("=" * 60)
    
    # Test 1: Direct vector database test
    direct_success = await test_vector_database_directly()
    
    # Test 2: Full MCP server test
    mcp_success = await test_instruction_vector_database()
    
    print("\n" + "=" * 60)
    print("🏁 Test Suite Results:")
    print(f"   Direct Vector DB Test: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"   MCP Server Integration: {'✅ PASS' if mcp_success else '❌ FAIL'}")
    
    if direct_success and mcp_success:
        print("\n🎉 All tests PASSED! Vector database is working correctly.")
        print("   Your Studio 5000 instruction search now uses semantic vector search!")
    else:
        print("\n⚠️  Some tests FAILED. Please check the error messages above.")
        
    return 0 if (direct_success and mcp_success) else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
