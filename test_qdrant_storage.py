#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.vector_store import VectorStore
from gates.advanced_llm.embedding import EmbeddingService

print("🔧 Testing Qdrant storage...")

try:
    # Initialize components
    vector_store = VectorStore({
        "use_qdrant": True,
        "qdrant_path": "./qdrant_test",
        "vector_size": 768
    })
    
    embedding_service = EmbeddingService({
        "provider": "local",
        "model": "nomic-embed-text"
    })
    
    print(f"✅ Components initialized successfully")
    
    # Test content
    test_content = """# Hello World

This is a simple Hello World repository.

## Features

- Simple and clean
- Easy to understand
- Perfect for beginners

## Usage

Just run the code and see "Hello World" printed.
"""
    
    print(f"🔧 Test content length: {len(test_content)}")
    print(f"🔧 Test content: {repr(test_content)}")
    
    # Generate embedding
    embedding = embedding_service.embed_single(test_content)
    print(f"🔧 Generated embedding length: {len(embedding)}")
    
    # Create test vector data
    vector_data = {
        "id": "test_chunk_1",
        "vector": embedding,
        "payload": {
            "repo_id": "test",
            "file_path": "/test/README.md",
            "language": "markdown",
            "symbol_name": None,
            "symbol_kind": None,
            "start_line": 1,
            "end_line": 14,
            "imports": [],
            "references": [],
            "hash": "test_hash",
            "mtime": 1234567890,
            "chunk_type": "sliding_window",
            "content": test_content
        }
    }
    
    # Create collection
    collection_name = "test_collection"
    vector_store.create_collection(collection_name)
    print(f"✅ Created collection: {collection_name}")
    
    # Store vector
    success = vector_store.upsert_vectors(collection_name, [vector_data])
    print(f"🔧 Upsert success: {success}")
    
    # Retrieve and check
    results = vector_store.search_similar(
        collection_name=collection_name,
        query_vector=embedding,
        limit=1,
        score_threshold=0.0
    )
    
    print(f"🔧 Retrieved {len(results)} results")
    
    if results:
        result = results[0]
        print(f"🔧 Result ID: {result.id}")
        print(f"🔧 Result score: {result.score}")
        print(f"🔧 Payload keys: {list(result.payload.keys())}")
        
        if 'content' in result.payload:
            content = result.payload['content']
            print(f"🔧 Content length: {len(content) if content else 0}")
            print(f"🔧 Content: {repr(content)}")
        else:
            print(f"🔧 Content: Not found in payload")
    
    # Clean up
    vector_store.delete_collection(collection_name)
    print(f"✅ Cleaned up collection: {collection_name}")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
