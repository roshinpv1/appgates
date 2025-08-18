#!/usr/bin/env python3
"""
Test script for Advanced LLM System
Demonstrates the enhanced LLM assistance features
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

async def test_advanced_llm_system():
    """Test the advanced LLM system"""
    
    print("🚀 Testing Advanced LLM System")
    print("=" * 50)
    
    try:
        # Import the advanced LLM service
        from advanced_llm import AdvancedLLMService
        
        # Configuration
        config = {
            "retrieval": {
                "max_chunks": 16,
                "max_tokens_per_chunk": 800,
                "vector_search_weight": 0.4,
                "keyword_search_weight": 0.3,
                "symbol_search_weight": 0.2,
                "proximity_weight": 0.1
            },
            "indexing": {
                "chunk_size": 800,
                "overlap_size": 120,
                "supported_languages": ["python", "javascript", "typescript", "java"],
                "enable_ast_parsing": True,
                "enable_symbol_extraction": True
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 2000,
                "enable_streaming": True
            },
            "vector_store": {
                "use_qdrant": False,  # Use memory store for testing
                "vector_size": 1536
            },
            "embedding": {
                "provider": "openai",
                "model": "text-embedding-3-small",
                "batch_size": 32
            },
            "cache": {
                "use_redis": False,  # Use memory cache for testing
                "ttl": 300
            }
        }
        
        # Initialize service
        print("📦 Initializing Advanced LLM Service...")
        service = AdvancedLLMService(config)
        
        # Test repository (use a small public repo for testing)
        test_repo = "https://github.com/octocat/Hello-World"
        
        print(f"📚 Testing repository indexing: {test_repo}")
        
        # Index repository
        indexing_result = await service.index_repository(
            repo_url=test_repo,
            branch="main"
        )
        
        print(f"✅ Indexing result: {json.dumps(indexing_result, indent=2)}")
        
        if indexing_result.get("status") == "indexed":
            repo_id = indexing_result["repo_id"]
            
            # Test context retrieval
            print(f"\n🔍 Testing context retrieval for repo: {repo_id}")
            
            test_queries = [
                "How is the main function implemented?",
                "What are the key features of this project?",
                "Show me the project structure"
            ]
            
            for query in test_queries:
                print(f"\n   Query: {query}")
                
                context_result = await service.get_context(
                    repo_id=repo_id,
                    query=query,
                    max_chunks=8
                )
                
                print(f"   📊 Retrieved {len(context_result.get('chunks', []))} chunks")
                print(f"   ⏱️ Retrieval time: {context_result.get('retrieval_time_ms', 0):.2f}ms")
                
                # Show first chunk as example
                chunks = context_result.get('chunks', [])
                if chunks:
                    first_chunk = chunks[0]
                    print(f"   📄 First chunk: {first_chunk.get('file_path', 'unknown')}")
                    print(f"      Lines: {first_chunk.get('start_line', 0)}-{first_chunk.get('end_line', 0)}")
                    print(f"      Score: {first_chunk.get('score', 0):.3f}")
            
            # Test LLM completion (if LLM is available)
            print(f"\n🤖 Testing LLM completion...")
            
            try:
                completion_result = await service.complete_with_context(
                    repo_id=repo_id,
                    instruction="Explain the main functionality of this project",
                    context_result=context_result,
                    mode="chat"
                )
                
                print(f"✅ Completion successful!")
                print(f"   📝 Response length: {len(completion_result.get('content', ''))} chars")
                print(f"   ⏱️ LLM time: {completion_result.get('llm_time_ms', 0):.2f}ms")
                print(f"   🔢 Total tokens: {completion_result.get('total_tokens', 0)}")
                
                # Show first 200 characters of response
                content = completion_result.get('content', '')
                if content:
                    print(f"   📄 Response preview: {content[:200]}...")
                
            except Exception as e:
                print(f"⚠️ LLM completion failed (expected if no API key): {e}")
            
            # Test patch generation
            print(f"\n🔧 Testing patch generation...")
            
            try:
                patch_result = await service.generate_patch(
                    repo_id=repo_id,
                    instruction="Add error handling to the main function",
                    context_result=context_result,
                    target_file="README.md"
                )
                
                print(f"✅ Patch generation successful!")
                print(f"   📝 Patch type: {patch_result.get('patch_type', 'unknown')}")
                
                patch_content = patch_result.get('patch_content', '')
                if patch_content:
                    print(f"   📄 Patch preview: {patch_content[:200]}...")
                
            except Exception as e:
                print(f"⚠️ Patch generation failed: {e}")
            
            # Show statistics
            print(f"\n📊 Service Statistics:")
            stats = service.get_stats()
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
        
        else:
            print(f"⚠️ Repository indexing failed: {indexing_result}")
        
        print(f"\n✅ Advanced LLM System test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_components_individually():
    """Test individual components"""
    
    print("\n🧪 Testing Individual Components")
    print("=" * 30)
    
    try:
        # Test Vector Store
        print("💾 Testing Vector Store...")
        from advanced_llm.vector_store import VectorStore
        
        vector_config = {"use_qdrant": False, "vector_size": 1536}
        vector_store = VectorStore(vector_config)
        
        # Test collection creation
        await vector_store.create_collection("test_collection")
        
        # Test vector storage
        test_vectors = [
            {
                "id": "test1",
                "vector": [0.1] * 1536,
                "payload": {"file": "test.py", "content": "test content"}
            }
        ]
        
        await vector_store.upsert_vectors("test_collection", test_vectors)
        
        # Test search
        search_results = await vector_store.search_similar(
            "test_collection", 
            [0.1] * 1536, 
            limit=5
        )
        
        print(f"✅ Vector Store: {len(search_results)} search results")
        
        # Test Embedding Service
        print("🧠 Testing Embedding Service...")
        from advanced_llm.embedding import EmbeddingService
        
        embedding_config = {
            "provider": "openai",
            "model": "text-embedding-3-small",
            "batch_size": 4
        }
        
        embedding_service = EmbeddingService(embedding_config)
        
        # Test health check
        health = await embedding_service.health_check()
        print(f"✅ Embedding Service: {health.get('status', 'unknown')}")
        
        # Show stats
        stats = embedding_service.get_stats()
        print(f"   📊 Providers available: {stats.get('providers_available', 0)}")
        
    except Exception as e:
        print(f"⚠️ Component test failed: {e}")

async def main():
    """Main test function"""
    print("🧪 Advanced LLM System Test Suite")
    print("=" * 50)
    
    # Test individual components first
    await test_components_individually()
    
    # Test full system
    await test_advanced_llm_system()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
