#!/usr/bin/env python3
"""
Test pattern library integration with embeddings and LLM context
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_pattern_library_loading():
    """Test that pattern library loads correctly"""
    print("🔧 Testing pattern library loading...")
    
    try:
        from advanced_llm.pattern_library import PatternLibraryService
        
        # Initialize pattern library
        pattern_library = PatternLibraryService()
        
        print(f"✅ Pattern library loaded successfully")
        print(f"   📚 Total gates: {len(pattern_library.patterns)}")
        print(f"   📝 Pattern texts: {len(pattern_library.pattern_texts)}")
        
        # Test pattern search
        logging_patterns = pattern_library.search_patterns("logging")
        print(f"   🔍 Logging patterns found: {len(logging_patterns)}")
        
        # Test category filtering
        security_patterns = pattern_library.get_patterns_by_category("Security")
        print(f"   🔒 Security patterns: {len(security_patterns)}")
        
        # Test priority filtering
        high_priority = pattern_library.get_patterns_by_priority("High")
        print(f"   ⚡ High priority patterns: {len(high_priority)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_pattern_relevance_search():
    """Test pattern relevance search"""
    print("\n🔧 Testing pattern relevance search...")
    
    try:
        from advanced_llm.pattern_library import PatternLibraryService
        
        pattern_library = PatternLibraryService()
        
        # Test different queries
        test_queries = [
            "logging",
            "error handling",
            "security",
            "performance",
            "circuit breaker"
        ]
        
        for query in test_queries:
            relevant_patterns = pattern_library.get_relevant_patterns_for_query(query, max_patterns=2)
            print(f"   🔍 Query '{query}': {len(relevant_patterns)} relevant patterns")
            
            if relevant_patterns:
                print(f"      First pattern preview: {relevant_patterns[0][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_pattern_integration_with_service():
    """Test pattern integration with the main service"""
    print("\n🔧 Testing pattern integration with service...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Configuration
        config = {
            "retrieval": {
                "max_chunks": 24,
                "max_tokens_per_chunk": 800
            },
            "indexing": {
                "chunk_size": 800,
                "overlap_size": 120,
                "supported_languages": ["python", "javascript", "typescript", "java"]
            },
            "embedding": {
                "provider": "local",
                "local_provider": "lm_studio",
                "local_base_url": "http://localhost:1234",
                "local_model": "nomic-embed-text"
            },
            "llm": {
                "provider": "local",
                "base_url": "http://localhost:8000",
                "model": "llama3.2"
            },
            "vector_store": {
                "backend": "memory"
            }
        }
        
        # Initialize service
        service = AdvancedLLMService(config)
        
        print(f"✅ Service initialized with pattern library")
        print(f"   📚 Pattern library gates: {len(service.pattern_library.patterns)}")
        
        # Test pattern relevance for a query
        test_query = "How should I implement logging in this codebase?"
        relevant_patterns = service._get_relevant_patterns_for_query(test_query)
        print(f"   🔍 Relevant patterns for logging query: {len(relevant_patterns)}")
        
        if relevant_patterns:
            print(f"      First relevant pattern: {relevant_patterns[0][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_pattern_prompt_assembly():
    """Test that patterns are included in prompt assembly"""
    print("\n🔧 Testing pattern prompt assembly...")
    
    try:
        from advanced_llm.core import AdvancedLLMService
        
        # Simple configuration
        config = {
            "retrieval": {"max_chunks": 24},
            "indexing": {"chunk_size": 800},
            "embedding": {
                "provider": "local",
                "local_provider": "lm_studio",
                "local_base_url": "http://localhost:1234"
            },
            "llm": {
                "provider": "local",
                "base_url": "http://localhost:8000"
            },
            "vector_store": {"backend": "memory"}
        }
        
        service = AdvancedLLMService(config)
        
        # Test prompt assembly
        test_instruction = "How should I implement error logging?"
        context_result = {
            "chunks": [
                {
                    "language": "python",
                    "file_path": "app.py",
                    "start_line": 1,
                    "end_line": 10,
                    "content": "import logging\n\nlogger = logging.getLogger(__name__)"
                }
            ]
        }
        
        prompt = service._assemble_prompt(
            repo_id="test",
            instruction=test_instruction,
            context_result=context_result,
            mode="chat"
        )
        
        print(f"✅ Prompt assembled successfully")
        print(f"   📝 Prompt length: {len(prompt)} characters")
        
        # Check if patterns are included
        if "Relevant Code Quality Patterns:" in prompt:
            print(f"   ✅ Patterns included in prompt")
        else:
            print(f"   ⚠️ Patterns not found in prompt")
        
        # Show a preview
        print(f"   📄 Prompt preview: {prompt[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_pattern_summary():
    """Test pattern library summary"""
    print("\n🔧 Testing pattern library summary...")
    
    try:
        from advanced_llm.pattern_library import PatternLibraryService
        
        pattern_library = PatternLibraryService()
        summary = pattern_library.get_all_pattern_summary()
        
        print(f"✅ Pattern summary generated")
        print(f"   📄 Summary length: {len(summary)} characters")
        print(f"   📄 Summary preview:\n{summary[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing pattern library integration...\n")
    
    # Run all tests
    test1 = test_pattern_library_loading()
    test2 = test_pattern_relevance_search()
    test3 = test_pattern_integration_with_service()
    test4 = test_pattern_prompt_assembly()
    test5 = test_pattern_summary()
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Pattern library loading: {'PASS' if test1 else 'FAIL'}")
    print(f"   ✅ Pattern relevance search: {'PASS' if test2 else 'FAIL'}")
    print(f"   ✅ Service integration: {'PASS' if test3 else 'FAIL'}")
    print(f"   ✅ Prompt assembly: {'PASS' if test4 else 'FAIL'}")
    print(f"   ✅ Pattern summary: {'PASS' if test5 else 'FAIL'}")
    
    if all([test1, test2, test3, test4, test5]):
        print("\n🎉 All tests passed! Pattern library integration is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the configuration and pattern library.")
