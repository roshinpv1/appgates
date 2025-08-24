#!/usr/bin/env python3
"""
Debug script to test project summary generation and identify issues
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vector_service import VectorService
from services.embedding_service import EmbeddingService

async def debug_project_summary(scan_id=None):
    """Debug project summary generation"""
    
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
    
    # Use provided scan_id or default
    if not scan_id:
        scan_id = "test_vectorization_debug"  # Use the existing collection
    
    repo_url = "https://github.com/spring-projects/spring-petclinic"
    
    print("🔍 Debugging Project Summary Generation")
    print("=" * 50)
    print(f"📋 Using scan_id: {scan_id}")
    
    try:
        # Initialize services
        print("1. Initializing services...")
        vector_service = VectorService(config["vector_store"])
        embedding_service = EmbeddingService(config["embedding"])
        
        # Check collections
        print("\n2. Checking collections...")
        main_collection = f"repo_{scan_id}"
        cd_collection = f"repo_{scan_id}_cd"
        
        print(f"Main collection: {main_collection}")
        print(f"CD collection: {cd_collection}")
        
        # List all collections
        if vector_service.use_qdrant:
            try:
                collections = vector_service.client.get_collections()
                print(f"Available collections: {[c.name for c in collections.collections]}")
            except Exception as e:
                print(f"❌ Failed to list collections: {e}")
        else:
            print(f"In-memory collections: {list(vector_service.collections.keys())}")
        
        # Check collection info
        print("\n3. Checking collection info...")
        main_info = vector_service.get_collection_info(main_collection)
        cd_info = vector_service.get_collection_info(cd_collection)
        
        print(f"Main collection info: {main_info}")
        print(f"CD collection info: {cd_info}")
        
        # Test different queries
        print("\n4. Testing different queries...")
        
        test_queries = [
            "high level project summary with key frameworks and technologies",
            "spring petclinic project technologies",
            "java spring framework",
            "project dependencies and technologies",
            "main application technologies",
            "spring boot application",
            "java project structure",
            "maven dependencies",
            "project configuration files",
            "application setup and configuration"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            query_embedding = embedding_service.embed_single(query)
            
            if not query_embedding:
                print("  ❌ Failed to generate embedding")
                continue
                
            print(f"  Embedding generated: {len(query_embedding)} dimensions")
            
            # Test different thresholds
            for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
                print(f"  Threshold {threshold}:")
                
                # Search in main collection
                try:
                    main_results = vector_service.search_similar(
                        collection_name=main_collection,
                        query_vector=query_embedding,
                        limit=5,
                        score_threshold=threshold
                    )
                    print(f"    Main results: {len(main_results)}")
                except Exception as e:
                    print(f"    ❌ Failed to search collection {main_collection}: {e}")
                    print(f"    Main results: 0")
                
                # Search in CD collection
                try:
                    cd_results = vector_service.search_similar(
                        collection_name=cd_collection,
                        query_vector=query_embedding,
                        limit=3,
                        score_threshold=threshold
                    )
                    print(f"    CD results: {len(cd_results)}")
                except Exception as e:
                    print(f"    ❌ Failed to search collection {cd_collection}: {e}")
                    print(f"    CD results: 0")
        
        # Test project summary generation
        print(f"\n5. Testing project summary generation...")
        project_info = vector_service.generate_project_summary(
            repo_url=repo_url,
            scan_id=scan_id
        )
        
        print(f"Project Summary Result:")
        print(json.dumps(project_info, indent=2))
        
        # Test with lower threshold
        print(f"\n6. Testing with lower threshold...")
        project_info_lower = vector_service.generate_project_summary(
            repo_url=repo_url,
            scan_id=scan_id
        )
        
        print(f"Project Summary with Lower Threshold:")
        print(json.dumps(project_info_lower, indent=2))
        
        # Test direct collection access
        print(f"\n7. Testing direct collection access...")
        try:
            if vector_service.use_qdrant:
                # Try to get collection directly
                collection_info = vector_service.client.get_collection(main_collection)
                print(f"✅ Collection found: {collection_info.points_count} points")
                
                # Try to get a few points
                points = vector_service.client.scroll(
                    collection_name=main_collection,
                    limit=5
                )
                print(f"✅ Retrieved {len(points[0])} points")
                
                # Show first point payload
                if points[0]:
                    first_point = points[0][0]
                    print(f"First point payload keys: {list(first_point.payload.keys())}")
                    print(f"First point content preview: {str(first_point.payload.get('content', ''))[:100]}...")
                
            else:
                print("Using in-memory storage")
                if main_collection in vector_service.collections:
                    print(f"✅ Collection found in memory: {vector_service.collections[main_collection]['count']} points")
                else:
                    print(f"❌ Collection not found in memory")
                    
        except Exception as e:
            print(f"❌ Failed to access collection directly: {e}")
        
        return project_info
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return None

if __name__ == "__main__":
    # Get scan_id from command line argument
    scan_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    asyncio.run(debug_project_summary(scan_id))
