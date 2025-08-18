#!/usr/bin/env python3
"""
Test persistent Qdrant storage
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_persistent_qdrant():
    """Test persistent Qdrant storage"""
    print("🔍 Testing persistent Qdrant storage...")
    
    try:
        from advanced_llm.vector_store import VectorStore
        
        # Test configuration with persistent storage
        config = {
            "use_qdrant": True,
            "qdrant_path": "./qdrant_data",
            "vector_size": 1536
        }
        
        # Initialize vector store
        vector_store = VectorStore(config)
        print("✅ Vector store initialized with persistent storage")
        
        # Check health
        health = vector_store.health_check()
        print(f"   Vector store health: {health}")
        
        # Test collection creation
        success = vector_store.create_collection("test-persistent")
        print(f"   Collection creation: {'✅ Success' if success else '❌ Failed'}")
        
        # Test vector upsert
        test_vectors = [
            {
                "id": "test1",
                "vector": [0.1] * 1536,
                "payload": {"text": "test document 1", "metadata": "test"}
            },
            {
                "id": "test2", 
                "vector": [0.2] * 1536,
                "payload": {"text": "test document 2", "metadata": "test"}
            }
        ]
        
        success = vector_store.upsert_vectors("test-persistent", test_vectors)
        print(f"   Vector upsert: {'✅ Success' if success else '❌ Failed'}")
        
        # Test vector search
        results = vector_store.search_similar("test-persistent", [0.1] * 1536, limit=2)
        print(f"   Vector search: {'✅ Success' if results else '❌ Failed'}")
        print(f"   Found {len(results)} results")
        
        # Check if data persists by creating a new instance
        print("\n🔄 Testing data persistence...")
        vector_store2 = VectorStore(config)
        
        # Check if collection exists
        exists = vector_store2.collection_exists("test-persistent")
        print(f"   Collection exists: {'✅ Yes' if exists else '❌ No'}")
        
        # Test search again
        results2 = vector_store2.search_similar("test-persistent", [0.1] * 1536, limit=2)
        print(f"   Persistent search: {'✅ Success' if results2 else '❌ Failed'}")
        print(f"   Found {len(results2)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Persistent Qdrant test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_llm_with_persistent():
    """Test advanced LLM service with persistent Qdrant"""
    print("🔍 Testing advanced LLM with persistent Qdrant...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Test configuration with persistent storage
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
                "supported_languages": ["python", "javascript"],
                "enable_ast_parsing": True,
                "enable_symbol_extraction": True,
                "batch_size": 64
            },
            "llm": {
                "provider": "ollama",
                "model": "gemma3:27b",
                "api_key": None,
                "base_url": "http://localhost:1234",
                "temperature": 0.3,
                "max_tokens": 2000,
                "enable_streaming": True,
                "max_concurrent_requests": 10
            },
            "vector_store": {
                "use_qdrant": True,
                "qdrant_path": "./qdrant_data",
                "vector_size": 1536
            },
            "embedding": {
                "provider": "local",
                "model": "gemma3:27b",
                "batch_size": 32
            },
            "cache": {
                "use_redis": False,
                "max_size": 1000,
                "default_ttl": 300
            }
        }
        
        # Initialize service
        service = AdvancedLLMService(config)
        print("✅ Advanced LLM service initialized with persistent Qdrant")
        
        # Check vector store health
        health = service.vector_store.health_check()
        print(f"   Vector store health: {health}")
        
        # Test indexing with persistence
        result = service.index_repository(
            repo_url="https://github.com/octocat/Hello-World",
            branch="master"
        )
        print(f"✅ Indexing result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced LLM with persistent Qdrant test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Testing persistent Qdrant storage...\n")
    
    tests = [
        ("Persistent Qdrant", test_persistent_qdrant),
        ("Advanced LLM with Persistent Qdrant", test_advanced_llm_with_persistent)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} test...")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
