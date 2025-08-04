#!/usr/bin/env python3
"""
Test script to check if the enhanced evaluation system is working
"""

import sys
import os
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, str(Path(__file__).parent / "gates"))

def test_enhanced_evaluator():
    """Test the enhanced evaluator with minimal data"""
    
    print("🧪 Testing Enhanced Gate Evaluator...")
    
    try:
        from gates.criteria_evaluator import EnhancedGateEvaluator
        
        # Create minimal test data
        test_files = ["test.py", "config.yml", "README.md"]
        test_contents = {
            "test.py": "import logging\nlogger.info('test')\n",
            "config.yml": "logging:\n  level: INFO\n",
            "README.md": "# Test Project\n"
        }
        
        print("   📁 Creating test evaluator...")
        evaluator = EnhancedGateEvaluator(test_files, test_contents)
        print("   ✅ Enhanced evaluator created successfully")
        
        # Test with a simple gate config
        test_gate_config = {
            "display_name": "Test Gate",
            "description": "Test gate for evaluation",
            "category": "Test",
            "priority": "Medium",
            "criteria": {
                "operator": "OR",
                "conditions": [
                    {
                        "name": "test_condition",
                        "type": "pattern",
                        "operator": "OR",
                        "weight": 1.0,
                        "patterns": [
                            {"pattern": "logging", "weight": 1.0}
                        ]
                    }
                ]
            }
        }
        
        print("   🔍 Testing gate evaluation...")
        result = evaluator.evaluate_gate("TEST_GATE", test_gate_config)
        print(f"   ✅ Gate evaluation completed: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Enhanced evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_criteria_evaluator():
    """Test the criteria evaluator directly"""
    
    print("🧪 Testing Criteria Evaluator...")
    
    try:
        from gates.criteria_evaluator import CriteriaEvaluator
        
        # Create minimal test data
        test_files = ["test.py"]
        test_contents = {
            "test.py": "import logging\nlogger.info('test')\n"
        }
        
        print("   📁 Creating criteria evaluator...")
        evaluator = CriteriaEvaluator(test_files, test_contents)
        print("   ✅ Criteria evaluator created successfully")
        
        # Test with simple criteria
        test_criteria = {
            "operator": "OR",
            "conditions": [
                {
                    "name": "test_condition",
                    "type": "pattern",
                    "operator": "OR",
                    "weight": 1.0,
                    "patterns": [
                        {"pattern": "logging", "weight": 1.0}
                    ]
                }
            ]
        }
        
        print("   🔍 Testing criteria evaluation...")
        result = evaluator.evaluate_criteria(test_criteria)
        print(f"   ✅ Criteria evaluation completed: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Criteria evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    
    print("🚀 Starting Enhanced System Tests")
    print("=" * 50)
    
    # Test criteria evaluator
    criteria_success = test_criteria_evaluator()
    
    print()
    
    # Test enhanced evaluator
    enhanced_success = test_enhanced_evaluator()
    
    print()
    print("=" * 50)
    print("📊 Test Results:")
    print(f"   Criteria Evaluator: {'✅ PASS' if criteria_success else '❌ FAIL'}")
    print(f"   Enhanced Evaluator: {'✅ PASS' if enhanced_success else '❌ FAIL'}")
    
    if criteria_success and enhanced_success:
        print("🎉 All tests passed! Enhanced system should work.")
        return 0
    else:
        print("💥 Some tests failed. Enhanced system may have issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 