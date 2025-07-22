#!/usr/bin/env python3
"""
Test script for AppDynamics integration
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# Add the gates directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gates'))

def test_appdynamics_connection():
    """Test AppDynamics connection"""
    print("🔍 Testing AppDynamics connection...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/appdynamics/test")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AppDynamics Connection: {result['status']}")
            print(f"📝 Message: {result['message']}")
            if result.get('appd_version'):
                print(f"🔧 AppDynamics Version: {result['appd_version']}")
            return True
        else:
            print(f"❌ AppDynamics Connection failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing AppDynamics connection: {str(e)}")
        return False

def test_get_applications():
    """Test getting AppDynamics applications"""
    print("🔍 Testing AppDynamics applications...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/appdynamics/applications")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AppDynamics Applications: {result['status']}")
            print(f"📊 Total Applications: {result['total_applications']}")
            for app in result['applications'][:5]:  # Show first 5 apps
                print(f"  📋 {app.get('name', 'Unknown')} (ID: {app.get('id', 'Unknown')})")
            return True
        else:
            print(f"❌ Failed to get applications: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting applications: {str(e)}")
        return False

def test_app_validation(app_name: str):
    """Test app validation in AppDynamics"""
    print(f"🔍 Testing app validation for app_name: {app_name}")
    
    try:
        payload = {
            "app_name": app_name,
            "time_range": "60"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/appdynamics/validate-app",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ App Validation: {result['status']}")
            print(f"📊 Overall Status: {result['overall_status']}")
            print(f"📝 App ID: {result.get('app_id', 'Unknown')}")
            print(f"🔧 Health Rules: {result['summary'].get('health_rules_count', 0)}")
            print(f"❌ Errors: {result['summary'].get('error_count', 0)}")
            return True
        else:
            print(f"❌ App Validation failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing app validation: {str(e)}")
        return False

def test_get_application(app_name: str):
    """Test getting specific application"""
    print(f"🔍 Testing get application: {app_name}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/appdynamics/application/{app_name}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Application Found: {result['status']}")
            if result.get('application'):
                app = result['application']
                print(f"  📋 Name: {app.get('name', 'Unknown')}")
                print(f"  🆔 ID: {app.get('id', 'Unknown')}")
                print(f"  📊 Description: {app.get('description', 'No description')}")
            return True
        else:
            print(f"❌ Failed to get application: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting application: {str(e)}")
        return False

def test_get_metrics(app_id: int):
    """Test getting application metrics"""
    print(f"🔍 Testing get metrics for app_id: {app_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/appdynamics/app/{app_id}/metrics")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Metrics Retrieved: {result['status']}")
            print(f"📊 Metric Path: {result.get('metric_path', 'Unknown')}")
            print(f"📈 Metrics Count: {len(result.get('metrics', []))}")
            return True
        else:
            print(f"❌ Failed to get metrics: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting metrics: {str(e)}")
        return False

def test_get_health_rules(app_id: int):
    """Test getting health rules"""
    print(f"🔍 Testing get health rules for app_id: {app_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/appdynamics/app/{app_id}/health-rules")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health Rules Retrieved: {result['status']}")
            print(f"📊 Total Health Rules: {result.get('total_health_rules', 0)}")
            return True
        else:
            print(f"❌ Failed to get health rules: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting health rules: {str(e)}")
        return False

def test_get_errors(app_id: int):
    """Test getting errors"""
    print(f"🔍 Testing get errors for app_id: {app_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/appdynamics/app/{app_id}/errors?time_range=60")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Errors Retrieved: {result['status']}")
            print(f"📊 Total Errors: {result.get('total_errors', 0)}")
            return True
        else:
            print(f"❌ Failed to get errors: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting errors: {str(e)}")
        return False

def test_get_performance(app_id: int):
    """Test getting performance data"""
    print(f"🔍 Testing get performance for app_id: {app_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/appdynamics/app/{app_id}/performance?time_range=60")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Performance Retrieved: {result['status']}")
            print(f"📊 Performance Metrics: {len(result.get('performance', {}))}")
            return True
        else:
            print(f"❌ Failed to get performance: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting performance: {str(e)}")
        return False

def test_health_check():
    """Test server health check"""
    print("🔍 Testing server health...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server Health: {result['status']}")
            print(f"🔧 AppDynamics Available: {result.get('appdynamics_available', 'Unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting AppDynamics Integration Tests")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1️⃣ Testing server health...")
    if not test_health_check():
        print("❌ Server health check failed. Make sure the server is running.")
        return
    
    # Test 2: AppDynamics connection
    print("\n2️⃣ Testing AppDynamics connection...")
    if not test_appdynamics_connection():
        print("❌ AppDynamics connection failed. Check your AppDynamics configuration.")
        return
    
    # Test 3: Get applications
    print("\n3️⃣ Testing get applications...")
    test_get_applications()
    
    # Test 4: Get specific application
    print("\n4️⃣ Testing get specific application...")
    test_app_name = "TestApp"  # Replace with a real app name for testing
    test_get_application(test_app_name)
    
    # Test 5: App validation
    print("\n5️⃣ Testing app validation...")
    test_app_validation(test_app_name)
    
    # Test 6: Get metrics (using a test app_id)
    print("\n6️⃣ Testing get metrics...")
    test_app_id = 123  # Replace with a real app_id for testing
    test_get_metrics(test_app_id)
    
    # Test 7: Get health rules
    print("\n7️⃣ Testing get health rules...")
    test_get_health_rules(test_app_id)
    
    # Test 8: Get errors
    print("\n8️⃣ Testing get errors...")
    test_get_errors(test_app_id)
    
    # Test 9: Get performance
    print("\n9️⃣ Testing get performance...")
    test_get_performance(test_app_id)
    
    print("\n" + "=" * 50)
    print("✅ AppDynamics Integration Tests Completed")
    print("\n📝 Notes:")
    print("- Replace test_app_name and test_app_id with real values for full testing")
    print("- Make sure your AppDynamics environment variables are configured")
    print("- Check the server logs for detailed error information")

if __name__ == "__main__":
    main() 