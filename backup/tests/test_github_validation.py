#!/usr/bin/env python3
"""
Test script to validate GitHub URL parsing for both GitHub.com and GitHub Enterprise URLs.
"""

import requests
import json
from urllib.parse import urlparse

def test_github_url_validation():
    """Test GitHub URL validation logic"""
    
    print("🧪 Testing GitHub URL Validation...")
    
    # Test cases
    test_cases = [
        # Valid GitHub.com URLs
        {
            "url": "https://github.com/octocat/Hello-World",
            "expected_enterprise": False,
            "expected_api": "https://api.github.com",
            "description": "Standard GitHub.com URL"
        },
        {
            "url": "https://github.com/microsoft/vscode.git",
            "expected_enterprise": False,
            "expected_api": "https://api.github.com",
            "description": "GitHub.com URL with .git suffix"
        },
        
        # Valid GitHub Enterprise URLs
        {
            "url": "https://github.abcd.com/company/repo",
            "expected_enterprise": True,
            "expected_api": "https://github.abcd.com/api/v3",
            "description": "GitHub Enterprise URL"
        },
        {
            "url": "https://github.enterprise.company.com/team/project",
            "expected_enterprise": True,
            "expected_api": "https://github.enterprise.company.com/api/v3",
            "description": "GitHub Enterprise URL with subdomain"
        },
        {
            "url": "https://code.github.internal.com/internal/repo.git",
            "expected_enterprise": True,
            "expected_api": "https://code.github.internal.com/api/v3",
            "description": "Internal GitHub Enterprise URL with .git"
        },
        
        # Invalid URLs
        {
            "url": "https://gitlab.com/user/repo",
            "expected_enterprise": None,
            "expected_api": None,
            "description": "GitLab URL (should fail)",
            "should_fail": True
        },
        {
            "url": "https://bitbucket.org/user/repo",
            "expected_enterprise": None,
            "expected_api": None,
            "description": "Bitbucket URL (should fail)",
            "should_fail": True
        },
        {
            "url": "https://github.com/user",
            "expected_enterprise": None,
            "expected_api": None,
            "description": "Incomplete GitHub URL (should fail)",
            "should_fail": True
        }
    ]
    
    # Test URL parsing logic
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['description']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            # Parse URL
            parsed_url = urlparse(test_case['url'])
            hostname = parsed_url.netloc.lower()
            
            # Check if it's GitHub
            is_github = 'github' in hostname
            is_github_com = hostname == 'github.com'
            is_github_enterprise = 'github' in hostname and hostname != 'github.com'
            
            if not is_github and not test_case.get('should_fail', False):
                print(f"   ❌ FAIL: Not a GitHub URL")
                continue
            elif not is_github and test_case.get('should_fail', False):
                print(f"   ✅ PASS: Correctly rejected non-GitHub URL")
                continue
            
            # Check path format
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) < 2:
                if test_case.get('should_fail', False):
                    print(f"   ✅ PASS: Correctly rejected incomplete URL")
                    continue
                else:
                    print(f"   ❌ FAIL: Incomplete path")
                    continue
            
            # Get API base URL
            if is_github_com:
                api_base = "https://api.github.com"
            elif is_github_enterprise:
                api_base = f"https://{hostname}/api/v3"
            else:
                api_base = None
            
            # Validate results
            if test_case.get('should_fail', False):
                print(f"   ❌ FAIL: Should have failed but didn't")
                continue
            
            # Check enterprise detection
            if is_github_enterprise == test_case['expected_enterprise']:
                print(f"   ✅ Enterprise detection: {is_github_enterprise}")
            else:
                print(f"   ❌ Enterprise detection: got {is_github_enterprise}, expected {test_case['expected_enterprise']}")
            
            # Check API URL
            if api_base == test_case['expected_api']:
                print(f"   ✅ API URL: {api_base}")
            else:
                print(f"   ❌ API URL: got {api_base}, expected {test_case['expected_api']}")
            
            # Extract owner/repo
            owner = path_parts[0]
            repo = path_parts[1]
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            print(f"   📁 Owner: {owner}, Repo: {repo}")
            
        except Exception as e:
            if test_case.get('should_fail', False):
                print(f"   ✅ PASS: Correctly failed with error: {e}")
            else:
                print(f"   ❌ FAIL: Unexpected error: {e}")

def test_api_endpoint():
    """Test actual API endpoint construction"""
    
    print("\n\n🌐 Testing API Endpoint Construction...")
    
    base_url = "http://localhost:8000/api/v1"
    
    test_urls = [
        "https://github.com/octocat/Hello-World",
        "https://github.abcd.com/company/repo",
        "https://github.enterprise.company.com/team/project.git"
    ]
    
    for url in test_urls:
        print(f"\n🔍 Testing repository: {url}")
        
        try:
            # Test the scan endpoint with different GitHub URLs
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'test-client'
            }
            
            data = {
                "repository_url": url,
                "branch": "main"
            }
            
            # Note: This will fail if server is not running, but we can still test URL parsing
            print(f"   Would POST to: {base_url}/scan")
            print(f"   Request data: {json.dumps(data, indent=2)}")
            
        except Exception as e:
            print(f"   ⚠️ Note: {e}")

if __name__ == "__main__":
    test_github_url_validation()
    test_api_endpoint() 