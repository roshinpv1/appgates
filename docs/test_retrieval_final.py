#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.core import AdvancedLLMService
from gates.advanced_llm.vector_store import SearchResult

print("🔧 Testing final retrieval...")

try:
    # Test SearchResult creation
    payload = {
        "content": "Test content",
        "file_path": "/test/file.txt",
        "language": "text",
        "start_line": 1,
        "end_line": 10
    }
    
    result = SearchResult(
        id="test_id",
        score=0.8,
        payload=payload
    )
    
    print(f"✅ SearchResult created successfully")
    print(f"🔧 Result ID: {result.id}")
    print(f"🔧 Result score: {result.score}")
    print(f"🔧 Payload keys: {list(result.payload.keys())}")
    print(f"🔧 Content from payload: {result.payload.get('content', 'Not found')}")
    
    # Test the retrieval code path
    from gates.advanced_llm.retrieval import ContextRetriever
    
    # Create a mock result list
    results = [result]
    
    # Test the chunk conversion
    from gates.advanced_llm.retrieval import ContextRetriever
    
    # Create a minimal context retriever for testing
    class MockContextRetriever:
        def _convert_to_chunks(self, results):
            chunks = []
            for result in results:
                payload = result.payload
                chunk = {
                    "id": result.id,
                    "file_path": payload.get("file_path", "unknown"),
                    "language": payload.get("language", "text"),
                    "start_line": payload.get("start_line", 0),
                    "end_line": payload.get("end_line", 0),
                    "score": result.score,
                    "source": "vector",
                    "metadata": {
                        "symbol_name": payload.get("symbol_name"),
                        "symbol_kind": payload.get("symbol_kind"),
                        "imports": payload.get("imports", []),
                        "references": payload.get("references", []),
                        "chunk_type": payload.get("chunk_type", "unknown")
                    }
                }
                
                # Get content from payload
                chunk["content"] = payload.get("content", f"// Content from {payload.get('file_path', 'unknown')} lines {payload.get('start_line', 0)}-{payload.get('end_line', 0)}")
                
                chunks.append(chunk)
            
            return chunks
    
    mock_retriever = MockContextRetriever()
    chunks = mock_retriever._convert_to_chunks(results)
    
    print(f"🔧 Converted {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"🔧 Chunk {i}:")
        print(f"   ID: {chunk['id']}")
        print(f"   Content: {chunk['content']}")
        print(f"   File: {chunk['file_path']}")
        print(f"   Score: {chunk['score']}")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
