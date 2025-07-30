#!/usr/bin/env python3
"""
Test script for Comments and JIRA Upload functionality
"""

import requests
import json
import time
import os

# Configuration
SERVER_URL = "http://localhost:8000"
TEST_REPO = "https://github.com/your-org/your-repo"  # Replace with actual repo

def test_comment_functionality():
    """Test the comment functionality"""
    print("🧪 Testing Comment Functionality")
    print("=" * 50)
    
    # 1. Start a scan
    print("1. Starting a scan...")
    scan_request = {
        "repository_url": TEST_REPO,
        "branch": "main",
        "threshold": 70
    }
    
    response = requests.post(f"{SERVER_URL}/api/v1/scan", json=scan_request)
    if response.status_code != 200:
        print(f"❌ Failed to start scan: {response.text}")
        return None
    
    scan_data = response.json()
    scan_id = scan_data["scan_id"]
    print(f"✅ Scan started with ID: {scan_id}")
    
    # 2. Wait for scan to complete
    print("2. Waiting for scan to complete...")
    while True:
        response = requests.get(f"{SERVER_URL}/api/v1/scan/{scan_id}")
        if response.status_code == 200:
            scan_status = response.json()
            if scan_status["status"] == "completed":
                print("✅ Scan completed!")
                break
            elif scan_status["status"] == "failed":
                print(f"❌ Scan failed: {scan_status.get('errors', [])}")
                return None
            else:
                print(f"⏳ Status: {scan_status['status']} - {scan_status.get('current_step', 'Processing...')}")
                time.sleep(5)
        else:
            print(f"❌ Failed to get scan status: {response.text}")
            return None
    
    # 3. Save some test comments
    print("3. Saving test comments...")
    test_comments = [
        {"gate_id": "alerting-alerting_actionable-0", "comment": "Need to implement proper alerting for production"},
        {"gate_id": "auditability-structured_logs-0", "comment": "Logging framework needs to be standardized"},
        {"gate_id": "availability-retry_logic-0", "comment": "Retry logic implemented but needs testing"}
    ]
    
    for comment_data in test_comments:
        comment_request = {
            "scan_id": scan_id,
            "gate_id": comment_data["gate_id"],
            "comment": comment_data["comment"]
        }
        
        response = requests.post(f"{SERVER_URL}/api/v1/comments/save", json=comment_request)
        if response.status_code == 200:
            print(f"✅ Comment saved for {comment_data['gate_id']}")
        else:
            print(f"❌ Failed to save comment: {response.text}")
    
    # 4. Get all comments
    print("4. Retrieving all comments...")
    response = requests.get(f"{SERVER_URL}/api/v1/comments/{scan_id}")
    if response.status_code == 200:
        comments_data = response.json()
        print("✅ Comments retrieved:")
        for gate_id, comment in comments_data["comments"].items():
            print(f"   - {gate_id}: {comment}")
    else:
        print(f"❌ Failed to retrieve comments: {response.text}")
    
    # 5. View the HTML report
    print("5. Viewing HTML report...")
    response = requests.get(f"{SERVER_URL}/api/v1/scan/{scan_id}/report/html")
    if response.status_code == 200:
        # Save the HTML report to a file
        with open("test_report_with_comments.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ HTML report saved to test_report_with_comments.html")
        print("   Open this file in your browser to see the comments functionality")
    else:
        print(f"❌ Failed to get HTML report: {response.text}")
    
    return scan_id

def test_jira_upload(scan_id):
    """Test JIRA upload functionality"""
    print("\n🧪 Testing JIRA Upload Functionality")
    print("=" * 50)
    
    # Check if JIRA environment variables are set
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")
    
    if not all([jira_url, jira_user, jira_token]):
        print("⚠️  JIRA environment variables not set. Skipping JIRA upload test.")
        print("   Set JIRA_URL, JIRA_USER, and JIRA_TOKEN environment variables to test JIRA upload.")
        return
    
    # Test JIRA upload with comments
    print("1. Uploading report to JIRA with comments...")
    jira_request = {
        "app_id": "TEST-APP",
        "scan_id": scan_id,
        "report_type": "html",
        "include_comments": True
    }
    
    response = requests.post(f"{SERVER_URL}/api/v1/jira/upload", json=jira_request)
    if response.status_code == 200:
        print("✅ JIRA upload started successfully")
        print("   Check your JIRA stories for the uploaded report with comments")
    else:
        print(f"❌ Failed to upload to JIRA: {response.text}")

def main():
    """Main test function"""
    print("🚀 CodeGates Comments and JIRA Upload Test")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/api/v1/health")
        if response.status_code != 200:
            print(f"❌ Server not responding: {response.status_code}")
            return
        print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on localhost:8000")
        return
    
    # Test comment functionality
    scan_id = test_comment_functionality()
    
    if scan_id:
        # Test JIRA upload
        test_jira_upload(scan_id)
    
    print("\n🎉 Test completed!")
    print("\nNext steps:")
    print("1. Open test_report_with_comments.html in your browser")
    print("2. Add comments to gates using the comment system")
    print("3. Use the 'Export Report with Comments' button to download the complete report")
    print("4. Upload to JIRA with comments included")

if __name__ == "__main__":
    main() 