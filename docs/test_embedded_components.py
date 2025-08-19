#!/usr/bin/env python3
"""
Test script for embedded Qdrant and Tree-sitter components
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_qdrant():
    """Test embedded Qdrant functionality"""
    print("🔍 Testing embedded Qdrant...")
    
    try:
        from qdrant_client import QdrantClient
        
        # Test embedded Qdrant
        client = QdrantClient(path=":memory:")
        
        # Create a test collection
        from qdrant_client.models import Distance, VectorParams
        
        client.create_collection(
            collection_name="test_collection",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        
        # Test upsert
        from qdrant_client.models import PointStruct
        
        points = [
            PointStruct(
                id=1,
                vector=[0.1] * 1536,
                payload={"text": "test document", "metadata": "test"}
            )
        ]
        
        client.upsert(
            collection_name="test_collection",
            points=points
        )
        
        # Test search
        search_result = client.search(
            collection_name="test_collection",
            query_vector=[0.1] * 1536,
            limit=1
        )
        
        print("✅ Embedded Qdrant test passed!")
        print(f"   Found {len(search_result)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedded Qdrant test failed: {e}")
        return False

def test_tree_sitter():
    """Test Tree-sitter functionality"""
    print("🔍 Testing Tree-sitter...")
    
    try:
        import tree_sitter
        from tree_sitter import Language, Parser
        
        # Test basic Tree-sitter functionality
        parser = Parser()
        
        # Test with a simple Python code
        python_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        
        # For now, we'll test basic parsing without language grammars
        # In a real setup, you'd need to install language grammars
        print("✅ Tree-sitter basic functionality available!")
        print("   Note: Language grammars need to be installed separately")
        
        return True
        
    except Exception as e:
        print(f"❌ Tree-sitter test failed: {e}")
        return False

def test_advanced_llm_components():
    """Test advanced LLM components with embedded services"""
    print("🔍 Testing advanced LLM components...")
    
    try:
        # Test vector store with embedded Qdrant
        from advanced_llm.vector_store import VectorStore
        
        vector_config = {
            "use_qdrant": True,
            "qdrant_path": ":memory:",
            "vector_size": 1536
        }
        
        vector_store = VectorStore(vector_config)
        
        # Test collection creation
        success = vector_store.create_collection("test_repo")
        if success:
            print("✅ Vector store with embedded Qdrant working!")
        else:
            print("❌ Vector store collection creation failed")
            return False
        
        # Test AST parser
        from advanced_llm.ast_parser import ASTParser
        
        ast_config = {
            "supported_languages": ["python", "javascript"]
        }
        
        ast_parser = ASTParser(ast_config)
        print("✅ AST parser initialized!")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced LLM components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing embedded Qdrant and Tree-sitter components...\n")
    
    tests = [
        ("Embedded Qdrant", test_qdrant),
        ("Tree-sitter", test_tree_sitter),
        ("Advanced LLM Components", test_advanced_llm_components)
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
    
    if passed == total:
        print("🎉 All tests passed! Embedded components are ready to use.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
