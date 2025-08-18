#!/usr/bin/env python3
"""
Test vector search functionality
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_vector_search():
    """Test vector search functionality"""
    print("🔍 Testing vector search functionality...")

    try:
        from advanced_llm.vector_store import VectorStore
        from advanced_llm.embedding import EmbeddingService

        # Initialize components
        vector_store = VectorStore({
            "use_qdrant": True,
            "qdrant_path": "./qdrant_data",
            "vector_size": 768  # nomic-embed-text generates 768-dimensional embeddings
        })

        embedding_service = EmbeddingService({
            "provider": "local",
            "model": "nomic-embed-text",
            "batch_size": 32
        })

        # Test collection exists
        repo_id = "e1115fe93def0923"
        exists = vector_store.collection_exists(repo_id)
        print(f"✅ Collection {repo_id} exists: {exists}")

        if exists:
            # Get collection stats
            stats = vector_store.get_collection_stats(repo_id)
            print(f"✅ Collection stats: {stats}")

            # Test embedding generation
            query = "What is this repository about?"
            embedding = embedding_service.embed_single(query)
            print(f"✅ Generated embedding: {len(embedding)} dimensions")

            if embedding:
                # Test vector search
                results = vector_store.search_similar(
                    collection_name=repo_id,
                    query_vector=embedding,
                    limit=5,
                    score_threshold=0.0
                )
                print(f"✅ Vector search found {len(results)} results")

                for i, result in enumerate(results[:3]):
                    print(f"   Result {i+1}:")
                    print(f"     Score: {result.score}")
                    print(f"     Content: {result.payload.get('content', '')[:100]}...")
                    print(f"     File: {result.payload.get('file_path', 'unknown')}")
            else:
                print("❌ Failed to generate embedding")

        return True

    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Testing vector search functionality...\n")

    success = test_vector_search()

    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)

    if success:
        print("✅ Vector search test PASSED")
    else:
        print("❌ Vector search test FAILED")

if __name__ == "__main__":
    main()
