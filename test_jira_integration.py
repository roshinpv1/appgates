#!/usr/bin/env python3
"""
Test script for JIRA integration
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# Add the gates directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gates'))

def test_jira_connection():
    """Test JIRA connection"""
    print("🔍 Testing JIRA connection...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/jira/test")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ JIRA Connection: {result['status']}")
            print(f"📝 Message: {result['message']}")
            if result.get('jira_version'):
                print(f"🔧 JIRA Version: {result['jira_version']}")
            return True
        else:
            print(f"❌ JIRA Connection failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing JIRA connection: {str(e)}")
        return False

def test_get_jira_stories(app_id: str):
    """Test getting JIRA stories for an app_id"""
    print(f"🔍 Testing JIRA stories for app_id: {app_id}")
    
    try:
        response = requests.get(f"http://localhost:8000/api/v1/jira/stories/{app_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {result['count']} JIRA stories")
            for story in result['stories']:
                print(f"  📋 {story}")
            return True
        else:
            print(f"❌ Failed to get JIRA stories: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting JIRA stories: {str(e)}")
        return False

def test_post_report_to_jira(scan_id: str, app_id: str):
    """Test posting report to JIRA"""
    print(f"🔍 Testing posting report to JIRA for scan_id: {scan_id}, app_id: {app_id}")
    
    try:
        payload = {
            "scan_id": scan_id,
            "app_id": app_id
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/jira/post-report",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Posted report to JIRA")
            print(f"📝 Message: {result['message']}")
            print(f"📊 Stories processed: {result['stories_processed']}")
            
            if result.get('results'):
                for story_result in result['results']:
                    print(f"  📋 {story_result['story_key']}: "
                          f"Comment: {'✅' if story_result['comment_added'] else '❌'}, "
                          f"Attachment: {'✅' if story_result['attachment_added'] else '❌'}")
            return True
        else:
            print(f"❌ Failed to post report to JIRA: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error posting report to JIRA: {str(e)}")
        return False

def test_health_check():
    """Test server health check"""
    print("🔍 Testing server health...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Server Health: {result['status']}")
            print(f"🔧 JIRA Available: {result.get('jira_available', 'Unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting JIRA Integration Tests")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1️⃣ Testing server health...")
    if not test_health_check():
        print("❌ Server health check failed. Make sure the server is running.")
        return
    
    # Test 2: JIRA connection
    print("\n2️⃣ Testing JIRA connection...")
    if not test_jira_connection():
        print("❌ JIRA connection failed. Check your JIRA configuration.")
        return
    
    # Test 3: Get JIRA stories (using a test app_id)
    print("\n3️⃣ Testing JIRA stories retrieval...")
    test_app_id = "TEST123"  # Replace with a real app_id for testing
    test_get_jira_stories(test_app_id)
    
    # Test 4: Post report to JIRA (using a test scan_id)
    print("\n4️⃣ Testing report posting to JIRA...")
    test_scan_id = "test-scan-123"  # Replace with a real scan_id for testing
    test_post_report_to_jira(test_scan_id, test_app_id)
    
    print("\n" + "=" * 50)
    print("✅ JIRA Integration Tests Completed")
    print("\n📝 Notes:")
    print("- Replace test_app_id and test_scan_id with real values for full testing")
    print("- Make sure your JIRA environment variables are configured")
    print("- Check the server logs for detailed error information")

if __name__ == "__main__":
    main() 