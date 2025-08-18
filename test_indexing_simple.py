#!/usr/bin/env python3
"""
Simple test for indexing functionality
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_advanced_llm_service():
    """Test advanced LLM service initialization and basic indexing"""
    print("🔍 Testing Advanced LLM Service...")
    
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
                "base_url": "http://localhost:11434",
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
        print("✅ Advanced LLM Service initialized successfully!")
        
        # Test health check
        health = service.vector_store.health_check()
        print(f"   Vector store backend: {health.get('backend', 'unknown')}")
        
        # Test if repository is indexed (should be False for new repo)
        is_indexed = service._is_repository_indexed("test-repo")
        print(f"   Test repo indexed: {is_indexed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced LLM Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_git_clone():
    """Test git cloning functionality"""
    print("🔍 Testing Git Clone...")
    
    try:
        from gates.utils.git_operations import clone_repository
        import tempfile
        
        # Test cloning a small repository
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = clone_repository(
                repo_url="https://github.com/octocat/Hello-World",
                branch="main",
                target_dir=temp_dir
            )
            
            if repo_path and repo_path.exists():
                print(f"✅ Git clone successful: {repo_path}")
                return True
            else:
                print("❌ Git clone failed: no path returned")
                return False
                
    except Exception as e:
        print(f"❌ Git clone test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Testing indexing components...\n")
    
    tests = [
        ("Advanced LLM Service", test_advanced_llm_service),
        ("Git Clone", test_git_clone)
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
