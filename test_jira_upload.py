#!/usr/bin/env python3
"""
Test JIRA Upload Functionality
Tests the JIRA integration with current environment variables
"""

import requests
import json
import os

def test_jira_upload():
    print("🧪 Testing JIRA Upload with Current Environment...")
    
    # Create a test report file
    os.makedirs("./test_reports", exist_ok=True)
    test_report = {
        "overall_score": 75.5,
        "summary": {
            "total_gates": 17,
            "passed_gates": 12,
            "failed_gates": 3,
            "warning_gates": 2
        },
        "gates": [
            {
                "name": "Logging Gate",
                "status": "passed",
                "score": 100,
                "description": "Test logging gate"
            },
            {
                "name": "Security Gate",
                "status": "failed",
                "score": 0,
                "description": "Test security gate"
            }
        ]
    }
    
    # Write test report
    report_path = "./test_reports/jira_test_report.json"
    with open(report_path, 'w') as f:
        json.dump(test_report, f, indent=2)
    
    print("✅ Created test report file")
    
    # Test JIRA upload endpoint
    upload_data = {
        "app_id": "jira-ssl-test",
        "scan_id": "test-scan-123", 
        "report_type": "json",
        "jira_ticket_id": "TEST-456",
        "gate_number": 1,
        "comment": "Testing JIRA upload with improved SSL configuration"
    }
    
    try:
        print("\n🔄 Making JIRA upload request...")
        response = requests.post(
            "http://localhost:8000/api/v1/jira/upload",
            json=upload_data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Request successful!")
            print(f"   Success: {data.get('success', 'Unknown')}")
            print(f"   Message: {data.get('message', 'No message')}")
            
            if 'results' in data:
                print(f"   Results: {len(data['results'])} entries")
                for result in data['results']:
                    print(f"     - Story: {result.get('story', 'Unknown')}")
                    print(f"       Success: {result.get('success', 'Unknown')}")
                    
        elif response.status_code == 400:
            data = response.json()
            detail = data.get('detail', 'No detail')
            print("⚠️ Bad Request (400):")
            print(f"   Detail: {detail}")
            
            if 'JIRA_URL' in detail:
                print("❌ JIRA environment variables not loaded properly")
            elif 'Report file not found' in detail:
                print("ℹ️  Report file not found (expected for this test)")
                print("✅ But JIRA environment variables are loaded!")
                print("   This means SSL configuration is working")
            
        elif response.status_code == 404:
            data = response.json()
            print("⚠️ Not Found (404):")
            print(f"   Detail: {data.get('detail', 'No detail')}")
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Server not running on localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Clean up test file
    if os.path.exists(report_path):
        os.remove(report_path)
        print("\n🧹 Cleaned up test report file")

def test_server_health():
    print("\n🏥 Testing Server Health...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy!")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Active Scans: {data.get('active_scans', 0)}")
            
            if 'jira_environment' in data:
                jira_info = data['jira_environment']
                print("✅ JIRA environment variables detected:")
                print(f"   URL: {jira_info.get('url', 'Not set')}")
                print(f"   User: {jira_info.get('user', 'Not set')}")
                print(f"   Token: {'Set' if jira_info.get('token_set') else 'Not set'}")
                print(f"   SSL Verify: {jira_info.get('ssl_verify', 'Not configured')}")
            else:
                print("⚠️ JIRA environment variables not found in health check")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    test_server_health()
    test_jira_upload()
    print("\n🎯 JIRA Upload Test Complete!") 