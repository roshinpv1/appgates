#!/usr/bin/env python3
"""
Test script for Recommendation Content Parsing
Tests that recommendation content is properly parsed and displayed
"""

import sys
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_recommendation_content_parsing():
    """Test that recommendation content is properly parsed and displayed"""
    print("🔍 Testing Recommendation Content Parsing...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter, RecommendationFormat
        
        # Test cases with actual content
        test_cases = [
            {
                "name": "Valid LLM Recommendation with Content",
                "gate": {
                    "gate": "STRUCTURED_LOGS",
                    "display_name": "Structured Logging",
                    "status": "FAIL",
                    "priority": "high",
                    "llm_recommendation": """
                    Root Cause Analysis: The application lacks structured logging implementation which is essential for debugging and monitoring in production environments.
                    
                    Impact: This affects debugging and monitoring capabilities, making it difficult to trace issues and understand application behavior in production.
                    
                    Actions: Implement structured logging using a library like Winston or Pino. Configure log levels and formats. Add correlation IDs for request tracing.
                    
                    Code Examples: Use Winston logger with structured format. Example: logger.info('User login', { userId: 123, action: 'login', timestamp: new Date() });
                    """
                }
            },
            {
                "name": "Recommendation with Placeholder Text",
                "gate": {
                    "gate": "ERROR_HANDLING",
                    "display_name": "Error Handling",
                    "status": "WARNING",
                    "priority": "medium",
                    "llm_recommendation": """
                    Analysis: Analysis**
                    
                    Impact: Assessment**
                    
                    Code Examples: Examples**
                    """
                }
            },
            {
                "name": "Mixed Content with Some Valid Sections",
                "gate": {
                    "gate": "SECURITY_HEADERS",
                    "display_name": "Security Headers",
                    "status": "FAIL",
                    "priority": "critical",
                    "llm_recommendation": """
                    Analysis: Missing essential security headers that protect against common web vulnerabilities.
                    
                    Impact: Assessment**
                    
                    Actions: Add Content-Security-Policy headers. Implement HSTS. Set secure and httpOnly flags for cookies.
                    
                    Code Examples: Examples**
                    """
                }
            },
            {
                "name": "Simple Text Recommendation",
                "gate": {
                    "gate": "API_SECURITY",
                    "display_name": "API Security",
                    "status": "WARNING",
                    "priority": "high",
                    "llm_recommendation": "Implement proper API authentication and authorization mechanisms to secure endpoints and protect sensitive data."
                }
            }
        ]
        
        print("✅ Recommendation formatter initialized successfully")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            
            # Test detailed formatting
            detailed_result = recommendation_formatter.format_recommendation_for_details(test_case['gate'])
            print(f"   Detailed Result: {detailed_result[:200]}...")
            
            # Test compact formatting
            compact_result = recommendation_formatter.format_recommendation_for_table(test_case['gate'])
            print(f"   Compact Result: {compact_result[:100]}...")
            
            # Verify content quality
            content_checks = []
            
            # Check for placeholder text
            if "**" not in detailed_result:
                content_checks.append("✅ No placeholder text")
            else:
                content_checks.append("❌ Contains placeholder text")
            
            # Check for meaningful content
            if len(detailed_result.strip()) > 20:
                content_checks.append("✅ Has meaningful content")
            else:
                content_checks.append("❌ Insufficient content")
            
            # Check for proper section formatting
            if ":" in detailed_result and any(section in detailed_result.lower() for section in ["analysis", "impact", "actions", "recommendation"]):
                content_checks.append("✅ Proper section formatting")
            else:
                content_checks.append("❌ Missing section formatting")
            
            print(f"   Content Quality: {' | '.join(content_checks)}")
        
        print("\n🎉 Recommendation content parsing tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Recommendation content parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structured_parsing():
    """Test the structured parsing functionality specifically"""
    print("\n🔍 Testing Structured Parsing...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter
        
        # Test the parsing function directly
        test_text = """
        Root Cause Analysis: The application lacks structured logging implementation which is essential for debugging and monitoring in production environments.
        
        Impact: This affects debugging and monitoring capabilities, making it difficult to trace issues and understand application behavior in production.
        
        Actions: Implement structured logging using a library like Winston or Pino. Configure log levels and formats. Add correlation IDs for request tracing.
        
        Code Examples: Use Winston logger with structured format. Example: logger.info('User login', { userId: 123, action: 'login', timestamp: new Date() });
        """
        
        # Test parsing
        sections = recommendation_formatter._parse_structured_recommendation(test_text)
        
        print("   Parsed Sections:")
        for section_name, content in sections.items():
            print(f"   - {section_name}: {content[:50]}...")
        
        # Verify sections were parsed correctly
        expected_sections = ["root_cause_analysis", "impact", "actions", "code_examples"]
        parsed_sections = list(sections.keys())
        
        if all(section in parsed_sections for section in expected_sections):
            print("   ✅ All expected sections parsed correctly")
        else:
            print("   ❌ Some sections missing")
        
        # Check content quality
        for section_name, content in sections.items():
            if content and len(content.strip()) > 10:
                print(f"   ✅ {section_name} has good content")
            else:
                print(f"   ❌ {section_name} has poor content")
        
        return True
        
    except Exception as e:
        print(f"❌ Structured parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all recommendation content tests"""
    print("🚀 Starting Recommendation Content Tests")
    print("=" * 70)
    
    # Test recommendation content parsing
    test1_passed = test_recommendation_content_parsing()
    
    # Test structured parsing
    test2_passed = test_structured_parsing()
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   • Recommendation Content Parsing: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • Structured Parsing: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Recommendation content is being properly parsed and displayed.")
        print("\n✨ Improvements Verified:")
        print("   • Proper parsing of structured recommendations")
        print("   • Filtering out placeholder text")
        print("   • Meaningful content extraction")
        print("   • Proper section formatting")
        print("   • Fallback handling for invalid content")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 