#!/usr/bin/env python3
"""
Test script for HardGate Agent
"""

import sys
import os

# Add the agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

def test_hardgate_tools():
    """Test importing all HardGate tools"""
    try:
        from hardgate_agent.tools import (
            analyze_repository,
            validate_gates,
            evidence_collection_tool,
            llm_analysis_tool,
            analyze_security,
            scan_code,
            check_compliance,
            generate_report,
            llm_integration,
            splunk_integration,
            jira_integration,
            gate_applicability,
            html_report_generator
        )
        print("✅ All HardGate tools imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Error importing HardGate tools: {e}")
        return False

def test_hardgate_agent():
    """Test importing the HardGate agent"""
    try:
        # Import the agent module as a package
        from hardgate_agent.agent import root_agent
        print("✅ HardGate agent imported successfully!")
        print(f"   Agent name: {root_agent.name}")
        print(f"   Agent description: {root_agent.description}")
        print(f"   Number of tools: {len(root_agent.tools)}")
        return True
    except Exception as e:
        print(f"❌ Error importing HardGate agent: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing HardGate Agent...")
    print("=" * 50)
    
    # Test tools
    print("\n1. Testing HardGate Tools...")
    tools_success = test_hardgate_tools()
    
    # Test agent
    print("\n2. Testing HardGate Agent...")
    agent_success = test_hardgate_agent()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Tools: {'✅ PASS' if tools_success else '❌ FAIL'}")
    print(f"   Agent: {'✅ PASS' if agent_success else '❌ FAIL'}")
    
    if tools_success and agent_success:
        print("\n🎉 All tests passed! HardGate Agent is ready to use.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 