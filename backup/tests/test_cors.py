#!/usr/bin/env python3
"""
Test script to verify CORS configuration is working correctly.
"""

import requests
import json

def test_cors():
    """Test CORS preflight and actual requests"""
    base_url = "http://localhost:8000/api/v1"
    
    print("🧪 Testing CORS Configuration...")
    
    # Test 1: Simple health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print(f"   CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: OPTIONS preflight request
    print("\n2. Testing OPTIONS preflight request...")
    try:
        headers = {
            'Origin': 'vscode-webview://test',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{base_url}/scan", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower() or 'origin' in key.lower():
                print(f"     {key}: {value}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Simulate VS Code extension request
    print("\n3. Testing simulated VS Code request...")
    try:
        headers = {
            'Origin': 'vscode-webview://test-extension',
            'Content-Type': 'application/json',
            'User-Agent': 'VS Code Extension'
        }
        data = {
            "repository_url": "https://github.com/octocat/Hello-World",
            "branch": "main"
        }
        response = requests.post(f"{base_url}/scan", headers=headers, json=data)
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower():
                print(f"     {key}: {value}")
        
        if response.status_code < 400:
            result = response.json()
            print(f"   Scan ID: {result.get('scan_id', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    test_cors() 