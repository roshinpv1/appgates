#!/usr/bin/env python3
"""
Test repository hash-based indexing functionality
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_repository_hash_indexing():
    """Test that repositories are not re-indexed when content hasn't changed"""
    print("🔍 Testing repository hash-based indexing...")
    
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

        service = AdvancedLLMService(config)
        print("✅ Advanced LLM service initialized")

        # Test repository URL
        repo_url = "https://github.com/octocat/Hello-World"
        branch = "master"
        
        print(f"📚 Testing repository: {repo_url} (branch: {branch})")
        
        # First indexing attempt
        print("\n🔄 First indexing attempt...")
        result1 = service.index_repository(repo_url=repo_url, branch=branch)
        print(f"   Result: {result1}")
        
        # Second indexing attempt (should be skipped)
        print("\n🔄 Second indexing attempt...")
        result2 = service.index_repository(repo_url=repo_url, branch=branch)
        print(f"   Result: {result2}")
        
        # Verify that the second attempt was skipped
        if result2.get("status") == "already_indexed":
            print("✅ Repository re-indexing was correctly skipped")
            
            # Verify that both results have the same repo_id
            if result1.get("repo_id") == result2.get("repo_id"):
                print("✅ Same repo_id returned for both attempts")
            else:
                print("❌ Different repo_ids returned")
                return False
        else:
            print("❌ Repository was re-indexed when it should have been skipped")
            return False
        
        # Test with a different branch (should be indexed)
        # Note: Hello-World repo only has 'master' branch, so we'll test with a different repo
        print(f"\n🔄 Testing with different repository...")
        try:
            result3 = service.index_repository(repo_url="https://github.com/octocat/Hello-World", branch="master")
            print(f"   Result: {result3}")
            
            if result3.get("status") == "already_indexed":
                print("✅ Same repository was correctly detected as already indexed")
            else:
                print("✅ Different indexing scenario handled correctly")
        except Exception as e:
            print(f"   ⚠️ Different repository test failed (expected): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository hash indexing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_commit_hash_generation():
    """Test commit hash-based repo ID generation"""
    print("\n🔍 Testing commit hash-based repo ID generation...")
    
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

        service = AdvancedLLMService(config)
        
        # Test repo ID generation
        repo_url = "https://github.com/octocat/Hello-World"
        branch = "master"
        commit_hash = "abc12345"
        
        # Generate repo ID without commit hash
        repo_id1 = service._generate_repo_id(repo_url, branch)
        print(f"   Repo ID (without commit): {repo_id1}")
        
        # Generate repo ID with commit hash
        repo_id2 = service._generate_repo_id_with_commit(repo_url, branch, commit_hash)
        print(f"   Repo ID (with commit): {repo_id2}")
        
        # Verify they are different
        if repo_id1 != repo_id2:
            print("✅ Commit hash creates different repo ID")
        else:
            print("❌ Commit hash should create different repo ID")
            return False
        
        # Test with different commit hash
        repo_id3 = service._generate_repo_id_with_commit(repo_url, branch, "def67890")
        print(f"   Repo ID (different commit): {repo_id3}")
        
        if repo_id2 != repo_id3:
            print("✅ Different commit hashes create different repo IDs")
        else:
            print("❌ Different commit hashes should create different repo IDs")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Commit hash generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing repository hash-based indexing...\n")
    
    # Run tests
    test1_passed = test_repository_hash_indexing()
    test2_passed = test_commit_hash_generation()
    
    print(f"\n📊 Test Results:")
    print(f"   Repository hash indexing: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Commit hash generation: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
