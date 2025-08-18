#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 Testing simple completion with LM Studio...")

try:
    from gates.utils.llm_client import LLMClient, LLMConfig, LLMProvider
    
    # Test simple completion
    config = LLMConfig(
        provider=LLMProvider.LOCAL,
        model="llama-3.2-3b-instruct",
        base_url="http://localhost:1234",
        temperature=0.3,
        max_tokens=100
    )
    
    print(f"✅ Creating LLMClient with config: {config}")
    llm_client = LLMClient(config)
    
    print(f"✅ LLMClient created successfully")
    
    # Test simple completion
    prompt = "What is Apache Fineract?"
    print(f"🔧 Testing completion with prompt: {prompt}")
    
    response = llm_client.complete(prompt)
    print(f"✅ Completion successful!")
    print(f"🔧 Response: {response}")
    
    print("✅ Simple completion test passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
