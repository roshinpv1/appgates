#!/usr/bin/env python3
"""
Test script for local LLM implementation
"""

import os
import sys
import json
import requests

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_local_llm_direct():
    """Test local LLM directly with requests"""
    print("🧪 Testing local LLM directly...")
    
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": "llama-3.2-3b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Please respond with 'Test successful!'"}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Direct test successful")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {result}")
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"   Content: {content[:100]}...")
        else:
            print(f"   Unexpected response format: {result}")
            
    except Exception as e:
        print(f"❌ Direct test failed: {e}")

def test_local_llm_client():
    """Test local LLM through the client"""
    print("\n🧪 Testing local LLM through client...")
    
    try:
        from utils.llm_client import LLMClient, LLMConfig, LLMProvider
        
        # Set environment variable
        os.environ["LOCAL_LLM_URL"] = "http://localhost:1234/v1"
        os.environ["LOCAL_LLM_MODEL"] = "llama-3.2-3b-instruct"
        
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="llama-3.2-3b-instruct",
            api_key="not-needed",
            base_url="http://localhost:1234/v1",
            temperature=0.1,
            max_tokens=40000
        )
        
        client = LLMClient(config)
        
        print(f"   Provider: {client.config.provider.value}")
        print(f"   Model: {client.config.model}")
        print(f"   Base URL: {client.config.base_url}")
        print(f"   Available: {client.is_available()}")
        
        if client.is_available():
            response = client.call_llm("Hello! Please respond with 'Client test successful!'")
            print(f"✅ Client test successful")
            print(f"   Response: {response[:100]}...")
        else:
            print("❌ Client not available")
            
    except Exception as e:
        print(f"❌ Client test failed: {e}")

def test_auto_detection():
    """Test auto-detection from environment"""
    print("\n🧪 Testing auto-detection...")
    
    try:
        from utils.llm_client import create_llm_client_from_env
        
        # Set environment variables
        os.environ["LOCAL_LLM_URL"] = "http://localhost:1234/v1"
        os.environ["LOCAL_LLM_MODEL"] = "llama-3.2-3b-instruct"
        
        client = create_llm_client_from_env()
        
        if client:
            print(f"✅ Auto-detection successful")
            print(f"   Provider: {client.config.provider.value}")
            print(f"   Model: {client.config.model}")
            print(f"   Available: {client.is_available()}")
            
            if client.is_available():
                response = client.call_llm("Hello! Please respond with 'Auto-detection test successful!'")
                print(f"   Response: {response[:100]}...")
        else:
            print("❌ Auto-detection failed - no client created")
            
    except Exception as e:
        print(f"❌ Auto-detection test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Local LLM Implementation")
    print("=" * 40)
    
    # Test 1: Direct API call
    test_local_llm_direct()
    
    # Test 2: Through client
    test_local_llm_client()
    
    # Test 3: Auto-detection
    test_auto_detection()
    
    print("\n✅ Testing complete!") 