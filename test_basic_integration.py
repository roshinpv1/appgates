#!/usr/bin/env python3
"""
Basic Integration Test
Tests the core integration functionality without requiring all dependencies
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_basic_integration():
    """Test basic integration functionality"""
    print("🧪 Testing Basic CodeGates Agent Integration...")
    print("=" * 60)
    
    try:
        # Test 1: Import integration module
        print("📦 Test 1: Importing agent integration...")
        from gates.agent_integration import create_agent_integration, get_integration_status
        print("✅ Agent integration module imported successfully")
        
        # Test 2: Check integration status
        print("\n📊 Test 2: Checking integration status...")
        status = get_integration_status()
        print(f"✅ Integration status retrieved")
        print(f"   Capabilities: {status.get('capabilities', {})}")
        print(f"   Services: {status.get('services_initialized', {})}")
        
        # Test 3: Create integration instance
        print("\n🔧 Test 3: Creating integration instance...")
        integration = create_agent_integration()
        print("✅ Integration instance created successfully")
        
        # Test 4: Check capabilities
        print("\n🎯 Test 4: Checking available capabilities...")
        capabilities = integration.get_available_capabilities()
        print(f"✅ Available capabilities:")
        for capability, available in capabilities.items():
            status_icon = "✅" if available else "❌"
            print(f"   {status_icon} {capability}: {available}")
        
        print("\n" + "=" * 60)
        print("🎉 Basic Integration Test Summary:")
        print("=" * 60)
        print("✅ Integration module loads successfully")
        print("✅ Status checking works")
        print("✅ Instance creation works")
        print("✅ Capability detection works")
        
        # Summary of what's available
        available_count = sum(capabilities.values())
        total_count = len(capabilities)
        print(f"\n📋 Integration Status: {available_count}/{total_count} capabilities available")
        
        if available_count > 0:
            print("✅ Integration is working - some capabilities are available")
        else:
            print("⚠️ No capabilities available - check dependencies")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 This indicates a fundamental issue with the integration")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_server_import():
    """Test that server can import the integration"""
    print("\n🌐 Testing Server Integration Import...")
    print("=" * 60)
    
    try:
        # Test server import
        print("📦 Test 1: Importing server module...")
        from gates.server import app
        print("✅ Server module imported successfully")
        
        # Check if agent endpoints are available
        print("\n🔗 Test 2: Checking agent endpoints...")
        routes = [route.path for route in app.routes]
        agent_routes = [route for route in routes if "/api/v1/agent" in route]
        
        if agent_routes:
            print(f"✅ Found {len(agent_routes)} agent endpoints:")
            for route in agent_routes:
                print(f"   - {route}")
        else:
            print("⚠️ No agent endpoints found")
        
        return True
        
    except Exception as e:
        print(f"❌ Server integration test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Basic CodeGates Agent Integration Test")
    print("=" * 60)
    print("This test verifies the basic integration functionality")
    print("without requiring all dependencies to be available.")
    print("=" * 60)
    
    # Test basic integration
    basic_ok = test_basic_integration()
    
    # Test server integration
    server_ok = test_server_import()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BASIC TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Integration: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"Server Integration: {'✅ PASS' if server_ok else '❌ FAIL'}")
    
    if basic_ok and server_ok:
        print("\n🎉 BASIC TESTS PASSED!")
        print("✅ Integration framework is working")
        print("✅ Server can import integration")
        print("✅ Ready for advanced testing")
    else:
        print("\n⚠️ Some basic tests failed")
        if not basic_ok:
            print("❌ Basic integration failed - check module structure")
        if not server_ok:
            print("❌ Server integration failed - check server configuration")
    
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    print("=" * 60)
    print("1. If basic tests pass, the integration framework is ready")
    print("2. Install optional dependencies for full functionality:")
    print("   - pip install google-adk")
    print("   - pip install litellm")
    print("3. Run full test: python3 test_agent_integration.py")
    print("4. Use the integration in your applications")


if __name__ == "__main__":
    main()
