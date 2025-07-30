#!/usr/bin/env python3
"""
Test script to verify CriteriaEvaluator integration with existing workflow
"""

import os
import sys
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gates'))

def test_enhanced_evaluation():
    """Test the enhanced evaluation system"""
    print("🧪 Testing CriteriaEvaluator Integration")
    print("=" * 50)
    
    try:
        # Test 1: Check if enhanced pattern library exists
        enhanced_library_path = Path("gates/patterns/enhanced_pattern_library.json")
        if enhanced_library_path.exists():
            print("✅ Enhanced pattern library found")
            
            with open(enhanced_library_path, "r") as f:
                enhanced_library = json.load(f)
            
            gates = enhanced_library.get("gates", {})
            print(f"📊 Found {len(gates)} enhanced gates")
            
            # List some gates
            for i, gate_name in enumerate(list(gates.keys())[:5]):
                gate_config = gates[gate_name]
                display_name = gate_config.get("display_name", gate_name)
                category = gate_config.get("category", "Unknown")
                print(f"   {i+1}. {gate_name} ({display_name}) - {category}")
            
            if len(gates) > 5:
                print(f"   ... and {len(gates) - 5} more gates")
        else:
            print("❌ Enhanced pattern library not found")
            return False
        
        # Test 2: Check if CriteriaEvaluator can be imported
        try:
            from gates.criteria_evaluator import CriteriaEvaluator, EnhancedGateEvaluator
            print("✅ CriteriaEvaluator and EnhancedGateEvaluator imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import CriteriaEvaluator: {e}")
            return False
        
        # Test 3: Test basic evaluation
        print("\n🔍 Testing basic criteria evaluation...")
        
        # Create sample codebase
        sample_files = [
            "src/main/java/UserService.java",
            "src/test/java/UserServiceTest.java",
            "src/main/java/LoggingService.java"
        ]
        
        sample_contents = {
            "src/main/java/UserService.java": """
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserService {
    private static final Logger logger = LoggerFactory.getLogger(UserService.class);
    
    public void createUser(String username) {
        logger.info("Creating user: {}", username);
        // User creation logic
    }
}
""",
            "src/test/java/UserServiceTest.java": """
package com.example;

import org.junit.Test;
import static org.junit.Assert.*;

public class UserServiceTest {
    @Test
    public void testUserCreation() {
        // Test implementation
    }
}
""",
            "src/main/java/LoggingService.java": """
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoggingService {
    private static final Logger logger = LoggerFactory.getLogger(LoggingService.class);
    
    public void logMessage(String message) {
        logger.info("Message: {}", message);
    }
}
"""
        }
        
        # Initialize evaluator
        evaluator = EnhancedGateEvaluator(sample_files, sample_contents)
        
        # Test with a simple gate
        test_gate_config = {
            "display_name": "Test Structured Logging",
            "description": "Test gate for structured logging",
            "category": "Logging",
            "priority": "High",
            "weight": 15.0,
            "expected_coverage": {
                "percentage": 25,
                "reasoning": "Structured logging should be implemented",
                "confidence": "High",
                "max_files_expected": 3
            },
            "scoring": {
                "pass_threshold": 20.0,
                "perfect_threshold": 80.0,
                "criteria_weight": 0.8,
                "coverage_weight": 0.2,
                "logic_multipliers": {
                    "AND": 1.0,
                    "OR": 0.8,
                    "NOT": 1.2
                },
                "condition_weights": {
                    "pattern": 1.0,
                    "file_pattern": 0.7,
                    "criteria": 1.2
                }
            },
            "criteria": {
                "operator": "AND",
                "conditions": [
                    {
                        "name": "logging_import",
                        "type": "pattern",
                        "operator": "OR",
                        "weight": 5.0,
                        "patterns": [
                            {"pattern": "import org.slf4j.Logger", "weight": 3.0, "technology": "java"}
                        ]
                    },
                    {
                        "name": "logging_usage",
                        "type": "pattern",
                        "operator": "OR",
                        "weight": 3.0,
                        "patterns": [
                            {"pattern": "logger\\.(info|debug|warn|error)", "weight": 2.0, "technology": "java"}
                        ]
                    }
                ]
            }
        }
        
        # Evaluate the test gate
        result = evaluator.evaluate_gate("TEST_STRUCTURED_LOGS", test_gate_config)
        
        print(f"✅ Test evaluation completed:")
        print(f"   Gate: {result.get('gate_name', 'TEST_STRUCTURED_LOGS')}")
        print(f"   Score: {result.get('score', 0.0):.1f}%")
        print(f"   Status: {result.get('status', 'FAIL')}")
        print(f"   Criteria Score: {result.get('criteria_score', 0.0):.1f}%")
        print(f"   Coverage Score: {result.get('coverage_score', 0.0):.1f}%")
        print(f"   Matches: {len(result.get('matches', []))}")
        
        # Test 4: Check if ValidateGatesNode can use enhanced evaluation
        print("\n🔍 Testing ValidateGatesNode integration...")
        
        try:
            from gates.nodes import ValidateGatesNode
            print("✅ ValidateGatesNode imported successfully")
            
            # Check if the enhanced evaluation methods exist
            node = ValidateGatesNode()
            
            if hasattr(node, '_evaluate_with_enhanced_system'):
                print("✅ Enhanced evaluation method found")
            else:
                print("❌ Enhanced evaluation method not found")
                return False
            
            if hasattr(node, '_prepare_codebase_for_enhanced_evaluation'):
                print("✅ Codebase preparation method found")
            else:
                print("❌ Codebase preparation method not found")
                return False
            
            if hasattr(node, '_convert_enhanced_result_to_legacy_format'):
                print("✅ Result conversion method found")
            else:
                print("❌ Result conversion method not found")
                return False
            
        except ImportError as e:
            print(f"❌ Failed to import ValidateGatesNode: {e}")
            return False
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_integration():
    """Test the workflow integration"""
    print("\n🔄 Testing Workflow Integration")
    print("=" * 50)
    
    try:
        # Check if the enhanced pattern library is properly configured
        enhanced_library_path = Path("gates/patterns/enhanced_pattern_library.json")
        
        if not enhanced_library_path.exists():
            print("❌ Enhanced pattern library not found - workflow will use legacy evaluation")
            return False
        
        # Load and validate the enhanced pattern library
        with open(enhanced_library_path, "r") as f:
            enhanced_library = json.load(f)
        
        # Check required fields
        required_fields = ["version", "metadata", "gates", "global_config"]
        for field in required_fields:
            if field not in enhanced_library:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ Enhanced pattern library structure is valid")
        
        # Check if gates have criteria configuration
        gates = enhanced_library.get("gates", {})
        gates_with_criteria = 0
        
        for gate_name, gate_config in gates.items():
            if "criteria" in gate_config:
                gates_with_criteria += 1
        
        print(f"✅ Found {gates_with_criteria}/{len(gates)} gates with criteria configuration")
        
        if gates_with_criteria == 0:
            print("⚠️ No gates have criteria configuration - workflow will use legacy evaluation")
            return False
        
        print("✅ Workflow integration ready for enhanced evaluation")
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 CriteriaEvaluator Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Enhanced evaluation
    enhanced_test_passed = test_enhanced_evaluation()
    
    # Test 2: Workflow integration
    workflow_test_passed = test_workflow_integration()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Enhanced Evaluation: {'✅ PASS' if enhanced_test_passed else '❌ FAIL'}")
    print(f"Workflow Integration: {'✅ PASS' if workflow_test_passed else '❌ FAIL'}")
    
    if enhanced_test_passed and workflow_test_passed:
        print("\n🎉 All tests passed! CriteriaEvaluator is fully integrated.")
        print("\n📝 Next Steps:")
        print("   1. Run a scan to see enhanced evaluation in action")
        print("   2. Check the HTML report for enhanced metrics")
        print("   3. Review condition results in the detailed view")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")
    
    return enhanced_test_passed and workflow_test_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 