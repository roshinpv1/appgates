#!/usr/bin/env python3
"""
Test script for Splunk integration
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# Add the gates directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gates'))

def test_splunk_connection():
    """Test Splunk connection"""
    print("🔍 Testing Splunk connection...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/splunk/test")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Splunk Connection: {result['status']}")
            print(f"📝 Message: {result['message']}")
            if result.get('splunk_version'):
                print(f"🔧 Splunk Version: {result['splunk_version']}")
            return True
        else:
            print(f"❌ Splunk Connection failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing Splunk connection: {str(e)}")
        return False

def test_splunk_search():
    """Test Splunk search functionality"""
    print("🔍 Testing Splunk search...")
    
    try:
        payload = {
            "query": "search index=* | head 10",
            "earliest_time": "-1h",
            "latest_time": "now",
            "max_results": 10
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/splunk/search",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Splunk Search: {result['status']}")
            print(f"📊 Total Results: {result['total_results']}")
            print(f"⏱️ Execution Time: {result.get('execution_time', 'N/A')}")
            return True
        else:
            print(f"❌ Splunk Search failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing Splunk search: {str(e)}")
        return False

def test_app_validation(app_id: str):
    """Test app validation in Splunk"""
    print(f"🔍 Testing app validation for app_id: {app_id}")
    
    try:
        payload = {
            "app_id": app_id,
            "time_range": "-24h"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/splunk/validate-app",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ App Validation: {result['status']}")
            print(f"📊 Overall Status: {result['overall_status']}")
            print(f"📝 Log Count: {result['log_validation'].get('log_count', 0)}")
            print(f"❌ Error Count: {result['error_validation'].get('error_count', 0)}")
            print(f"⚡ Metric Count: {result['performance_validation'].get('metric_count', 0)}")
            return True
        else:
            print(f"❌ App Validation failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing app validation: {str(e)}")
        return False

def test_splunk_job():
    """Test Splunk job functionality"""
    print("🔍 Testing Splunk job creation...")
    
    try:
        # Start a job
        payload = {
            "query": "search index=* | head 100",
            "earliest_time": "-1h",
            "latest_time": "now"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/splunk/job",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Job Created: {job_id}")
            
            # Check job status
            status_response = requests.get(f"http://localhost:8000/api/v1/splunk/job/{job_id}")
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"📊 Job Status: Done={status_result.get('is_done', False)}, Progress={status_result.get('progress', 0)}")
            
            return True
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing Splunk job: {str(e)}")
        return False

def test_health_check():
    """Test server health check"""
    print("🔍 Testing server health...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server Health: {result['status']}")
            print(f"🔧 Splunk Available: {result.get('splunk_available', 'Unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Splunk Integration Tests")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1️⃣ Testing server health...")
    if not test_health_check():
        print("❌ Server health check failed. Make sure the server is running.")
        return
    
    # Test 2: Splunk connection
    print("\n2️⃣ Testing Splunk connection...")
    if not test_splunk_connection():
        print("❌ Splunk connection failed. Check your Splunk configuration.")
        return
    
    # Test 3: Splunk search
    print("\n3️⃣ Testing Splunk search...")
    test_splunk_search()
    
    # Test 4: App validation
    print("\n4️⃣ Testing app validation...")
    test_app_id = "TEST123"  # Replace with a real app_id for testing
    test_app_validation(test_app_id)
    
    # Test 5: Splunk job
    print("\n5️⃣ Testing Splunk job...")
    test_splunk_job()
    
    print("\n" + "=" * 50)
    print("✅ Splunk Integration Tests Completed")
    print("\n📝 Notes:")
    print("- Replace test_app_id with real values for full testing")
    print("- Make sure your Splunk environment variables are configured")
    print("- Check the server logs for detailed error information")

if __name__ == "__main__":
    main() 