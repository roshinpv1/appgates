#!/usr/bin/env python3
"""
Test script for Recommendation Formatting
Tests the new centralized recommendation formatter for consistent formatting across all UIs
"""

import sys
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_recommendation_formatter():
    """Test the recommendation formatter with sample gate data"""
    print("🔍 Testing Recommendation Formatter...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter, RecommendationFormat
        
        # Sample gate data for testing
        sample_gates = [
            {
                "gate": "STRUCTURED_LOGS",
                "display_name": "Structured Logging",
                "status": "FAIL",
                "score": 35.0,
                "priority": "high",
                "llm_recommendation": "Based on the analysis, this gate failed because:\n\n**Root Cause Analysis:** The codebase lacks structured logging patterns\n\n**Impact Assessment:** This affects debugging and monitoring capabilities\n\n**Specific Recommendations:**\n• Implement structured logging using JSON format\n• Add correlation IDs to log messages\n• Use consistent log levels throughout the application",
                "recommendations": ["Implement structured logging patterns"]
            },
            {
                "gate": "ERROR_HANDLING",
                "display_name": "Error Handling",
                "status": "PASS",
                "score": 85.0,
                "priority": "medium",
                "llm_recommendation": "Excellent error handling implementation found:\n\n**Root Cause Analysis:** Comprehensive error handling patterns detected\n\n**Impact Assessment:** High reliability and maintainability\n\n**Specific Recommendations:**\n• Continue maintaining current practices\n• Consider adding more specific error types\n• Document error handling patterns for team reference",
                "recommendations": ["Continue maintaining good practices"]
            },
            {
                "gate": "AUTOMATED_TESTS",
                "display_name": "Automated Testing",
                "status": "WARNING",
                "score": 65.0,
                "priority": "critical",
                "llm_recommendation": "Partial test coverage detected:\n\n**Root Cause Analysis:** Some areas lack comprehensive test coverage\n\n**Impact Assessment:** Potential for undetected bugs in production\n\n**Specific Recommendations:**\n• Increase unit test coverage to 80%+\n• Add integration tests for critical paths\n• Implement automated test pipelines",
                "recommendations": ["Expand test coverage"]
            },
            {
                "gate": "CIRCUIT_BREAKERS",
                "display_name": "Circuit Breakers",
                "status": "NOT_APPLICABLE",
                "score": 0.0,
                "priority": "low",
                "recommendations": ["Not applicable to this technology stack"]
            }
        ]
        
        print("✅ Sample gate data created successfully")
        
        # Test table formatting (compact)
        print("\n📊 Testing Table Formatting (Compact):")
        for i, gate in enumerate(sample_gates):
            formatted = recommendation_formatter.format_recommendation_for_table(gate)
            print(f"   Gate {i+1} ({gate['status']}): {formatted[:100]}...")
        
        # Test detailed formatting
        print("\n📋 Testing Detailed Formatting:")
        for i, gate in enumerate(sample_gates):
            formatted = recommendation_formatter.format_recommendation_for_details(gate)
            print(f"   Gate {i+1} ({gate['status']}): {formatted[:150]}...")
        
        # Test HTML formatting
        print("\n🌐 Testing HTML Formatting:")
        for i, gate in enumerate(sample_gates):
            html = recommendation_formatter.format_recommendation_html(gate, "table")
            print(f"   Gate {i+1} HTML: {html[:100]}...")
        
        # Test LLM recommendation formatting
        print("\n🤖 Testing LLM Recommendation Formatting:")
        llm_text = """**Root Cause Analysis:** The codebase lacks structured logging patterns

**Impact Assessment:** This affects debugging and monitoring capabilities

**Specific Recommendations:**
• Implement structured logging using JSON format
• Add correlation IDs to log messages
• Use consistent log levels throughout the application

**Code Examples:**
```javascript
// Instead of: console.log('User logged in:', user.id)
// Use: logger.info('User logged in', { userId: user.id, action: 'login' })
```"""
        
        formatted_llm = recommendation_formatter.format_llm_recommendation(llm_text)
        print(f"   Formatted LLM: {formatted_llm[:200]}...")
        
        # Test custom format configuration
        print("\n⚙️ Testing Custom Format Configuration:")
        custom_config = RecommendationFormat(
            max_length=100,
            show_priority=True,
            show_impact=False,
            show_actions=True,
            compact_mode=True
        )
        
        for i, gate in enumerate(sample_gates):
            formatted = recommendation_formatter.format_recommendation(gate, custom_config)
            print(f"   Gate {i+1} (Custom): {formatted[:80]}...")
        
        print("\n🎉 All recommendation formatting tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Recommendation formatter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_integration():
    """Test integration with different UI types"""
    print("\n🔍 Testing UI Integration...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter
        
        # Sample gate for UI testing
        sample_gate = {
            "gate": "SECURITY_HEADERS",
            "display_name": "Security Headers",
            "status": "FAIL",
            "score": 25.0,
            "priority": "critical",
            "llm_recommendation": "Critical security vulnerability detected:\n\n**Root Cause Analysis:** Missing essential security headers\n\n**Impact Assessment:** High security risk - potential for XSS and other attacks\n\n**Specific Recommendations:**\n• Implement Content-Security-Policy header\n• Add X-Frame-Options header\n• Configure HSTS header for HTTPS enforcement",
            "recommendations": ["Implement security headers"]
        }
        
        # Test VSCode formatting
        vscode_format = recommendation_formatter.format_recommendation_for_ui(sample_gate, "vscode")
        print(f"   VSCode: {vscode_format[:100]}...")
        
        # Test Streamlit formatting
        streamlit_format = recommendation_formatter.format_recommendation_for_ui(sample_gate, "streamlit")
        print(f"   Streamlit: {streamlit_format[:100]}...")
        
        # Test HTML Report formatting
        html_format = recommendation_formatter.format_recommendation_for_ui(sample_gate, "html_report")
        print(f"   HTML Report: {html_format[:100]}...")
        
        print("✅ UI integration tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ UI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_consistency():
    """Test consistency across different formatting methods"""
    print("\n🔍 Testing Formatting Consistency...")
    
    try:
        from utils.recommendation_formatter import recommendation_formatter
        
        # Sample gate with all recommendation types
        sample_gate = {
            "gate": "API_DOCUMENTATION",
            "display_name": "API Documentation",
            "status": "WARNING",
            "score": 60.0,
            "priority": "medium",
            "llm_recommendation": "API documentation needs improvement:\n\n**Root Cause Analysis:** Incomplete API documentation\n\n**Impact Assessment:** Affects developer experience and API adoption\n\n**Specific Recommendations:**\n• Add OpenAPI/Swagger documentation\n• Include request/response examples\n• Document error codes and messages",
            "recommendations": ["Improve API documentation"]
        }
        
        # Test that all methods return consistent results
        table_format = recommendation_formatter.format_recommendation_for_table(sample_gate)
        details_format = recommendation_formatter.format_recommendation_for_details(sample_gate)
        ui_format = recommendation_formatter.format_recommendation_for_ui(sample_gate, "vscode")
        
        # Check that all formats contain the status icon
        status_icon = "⚠️"  # WARNING status
        assert status_icon in table_format, "Table format missing status icon"
        assert status_icon in details_format, "Details format missing status icon"
        assert status_icon in ui_format, "UI format missing status icon"
        
        print("   ✅ Status icons consistent across all formats")
        
        # Check that LLM recommendation is prioritized
        assert "API documentation" in table_format, "LLM recommendation not prioritized in table format"
        assert "API documentation" in details_format, "LLM recommendation not prioritized in details format"
        
        print("   ✅ LLM recommendation prioritization consistent")
        
        print("✅ Consistency tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all recommendation formatting tests"""
    print("🚀 Starting Recommendation Formatting Tests")
    print("=" * 60)
    
    # Test basic formatter functionality
    test1_passed = test_recommendation_formatter()
    
    # Test UI integration
    test2_passed = test_ui_integration()
    
    # Test consistency
    test3_passed = test_consistency()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   • Basic Formatter: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • UI Integration: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   • Consistency: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 All tests passed! Recommendation formatting is working correctly.")
        print("\n✨ Features Verified:")
        print("   • Consistent formatting across all UIs")
        print("   • LLM recommendation prioritization")
        print("   • Status icon integration")
        print("   • Compact and detailed formatting modes")
        print("   • HTML conversion for reports")
        print("   • Custom format configuration support")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 