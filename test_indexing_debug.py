#!/usr/bin/env python3
"""
Test indexing functionality
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_indexing_debug():
    """Test indexing functionality step by step"""
    print("🔍 Debugging indexing functionality...")

    try:
        from advanced_llm.core import AdvancedLLMService

        # Initialize service with same config as server
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
                "base_url": "http://localhost:11434",
                "temperature": 0.3,
                "max_tokens": 2000,
                "enable_streaming": True,
                "max_concurrent_requests": 10
            },
            "vector_store": {
                "use_qdrant": True,
                "qdrant_path": "./qdrant_data",
                "vector_size": 768
            },
            "embedding": {
                "provider": "local",
                "model": "nomic-embed-text",
                "batch_size": 32
            },
            "cache": {
                "use_redis": False,
                "max_size": 1000,
                "default_ttl": 300
            }
        }

        service = AdvancedLLMService(config)
        print("✅ Advanced LLM service initialized")

        # Test 1: Check if repository is indexed
        repo_id = "e1115fe93def0923"
        is_indexed = service._is_repository_indexed(repo_id)
        print(f"✅ Repository {repo_id} indexed: {is_indexed}")
        
        # Force reindexing by deleting the collection
        if is_indexed:
            print("🗑️ Deleting existing collection to force reindexing...")
            service.vector_store.delete_collection(repo_id)
            print("✅ Collection deleted")
        
        # Attempt to index repository
        print("🔍 Attempting to index repository...")
        try:
            result = service.index_repository(
                repo_url="https://github.com/octocat/Hello-World",
                branch="master"
            )
            print(f"✅ Indexing result: {result}")
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            return False

        # Test 3: Check if indexed after indexing
        is_indexed_after = service._is_repository_indexed(repo_id)
        print(f"✅ Repository {repo_id} indexed after indexing: {is_indexed_after}")
        
        if is_indexed_after:
            # Test 4: Get collection stats
            stats = service.vector_store.get_collection_stats(repo_id)
            print(f"✅ Collection stats: {stats}")

        return True

    except Exception as e:
        print(f"❌ Indexing debug test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    print("🚀 Debugging indexing functionality...\n")

    success = test_indexing_debug()

    print(f"\n{'='*50}")
    print("DEBUG SUMMARY")
    print('='*50)

    if success:
        print("✅ Indexing debug test completed")
    else:
        print("❌ Indexing debug test failed")

if __name__ == "__main__":
    main()
