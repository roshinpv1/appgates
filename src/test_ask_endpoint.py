#!/usr/bin/env python3
"""
Test for the ask endpoint functionality
"""

import asyncio
import json
from datetime import datetime
from services.question_service import QuestionService
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService


def test_question_service():
    """Test the question service functionality"""
    
    print("🧪 Testing Question Service")
    print("=" * 30)
    
    # Configuration
    config = {
        "vector_store": {
            "use_qdrant": True,
            "qdrant_path": "./qdrant_data",
            "vector_size": 768
        },
        "embedding": {
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234",
            "batch_size": 32,
            "vector_size": 768
        },
        "llm": {
            "provider": "local",
            "model": "llama-3.2-3b-instruct",
            "base_url": "http://localhost:1234",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    }
    
    # Initialize question service
    print("📊 Initializing Question Service...")
    question_service = QuestionService(config)
    
    # Test getting available scans
    print("\n📋 Testing Available Scans...")
    available_scans = question_service.get_available_scans()
    print(f"   Available scans: {available_scans}")
    
    if not available_scans:
        print("⚠️ No scans available for testing")
        return False
    
    # Test with the first available scan
    test_scan_id = available_scans[0]
    print(f"\n🔍 Testing with scan ID: {test_scan_id}")
    
    # Get scan info
    scan_info = question_service.get_scan_info(test_scan_id)
    print(f"📊 Scan Info: {json.dumps(scan_info, indent=2)}")
    
    # Test questions
    test_questions = [
        "What is the main technology stack used in this project?",
        "How is error handling implemented?",
        "What are the main dependencies?",
        "Describe the project structure"
    ]
    
    print(f"\n❓ Testing Questions...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n   {i}. Question: {question}")
        
        try:
            # Test the question (synchronous version for testing)
            result = asyncio.run(question_service.ask_question(
                scan_id=test_scan_id,
                question=question,
                max_context_chunks=4,
                include_metadata=True
            ))
            
            if result["status"] == "success":
                print(f"      ✅ Success!")
                print(f"      📝 Answer: {result['answer'][:200]}...")
                print(f"      📊 Context chunks: {result['context_used']['chunks_retrieved']}")
                print(f"      ⏱️  Total time: {result['context_used']['total_time_ms']:.2f}ms")
            else:
                print(f"      ❌ Failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"      ❌ Exception: {e}")
    
    return True


def test_vector_search():
    """Test vector search functionality"""
    
    print("\n🔍 Testing Vector Search")
    print("=" * 25)
    
    # Configuration
    config = {
        "vector_store": {
            "use_qdrant": True,
            "qdrant_path": "./qdrant_data",
            "vector_size": 768
        },
        "embedding": {
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234",
            "batch_size": 32,
            "vector_size": 768
        }
    }
    
    # Initialize services
    vector_service = VectorService(config["vector_store"])
    embedding_service = EmbeddingService(config["embedding"])
    
    # Get available scans
    available_scans = question_service.get_available_scans()
    
    if not available_scans:
        print("⚠️ No scans available for testing")
        return False
    
    test_scan_id = available_scans[0]
    main_collection = f"repo_{test_scan_id}"
    
    print(f"📋 Testing with scan ID: {test_scan_id}")
    print(f"📁 Collection: {main_collection}")
    
    # Test search query
    query = "technology stack frameworks dependencies"
    query_embedding = embedding_service.embed_single(query)
    
    if not query_embedding:
        print("❌ Failed to generate query embedding")
        return False
    
    print(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
    
    # Test search
    try:
        results = vector_service.search_similar(
            collection_name=main_collection,
            query_vector=query_embedding,
            limit=5,
            score_threshold=0.3
        )
        
        print(f"📊 Search results: {len(results)} found")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result.score:.3f}")
            print(f"      File: {result.payload.get('file_path', 'Unknown')}")
            print(f"      Language: {result.payload.get('language', 'Unknown')}")
            print(f"      Symbol: {result.payload.get('symbol_name', 'Unknown')}")
        
        if results:
            print("✅ Vector search working correctly!")
            return True
        else:
            print("❌ No search results found")
            return False
            
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Question Service and Ask Endpoint Test")
    print("=" * 50)
    
    # Test question service
    question_ok = test_question_service()
    
    # Test vector search
    search_ok = test_vector_search()
    
    print(f"\n📋 Test Results:")
    print(f"   Question Service: {'✅ PASS' if question_ok else '❌ FAIL'}")
    print(f"   Vector Search: {'✅ PASS' if search_ok else '❌ FAIL'}")
    
    if question_ok and search_ok:
        print("\n🎉 All tests passed! Ask functionality is working.")
    else:
        print("\n⚠️ Some tests failed. Check the implementation.")
