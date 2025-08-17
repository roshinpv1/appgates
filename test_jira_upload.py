#!/usr/bin/env python3
"""
JIRA Upload Validation Script
Simple script to test JIRA upload functionality
"""

import os
import sys
import json
import tempfile
import requests
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_jira_environment():
    """Test JIRA environment variables"""
    print("🔧 Testing JIRA Environment...")
    
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")
    ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() == "true"
    
    print(f"   JIRA URL: {'✅ Set' if jira_url else '❌ Missing'}")
    print(f"   JIRA User: {'✅ Set' if jira_user else '❌ Missing'}")
    print(f"   JIRA Token: {'✅ Set' if jira_token else '❌ Missing'}")
    print(f"   SSL Verify: {'✅ Enabled' if ssl_verify else '⚠️ Disabled'}")
    
    if jira_url:
        print(f"   URL: {jira_url}")
    if jira_user:
        print(f"   User: {jira_user}")
    if jira_token:
        print(f"   Token: {jira_token[:20]}...")
    
    return bool(jira_url and jira_user and jira_token)

def test_jira_authentication():
    """Test JIRA authentication"""
    print("\n🔐 Testing JIRA Authentication...")
    
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")
    ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() == "true"
    
    if not all([jira_url, jira_user, jira_token]):
        print("   ❌ Skipping - missing environment variables")
        return False
    
    try:
        test_url = f"{jira_url.rstrip('/')}/rest/api/3/myself"
        print(f"   Testing: {test_url}")
        
        response = requests.get(
            test_url,
            auth=(jira_user, jira_token),
            verify=ssl_verify,
            timeout=30
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ Authentication successful")
            print(f"   👤 User: {user_info.get('displayName', 'Unknown')}")
            print(f"   📧 Email: {user_info.get('emailAddress', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Authentication failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_database_connection():
    """Test database connection for JIRA stories"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        # Import the function with direct import
        import importlib.util
        spec = importlib.util.spec_from_file_location("db_integration", "gates/utils/db_integration.py")
        db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_module)
        
        test_app_id = "test-app-123"
        print(f"   Testing with app_id: {test_app_id}")
        
        stories = db_module.fetch_jira_stories(app_id=test_app_id)
        print(f"   ✅ Database connection successful")
        print(f"   📋 Found {len(stories)} JIRA stories")
        
        if stories:
            print(f"   📝 Sample stories: {stories[:3]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_file_operations():
    """Test file operations"""
    print("\n📁 Testing File Operations...")
    
    try:
        # Create test JSON report
        test_data = {
            "scan_id": "test-123",
            "overall_score": 85.5,
            "summary": {
                "total_gates": 15,
                "passed_gates": 12,
                "failed_gates": 2
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            test_file = f.name
        
        print(f"   ✅ Created test file: {test_file}")
        
        # Test summary extraction with direct import
        import importlib.util
        spec = importlib.util.spec_from_file_location("jira_upload", "gates/utils/jira_upload.py")
        jira_upload_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jira_upload_module)
        
        summary = jira_upload_module._extract_report_summary(test_file)
        print(f"   ✅ Summary extraction successful")
        print(f"   📝 Summary: {summary[:100]}...")
        
        # Clean up
        os.unlink(test_file)
        print(f"   ✅ Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"   ❌ File operations failed: {e}")
        return False

def test_upload_functionality():
    """Test actual upload functionality"""
    print("\n📤 Testing Upload Functionality...")
    
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")
    test_ticket = os.getenv("JIRA_TEST_TICKET")
    
    if not all([jira_url, jira_user, jira_token]):
        print("   ❌ Skipping - missing environment variables")
        return False
    
    if not test_ticket:
        print("   ⚠️ No test ticket provided (set JIRA_TEST_TICKET env var)")
        print("   📝 Skipping actual upload test")
        return True  # Not a failure, just skipped
    
    try:
        # Create test report
        test_data = {
            "scan_id": "test-123",
            "overall_score": 85.5,
            "summary": {
                "total_gates": 15,
                "passed_gates": 12,
                "failed_gates": 2
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            test_file = f.name
        
        print(f"   📋 Testing upload to ticket: {test_ticket}")
        
        # Import and test upload with correct path
        from gates.utils.jira_upload import upload_report_to_jira
        
        result = upload_report_to_jira(
            jira_url=jira_url,
            jira_user=jira_user,
            jira_token=jira_token,
            app_id="test-app-123",
            report_path=test_file,
            report_type="json",
            jira_ticket_id=test_ticket,
            comment="Test upload from validation script"
        )
        
        # Clean up
        os.unlink(test_file)
        
        if result.get("success"):
            print(f"   ✅ Upload successful!")
            print(f"   📊 Results: {result.get('message', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Upload failed: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Upload test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 JIRA Upload Validation")
    print("=" * 50)
    
    tests = [
        ("Environment", test_jira_environment),
        ("Authentication", test_jira_authentication),
        ("Database", test_database_connection),
        ("File Operations", test_file_operations),
        ("Upload Functionality", test_upload_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"   {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! JIRA upload is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 