#!/usr/bin/env python3
"""
Debug test for vector search functionality
"""

import os
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService


def test_vector_search_debug():
    """Debug vector search functionality"""
    
    print("🔍 Debugging Vector Search Functionality")
    print("=" * 40)
    
    # Initialize services
    config = {
        "vector_size": 768,
        "distance_metric": "cosine",
        "use_qdrant": False,
        "provider": "local",
        "model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "base_url": "http://localhost:1234"
    }
    
    vector_service = VectorService(config)
    embedding_service = EmbeddingService(config)
    
    # Test collection
    collection_name = "debug_test"
    
    # Create collection
    print(f"📁 Creating collection: {collection_name}")
    vector_service.create_collection(collection_name)
    
    # Test data
    test_files = [
        {
            "id": "file1",
            "content": "python django web framework",
            "file_path": "views.py"
        },
        {
            "id": "file2", 
            "content": "javascript react frontend framework",
            "file_path": "App.js"
        },
        {
            "id": "file3",
            "content": "docker container deployment",
            "file_path": "Dockerfile"
        }
    ]
    
    # Add vectors
    print("📊 Adding test vectors...")
    for file_data in test_files:
        embedding = embedding_service.embed_single(file_data["content"])
        if embedding:
            print(f"   ✅ Generated embedding for {file_data['file_path']}")
            vector_service.upsert_vectors(
                collection_name=collection_name,
                vectors=[{
                    "id": file_data["id"],
                    "vector": embedding,
                    "payload": {
                        "content": file_data["content"],
                        "file_path": file_data["file_path"]
                    }
                }]
            )
        else:
            print(f"   ❌ Failed to generate embedding for {file_data['file_path']}")
    
    # Test search
    print("\n🔍 Testing vector search...")
    
    # Search query
    query = "high level project summary with key frameworks and technologies"
    query_embedding = embedding_service.embed_single(query)
    
    if query_embedding:
        print("   ✅ Generated query embedding")
        
        # Search with different thresholds
        for threshold in [0.3, 0.5, 0.7, 0.8]:
            print(f"\n   🔍 Searching with threshold {threshold}...")
            results = vector_service.search_similar(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=5,
                score_threshold=threshold
            )
            
            print(f"      Found {len(results)} results:")
            for result in results:
                print(f"        - {result.payload.get('file_path', 'Unknown')}: {result.score:.3f}")
    else:
        print("   ❌ Failed to generate query embedding")
    
    # Test direct content search
    print("\n🔍 Testing direct content search...")
    
    for content in ["python", "django", "javascript", "react", "docker"]:
        content_embedding = embedding_service.embed_single(content)
        if content_embedding:
            results = vector_service.search_similar(
                collection_name=collection_name,
                query_vector=content_embedding,
                limit=3,
                score_threshold=0.3
            )
            print(f"   '{content}': {len(results)} results")
            for result in results:
                print(f"     - {result.payload.get('file_path', 'Unknown')}: {result.score:.3f}")
    
    # Clean up
    vector_service.delete_collection(collection_name)
    print(f"\n🧹 Cleaned up collection: {collection_name}")


if __name__ == "__main__":
    test_vector_search_debug()
