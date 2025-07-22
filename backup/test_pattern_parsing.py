#!/usr/bin/env python3
"""
Test script for pattern parsing improvements
"""

import sys
import re

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_pattern_extraction():
    """Test the improved pattern extraction"""
    print("🧪 Testing Pattern Extraction Improvements")
    print("=" * 50)
    
    # Sample LLM response in the format we're seeing
    sample_response = """Based on the provided codebase analysis, I will generate comprehensive regex patterns for each hard gate that are effective for this specific codebase.

**STRUCTURED_LOGS**

*   **Patterns**
    *   `r'import\s+org\.slf4j\.Logger|@Slf4j|log\.(info|debug|error|warn|trace)\(|logger\.(info|debug|error|warn|trace)\('`
    *   `r'\b\w*logger\w*\.(info|debug|error|warn|trace)\('`
*   **Description**: Comprehensive logging patterns for this technology stack.
*   **Significance**: Critical for monitoring and debugging in production environments.
*   **Expected Coverage**
    *   **Percentage**: 25
    *   **Reasoning**: Based on project structure and framework usage patterns. This pattern covers the main logging frameworks used in the codebase, including SLF4J and Logback.
    *   **Confidence**: High

**AVOID_LOGGING_SECRETS**

*   **Patterns**
    *   `r'\bpassword\b|secret\b|token\b|key\b'`
*   **Description**: Prevent sensitive data from being logged accidentally.
*   **Significance**: Important for security and compliance.
*   **Expected Coverage**
    *   **Percentage**: 10
    *   **Reasoning**: This pattern covers common sensitive keywords that should not be logged. It's essential to prevent accidental logging of sensitive information like passwords, secrets, tokens, or keys.
    *   **Confidence**: Medium"""

    try:
        from nodes import CallLLMNode
        
        # Create a CallLLMNode instance to test the parsing
        llm_node = CallLLMNode()
        
        # Test the pattern extraction
        pattern_data = llm_node._extract_patterns_from_text(sample_response)
        
        print("✅ Pattern extraction successful!")
        print(f"   Found {len(pattern_data)} gates")
        
        for gate_name, gate_data in pattern_data.items():
            patterns = gate_data.get("patterns", [])
            description = gate_data.get("description", "")
            significance = gate_data.get("significance", "")
            expected_coverage = gate_data.get("expected_coverage", {})
            
            print(f"\n📋 {gate_name}:")
            print(f"   Patterns: {len(patterns)} found")
            for i, pattern in enumerate(patterns[:3]):  # Show first 3 patterns
                print(f"     {i+1}. {pattern}")
            if len(patterns) > 3:
                print(f"     ... and {len(patterns) - 3} more")
            
            print(f"   Description: {description[:100]}...")
            print(f"   Significance: {significance[:100]}...")
            print(f"   Expected Coverage: {expected_coverage.get('percentage', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gate_recommendations():
    """Test the _generate_gate_recommendations method"""
    print("\n🧪 Testing Gate Recommendations Method")
    print("=" * 50)
    
    try:
        from nodes import ValidateGatesNode
        
        # Create a ValidateGatesNode instance to test the method
        validate_node = ValidateGatesNode()
        
        # Test case 1: Infrastructure pattern (expected_percentage = 100)
        gate_1 = {
            "display_name": "Structured Logs",
            "description": "Implement structured logging",
            "expected_coverage": {
                "percentage": 100,
                "reasoning": "Infrastructure framework detected",
                "confidence": "high"
            },
            "total_files": 100,
            "relevant_files": 50
        }
        
        matches_1 = [{"file": "file1.java", "line": 10}, {"file": "file2.java", "line": 20}]
        
        recommendations_1 = validate_node._generate_gate_recommendations(gate_1, matches_1, 80.0)
        
        print("✅ Infrastructure pattern recommendations generated successfully!")
        print(f"   Found {len(recommendations_1)} recommendations")
        for i, rec in enumerate(recommendations_1):
            print(f"     {i+1}. {rec}")
        
        # Test case 2: Standard pattern (expected_percentage < 100)
        gate_2 = {
            "display_name": "Error Handling",
            "description": "Implement proper error handling",
            "expected_coverage": {
                "percentage": 25,
                "reasoning": "Standard expectation",
                "confidence": "medium"
            },
            "total_files": 100,
            "relevant_files": 50
        }
        
        matches_2 = []  # No matches
        
        recommendations_2 = validate_node._generate_gate_recommendations(gate_2, matches_2, 30.0)
        
        print("\n✅ Standard pattern recommendations generated successfully!")
        print(f"   Found {len(recommendations_2)} recommendations")
        for i, rec in enumerate(recommendations_2):
            print(f"     {i+1}. {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gate recommendations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_pattern_extraction()
    success2 = test_gate_recommendations()
    
    if success1 and success2:
        print("\n✅ All tests passed! The fixes are working correctly.")
    else:
        print("\n❌ Some tests failed - further investigation needed.") 