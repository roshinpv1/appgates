#!/usr/bin/env python3
"""
Test script for JIRA HTML attachment functionality

This script demonstrates how to:
1. Configure JIRA integration with HTML attachments
2. Test JIRA connection
3. Post reports with HTML attachments
4. Verify attachment functionality

Usage:
    python test_jira_html_attachment.py
"""

import os
import json
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_SCAN_REQUEST = {
    "repository_url": "https://github.com/microsoft/vscode",
    "branch": "main",
    "jira_options": {
        "enabled": True,
        "issue_key": "TEST-123",  # Replace with your JIRA issue
        "comment_format": "markdown",
        "include_details": True,
        "include_recommendations": True,
        "attach_html_report": True  # This enables HTML attachment
    }
}

def test_jira_status():
    """Test JIRA integration status"""
    print("🧪 Testing JIRA integration status...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/jira/status")
        result = response.json()
        
        print(f"JIRA Available: {result.get('available', False)}")
        print(f"JIRA Enabled: {result.get('enabled', False)}")
        
        if result.get('connection_test'):
            conn_test = result['connection_test']
            print(f"Connection Test: {'✅ Success' if conn_test.get('success') else '❌ Failed'}")
            print(f"Message: {conn_test.get('message', 'No message')}")
        
        return result.get('enabled', False)
        
    except Exception as e:
        print(f"❌ Failed to check JIRA status: {e}")
        return False

def start_test_scan():
    """Start a test scan with JIRA integration enabled"""
    print("🚀 Starting test scan with JIRA HTML attachment...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/scan",
            json=TEST_SCAN_REQUEST,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            scan_id = result['scan_id']
            print(f"✅ Scan started successfully: {scan_id}")
            return scan_id
        else:
            print(f"❌ Failed to start scan: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start scan: {e}")
        return None

def wait_for_scan_completion(scan_id, max_wait_minutes=10):
    """Wait for scan to complete"""
    import time
    
    print(f"⏳ Waiting for scan {scan_id} to complete...")
    
    max_wait_seconds = max_wait_minutes * 60
    check_interval = 30  # Check every 30 seconds
    elapsed = 0
    
    while elapsed < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/scan/{scan_id}/status")
            result = response.json()
            
            status = result.get('status', 'unknown')
            print(f"📊 Scan status: {status}")
            
            if status == 'completed':
                print("✅ Scan completed successfully!")
                return True
            elif status == 'failed':
                print(f"❌ Scan failed: {result.get('message', 'Unknown error')}")
                return False
            
            # Check if JIRA posting happened
            jira_result = result.get('jira_result')
            if jira_result:
                print(f"📎 JIRA Integration:")
                print(f"  - Posted: {jira_result.get('posted', False)}")
                print(f"  - Message: {jira_result.get('message', 'No message')}")
                
                if jira_result.get('attachment_result'):
                    attach_result = jira_result['attachment_result']
                    print(f"  - Attachment: {'✅ Success' if attach_result.get('success') else '❌ Failed'}")
                    print(f"  - Attachment Message: {attach_result.get('message', 'No message')}")
            
            time.sleep(check_interval)
            elapsed += check_interval
            
        except Exception as e:
            print(f"⚠️ Error checking scan status: {e}")
            time.sleep(check_interval)
            elapsed += check_interval
    
    print(f"⏰ Scan did not complete within {max_wait_minutes} minutes")
    return False

def test_manual_jira_post(scan_id):
    """Test manual JIRA posting with HTML attachment"""
    print(f"📤 Testing manual JIRA post for scan {scan_id}...")
    
    request_data = {
        "scan_id": scan_id,
        "issue_key": "TEST-456",  # Different issue for manual test
        "comment_format": "markdown",
        "include_details": True,
        "include_recommendations": True,
        "attach_html_report": True  # Enable HTML attachment
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jira/post",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Manual JIRA post successful!")
            print(f"  - Posted: {result.get('posted', False)}")
            print(f"  - JIRA Issue: {result.get('jira_issue', 'Unknown')}")
            print(f"  - Comment URL: {result.get('comment_url', 'Not provided')}")
            
            if result.get('attachment_result'):
                attach_result = result['attachment_result']
                print(f"  - Attachment: {'✅ Success' if attach_result.get('success') else '❌ Failed'}")
                print(f"  - Attachment Message: {attach_result.get('message', 'No message')}")
            
            return True
        else:
            print(f"❌ Manual JIRA post failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed manual JIRA post: {e}")
        return False

def show_usage_examples():
    """Show usage examples for JIRA HTML attachments"""
    print("\n📚 JIRA HTML Attachment Usage Examples:")
    print("=" * 50)
    
    print("\n1. Environment Configuration:")
    print("   JIRA_ENABLED=true")
    print("   JIRA_URL=https://your-company.atlassian.net")
    print("   JIRA_USERNAME=your-email@company.com")
    print("   JIRA_API_TOKEN=your-api-token")
    print("   JIRA_ATTACH_HTML_REPORT=true")
    
    print("\n2. Scan Request with HTML Attachment:")
    print(json.dumps({
        "repository_url": "https://github.com/user/repo",
        "branch": "main",
        "jira_options": {
            "enabled": True,
            "issue_key": "PROJ-123",
            "attach_html_report": True
        }
    }, indent=2))
    
    print("\n3. Manual JIRA Post with Attachment:")
    print("   curl -X POST 'http://localhost:8000/api/v1/jira/post' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print("       \"scan_id\": \"your-scan-id\",")
    print("       \"issue_key\": \"PROJ-123\",")
    print("       \"attach_html_report\": true")
    print("     }'")

def main():
    """Main test function"""
    print("🧪 JIRA HTML Attachment Test Suite")
    print("=" * 40)
    
    # Check if JIRA is configured
    if not test_jira_status():
        print("\n⚠️ JIRA integration is not properly configured.")
        print("Please set up JIRA configuration before running this test.")
        show_usage_examples()
        return
    
    # Ask user if they want to proceed
    print(f"\n📋 This test will:")
    print(f"   1. Start a scan of: {TEST_SCAN_REQUEST['repository_url']}")
    print(f"   2. Post results to JIRA issue: {TEST_SCAN_REQUEST['jira_options']['issue_key']}")
    print(f"   3. Attach HTML report to the JIRA issue")
    print(f"   4. Test manual JIRA posting")
    
    proceed = input("\n❓ Do you want to proceed? (y/N): ").lower().strip()
    if proceed != 'y':
        print("❌ Test cancelled by user")
        show_usage_examples()
        return
    
    # Start the test scan
    scan_id = start_test_scan()
    if not scan_id:
        print("❌ Failed to start test scan")
        return
    
    # Wait for completion
    if wait_for_scan_completion(scan_id):
        print("\n🎉 Scan completed successfully!")
        
        # Test manual JIRA posting
        test_manual_jira_post(scan_id)
        
        print(f"\n✅ Test completed!")
        print(f"Check your JIRA issues for:")
        print(f"  - {TEST_SCAN_REQUEST['jira_options']['issue_key']} (automatic)")
        print(f"  - TEST-456 (manual)")
        print(f"Both should have HTML reports attached!")
        
    else:
        print("❌ Scan did not complete successfully")
    
    show_usage_examples()

if __name__ == "__main__":
    main() 