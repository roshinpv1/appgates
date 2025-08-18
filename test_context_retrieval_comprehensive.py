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
        "score_threshold": 0.1  # Very low threshold for testing
    },
    "indexing": {
        "chunk_size": 800,
        "overlap_size": 120,
        "supported_languages": ["python", "javascript", "typescript", "java", "csharp", "go", "rust"],
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
        "max_tokens": 2000
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

print("🔧 Testing comprehensive context retrieval...")

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
        # Get collection stats
        stats = service.vector_store.get_collection_stats(repo_id)
        print(f"🔧 Collection stats: {stats}")
        
        # Test context retrieval
        query = "What is this repository about?"
        print(f"🔧 Testing context retrieval with query: {query}")
        
        context_result = service.get_context(repo_id, query)
        print(f"🔧 Context result: {context_result}")
        
        # Check chunks
        chunks = context_result.get("chunks", [])
        print(f"🔧 Number of chunks retrieved: {len(chunks)}")
        
        if chunks:
            print(f"🔧 First chunk: {chunks[0]}")
        else:
            print("🔧 No chunks retrieved")
            
            # Test vector search directly
            print("🔧 Testing vector search directly...")
            from gates.advanced_llm.retrieval import ContextRetriever
            
            # Ensure context retriever is initialized
            service._ensure_context_retriever()
            
            # Test vector search
            search_results = service.context_retriever._vector_search(repo_id, query)
            print(f"🔧 Vector search results: {len(search_results)}")
            
            for i, result in enumerate(search_results[:3]):
                print(f"🔧 Result {i}: score={result.score}, id={result.id}")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
