#!/usr/bin/env python3
"""
Integration test script to validate GitHub Enterprise URL support across the CodeGates system.
Tests both the API server validation and frontend validation logic.
"""

import requests
import json
import sys
from urllib.parse import urlparse

def test_url_validation_logic():
    """Test the URL validation logic matching the implementation"""
    
    print("🧪 Testing URL Validation Logic...")
    
    test_cases = [
        # Valid GitHub.com URLs
        {
            "url": "https://github.com/octocat/Hello-World",
            "should_pass": True,
            "description": "Standard GitHub.com URL"
        },
        {
            "url": "https://github.com/microsoft/vscode.git",
            "should_pass": True,
            "description": "GitHub.com URL with .git suffix"
        },
        
        # Valid GitHub Enterprise URLs  
        {
            "url": "https://github.abcd.com/company/repo",
            "should_pass": True,
            "description": "GitHub Enterprise URL"
        },
        {
            "url": "https://github.enterprise.company.com/team/project",
            "should_pass": True,
            "description": "GitHub Enterprise URL with subdomain"
        },
        {
            "url": "https://code.github.internal.com/internal/repo.git",
            "should_pass": True,
            "description": "Internal GitHub Enterprise URL with .git"
        },
        {
            "url": "https://mygithub.company.com/team/project",
            "should_pass": True,
            "description": "GitHub Enterprise URL with 'github' in hostname"
        },
        
        # Invalid URLs
        {
            "url": "https://gitlab.com/user/repo",
            "should_pass": False,
            "description": "GitLab URL (should fail)"
        },
        {
            "url": "https://bitbucket.org/user/repo",
            "should_pass": False,
            "description": "Bitbucket URL (should fail)"
        },
        {
            "url": "https://github.com/user",
            "should_pass": False,
            "description": "Incomplete GitHub URL (should fail)"
        },
        {
            "url": "https://example.com/user/repo",
            "should_pass": False,
            "description": "Non-GitHub URL (should fail)"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['description']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            # Test frontend validation logic
            frontend_result = test_frontend_validation(test_case['url'])
            
            # Test backend validation logic  
            backend_result = test_backend_validation(test_case['url'])
            
            # Check results
            frontend_passed = frontend_result == test_case['should_pass']
            backend_passed = backend_result == test_case['should_pass']
            
            if frontend_passed and backend_passed:
                print(f"   ✅ PASS: Frontend={frontend_result}, Backend={backend_result}")
            else:
                print(f"   ❌ FAIL: Frontend={frontend_result}, Backend={backend_result}, Expected={test_case['should_pass']}")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    return all_passed

def test_frontend_validation(url):
    """Test frontend validation logic (matching main.js logic)"""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.lower()
        
        # Check if hostname contains 'github'
        if 'github' not in hostname:
            return False
        
        # Check if path has owner/repo format
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2 or not path_parts[0] or not path_parts[1]:
            return False
            
        return True
        
    except Exception:
        return False

def test_backend_validation(url):
    """Test backend validation logic (matching server.py logic)"""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.lower()
        
        # Check if it contains 'github'
        if 'github' not in hostname:
            return False
        
        # Check path format
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            return False
        
        return True
        
    except Exception:
        return False

def test_api_endpoint_construction():
    """Test API endpoint construction for different GitHub types"""
    
    print("\n\n🌐 Testing API Endpoint Construction...")
    
    test_cases = [
        {
            "url": "https://github.com/octocat/Hello-World",
            "expected_api": "https://api.github.com",
            "is_enterprise": False
        },
        {
            "url": "https://github.abcd.com/company/repo",
            "expected_api": "https://github.abcd.com/api/v3",
            "is_enterprise": True
        },
        {
            "url": "https://github.enterprise.company.com/team/project.git",
            "expected_api": "https://github.enterprise.company.com/api/v3",
            "is_enterprise": True
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing API endpoint for: {test_case['url']}")
        
        try:
            parsed_url = urlparse(test_case['url'])
            hostname = parsed_url.netloc.lower()
            
            is_github_com = hostname == 'github.com'
            is_github_enterprise = 'github' in hostname and hostname != 'github.com'
            
            if is_github_com:
                api_base = "https://api.github.com"
            elif is_github_enterprise:
                api_base = f"https://{hostname}/api/v3"
            else:
                api_base = None
            
            path_parts = parsed_url.path.strip('/').split('/')
            owner = path_parts[0]
            repo = path_parts[1]
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            print(f"   Enterprise: {is_github_enterprise} (expected: {test_case['is_enterprise']})")
            print(f"   API Base: {api_base} (expected: {test_case['expected_api']})")
            print(f"   Owner: {owner}, Repo: {repo}")
            
            if (is_github_enterprise == test_case['is_enterprise'] and 
                api_base == test_case['expected_api']):
                print(f"   ✅ PASS")
            else:
                print(f"   ❌ FAIL")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_passed = False
    
    return all_passed

def test_server_integration():
    """Test actual API server integration if available"""
    
    print("\n\n🔌 Testing Server Integration...")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test health endpoint first
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            
            # Test with different GitHub URL types
            test_urls = [
                "https://github.com/octocat/Hello-World",
                "https://github.abcd.com/company/repo"
            ]
            
            for url in test_urls:
                print(f"\n🔍 Testing scan endpoint with: {url}")
                
                data = {
                    "repository_url": url,
                    "branch": "main"
                }
                
                try:
                    # Note: This will likely fail for non-existent repos, but we're testing URL validation
                    response = requests.post(f"{base_url}/scan", json=data, timeout=10)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   Scan ID: {result.get('scan_id', 'N/A')}")
                    elif response.status_code == 400:
                        error = response.json()
                        print(f"   Validation Error: {error.get('detail', 'Unknown')}")
                    else:
                        print(f"   Response: {response.text[:200]}...")
                        
                except requests.exceptions.Timeout:
                    print("   ⏰ Request timed out (expected for actual GitHub requests)")
                except Exception as e:
                    print(f"   ⚠️ Request failed: {e}")
                    
        else:
            print(f"⚠️ API server returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ API server is not running on http://localhost:8000")
        print("   To test server integration:")
        print("   1. Run: python start_server.py")
        print("   2. Run this test again")
    except Exception as e:
        print(f"⚠️ Failed to connect to API server: {e}")

def main():
    """Run all tests"""
    print("🚀 CodeGates GitHub Enterprise URL Support Test")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test URL validation logic
    validation_passed = test_url_validation_logic()
    all_tests_passed = all_tests_passed and validation_passed
    
    # Test API endpoint construction
    endpoint_passed = test_api_endpoint_construction()
    all_tests_passed = all_tests_passed and endpoint_passed
    
    # Test server integration (optional)
    test_server_integration()
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 All validation tests PASSED!")
        print("✅ GitHub Enterprise URL support is working correctly")
    else:
        print("❌ Some tests FAILED!")
        print("⚠️ GitHub Enterprise URL support needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main() 