#!/usr/bin/env python3
import requests
import json

print("🔧 Testing LM Studio with smaller model...")

try:
    # Test LM Studio chat completions with smaller model
    url = "http://localhost:1234/v1/chat/completions"
    
    payload = {
        "model": "deepseek-r1-qwen3-8b-abliterated",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🔧 Sending request to: {url}")
    print(f"🔧 Model: deepseek-r1-qwen3-8b-abliterated")
    print(f"🔧 Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"🔧 Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Error response: {response.text}")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
