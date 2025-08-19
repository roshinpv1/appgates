#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 Testing server LM Studio configuration...")

try:
    # Import the server configuration
    from gates.server import advanced_config, ADVANCED_LLM_AVAILABLE
    
    print(f"✅ Advanced LLM available: {ADVANCED_LLM_AVAILABLE}")
    print(f"🔧 Advanced config: {advanced_config}")
    
    if ADVANCED_LLM_AVAILABLE and advanced_config:
        print("🔧 LLM config:")
        llm_config = advanced_config.get("llm", {})
        print(f"   Provider: {llm_config.get('provider')}")
        print(f"   Model: {llm_config.get('model')}")
        print(f"   Base URL: {llm_config.get('base_url')}")
        
        print("🔧 Embedding config:")
        embedding_config = advanced_config.get("embedding", {})
        print(f"   Provider: {embedding_config.get('provider')}")
        print(f"   Model: {embedding_config.get('model')}")
        print(f"   Base URL: {embedding_config.get('base_url')}")
        
        print("🔧 Vector store config:")
        vector_config = advanced_config.get("vector_store", {})
        print(f"   Use Qdrant: {vector_config.get('use_qdrant')}")
        print(f"   Qdrant path: {vector_config.get('qdrant_path')}")
        print(f"   Vector size: {vector_config.get('vector_size')}")
        
        # Test AdvancedLLMService initialization
        print("🔧 Testing AdvancedLLMService initialization...")
        from gates.advanced_llm import AdvancedLLMService
        
        service = AdvancedLLMService(advanced_config)
        print("✅ AdvancedLLMService initialized successfully")
        
        # Test health check
        health = service.health_check()
        print(f"🔧 Health check: {health}")
        
    else:
        print("❌ Advanced LLM not available or config not found")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
