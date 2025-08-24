#!/usr/bin/env python3
"""
Test script to demonstrate HTML report functionality
"""

import requests
import json
import time
from pathlib import Path

def test_html_report():
    """Test the complete HTML report workflow"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing CodeGates HTML Report Functionality")
    print("=" * 50)
    
    # Step 1: Run a scan
    print("\n1️⃣ Running a scan...")
    scan_request = {
        "repo_url": "https://github.com/octocat/Hello-World",
        "branch": "main"
    }
    
    response = requests.post(f"{base_url}/api/v1/scan", json=scan_request)
    
    if response.status_code != 200:
        print(f"❌ Scan failed: {response.status_code}")
        return
    
    scan_result = response.json()
    scan_id = scan_result["scan_id"]
    print(f"✅ Scan completed: {scan_id}")
    print(f"   Status: {scan_result['status']}")
    print(f"   Message: {scan_result['message']}")
    
    # Step 2: Get JSON results
    print("\n2️⃣ Getting JSON results...")
    response = requests.get(f"{base_url}/api/v1/scan/{scan_id}")
    
    if response.status_code == 200:
        json_data = response.json()
        print(f"✅ JSON results retrieved")
        print(f"   Total gates: {json_data.get('result', {}).get('total_gates', 0)}")
        print(f"   Passed gates: {json_data.get('result', {}).get('passed_gates', 0)}")
        print(f"   Failed gates: {json_data.get('result', {}).get('failed_gates', 0)}")
    else:
        print(f"❌ Failed to get JSON results: {response.status_code}")
    
    # Step 3: Get HTML report
    print("\n3️⃣ Getting HTML report...")
    response = requests.get(f"{base_url}/api/v1/report/{scan_id}/html")
    
    if response.status_code == 200:
        html_content = response.text
        print(f"✅ HTML report generated successfully!")
        print(f"   Content length: {len(html_content)} characters")
        print(f"   Report URL: {base_url}/api/v1/report/{scan_id}/html")
        
        # Save HTML report to file for viewing
        report_file = f"scan_report_{scan_id}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   📄 Report saved to: {report_file}")
        print(f"   🌐 Open in browser: file://{Path(report_file).absolute()}")
        
        # Show a preview of the HTML
        print("\n📋 HTML Report Preview:")
        print("-" * 30)
        lines = html_content.split('\n')
        for i, line in enumerate(lines):
            if i < 20:  # Show first 20 lines
                print(line)
            elif i == 20:
                print("... (truncated)")
                break
        
    else:
        print(f"❌ Failed to get HTML report: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Step 4: List all scans
    print("\n4️⃣ Listing all scans...")
    response = requests.get(f"{base_url}/api/v1/scans")
    
    if response.status_code == 200:
        scans = response.json()
        print(f"✅ Found {len(scans)} scans")
        for scan in scans:
            print(f"   - {scan.get('scan_id', 'unknown')}: {scan.get('status', 'unknown')}")
    else:
        print(f"❌ Failed to list scans: {response.status_code}")
    
    print("\n🎉 HTML Report Test Complete!")
    print("\n📖 How to view the report:")
    print("1. Open the saved HTML file in your browser")
    print("2. Or visit the API endpoint directly")
    print("3. The report uses the same template as the gates system")

if __name__ == "__main__":
    test_html_report()
