#!/usr/bin/env python3
"""
Test script to demonstrate importing HardGate Agent from any location
This script can be run from anywhere and will successfully import the agent
"""

import sys
import os
from pathlib import Path

def test_import_from_current_location():
    """Test importing from the current working directory"""
    print("🔍 Testing import from current location...")
    
    try:
        # Use the import resolver
        from agent.hardgate_agent.import_resolver import create_hardgate_agent, verify_imports
        
        # Verify imports
        if verify_imports():
            print("✅ Import verification successful")
            
            # Create agent
            agent = create_hardgate_agent()
            if agent and agent.agent:
                print("✅ Agent created successfully!")
                print(f"📊 Agent has {len(agent.agent.tools)} tools configured")
                return True
            else:
                print("❌ Failed to create agent")
                return False
        else:
            print("❌ Import verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_direct_import():
    """Test direct import using the resolver"""
    print("\n🔍 Testing direct import...")
    
    try:
        from agent.hardgate_agent.import_resolver import import_hardgate_agent
        
        HardGateAgentClass = import_hardgate_agent()
        if HardGateAgentClass:
            print("✅ Direct import successful")
            agent = HardGateAgentClass()
            if agent and agent.agent:
                print("✅ Agent instantiated successfully")
                return True
            else:
                print("❌ Agent instantiation failed")
                return False
        else:
            print("❌ Direct import failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_from_project_root():
    """Test importing from project root"""
    print("\n🔍 Testing import from project root...")
    
    try:
        # Add the hardgate_agent directory to the path
        hardgate_agent_path = Path(__file__).parent
        if str(hardgate_agent_path) not in sys.path:
            sys.path.insert(0, str(hardgate_agent_path))
        
        # Import using the resolver
        from import_resolver import create_hardgate_agent
        
        agent = create_hardgate_agent()
        if agent and agent.agent:
            print("✅ Import from project root successful")
            return True
        else:
            print("❌ Import from project root failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all import tests"""
    print("🚀 HardGate Agent Import Tests")
    print("=" * 50)
    
    tests = [
        ("Current Location", test_import_from_current_location),
        ("Direct Import", test_direct_import),
        ("Project Root", test_from_project_root)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All import tests passed! HardGate Agent is ready for use from any location.")
        return True
    else:
        print("⚠️ Some import tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 