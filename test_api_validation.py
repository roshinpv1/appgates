#!/usr/bin/env python3
"""
Test script for API validation functionality
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the gates directory to the path
sys.path.append(str(Path(__file__).parent / "gates"))

from gates.utils.api_validator import (
    APIValidator, 
    APIEndpointConfig, 
    APIManager,
    validate_api_endpoint,
    is_api_validation_available
)


def test_api_validation_availability():
    """Test if API validation is available"""
    print("🔍 Testing API validation availability...")
    
    if is_api_validation_available():
        print("✅ API validation is available")
        return True
    else:
        print("❌ API validation is not available")
        print("   Install with: pip install requests aiohttp")
        return False


def test_single_endpoint_validation():
    """Test single endpoint validation"""
    print("\n🔍 Testing single endpoint validation...")
    
    # Test with a public API
    config = APIEndpointConfig(
        url="https://httpbin.org/json",
        method="GET",
        expected_status_codes=[200],
        response_validation={
            "required_fields": ["slideshow"],
            "field_patterns": {
                "slideshow": ".*"
            },
            "max_size": 10000
        }
    )
    
    validator = APIValidator()
    
    async def test():
        result = await validator.validate_endpoint(config)
        return result
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test())
        loop.close()
        
        print(f"✅ Endpoint validation completed")
        print(f"   URL: {result.endpoint}")
        print(f"   Status: {result.status_code}")
        print(f"   Success: {result.success}")
        print(f"   Response Time: {result.response_time:.2f}s")
        
        if result.validation_results:
            print(f"   Validation Results:")
            for key, value in result.validation_results.items():
                print(f"     {key}: {value}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Endpoint validation failed: {e}")
        return False


def test_multiple_endpoints():
    """Test multiple endpoint validation"""
    print("\n🔍 Testing multiple endpoint validation...")
    
    configs = [
        APIEndpointConfig(
            url="https://httpbin.org/get",
            method="GET",
            expected_status_codes=[200]
        ),
        APIEndpointConfig(
            url="https://httpbin.org/status/404",
            method="GET",
            expected_status_codes=[404]
        ),
        APIEndpointConfig(
            url="https://httpbin.org/post",
            method="POST",
            body={"test": "data"},
            expected_status_codes=[200]
        )
    ]
    
    validator = APIValidator()
    
    try:
        results = validator.validate_multiple_endpoints(configs)
        
        print(f"✅ Multiple endpoint validation completed")
        print(f"   Total endpoints: {len(results)}")
        
        successful = 0
        for i, result in enumerate(results, 1):
            print(f"   Endpoint {i}: {result.endpoint}")
            print(f"     Status: {result.status_code}")
            print(f"     Success: {result.success}")
            if result.success:
                successful += 1
        
        print(f"   Successful: {successful}/{len(results)}")
        return successful == len(results)
        
    except Exception as e:
        print(f"❌ Multiple endpoint validation failed: {e}")
        return False


def test_api_manager():
    """Test API manager with gate configuration"""
    print("\n🔍 Testing API manager...")
    
    # Mock gate configuration
    class MockGateConfig:
        def __init__(self):
            self.name = "TEST_GATE"
            self.validation_types = {
                'api': type('obj', (object,), {
                    'enabled': True,
                    'config': {
                        'api_validation': {
                            'enabled': True,
                            'endpoints': [
                                {
                                    'url': 'https://httpbin.org/json',
                                    'method': 'GET',
                                    'expected_status_codes': [200],
                                    'response_validation': {
                                        'required_fields': ['slideshow']
                                    }
                                }
                            ]
                        }
                    }
                })()
            }
    
    gate_config = MockGateConfig()
    api_manager = APIManager()
    
    try:
        results = api_manager.validate_gate_apis(gate_config, "httpbin.org")
        
        print(f"✅ API manager test completed")
        print(f"   Results: {len(results)} endpoints")
        
        for key, value in results.items():
            if key != 'error':
                print(f"   {key}: {value.get('success', False)}")
        
        return len(results) > 0 and 'error' not in results
        
    except Exception as e:
        print(f"❌ API manager test failed: {e}")
        return False


def test_convenience_function():
    """Test convenience function"""
    print("\n🔍 Testing convenience function...")
    
    try:
        result = validate_api_endpoint(
            url="https://httpbin.org/json",
            method="GET",
            expected_status_codes=[200]
        )
        
        print(f"✅ Convenience function test completed")
        print(f"   Success: {result.success}")
        print(f"   Status: {result.status_code}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")
        return False


def main():
    """Run all API validation tests"""
    print("🚀 API Validation Test Suite")
    print("=" * 40)
    
    tests = [
        ("API Validation Availability", test_api_validation_availability),
        ("Single Endpoint Validation", test_single_endpoint_validation),
        ("Multiple Endpoints Validation", test_multiple_endpoints),
        ("API Manager", test_api_manager),
        ("Convenience Function", test_convenience_function)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API validation is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main()) 