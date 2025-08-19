#!/usr/bin/env python3
import requests
import json

print("🔧 Checking available models in LM Studio...")

try:
    # Check available models
    url = "http://localhost:1234/v1/models"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🔧 Sending request to: {url}")
    
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"🔧 Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Available models: {json.dumps(result, indent=2)}")
        
        # List model names
        if 'data' in result:
            print("\n📋 Model names:")
            for model in result['data']:
                print(f"   - {model.get('id', 'Unknown')}")
    else:
        print(f"❌ Error response: {response.text}")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
