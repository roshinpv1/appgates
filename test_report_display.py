#!/usr/bin/env python3
"""
Test script for the Enhanced Report Display
Demonstrates the inline report viewing functionality
"""

import requests
import time
import json

API_BASE = "http://localhost:8000/api/v1"

def test_report_display():
    """Test the enhanced report display functionality"""
    print("🧪 Testing Enhanced Report Display")
    print("=" * 50)
    
    # Start a test scan
    print("🚀 Starting test scan...")
    scan_request = {
        "repository_url": "https://github.com/fastapi/fastapi",
        "branch": "main",
        "github_token": None,
        "threshold": 70,
        "report_format": "both"
    }
    
    try:
        response = requests.post(f"{API_BASE}/scan", json=scan_request, timeout=30)
        if response.status_code == 200:
            scan_data = response.json()
            scan_id = scan_data["scan_id"]
            print(f"✅ Scan started: {scan_id}")
            
            # Wait for scan to complete
            print("⏳ Waiting for scan to complete...")
            time.sleep(12)  # Wait for mock scan to finish
            
            # Check scan status
            status_response = requests.get(f"{API_BASE}/scan/{scan_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📊 Scan Status: {status_data['status']}")
                print(f"📈 Overall Score: {status_data.get('overall_score', 0)}%")
                print(f"✅ Gates Passed: {status_data.get('passed_gates', 0)}/{status_data.get('total_gates', 0)}")
                
                # Test HTML report
                print("\n📄 Testing HTML Report...")
                html_response = requests.get(f"{API_BASE}/scan/{scan_id}/report/html")
                if html_response.status_code == 200:
                    html_content = html_response.text
                    print(f"✅ HTML Report loaded ({len(html_content)} characters)")
                    print(f"📋 Preview: {html_content[:100]}...")
                else:
                    print(f"❌ HTML Report failed: {html_response.status_code}")
                
                # Test JSON report
                print("\n🔢 Testing JSON Report...")
                json_response = requests.get(f"{API_BASE}/scan/{scan_id}/report/json")
                if json_response.status_code == 200:
                    json_content = json_response.json()
                    print(f"✅ JSON Report loaded")
                    print(f"📋 Report Data:")
                    print(json.dumps(json_content, indent=2))
                else:
                    print(f"❌ JSON Report failed: {json_response.status_code}")
                
                return True
            else:
                print(f"❌ Failed to get scan status: {status_response.status_code}")
                return False
        else:
            print(f"❌ Failed to start scan: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎯 Enhanced Report Display Test")
    print()
    
    # Check server health first
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure to run: python3 run_simple_app.py")
        return
    
    # Run the report display test
    if test_report_display():
        print("\n🎉 Report Display Test Successful!")
        print("\n📱 New Features Available:")
        print("   • 📊 Summary Tab - Overview with metrics and progress bar")
        print("   • 📄 HTML Report Tab - Full HTML report displayed inline")
        print("   • 🔢 JSON Report Tab - Structured data with key insights")
        print("   • 🔄 Auto-loading - Reports load automatically when scan completes")
        print("   • 📋 Rich Display - HTML rendered properly, JSON formatted nicely")
        print("\n🚀 Visit http://localhost:8000/ui to see the enhanced reports!")
    else:
        print("\n❌ Report Display Test Failed")

if __name__ == "__main__":
    main() 