#!/usr/bin/env python3
"""
Debug script for context retrieval
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm import AdvancedLLMService

def test_context_retrieval():
    """Test context retrieval functionality"""
    
    # Configuration
    config = {
        "retrieval": {
            "max_chunks": 24,
            "max_tokens_per_chunk": 800,
            "vector_search_weight": 0.4,
            "keyword_search_weight": 0.3,
            "symbol_search_weight": 0.2,
            "proximity_weight": 0.1,
            "score_threshold": 0.7
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
    
    try:
        print("🚀 Initializing Advanced LLM Service...")
        service = AdvancedLLMService(config)
        
        print("✅ Service initialized successfully")
        
        # Test context retrieval
        repo_id = "e1115fe93def0923"
        query = "What is this repository about?"
        
        print(f"🔍 Testing context retrieval for repo {repo_id} with query: {query}")
        
        result = service.get_context(
            repo_id=repo_id,
            query=query
        )
        
        print(f"✅ Context retrieval successful: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_retrieval()
