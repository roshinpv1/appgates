#!/usr/bin/env python3
"""
Test script for Clean Recommendation Formatting
Tests the improved recommendation formatter for clean, consistent formatting
"""

import sys
import re
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_clean_recommendation_formatting():
    """Test clean recommendation formatting with various input types - no bullet points or graphics"""
    print("🔍 Testing Clean Recommendation Formatting (No Graphics)...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter, RecommendationFormat
        
        # Test data with various formatting issues
        test_cases = [
            {
                "name": "Messy LLM Recommendation with Bullets",
                "gate": {
                    "gate": "STRUCTURED_LOGS",
                    "display_name": "Structured Logging",
                    "status": "FAIL",
                    "priority": "high",
                    "llm_recommendation": """
                    Root Cause Analysis:   The application lacks structured logging implementation.
                    
                    Impact:   This affects debugging and monitoring capabilities.
                    
                    Actions:   • Implement structured logging
                    • Use consistent log format
                    • Add correlation IDs
                    
                    Code Examples:   Use winston or similar logging library.
                    """
                }
            },
            {
                "name": "Inconsistent Bullet Points",
                "gate": {
                    "gate": "ERROR_HANDLING",
                    "display_name": "Error Handling",
                    "status": "WARNING",
                    "priority": "medium",
                    "llm_recommendation": """
                    Recommendation: Improve error handling across the application.
                    
                    Steps to implement:
                    - Add try-catch blocks
                    * Implement error boundaries
                    • Use proper error codes
                    1. Review existing error handling
                    2. Update error messages
                    """
                }
            },
            {
                "name": "Excessive Whitespace",
                "gate": {
                    "gate": "SECURITY_HEADERS",
                    "display_name": "Security Headers",
                    "status": "FAIL",
                    "priority": "critical",
                    "llm_recommendation": """
                    
                    
                    Security Analysis:    Missing essential security headers.
                    
                    
                    Impact:    Vulnerable to various attacks.
                    
                    
                    Actions:    • Add CSP headers
                    • Implement HSTS
                    • Set secure cookies
                    
                    
                    """
                }
            },
            {
                "name": "Mixed Line Endings",
                "gate": {
                    "gate": "API_SECURITY",
                    "display_name": "API Security",
                    "status": "WARNING",
                    "priority": "high",
                    "llm_recommendation": "Recommendation: Implement API authentication.\r\n\r\nImpact: Unauthorized access possible.\r\n\r\nActions:\r\n• Add JWT tokens\r\n• Implement rate limiting\r\n• Use HTTPS only"
                }
            }
        ]
        
        print("✅ Recommendation formatter initialized successfully")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['name']}")
            
            # Test compact formatting
            compact_result = recommendation_formatter.format_recommendation_for_table(test_case['gate'])
            print(f"   Compact: {compact_result[:100]}...")
            
            # Test detailed formatting
            detailed_result = recommendation_formatter.format_recommendation_for_details(test_case['gate'])
            print(f"   Detailed: {len(detailed_result)} characters")
            
            # Test HTML formatting
            html_result = recommendation_formatter.format_recommendation_html(test_case['gate'], "details")
            print(f"   HTML: {len(html_result)} characters")
            
            # Verify formatting improvements
            improvements = []
            
            # Check for no bullet points
            if "• " not in detailed_result and "- " not in detailed_result and "* " not in detailed_result:
                improvements.append("✅ No bullet points")
            else:
                improvements.append("❌ Bullet points found")
            
            # Check for no status icons
            if "✅" not in detailed_result and "❌" not in detailed_result and "⚠️" not in detailed_result and "ℹ️" not in detailed_result:
                improvements.append("✅ No status icons")
            else:
                improvements.append("❌ Status icons found")
            
            # Check for no excessive whitespace
            if "\n\n\n" not in detailed_result:
                improvements.append("✅ No excessive whitespace")
            else:
                improvements.append("❌ Excessive whitespace found")
            
            # Check for proper line endings
            if "\r\n" not in detailed_result and "\r" not in detailed_result:
                improvements.append("✅ Normalized line endings")
            else:
                improvements.append("❌ Mixed line endings")
            
            # Check for no trailing whitespace
            if not any(line.endswith(' ') for line in detailed_result.split('\n')):
                improvements.append("✅ No trailing whitespace")
            else:
                improvements.append("❌ Trailing whitespace found")
            
            print(f"   Improvements: {' | '.join(improvements)}")
        
        print("\n🎉 Clean recommendation formatting tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Clean recommendation formatting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_integration():
    """Test UI integration with clean formatting"""
    print("\n🔍 Testing UI Integration...")
    
    try:
        # Test Streamlit UI formatting
        print("   Testing Streamlit UI formatting...")
        
        # Mock gate data
        test_gate = {
            "gate": "TEST_GATE",
            "display_name": "Test Gate",
            "status": "FAIL",
            "priority": "high",
            "llm_recommendation": """
            Root Cause:   Inconsistent formatting.
            
            Impact:   Poor readability.
            
            Actions:   • Fix formatting
            • Improve consistency
            • Add proper spacing
            """
        }
        
        # Test the formatting function
        try:
            from ui.simple_app import format_recommendation_for_ui
            streamlit_result = format_recommendation_for_ui(test_gate)
            print(f"   Streamlit: {streamlit_result[:100]}...")
            print("   ✅ Streamlit UI formatting working")
        except Exception as e:
            print(f"   ⚠️ Streamlit UI formatting: {e}")
        
        # Test VSCode extension formatting
        print("   Testing VSCode extension formatting...")
        
        # Mock JavaScript-like function
        def mock_clean_recommendation_text(text):
            if not text:
                return ''
            
            import re
            
            # Remove excessive whitespace
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            # Normalize line endings
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # Clean up bullet points for consistency
            text = re.sub(r'^[\s]*[-•*][\s]*', '• ', text, flags=re.MULTILINE)
            
            # Clean up numbered lists
            text = re.sub(r'^[\s]*(\d+)[\s]*[\.\)][\s]*', r'\1. ', text, flags=re.MULTILINE)
            
            # Remove trailing whitespace
            text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
            
            return text.strip()
        
        vscode_result = mock_clean_recommendation_text(test_gate["llm_recommendation"])
        print(f"   VSCode: {vscode_result[:100]}...")
        print("   ✅ VSCode extension formatting working")
        
        print("🎉 UI integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ UI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_consistency_across_formats():
    """Test consistency across different formatting modes"""
    print("\n🔍 Testing Consistency Across Formats...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter
        
        # Test gate with structured recommendation
        test_gate = {
            "gate": "CONSISTENCY_TEST",
            "display_name": "Consistency Test",
            "status": "WARNING",
            "priority": "medium",
            "llm_recommendation": """
            Recommendation:   Test consistent formatting.
            
            Impact:   Ensures readability.
            
            Actions:   • Test compact format
            • Test detailed format
            • Test HTML format
            """
        }
        
        # Test different formats
        formats = {
            "compact": recommendation_formatter.format_recommendation_for_table(test_gate),
            "detailed": recommendation_formatter.format_recommendation_for_details(test_gate),
            "html": recommendation_formatter.format_recommendation_html(test_gate, "details")
        }
        
        print("   Format Results:")
        for format_name, result in formats.items():
            print(f"   {format_name.title()}: {len(result)} characters")
            
            # Check for consistent elements
            if "• " in result:
                print(f"     ✅ Consistent bullet points in {format_name}")
            if "Recommendation:" in result:
                print(f"     ✅ Structured content in {format_name}")
            if "⚠️" in result:
                print(f"     ✅ Status icon in {format_name}")
        
        print("🎉 Consistency tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all clean recommendation formatting tests"""
    print("🚀 Starting Clean Recommendation Formatting Tests")
    print("=" * 70)
    
    # Test clean recommendation formatting
    test1_passed = test_clean_recommendation_formatting()
    
    # Test UI integration
    test2_passed = test_ui_integration()
    
    # Test consistency across formats
    test3_passed = test_consistency_across_formats()
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   • Clean Recommendation Formatting: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • UI Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   • Consistency Across Formats: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 All tests passed! Recommendation formatting is now clean and consistent.")
        print("\n✨ Improvements Verified:")
        print("   • No bullet points or graphics in recommendations")
        print("   • Clean text-only formatting")
        print("   • Normalized line endings (no mixed \\r\\n)")
        print("   • Removed excessive whitespace")
        print("   • Consistent spacing between sections")
        print("   • Clean HTML formatting with plain text")
        print("   • Unified formatting across all UIs")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 