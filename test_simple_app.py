#!/usr/bin/env python3
"""
Test script for the Simple CodeGates App
Tests the APP ID → Repository → Branch → Scan workflow
"""

import requests
import time
import json

API_BASE = "http://localhost:8000/api/v1"

def test_health():
    """Test server health"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy: {data['server']} v{data['version']}")
            print(f"📱 Streamlit port: {data['streamlit_port']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_gates():
    """Test gates endpoint"""
    print("\n🔍 Testing gates endpoint...")
    try:
        response = requests.get(f"{API_BASE}/gates", timeout=5)
        if response.status_code == 200:
            gates = response.json()
            print(f"✅ Found {len(gates)} gates:")
            for gate in gates[:3]:  # Show first 3
                print(f"   • {gate['name']}: {gate['description']}")
            return True
        else:
            print(f"❌ Gates endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Gates endpoint error: {e}")
        return False

def test_scan_workflow():
    """Test the scan workflow"""
    print("\n🔍 Testing scan workflow...")
    
    # Test scan request
    scan_request = {
        "repository_url": "https://github.com/fastapi/fastapi",
        "branch": "main",
        "github_token": None,
        "threshold": 70,
        "report_format": "both"
    }
    
    try:
        # Start scan
        print("🚀 Starting scan...")
        response = requests.post(f"{API_BASE}/scan", json=scan_request, timeout=30)
        
        if response.status_code == 200:
            scan_data = response.json()
            scan_id = scan_data["scan_id"]
            print(f"✅ Scan started: {scan_id}")
            
            # Monitor scan progress
            print("⏳ Monitoring scan progress...")
            for i in range(30):  # Monitor for up to 30 seconds
                status_response = requests.get(f"{API_BASE}/scan/{scan_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["status"]
                    progress = status_data.get("progress_percentage", 0)
                    step = status_data.get("current_step", "Unknown")
                    
                    print(f"   📊 {status.upper()}: {progress}% - {step}")
                    
                    if status == "completed":
                        print(f"🎉 Scan completed!")
                        print(f"   📈 Overall Score: {status_data.get('overall_score', 0)}%")
                        print(f"   ✅ Gates Passed: {status_data.get('passed_gates', 0)}/{status_data.get('total_gates', 0)}")
                        print(f"   📁 Files Analyzed: {status_data.get('total_files', 0)}")
                        print(f"   📝 Lines Analyzed: {status_data.get('total_lines', 0)}")
                        
                        # Test report endpoints
                        if status_data.get("html_report_url"):
                            html_response = requests.get(f"http://localhost:8000{status_data['html_report_url']}", timeout=10)
                            if html_response.status_code == 200:
                                print(f"   📄 HTML Report: Available ({len(html_response.content)} bytes)")
                            else:
                                print(f"   ❌ HTML Report: Not available ({html_response.status_code})")
                        
                        if status_data.get("json_report_url"):
                            json_response = requests.get(f"http://localhost:8000{status_data['json_report_url']}", timeout=10)
                            if json_response.status_code == 200:
                                print(f"   📊 JSON Report: Available")
                            else:
                                print(f"   ❌ JSON Report: Not available ({json_response.status_code})")
                        
                        return True
                    elif status == "failed":
                        print(f"❌ Scan failed!")
                        errors = status_data.get("errors", [])
                        for error in errors:
                            print(f"   Error: {error}")
                        return False
                
                time.sleep(2)
            
            print("⚠️ Scan monitoring timeout")
            return False
        else:
            print(f"❌ Scan start failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Scan workflow error: {e}")
        return False

def test_ui_endpoints():
    """Test UI endpoints"""
    print("\n🔍 Testing UI endpoints...")
    
    endpoints = [
        ("Main Page", "http://localhost:8000/"),
        ("UI Interface", "http://localhost:8000/ui"),
        ("API Docs", "http://localhost:8000/docs"),
        ("Direct Streamlit", "http://localhost:8501")
    ]
    
    all_good = True
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Accessible ({len(response.content)} bytes)")
            else:
                print(f"❌ {name}: Failed ({response.status_code})")
                all_good = False
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            all_good = False
    
    return all_good

def main():
    """Main test function"""
    print("🧪 CodeGates Simple App Tests")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Server Health", test_health),
        ("Gates Endpoint", test_gates),
        ("UI Endpoints", test_ui_endpoints),
        ("Scan Workflow", test_scan_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The simple app is working correctly.")
        print("\n📱 You can now access:")
        print("   • Main App: http://localhost:8000")
        print("   • UI Interface: http://localhost:8000/ui")
        print("   • API Docs: http://localhost:8000/docs")
        print("   • Direct Streamlit: http://localhost:8501")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 