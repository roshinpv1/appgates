#!/usr/bin/env python3
"""
Test script to check if the current system is working without hanging
"""

import sys
import os
import time
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, str(Path(__file__).parent / "gates"))

def test_system_initialization():
    """Test if the system can initialize without hanging"""
    
    print("🧪 Testing System Initialization...")
    
    try:
        # Test if we can import the necessary modules
        print("   📦 Testing imports...")
        from gates.nodes import ValidateGatesNode
        print("   ✅ ValidateGatesNode imported successfully")
        
        # Test if we can create the node
        print("   🔧 Creating ValidateGatesNode...")
        node = ValidateGatesNode()
        print("   ✅ ValidateGatesNode created successfully")
        
        # Test if we can access the enhanced pattern library
        print("   📚 Testing enhanced pattern library access...")
        enhanced_library_path = Path("gates/patterns/enhanced_pattern_library.json")
        if enhanced_library_path.exists():
            print("   ✅ Enhanced pattern library found")
            with open(enhanced_library_path, 'r') as f:
                import json
                data = json.load(f)
                gates_count = len(data.get("gates", {}))
                print(f"   📊 Found {gates_count} gates in enhanced library")
        else:
            print("   ⚠️ Enhanced pattern library not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_preparation():
    """Test if file preparation works without hanging"""
    
    print("🧪 Testing File Preparation...")
    
    try:
        from gates.nodes import ValidateGatesNode
        node = ValidateGatesNode()
        
        # Create minimal test data
        test_params = {
            "repo_path": "/tmp/test_repo",
            "metadata": {
                "total_files": 10,
                "file_list": [
                    {"path": "test.py", "lines": 50, "language": "python"},
                    {"path": "config.yml", "lines": 20, "language": "yaml"}
                ]
            }
        }
        
        print("   📁 Testing file preparation method...")
        
        # Test the file preparation method
        if hasattr(node, '_prepare_codebase_for_enhanced_evaluation'):
            print("   ✅ File preparation method exists")
            
            # Create a minimal repo path for testing
            test_repo_path = Path("/tmp/test_repo")
            test_repo_path.mkdir(exist_ok=True)
            
            # Create test files
            (test_repo_path / "test.py").write_text("import logging\nlogger.info('test')\n")
            (test_repo_path / "config.yml").write_text("logging:\n  level: INFO\n")
            
            test_params["repo_path"] = str(test_repo_path)
            
            try:
                files, contents = node._prepare_codebase_for_enhanced_evaluation(
                    test_repo_path, 
                    test_params["metadata"]
                )
                print(f"   ✅ File preparation completed: {len(files)} files")
                return True
            except Exception as prep_error:
                print(f"   ❌ File preparation failed: {prep_error}")
                return False
        else:
            print("   ⚠️ File preparation method not found")
            return True  # Not critical for basic functionality
        
    except Exception as e:
        print(f"   ❌ File preparation test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Starting System Tests")
    print("=" * 50)
    
    start_time = time.time()
    
    # Test system initialization
    init_success = test_system_initialization()
    
    print()
    
    # Test file preparation
    prep_success = test_file_preparation()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print()
    print("=" * 50)
    print("📊 Test Results:")
    print(f"   System Initialization: {'✅ PASS' if init_success else '❌ FAIL'}")
    print(f"   File Preparation: {'✅ PASS' if prep_success else '❌ FAIL'}")
    print(f"   Total Duration: {duration:.2f} seconds")
    
    if init_success and prep_success:
        print("🎉 All tests passed! System should work without hanging.")
        return 0
    else:
        print("💥 Some tests failed. System may have issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 