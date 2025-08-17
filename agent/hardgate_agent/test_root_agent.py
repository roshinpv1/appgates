#!/usr/bin/env python3
"""
Test script to verify HardGate Agent root_agent structure
"""

import sys
import os
from pathlib import Path

def test_root_agent_structure():
    """Test that the root_agent is properly structured for Google ADK"""
    print("🔍 Testing HardGate Agent root_agent structure...")
    
    try:
        # Add current directory to path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        # Import the root_agent directly from agent.py
        from agent import root_agent
        
        print("✅ root_agent imported successfully")
        
        # Check required attributes
        required_attrs = ['name', 'description', 'tools', 'model']
        missing_attrs = []
        
        for attr in required_attrs:
            if hasattr(root_agent, attr):
                print(f"✅ root_agent has {attr}: {getattr(root_agent, attr)}")
            else:
                missing_attrs.append(attr)
                print(f"❌ root_agent missing {attr}")
        
        if missing_attrs:
            print(f"❌ Missing required attributes: {missing_attrs}")
            return False
        
        # Check tools
        if hasattr(root_agent, 'tools') and root_agent.tools:
            print(f"✅ root_agent has {len(root_agent.tools)} tools")
            
            # Check tool names
            tool_names = [tool.name for tool in root_agent.tools if hasattr(tool, 'name')]
            print(f"✅ Tool names: {tool_names}")
        else:
            print("❌ root_agent has no tools")
            return False
        
        # Check model
        if hasattr(root_agent, 'model'):
            print(f"✅ root_agent model: {root_agent.model}")
        else:
            print("❌ root_agent has no model")
            return False
        
        print("🎉 HardGate Agent root_agent structure is correct!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing root_agent structure: {e}")
        return False

def test_google_adk_compatibility():
    """Test Google ADK compatibility"""
    print("\n🔍 Testing Google ADK compatibility...")
    
    try:
        # Add current directory to path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        from agent import root_agent
        from google.adk.runners import InMemoryRunner
        
        # Test creating a runner
        runner = InMemoryRunner(root_agent)
        print("✅ InMemoryRunner created successfully")
        
        print("🎉 Google ADK compatibility confirmed!")
        return True
        
    except Exception as e:
        print(f"❌ Google ADK compatibility error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 HardGate Agent Root Agent Structure Test")
    print("=" * 50)
    
    # Test root_agent structure
    structure_ok = test_root_agent_structure()
    
    # Test Google ADK compatibility
    adk_ok = test_google_adk_compatibility()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Root Agent Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"   Google ADK Compatibility: {'✅ PASS' if adk_ok else '❌ FAIL'}")
    
    if structure_ok and adk_ok:
        print("\n🎉 All tests passed! HardGate Agent is ready for Google ADK!")
        print("📍 The root_agent should now be discoverable by the Google ADK Agent Development Kit")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 