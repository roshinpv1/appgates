#!/usr/bin/env python3
"""
Test script to demonstrate SSL bypass functionality for GitHub API connections.
"""

import os
import sys
import requests
import urllib3
from urllib.parse import urlparse

def test_ssl_bypass_options():
    """Test different SSL bypass options"""
    print("🔧 SSL Bypass Options for CodeGates")
    print("=" * 50)
    
    # Test URL (replace with your actual GitHub Enterprise URL)
    test_url = "https://api.github.com"
    
    print(f"📡 Testing connection to: {test_url}")
    print()
    
    # Option 1: Environment Variable for GitHub Enterprise
    print("1️⃣ Option 1: GITHUB_ENTERPRISE_DISABLE_SSL")
    print("   export GITHUB_ENTERPRISE_DISABLE_SSL=true")
    print("   python3 your_script.py")
    print()
    
    # Option 2: Global CodeGates SSL bypass
    print("2️⃣ Option 2: CODEGATES_DISABLE_SSL")
    print("   export CODEGATES_DISABLE_SSL=true")
    print("   python3 your_script.py")
    print()
    
    # Option 3: Global SSL bypass
    print("3️⃣ Option 3: DISABLE_SSL_VERIFICATION")
    print("   export DISABLE_SSL_VERIFICATION=true")
    print("   python3 your_script.py")
    print()
    
    # Option 4: Custom CA Bundle
    print("4️⃣ Option 4: Custom CA Bundle")
    print("   export GITHUB_ENTERPRISE_CA_BUNDLE=/path/to/your/ca-bundle.crt")
    print("   python3 your_script.py")
    print()
    
    # Option 5: Python requests SSL bypass
    print("5️⃣ Option 5: Direct Python SSL bypass")
    print("   import urllib3")
    print("   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)")
    print("   requests.get(url, verify=False)")
    print()

def test_connection_with_ssl_bypass():
    """Test connection with SSL bypass"""
    print("🧪 Testing Connection with SSL Bypass")
    print("=" * 40)
    
    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Test URLs
    test_urls = [
        "https://api.github.com",
        "https://github.com"
    ]
    
    for url in test_urls:
        print(f"🔍 Testing: {url}")
        try:
            # Try with SSL verification first
            response = requests.get(url, timeout=10)
            print(f"   ✅ Success with SSL verification: {response.status_code}")
        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL Error: {e}")
            try:
                # Retry without SSL verification
                response = requests.get(url, verify=False, timeout=10)
                print(f"   ✅ Success without SSL verification: {response.status_code}")
            except Exception as e2:
                print(f"   ❌ Failed even without SSL: {e2}")
        except Exception as e:
            print(f"   ❌ Other error: {e}")
        print()

def show_environment_setup():
    """Show how to set up environment variables"""
    print("🔧 Environment Setup")
    print("=" * 30)
    
    print("For temporary use (current session):")
    print("export GITHUB_ENTERPRISE_DISABLE_SSL=true")
    print("export CODEGATES_DISABLE_SSL=true")
    print()
    
    print("For permanent use (add to ~/.bashrc or ~/.zshrc):")
    print("echo 'export GITHUB_ENTERPRISE_DISABLE_SSL=true' >> ~/.bashrc")
    print("echo 'export CODEGATES_DISABLE_SSL=true' >> ~/.bashrc")
    print("source ~/.bashrc")
    print()
    
    print("For Windows (Command Prompt):")
    print("set GITHUB_ENTERPRISE_DISABLE_SSL=true")
    print("set CODEGATES_DISABLE_SSL=true")
    print()
    
    print("For Windows (PowerShell):")
    print("$env:GITHUB_ENTERPRISE_DISABLE_SSL='true'")
    print("$env:CODEGATES_DISABLE_SSL='true'")
    print()

def show_troubleshooting():
    """Show troubleshooting steps"""
    print("🔍 Troubleshooting SSL Issues")
    print("=" * 35)
    
    print("1. Check if it's a GitHub Enterprise instance:")
    print("   - Look for custom hostname (not github.com)")
    print("   - Check if using corporate VPN")
    print()
    
    print("2. Common SSL Issues:")
    print("   - Self-signed certificates")
    print("   - Corporate proxy certificates")
    print("   - Expired certificates")
    print("   - Hostname mismatches")
    print()
    
    print("3. Solutions:")
    print("   - Set GITHUB_ENTERPRISE_DISABLE_SSL=true")
    print("   - Contact your IT team for proper CA bundle")
    print("   - Use git clone instead of API")
    print("   - Check corporate firewall settings")
    print()
    
    print("4. Alternative approaches:")
    print("   - Use local repository path")
    print("   - Use git clone with --insecure flag")
    print("   - Use SSH instead of HTTPS")
    print()

if __name__ == "__main__":
    print("🚀 CodeGates SSL Bypass Guide")
    print("=" * 40)
    print()
    
    test_ssl_bypass_options()
    print()
    
    test_connection_with_ssl_bypass()
    print()
    
    show_environment_setup()
    print()
    
    show_troubleshooting()
    print()
    
    print("💡 Quick Fix for Your Issue:")
    print("   export GITHUB_ENTERPRISE_DISABLE_SSL=true")
    print("   python3 your_codegates_script.py")
    print()
    
    print("🎯 This should resolve the 'Connection reset by peer' error!") 