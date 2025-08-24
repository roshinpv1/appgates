#!/usr/bin/env python3
"""
Simple test for the ask functionality
"""

import asyncio
from services.question_service import QuestionService


async def test_ask_functionality():
    """Test the ask functionality"""
    
    print("🧪 Testing Ask Functionality")
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
    question_service = QuestionService(config)
    
    # Get available scans
    available_scans = question_service.get_available_scans()
    print(f"📋 Available scans: {available_scans}")
    
    if not available_scans:
        print("⚠️ No scans available for testing")
        return False
    
    # Test with first available scan
    test_scan_id = available_scans[0]
    print(f"🔍 Testing with scan ID: {test_scan_id}")
    
    # Test question
    question = "What is the main technology stack used in this project?"
    print(f"❓ Question: {question}")
    
    try:
        result = await question_service.ask_question(
            scan_id=test_scan_id,
            question=question,
            max_context_chunks=4,
            include_metadata=True
        )
        
        if result["status"] == "success":
            print("✅ Question answered successfully!")
            print(f"📝 Answer: {result['answer'][:300]}...")
            print(f"📊 Context chunks: {result['context_used']['chunks_retrieved']}")
            print(f"⏱️  Total time: {result['context_used']['total_time_ms']:.2f}ms")
            return True
        else:
            print(f"❌ Failed: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ask_functionality())
    
    if success:
        print("\n🎉 Ask functionality test passed!")
    else:
        print("\n⚠️ Ask functionality test failed!")
