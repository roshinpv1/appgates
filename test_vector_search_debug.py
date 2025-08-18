#!/usr/bin/env python3
"""
Debug script for vector search
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm import AdvancedLLMService

def test_vector_search():
    """Test vector search functionality"""
    
    # Configuration
    config = {
        "retrieval": {
            "max_chunks": 24,
            "score_threshold": 0.7
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
    
    try:
        print("🚀 Initializing Advanced LLM Service...")
        service = AdvancedLLMService(config)
        
        print("✅ Service initialized successfully")
        
        # Test vector search directly
        repo_id = "e1115fe93def0923"
        query = "What is this repository about?"
        
        print(f"🔍 Testing vector search for repo {repo_id} with query: {query}")
        
        # Generate embedding for query
        query_embedding = service.embedding_service.embed_single(query)
        print(f"📊 Query embedding generated: {len(query_embedding) if query_embedding else 0} dimensions")
        
        if query_embedding:
            # Search vector store
            results = service.vector_store.search_similar(
                collection_name=repo_id,
                query_vector=query_embedding,
                limit=10,
                score_threshold=0.1  # Lower threshold for testing
            )
            
            print(f"🔍 Vector search found {len(results)} results")
            for i, result in enumerate(results):
                print(f"  Result {i+1}: score={result.score}, id={result.id}")
                if hasattr(result, 'payload'):
                    print(f"    Payload: {result.payload}")
        else:
            print("❌ Failed to generate query embedding")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vector_search()
