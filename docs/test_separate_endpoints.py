#!/usr/bin/env python3
"""
Test separate endpoints for embeddings and LLM services
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_separate_endpoints():
    """Test configuration with separate endpoints for embeddings and LLM"""
    print("🔧 Testing separate endpoints configuration...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Configuration with separate endpoints
        config = {
            "retrieval": {
                "max_chunks": 24,
                "max_tokens_per_chunk": 800,
                "vector_search_weight": 0.4,
                "keyword_search_weight": 0.3,
                "symbol_search_weight": 0.2,
                "proximity_weight": 0.1
            },
            "indexing": {
                "chunk_size": 800,
                "overlap_size": 120,
                "supported_languages": ["python", "javascript", "typescript", "java"]
            },
            # Separate embedding configuration
            "embedding": {
                "provider": "local",
                "local_provider": "lm_studio",  # Use LM Studio for embeddings
                "local_base_url": "http://localhost:1234",  # Embeddings on port 1234
                "local_model": "nomic-embed-text",
                "batch_size": 64,
                "timeout": 30
            },
            # Separate LLM configuration
            "llm": {
                "provider": "local",
                "base_url": "http://localhost:8000",  # LLM on port 8000
                "model": "llama3.2",
                "temperature": 0.3,
                "max_tokens": 2000,
                "timeout": 30
            },
            "vector_store": {
                "backend": "memory"
            }
        }
        
        # Initialize service
        service = AdvancedLLMService(config)
        
        print("✅ Service initialized with separate endpoints:")
        print(f"   🧠 Embeddings: {config['embedding']['local_provider']} at {config['embedding']['local_base_url']}")
        print(f"   🤖 LLM: {config['llm']['provider']} at {config['llm']['base_url']}")
        
        # Test embedding generation
        print("\n🧠 Testing embedding generation...")
        test_texts = ["Hello world", "This is a test"]
        embeddings = service.embedding_service.embed_texts(test_texts)
        print(f"   ✅ Generated {len(embeddings)} embeddings")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_ollama_embeddings():
    """Test Ollama embeddings with separate endpoint"""
    print("\n🔧 Testing Ollama embeddings configuration...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Configuration with Ollama embeddings
        config = {
            "retrieval": {
                "max_chunks": 24,
                "max_tokens_per_chunk": 800
            },
            "indexing": {
                "chunk_size": 800,
                "overlap_size": 120,
                "supported_languages": ["python", "javascript", "typescript", "java"]
            },
            # Ollama embeddings
            "embedding": {
                "provider": "local",
                "local_provider": "ollama",
                "local_base_url": "http://localhost:1234",  # Ollama default port
                "local_model": "nomic-embed-text",
                "batch_size": 64,
                "timeout": 30
            },
            # LLM on different port
            "llm": {
                "provider": "local",
                "base_url": "http://localhost:8000",
                "model": "llama3.2",
                "temperature": 0.3,
                "max_tokens": 2000,
                "timeout": 30
            },
            "vector_store": {
                "backend": "memory"
            }
        }
        
        # Initialize service
        service = AdvancedLLMService(config)
        
        print("✅ Service initialized with Ollama embeddings:")
        print(f"   🧠 Embeddings: {config['embedding']['local_provider']} at {config['embedding']['local_base_url']}")
        print(f"   🤖 LLM: {config['llm']['provider']} at {config['llm']['base_url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_openai_embeddings_local_llm():
    """Test OpenAI embeddings with local LLM"""
    print("\n🔧 Testing OpenAI embeddings with local LLM...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Configuration with OpenAI embeddings and local LLM
        config = {
            "retrieval": {
                "max_chunks": 24,
                "max_tokens_per_chunk": 800
            },
            "indexing": {
                "chunk_size": 800,
                "overlap_size": 120,
                "supported_languages": ["python", "javascript", "typescript", "java"]
            },
            # OpenAI embeddings
            "embedding": {
                "provider": "openai",
                "model": "text-embedding-3-small",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "batch_size": 64,
                "timeout": 30
            },
            # Local LLM
            "llm": {
                "provider": "local",
                "base_url": "http://localhost:8000",
                "model": "llama3.2",
                "temperature": 0.3,
                "max_tokens": 2000,
                "timeout": 30
            },
            "vector_store": {
                "backend": "memory"
            }
        }
        
        # Initialize service
        service = AdvancedLLMService(config)
        
        print("✅ Service initialized with OpenAI embeddings and local LLM:")
        print(f"   🧠 Embeddings: {config['embedding']['provider']} (cloud)")
        print(f"   🤖 LLM: {config['llm']['provider']} at {config['llm']['base_url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing separate endpoints configuration...\n")
    
    # Test different configurations
    test1 = test_separate_endpoints()
    test2 = test_ollama_embeddings()
    test3 = test_openai_embeddings_local_llm()
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Separate endpoints (LM Studio): {'PASS' if test1 else 'FAIL'}")
    print(f"   ✅ Ollama embeddings: {'PASS' if test2 else 'FAIL'}")
    print(f"   ✅ OpenAI + Local LLM: {'PASS' if test3 else 'FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 All tests passed! Separate endpoints configuration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the configuration and service availability.")
