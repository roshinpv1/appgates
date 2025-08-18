#!/usr/bin/env python3
"""
Test indexing in isolation to identify the issue
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_indexing_isolated():
    """Test indexing in isolation"""
    print("🔍 Testing indexing in isolation...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Simple configuration
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
                "qdrant_path": ":memory:",
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
        print("✅ Service initialized")
        
        # Test indexing with a small repository
        try:
            result = service.index_repository(
                repo_url="https://github.com/octocat/Hello-World",
                branch="master"  # Use master instead of main
            )
            print(f"✅ Indexing result: {result}")
            return True
        except Exception as e:
            print(f"❌ Indexing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run test"""
    print("🚀 Testing indexing in isolation...\n")
    
    result = test_indexing_isolated()
    
    if result:
        print("\n✅ Indexing test passed!")
    else:
        print("\n❌ Indexing test failed!")

if __name__ == "__main__":
    main()
