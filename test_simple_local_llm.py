#!/usr/bin/env python3
"""
Simple test for local LLM with short prompt
"""

import os
import sys

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_simple_local_llm():
    """Test local LLM with a simple, short prompt"""
    print("🧪 Testing Local LLM with Simple Prompt")
    print("=" * 40)
    
    # Set environment variables for local LLM
    os.environ["LOCAL_LLM_URL"] = "http://localhost:1234/v1"
    os.environ["LOCAL_LLM_MODEL"] = "llama-3.2-3b-instruct"
    os.environ["LOCAL_LLM_API_KEY"] = "not-needed"
    
    try:
        from utils.llm_client import LLMClient, LLMConfig, LLMProvider
        
        # Create a simple configuration
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="llama-3.2-3b-instruct",
            api_key="not-needed",
            base_url="http://localhost:1234/v1",
            temperature=0.1,
            max_tokens=1000,  # Reduced for faster response
            timeout=30  # Reduced timeout
        )
        
        client = LLMClient(config)
        
        print(f"   Provider: {client.config.provider.value}")
        print(f"   Model: {client.config.model}")
        print(f"   Base URL: {client.config.base_url}")
        print(f"   Timeout: {client.config.timeout} seconds")
        print(f"   Max Tokens: {client.config.max_tokens}")
        print(f"   Available: {client.is_available()}")
        
        if client.is_available():
            # Test with a very simple prompt
            simple_prompt = "Generate 3 simple regex patterns for input validation. Respond with JSON only."
            
            print(f"\n📝 Sending simple prompt ({len(simple_prompt)} characters)...")
            
            response = client.call_llm(simple_prompt)
            
            print(f"✅ Simple LLM call successful")
            print(f"   Response length: {len(response)} characters")
            print(f"   Response preview: {response[:200]}...")
            
            # Test with the CallLLMNode
            print(f"\n🧪 Testing CallLLMNode with simple prompt...")
            
            from nodes import CallLLMNode
            
            llm_node = CallLLMNode()
            
            shared = {
                "llm": {
                    "prompt": simple_prompt
                },
                "llm_config": {
                    "url": "http://localhost:1234/v1",
                    "model": "llama-3.2-3b-instruct",
                    "api_key": "not-needed",
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                "request": {
                    "repository_url": "https://github.com/test/repo",
                    "branch": "main"
                }
            }
            
            params = llm_node.prep(shared)
            result = llm_node.exec(params)
            
            print(f"✅ CallLLMNode test successful")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Source: {result.get('source', 'unknown')}")
            print(f"   Model: {result.get('model', 'unknown')}")
            
            if result.get('pattern_data'):
                print(f"   Pattern data generated: {len(result['pattern_data'])} categories")
                for category, data in result['pattern_data'].items():
                    patterns = data.get('patterns', [])
                    print(f"     - {category}: {len(patterns)} patterns")
        else:
            print("❌ Client not available")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_local_llm()
    print("\n✅ Simple Local LLM Test Complete!") 