#!/usr/bin/env python3
"""
Test script to verify report storage functionality
"""

import os
import json
import requests
import time
from pathlib import Path


def test_report_storage():
    """Test report storage functionality"""
    
    print("🧪 Testing Report Storage Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Step 1: Start a scan
    print("\n1️⃣ Starting a test scan...")
    
    scan_request = {
        "repo_url": "https://github.com/example/test-repo",
        "branch": "main",
        "git_token": "test-token",
        "scan_id": f"test_scan_{int(time.time())}"
    }
    
    response = requests.post(f"{base_url}/api/v1/scan", json=scan_request)
    
    if response.status_code == 200:
        scan_data = response.json()
        scan_id = scan_data.get("scan_id")
        print(f"✅ Scan started: {scan_id}")
    else:
        print(f"❌ Failed to start scan: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # Step 2: Wait for scan completion
    print("\n2️⃣ Waiting for scan completion...")
    
    max_wait = 60  # 60 seconds
    wait_time = 0
    
    while wait_time < max_wait:
        response = requests.get(f"{base_url}/api/v1/scan/{scan_id}")
        
        if response.status_code == 200:
            scan_status = response.json()
            status = scan_status.get("status", "unknown")
            
            print(f"   Status: {status}")
            
            if status == "completed":
                print("✅ Scan completed!")
                break
            elif status == "failed":
                print("❌ Scan failed!")
                return
        else:
            print(f"   Error checking status: {response.status_code}")
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("❌ Scan timed out!")
        return
    
    # Step 3: Check if reports were stored
    print("\n3️⃣ Checking report storage...")
    
    # Check reports directory structure
    reports_dir = "reports"
    scan_dir = os.path.join(reports_dir, scan_id)
    
    print(f"📁 Reports directory: {reports_dir}")
    print(f"📁 Scan directory: {scan_dir}")
    
    if os.path.exists(reports_dir):
        print(f"✅ Reports directory exists")
        
        if os.path.exists(scan_dir):
            print(f"✅ Scan directory exists")
            
            # List files in scan directory
            files = os.listdir(scan_dir)
            print(f"📄 Files in scan directory: {files}")
            
            # Check specific files
            expected_files = [
                f"codegates_report_{scan_id}.html",
                f"codegates_report_{scan_id}.json",
                f"report_summary_{scan_id}.txt"
            ]
            
            for expected_file in expected_files:
                file_path = os.path.join(scan_dir, expected_file)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"✅ {expected_file}: {file_size} bytes")
                else:
                    print(f"❌ {expected_file}: Not found")
        else:
            print(f"❌ Scan directory does not exist")
    else:
        print(f"❌ Reports directory does not exist")
    
    # Step 4: Test report files API endpoint
    print("\n4️⃣ Testing report files API endpoint...")
    
    response = requests.get(f"{base_url}/api/v1/report/{scan_id}/files")
    
    if response.status_code == 200:
        files_data = response.json()
        print(f"✅ Report files endpoint response:")
        print(f"   Scan ID: {files_data.get('scan_id')}")
        print(f"   Report Directory: {files_data.get('report_directory')}")
        print(f"   Report Paths: {files_data.get('report_paths')}")
    else:
        print(f"❌ Failed to get report files: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Step 5: Test list all reports endpoint
    print("\n5️⃣ Testing list all reports endpoint...")
    
    response = requests.get(f"{base_url}/api/v1/reports/list")
    
    if response.status_code == 200:
        reports_data = response.json()
        print(f"✅ List reports endpoint response:")
        print(f"   Total reports: {reports_data.get('total')}")
        print(f"   Reports directory: {reports_data.get('reports_directory')}")
        
        reports = reports_data.get('reports', [])
        for report in reports:
            print(f"   - {report.get('scan_id')}: HTML={report.get('has_html')}, JSON={report.get('has_json')}")
    else:
        print(f"❌ Failed to list reports: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Step 6: Verify HTML report content
    print("\n6️⃣ Verifying HTML report content...")
    
    html_path = os.path.join(scan_dir, f"codegates_report_{scan_id}.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"✅ HTML report loaded: {len(html_content)} characters")
        
        # Check for key HTML elements
        checks = [
            ("DOCTYPE", "<!DOCTYPE html>" in html_content),
            ("Title", "CodeGates" in html_content),
            ("Scan ID", scan_id in html_content),
            ("CSS Styles", "style" in html_content),
            ("Table", "<table" in html_content)
        ]
        
        print("📋 HTML Content Verification:")
        for check_name, found in checks:
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    else:
        print(f"❌ HTML report file not found")
    
    # Step 7: Verify JSON report content
    print("\n7️⃣ Verifying JSON report content...")
    
    json_path = os.path.join(scan_dir, f"codegates_report_{scan_id}.json")
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = f.read()
        
        print(f"✅ JSON report loaded: {len(json_content)} characters")
        
        try:
            json_data = json.loads(json_content)
            print(f"✅ JSON is valid")
            
            # Check for key fields
            checks = [
                ("scan_id", json_data.get("scan_id") == scan_id),
                ("repo_url", "repo_url" in json_data),
                ("gate_results", "gate_results" in json_data),
                ("risk_score", "risk_score" in json_data),
                ("total_gates", "total_gates" in json_data)
            ]
            
            print("📋 JSON Content Verification:")
            for check_name, found in checks:
                status = "✅" if found else "❌"
                print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON is invalid: {e}")
    else:
        print(f"❌ JSON report file not found")
    
    # Step 8: Verify summary file content
    print("\n8️⃣ Verifying summary file content...")
    
    summary_path = os.path.join(scan_dir, f"report_summary_{scan_id}.txt")
    if os.path.exists(summary_path):
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_content = f.read()
        
        print(f"✅ Summary file loaded: {len(summary_content)} characters")
        
        # Check for key content
        checks = [
            ("Scan ID", scan_id in summary_content),
            ("Repository", "Repository:" in summary_content),
            ("Results Summary", "Results Summary:" in summary_content),
            ("Report Files", "Report Files:" in summary_content),
            ("Report Directory", "Report Directory:" in summary_content)
        ]
        
        print("📋 Summary Content Verification:")
        for check_name, found in checks:
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    else:
        print(f"❌ Summary file not found")
    
    print("\n🎉 Report Storage Test Complete!")
    print(f"\n📖 Report files are available at:")
    print(f"   📁 Directory: {scan_dir}")
    print(f"   🌐 HTML: file://{Path(html_path).absolute()}" if os.path.exists(html_path) else "   ❌ HTML: Not found")
    print(f"   📄 JSON: {json_path}" if os.path.exists(json_path) else "   ❌ JSON: Not found")
    print(f"   📋 Summary: {summary_path}" if os.path.exists(summary_path) else "   ❌ Summary: Not found")


if __name__ == "__main__":
    test_report_storage()
