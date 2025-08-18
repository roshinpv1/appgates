#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.core import AdvancedLLMService

# Test configuration
config = {
    "retrieval": {
        "max_chunks": 24,
        "max_tokens_per_chunk": 800,
        "vector_search_weight": 0.4,
        "keyword_search_weight": 0.3,
        "symbol_search_weight": 0.2,
        "proximity_weight": 0.1,
        "score_threshold": 0.1
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

print("🔧 Testing simple context retrieval...")

try:
    # Initialize service
    service = AdvancedLLMService(config)
    print(f"✅ AdvancedLLMService initialized successfully")
    
    # Test repository ID
    repo_id = "e1115fe93def0923"
    print(f"🔧 Testing with repo_id: {repo_id}")
    
    # Check if repository is indexed
    is_indexed = service._is_repository_indexed(repo_id)
    print(f"🔧 Repository indexed: {is_indexed}")
    
    if is_indexed:
        # Test context retrieval
        query = "What is this repository about?"
        print(f"🔧 Testing context retrieval with query: {query}")
        
        try:
            context_result = service.get_context(repo_id, query)
            print(f"🔧 Context result: {context_result}")
        except Exception as e:
            print(f"❌ Context retrieval failed: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
