#!/usr/bin/env python3
"""
Demonstration script for the new "Export Report with Comments" functionality
"""

import requests
import json
import time
import os

# Configuration
SERVER_URL = "http://localhost:8000"
TEST_REPO = "https://github.com/your-org/your-repo"  # Replace with actual repo

def demonstrate_export_functionality():
    """Demonstrate the new export report with comments functionality"""
    print("🎯 Demonstrating Export Report with Comments Functionality")
    print("=" * 70)
    
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
    
    # 3. Add comprehensive test comments
    print("3. Adding test comments to demonstrate export functionality...")
    test_comments = [
        {
            "gate_id": "alerting-alerting_actionable-0", 
            "comment": "Need to implement proper alerting for production. Current setup only has basic logging."
        },
        {
            "gate_id": "auditability-structured_logs-0", 
            "comment": "Logging framework needs to be standardized across all services. Currently using different formats."
        },
        {
            "gate_id": "availability-retry_logic-0", 
            "comment": "Retry logic implemented but needs testing under high load conditions."
        },
        {
            "gate_id": "error-handling-error_logs-0", 
            "comment": "Error logging is basic. Need to add structured error logging with correlation IDs."
        },
        {
            "gate_id": "testing-automated_tests-0", 
            "comment": "Test coverage is at 65%. Target should be 80% for critical paths."
        }
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
    
    # 4. Get the HTML report
    print("4. Retrieving HTML report with comments...")
    response = requests.get(f"{SERVER_URL}/api/v1/scan/{scan_id}/report/html")
    if response.status_code == 200:
        # Save the HTML report to a file
        with open("demo_report_with_comments.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ HTML report saved to demo_report_with_comments.html")
        print("   Open this file in your browser to see the comments functionality")
    else:
        print(f"❌ Failed to get HTML report: {response.text}")
        return None
    
    # 5. Demonstrate the export functionality
    print("\n5. Export Functionality Demonstration:")
    print("   - Open demo_report_with_comments.html in your browser")
    print("   - You'll see a '📥 Export Report with Comments' button")
    print("   - Click the button to download a complete HTML report")
    print("   - The exported report will include:")
    print("     * All your comments embedded as read-only displays")
    print("     * A comments summary section")
    print("     * Export metadata (date, scan ID, etc.)")
    print("     * Self-contained HTML that can be shared")
    
    return scan_id

def explain_export_features():
    """Explain the key features of the export functionality"""
    print("\n📋 Export Report with Comments - Key Features")
    print("=" * 50)
    
    print("\n🎯 What it does:")
    print("   - Exports the complete HTML report with all comments embedded")
    print("   - Converts interactive comment inputs to read-only displays")
    print("   - Adds a comments summary section at the top")
    print("   - Includes export metadata and timestamps")
    print("   - Creates a self-contained HTML file for sharing")
    
    print("\n📄 Export includes:")
    print("   - Complete report content with all gates and details")
    print("   - All user comments embedded as read-only text")
    print("   - Comments summary with gate names and comment text")
    print("   - Export date and scan ID information")
    print("   - Professional styling for the exported version")
    
    print("\n🚀 Benefits:")
    print("   - Share complete reports with stakeholders")
    print("   - Archive reports with team feedback")
    print("   - Include comments in JIRA uploads")
    print("   - Maintain context when sharing externally")
    print("   - Self-contained files that work offline")

def main():
    """Main demonstration function"""
    print("🚀 CodeGates Export Report with Comments Demo")
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
    
    # Explain the features
    explain_export_features()
    
    # Demonstrate the functionality
    scan_id = demonstrate_export_functionality()
    
    if scan_id:
        print(f"\n🎉 Demonstration completed successfully!")
        print(f"\n📁 Files created:")
        print(f"   - demo_report_with_comments.html (interactive report)")
        print(f"   - Exported report (when you click the export button)")
        
        print(f"\n🔗 Report URL:")
        print(f"   http://localhost:8000/api/v1/scan/{scan_id}/report/html")
        
        print(f"\n📝 Next steps:")
        print(f"   1. Open demo_report_with_comments.html in your browser")
        print(f"   2. Add more comments to different gates")
        print(f"   3. Click '📥 Export Report with Comments' button")
        print(f"   4. Check the downloaded file - it contains all comments!")
        print(f"   5. Share the exported file with your team")
    else:
        print("\n❌ Demonstration failed. Check the error messages above.")

if __name__ == "__main__":
    main() 