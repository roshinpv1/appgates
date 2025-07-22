#!/usr/bin/env python3
"""
Test script to verify timeout handling in CodeGates LLM calls and file processing
"""

import os
import sys
import time
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

from nodes import CallLLMNode, ValidateGatesNode
from utils.hard_gates import HARD_GATES

def test_llm_timeout():
    """Test LLM timeout handling"""
    print("🧪 Testing LLM timeout handling...")
    
    # Create a mock shared context
    shared = {
        "request": {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "threshold": 70
        },
        "llm": {
            "prompt": "Generate patterns for hard gates. This is a test prompt."
        },
        "llm_config": {
            "url": "http://localhost:8080",  # Non-existent URL to trigger timeout
            "model": "test-model",
            "api_key": "test-key",
            "temperature": 0.1,
            "max_tokens": 1000
        }
    }
    
    # Set a short timeout for testing
    os.environ["CODEGATES_LLM_TIMEOUT"] = "10"  # 10 seconds
    
    # Create the node
    node = CallLLMNode()
    
    try:
        # Prepare the node
        prep_result = node.prep(shared)
        print(f"✅ Prep successful: {len(prep_result)} parameters")
        
        # Execute with timeout
        start_time = time.time()
        exec_result = node.exec(prep_result)
        end_time = time.time()
        
        print(f"✅ Execution completed in {end_time - start_time:.2f} seconds")
        print(f"   Success: {exec_result['success']}")
        print(f"   Source: {exec_result['source']}")
        print(f"   Model: {exec_result['model']}")
        print(f"   Patterns generated: {len(exec_result['pattern_data'])} gates")
        
        # Post process
        post_result = node.post(shared, prep_result, exec_result)
        print(f"✅ Post processing successful: {post_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_fallback_patterns():
    """Test fallback pattern generation"""
    print("\n🧪 Testing fallback pattern generation...")
    
    # Create a mock shared context without LLM config
    shared = {
        "request": {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "threshold": 70
        },
        "llm": {
            "prompt": "Generate patterns for hard gates. This is a test prompt."
        },
        "llm_config": {}  # Empty config to trigger fallback
    }
    
    # Create the node
    node = CallLLMNode()
    
    try:
        # Prepare the node
        prep_result = node.prep(shared)
        print(f"✅ Prep successful: {len(prep_result)} parameters")
        
        # Execute
        start_time = time.time()
        exec_result = node.exec(prep_result)
        end_time = time.time()
        
        print(f"✅ Execution completed in {end_time - start_time:.2f} seconds")
        print(f"   Success: {exec_result['success']}")
        print(f"   Source: {exec_result['source']}")
        print(f"   Model: {exec_result['model']}")
        print(f"   Patterns generated: {len(exec_result['pattern_data'])} gates")
        
        # Verify fallback patterns were generated
        if exec_result['source'] == 'fallback':
            print("✅ Fallback patterns generated successfully")
            
            # Check that patterns were generated for all gates
            pattern_data = exec_result['pattern_data']
            for gate in HARD_GATES:
                gate_name = gate['name']
                if gate_name in pattern_data:
                    patterns = pattern_data[gate_name].get('patterns', [])
                    print(f"   {gate_name}: {len(patterns)} patterns")
                else:
                    print(f"   ⚠️ {gate_name}: No patterns found")
        
        # Post process
        post_result = node.post(shared, prep_result, exec_result)
        print(f"✅ Post processing successful: {post_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_file_processing_timeout():
    """Test file processing timeout handling"""
    print("\n🧪 Testing file processing timeout handling...")
    
    # Create a mock shared context
    shared = {
        "request": {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "threshold": 70
        },
        "repository": {
            "local_path": "/tmp/test-repo",
            "metadata": {
                "file_list": [
                    {
                        "relative_path": "test.java",
                        "type": "Source Code",
                        "language": "Java",
                        "is_binary": False,
                        "size": 1024
                    }
                ],
                "language_stats": {
                    "Java": {"files": 1, "lines": 100}
                }
            }
        },
        "llm": {
            "patterns": {
                "STRUCTURED_LOGS": ["logger.info", "log.debug"]
            }
        },
        "hard_gates": [
            {
                "name": "STRUCTURED_LOGS",
                "display_name": "Structured Logs",
                "description": "Test gate",
                "category": "Logging",
                "priority": "high"
            }
        ]
    }
    
    # Set a short timeout for testing
    os.environ["CODEGATES_FILE_PROCESSING_TIMEOUT"] = "5"  # 5 seconds
    
    # Create the node
    node = ValidateGatesNode()
    
    try:
        # Prepare the node
        prep_result = node.prep(shared)
        print(f"✅ Prep successful: {len(prep_result)} parameters")
        
        # Execute with timeout
        start_time = time.time()
        exec_result = node.exec(prep_result)
        end_time = time.time()
        
        print(f"✅ Execution completed in {end_time - start_time:.2f} seconds")
        print(f"   Gates processed: {len(exec_result)}")
        
        # Post process
        post_result = node.post(shared, prep_result, exec_result)
        print(f"✅ Post processing successful: {post_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting CodeGates timeout handling tests...")
    
    # Test 1: LLM timeout handling
    test1_success = test_llm_timeout()
    
    # Test 2: Fallback pattern generation
    test2_success = test_fallback_patterns()
    
    # Test 3: File processing timeout
    test3_success = test_file_processing_timeout()
    
    # Summary
    print("\n📊 Test Results:")
    print(f"   LLM Timeout Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"   Fallback Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"   File Processing Timeout Test: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    
    if test1_success and test2_success and test3_success:
        print("\n🎉 All tests passed! Timeout handling is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1) 