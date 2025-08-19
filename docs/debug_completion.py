#!/usr/bin/env python3
"""
Debug completion functionality
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_completion_debug():
    """Test completion functionality step by step"""
    print("🔍 Debugging completion functionality...")

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
                "base_url": "http://localhost:1234",
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
        repo_id = "0c698eac5935cf6a"
        is_indexed = service._is_repository_indexed(repo_id)
        print(f"✅ Repository {repo_id} indexed: {is_indexed}")

        if is_indexed:
            # Test 2: Get collection stats
            stats = service.vector_store.get_collection_stats(repo_id)
            print(f"✅ Collection stats: {stats}")

            # Test 3: Test context retrieval
            query = "What is this repository about?"
            print(f"🔍 Testing context retrieval for query: {query}")
            
            context_result = service.get_context(
                repo_id=repo_id,
                query=query,
                cursor_context=None
            )
            
            print(f"✅ Context retrieval result:")
            print(f"   Total chunks: {context_result.get('total_chunks', 0)}")
            print(f"   Chunks: {len(context_result.get('chunks', []))}")
            
            if context_result.get('chunks'):
                print(f"   First chunk content: {context_result['chunks'][0].get('content', '')[:100]}...")
            else:
                print("   ❌ No chunks found")

            # Test 4: Test completion
            if context_result.get('chunks'):
                print(f"🔍 Testing completion with {len(context_result['chunks'])} chunks")
                
                import asyncio
                completion_result = asyncio.run(service.complete_with_context(
                    repo_id=repo_id,
                    instruction=query,
                    context_result=context_result,
                    mode="chat"
                ))
                
                print(f"✅ Completion result:")
                print(f"   Content: {completion_result.get('content', '')[:200]}...")
                print(f"   Context chunks used: {completion_result.get('context_chunks_used', 0)}")
            else:
                print("❌ Skipping completion test - no context chunks")

        return True

    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debug tests"""
    print("🚀 Debugging completion functionality...\n")

    success = test_completion_debug()

    print(f"\n{'='*50}")
    print("DEBUG SUMMARY")
    print('='*50)

    if success:
        print("✅ Debug test completed")
    else:
        print("❌ Debug test failed")

if __name__ == "__main__":
    main()
