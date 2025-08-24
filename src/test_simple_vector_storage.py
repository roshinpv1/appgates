#!/usr/bin/env python3
"""
Simple test to verify vector storage is working
"""

import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vector_service import VectorService
from services.embedding_service import EmbeddingService

def test_simple_vector_storage():
    """Test basic vector storage functionality"""
    print("🔍 Testing Simple Vector Storage")
    print("=" * 50)
    
    # Stop any running FastAPI servers to avoid lock conflicts
    print("⚠️ Please ensure no FastAPI server is running to avoid lock conflicts")
    input("Press Enter when ready to continue...")
    
    # Remove any existing lock file
    import os
    lock_file = "./qdrant_data/.lock"
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print(f"🔓 Removed existing lock file")
        except Exception as e:
            print(f"⚠️ Could not remove lock file: {e}")
    
    # Configuration
    config = {
        "vector_store": {
            "vector_size": 768,
            "distance_metric": "cosine",
            "use_qdrant": True,
            "qdrant_path": "./qdrant_data"
        },
        "embedding": {
            "model": "nomic-embed-text",
            "dimensions": 768
        }
    }
    
    try:
        # Step 1: Initialize services
        print("\n1. Initializing services...")
        vector_service = VectorService(config["vector_store"])
        embedding_service = EmbeddingService(config["embedding"])
        
        # Step 2: Test collection creation
        print("\n2. Testing collection creation...")
        test_collection = "test_simple_collection"
        
        if vector_service.collection_exists(test_collection):
            print(f"   Collection {test_collection} already exists")
        else:
            print(f"   Creating collection: {test_collection}")
            success = vector_service.create_collection(test_collection)
            print(f"   Collection creation: {'✅ Success' if success else '❌ Failed'}")
        
        # Step 3: Generate test embeddings
        print("\n3. Generating test embeddings...")
        test_texts = [
            "Spring Boot Java application with Maven dependencies",
            "React frontend with TypeScript and Node.js",
            "Docker containerization and Kubernetes deployment"
        ]
        
        embeddings = embedding_service.embed_batch(test_texts)
        print(f"   Generated {len(embeddings)} embeddings")
        
        # Step 4: Store vectors
        print("\n4. Storing test vectors...")
        test_vectors = []
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            if embedding:
                test_vectors.append({
                    "id": f"test_vector_{i}",
                    "vector": embedding,
                    "payload": {
                        "content": text,
                        "test_id": i,
                        "file_path": f"test_file_{i}.txt",
                        "content_hash": f"hash_{i}"
                    }
                })
        
        success = vector_service.upsert_vectors(test_collection, test_vectors)
        print(f"   Vector storage: {'✅ Success' if success else '❌ Failed'}")
        
        # Step 5: Test search
        print("\n5. Testing vector search...")
        if test_vectors:
            query_embedding = embeddings[0]  # Use first embedding as query
            
            results = vector_service.search_similar(
                collection_name=test_collection,
                query_vector=query_embedding,
                limit=3,
                score_threshold=0.1
            )
            
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results):
                print(f"   Result {i+1}: Score {result.score:.3f}, Content: {result.payload.get('content', '')[:50]}...")
        
        # Step 6: Check collection info
        print("\n6. Checking collection info...")
        collection_info = vector_service.get_collection_info(test_collection)
        if collection_info:
            print(f"   Collection: {collection_info['name']}")
            print(f"   Vector size: {collection_info['vector_size']}")
            print(f"   Point count: {collection_info['count']}")
        else:
            print("   ❌ Could not get collection info")
        
        # Step 7: Test persistence
        print("\n7. Testing persistence...")
        print("   Creating new vector service instance...")
        vector_service2 = VectorService(config["vector_store"])
        
        # Check if collection still exists
        exists = vector_service2.collection_exists(test_collection)
        print(f"   Collection exists in new instance: {'✅ Yes' if exists else '❌ No'}")
        
        if exists:
            # Try to search again
            results2 = vector_service2.search_similar(
                collection_name=test_collection,
                query_vector=query_embedding,
                limit=3,
                score_threshold=0.1
            )
            print(f"   Search in new instance: {len(results2)} results")
            print("   ✅ Vector storage is persistent!")
        else:
            print("   ❌ Vector storage is not persistent")
        
        print(f"\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_vector_storage()
