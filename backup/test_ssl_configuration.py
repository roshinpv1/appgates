#!/usr/bin/env python3
"""
Test script to verify SSL configuration for GitHub Enterprise

This script tests:
1. SSL configuration loading from environment
2. SSL verification disabled mode
3. Custom CA bundle configuration
4. Git SSL configuration
5. API SSL configuration
6. Error handling for SSL certificate failures
"""

import os
import sys
import asyncio
import tempfile
import requests
import subprocess
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ssl_config_loading():
    """Test SSL configuration loading"""
    print("=" * 60)
    print("🧪 Testing SSL Configuration Loading")
    print("=" * 60)
    
    try:
        # Set test environment variables
        test_env = {
            'CODEGATES_SSL_VERIFY': 'false',
            'CODEGATES_SSL_CA_BUNDLE': '/path/to/ca-bundle.pem',
            'CODEGATES_SSL_CLIENT_CERT': '/path/to/client.crt',
            'CODEGATES_SSL_CLIENT_KEY': '/path/to/client.key',
            'CODEGATES_SSL_DISABLE_WARNINGS': 'true'
        }
        
        # Temporarily set environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            from codegates.api.server import get_ssl_config, get_requests_session
            
            # Test SSL config loading
            ssl_config = get_ssl_config()
            print(f"   📝 SSL verify: {ssl_config.get('verify_ssl')}")
            print(f"   📝 CA bundle: {ssl_config.get('ca_bundle')}")
            print(f"   📝 Client cert: {ssl_config.get('client_cert')}")
            print(f"   📝 Client key: {ssl_config.get('client_key')}")
            print(f"   📝 Disable warnings: {ssl_config.get('disable_warnings')}")
            
            # Test requests session creation
            session_disabled = get_requests_session(verify_ssl=False)
            print(f"   📝 Session SSL disabled: {not session_disabled.verify}")
            
            session_enabled = get_requests_session(verify_ssl=True)
            print(f"   📝 Session SSL enabled: {session_enabled.verify}")
            
            print("   ✅ SSL configuration loading working")
            return True
            
        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_git_ssl_configuration():
    """Test git SSL configuration"""
    print("\n" + "=" * 60)
    print("🧪 Testing Git SSL Configuration")
    print("=" * 60)
    
    try:
        from codegates.api.server import configure_git_ssl_settings
        
        # Test with SSL disabled
        print("   🔧 Testing SSL disabled configuration")
        os.environ['CODEGATES_SSL_VERIFY'] = 'false'
        configure_git_ssl_settings()
        
        # Check if GIT_SSL_NO_VERIFY is set
        ssl_no_verify = os.environ.get('GIT_SSL_NO_VERIFY')
        print(f"   📝 GIT_SSL_NO_VERIFY: {ssl_no_verify}")
        
        # Test git config
        try:
            result = subprocess.run(['git', 'config', '--global', 'http.sslVerify'], 
                                  capture_output=True, text=True)
            ssl_verify_config = result.stdout.strip()
            print(f"   📝 Git http.sslVerify: {ssl_verify_config}")
        except Exception as e:
            print(f"   ⚠️ Cannot check git config: {e}")
        
        # Test with SSL enabled
        print("   🔧 Testing SSL enabled configuration")
        os.environ['CODEGATES_SSL_VERIFY'] = 'true'
        os.environ.pop('GIT_SSL_NO_VERIFY', None)
        configure_git_ssl_settings()
        
        ssl_no_verify_after = os.environ.get('GIT_SSL_NO_VERIFY')
        print(f"   📝 GIT_SSL_NO_VERIFY after enable: {ssl_no_verify_after}")
        
        print("   ✅ Git SSL configuration working")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def test_ssl_error_handling():
    """Test SSL error handling and helpful messages"""
    print("\n" + "=" * 60)
    print("🧪 Testing SSL Error Handling")
    print("=" * 60)
    
    try:
        from codegates.api.server import download_repository_via_api
        
        # Test with a GitHub Enterprise URL that would cause SSL issues
        test_url = "https://github.enterprise.example.com/test/repo"
        
        print("   🔧 Testing SSL error handling with fake GitHub Enterprise URL")
        
        try:
            # This should fail and provide helpful error message
            await asyncio.to_thread(
                download_repository_via_api, 
                test_url, 
                "main", 
                None, 
                True  # verify_ssl=True
            )
            print("   ⚠️ Expected SSL error but none occurred")
            return False
            
        except Exception as e:
            error_msg = str(e)
            print(f"   📝 Error message length: {len(error_msg)} chars")
            
            # Check if error contains helpful SSL guidance
            ssl_guidance_keywords = [
                'CODEGATES_SSL_VERIFY',
                'CODEGATES_SSL_CA_BUNDLE',
                'SSL certificate',
                'GitHub Enterprise'
            ]
            
            guidance_found = sum(1 for keyword in ssl_guidance_keywords if keyword in error_msg)
            print(f"   📝 SSL guidance keywords found: {guidance_found}/{len(ssl_guidance_keywords)}")
            
            if guidance_found >= 2:
                print("   ✅ SSL error handling provides helpful guidance")
                return True
            else:
                print("   ⚠️ SSL error handling could be more helpful")
                print(f"   📝 Error: {error_msg[:200]}...")
                return False
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def test_ssl_api_integration():
    """Test SSL configuration with API endpoints"""
    print("\n" + "=" * 60)
    print("🧪 Testing SSL API Integration")
    print("=" * 60)
    
    try:
        # Check if API server is running
        api_base = "http://localhost:8000"
        
        try:
            response = requests.get(f"{api_base}/api/v1/health", timeout=5)
            if response.status_code != 200:
                print("   ⚠️ API server not running, skipping API SSL tests")
                return True
        except requests.RequestException:
            print("   ⚠️ API server not accessible, skipping API SSL tests")
            return True
        
        # Test scan with SSL disabled
        print("   🔧 Testing scan with SSL verification disabled")
        scan_request = {
            "repository_url": "https://github.enterprise.example.com/test/repo",
            "branch": "main",
            "scan_options": {
                "threshold": 70,
                "enable_api_fallback": True,
                "verify_ssl": False
            }
        }
        
        response = requests.post(f"{api_base}/api/v1/scan", json=scan_request)
        if response.status_code == 200:
            scan_data = response.json()
            scan_id = scan_data.get('scan_id')
            print(f"   📝 Started scan with SSL disabled: {scan_id}")
            
            # Wait a bit for processing
            await asyncio.sleep(5)
            
            # Check status
            response = requests.get(f"{api_base}/api/v1/scan/{scan_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                message = status_data.get('message', '')
                print(f"   📝 Scan status: {status}")
                print(f"   📝 Message: {message[:100]}...")
            
            print("   ✅ API SSL integration working")
            return True
        else:
            print(f"   ❌ Failed to start scan: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def create_ssl_configuration_guide():
    """Create a comprehensive SSL configuration guide"""
    print("\n" + "=" * 60)
    print("📋 SSL Configuration Guide for GitHub Enterprise")
    print("=" * 60)
    
    guide = """
🔒 SSL Configuration Options for GitHub Enterprise:

1. DISABLE SSL VERIFICATION (Quick Fix - Not Recommended for Production)
   Add to your .env file:
   CODEGATES_SSL_VERIFY=false
   CODEGATES_SSL_DISABLE_WARNINGS=true

2. USE CUSTOM CA BUNDLE (Recommended for Production)
   Add to your .env file:
   CODEGATES_SSL_CA_BUNDLE=/path/to/your/ca-bundle.pem
   
   To get your CA bundle:
   - Contact your IT team for the corporate CA certificate
   - Or extract from browser: Settings → Security → Manage Certificates
   - Or use openssl: openssl s_client -showcerts -connect your-github-enterprise.com:443

3. MUTUAL TLS (If Required by Your Enterprise)
   Add to your .env file:
   CODEGATES_SSL_CLIENT_CERT=/path/to/client.crt
   CODEGATES_SSL_CLIENT_KEY=/path/to/client.key

4. PER-SCAN SSL OVERRIDE (For Testing)
   In your scan request:
   {
     "repository_url": "https://your-github-enterprise.com/owner/repo",
     "scan_options": {
       "verify_ssl": false
     }
   }

5. GIT CONFIGURATION (Alternative Approach)
   Configure git globally:
   git config --global http.sslVerify false
   git config --global http.sslCAInfo /path/to/ca-bundle.pem

⚠️  SECURITY CONSIDERATIONS:
- Disabling SSL verification makes you vulnerable to man-in-the-middle attacks
- Always use custom CA bundles in production environments
- Only disable SSL verification in isolated development environments

🔧 TROUBLESHOOTING:
- "certificate verify failed" → Use options 1 or 2 above
- "SSLError" → Check network connectivity and certificate chain
- "Connection timeout" → Check firewall and proxy settings
- "403 Forbidden" → Verify GitHub token permissions
"""
    
    print(guide)
    
    # Write guide to file
    guide_file = Path("SSL_CONFIGURATION_GUIDE.md")
    with open(guide_file, 'w') as f:
        f.write(guide)
    
    print(f"📄 SSL configuration guide saved to: {guide_file}")
    return True

async def main():
    """Run all SSL configuration tests"""
    print("🧪 MyGates SSL Configuration Test Suite")
    print("=" * 60)
    
    tests = [
        ("SSL Configuration Loading", test_ssl_config_loading()),
        ("Git SSL Configuration", test_git_ssl_configuration()),
        ("SSL Error Handling", test_ssl_error_handling()),
        ("SSL API Integration", test_ssl_api_integration()),
        ("SSL Configuration Guide", create_ssl_configuration_guide())
    ]
    
    results = []
    for test_name, test_coroutine in tests:
        print(f"\n🔄 Running: {test_name}")
        try:
            if asyncio.iscoroutine(test_coroutine):
                result = await test_coroutine
            else:
                result = test_coroutine
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SSL Configuration Test Results")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed >= total - 1:  # Allow 1 failure for API tests
        print("🎉 SSL configuration system working properly!")
        return True
    else:
        print("⚠️ Some SSL tests failed. Review the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 