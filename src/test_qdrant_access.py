#!/usr/bin/env python3
"""
Test Qdrant access and vector data availability
"""

import os
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService


def test_qdrant_access():
    """Test Qdrant access and vector data availability"""
    
    print("🔍 Testing Qdrant Access and Vector Data Availability")
    print("=" * 55)
    
    # Initialize services with Qdrant configuration
    config = {
        "vector_size": 768,
        "distance_metric": "cosine",
        "use_qdrant": True,
        "qdrant_path": "./qdrant_data",
        "provider": "local",
        "model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "base_url": "http://localhost:1234"
    }
    
    print("📊 Initializing Vector Service with Qdrant...")
    vector_service = VectorService(config)
    
    print(f"🔗 Using Qdrant: {vector_service.use_qdrant}")
    print(f"📁 Qdrant Path: {config['qdrant_path']}")
    
    # Check if Qdrant directory exists
    if os.path.exists(config['qdrant_path']):
        print(f"✅ Qdrant data directory exists: {config['qdrant_path']}")
    else:
        print(f"❌ Qdrant data directory not found: {config['qdrant_path']}")
        return False
    
    # List all collections
    print("\n📋 Checking Qdrant Collections:")
    try:
        if vector_service.use_qdrant:
            collections = vector_service.client.get_collections()
            print(f"📊 Found {len(collections.collections)} collections:")
            
            for collection in collections.collections:
                print(f"   📁 {collection.name}: {collection.points_count} points")
        else:
            print("⚠️ Not using Qdrant, using in-memory storage")
            if hasattr(vector_service, 'collections'):
                print(f"📊 In-memory collections: {list(vector_service.collections.keys())}")
    except Exception as e:
        print(f"❌ Failed to list collections: {e}")
    
    # Test with specific scan ID
    scan_id = "scan_1756022002"  # spring-petclinic scan
    print(f"\n🔍 Testing with scan ID: {scan_id}")
    
    # Check for main repository collection
    main_collection = f"repo_{scan_id}"
    cd_collection = f"repo_{scan_id}_cd"
    
    print(f"📁 Looking for collections:")
    print(f"   Main: {main_collection}")
    print(f"   CD: {cd_collection}")
    
    try:
        if vector_service.use_qdrant:
            # Check if collections exist
            try:
                main_info = vector_service.client.get_collection(main_collection)
                print(f"✅ Main collection found: {main_info.points_count} points")
            except Exception as e:
                print(f"❌ Main collection not found: {e}")
            
            try:
                cd_info = vector_service.client.get_collection(cd_collection)
                print(f"✅ CD collection found: {cd_info.points_count} points")
            except Exception as e:
                print(f"❌ CD collection not found: {e}")
        else:
            # Check in-memory collections
            if main_collection in vector_service.collections:
                print(f"✅ Main collection found in memory: {vector_service.collections[main_collection]['count']} points")
            else:
                print(f"❌ Main collection not found in memory")
            
            if cd_collection in vector_service.collections:
                print(f"✅ CD collection found in memory: {vector_service.collections[cd_collection]['count']} points")
            else:
                print(f"❌ CD collection not found in memory")
    except Exception as e:
        print(f"❌ Error checking collections: {e}")
    
    # Test project summary generation
    print(f"\n🔍 Testing Project Summary Generation...")
    try:
        project_info = vector_service.generate_project_summary(
            repo_url="https://github.com/spring-projects/spring-petclinic",
            scan_id=scan_id
        )
        
        print(f"📋 Project Summary Results:")
        print(f"   Summary: {project_info.get('summary', 'No summary')}")
        print(f"   Technologies: {project_info.get('technologies', [])}")
        print(f"   File Types: {project_info.get('file_types', [])}")
        print(f"   Dependencies: {project_info.get('dependencies', [])}")
        print(f"   Has CD Repo: {project_info.get('has_cd_repo', False)}")
        print(f"   Files Analyzed: {project_info.get('total_files_analyzed', 0)}")
        
        if project_info.get('total_files_analyzed', 0) > 0:
            print("✅ Project summary generated successfully with data!")
            return True
        else:
            print("❌ Project summary generated but no data found")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate project summary: {e}")
        return False


def test_vector_search():
    """Test vector search functionality"""
    
    print("\n🔍 Testing Vector Search Functionality")
    print("=" * 40)
    
    # Initialize services
    config = {
        "vector_size": 768,
        "distance_metric": "cosine",
        "use_qdrant": True,
        "qdrant_path": "./qdrant_data",
        "provider": "local",
        "model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "base_url": "http://localhost:1234"
    }
    
    vector_service = VectorService(config)
    embedding_service = EmbeddingService(config)
    
    # Test search query
    query = "high level project summary with key frameworks and technologies"
    query_embedding = embedding_service.embed_single(query)
    
    if not query_embedding:
        print("❌ Failed to generate query embedding")
        return False
    
    print(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
    
    # Test search in main collection
    scan_id = "scan_1756022002"
    main_collection = f"repo_{scan_id}"
    
    print(f"🔍 Searching in collection: {main_collection}")
    
    try:
        results = vector_service.search_similar(
            collection_name=main_collection,
            query_vector=query_embedding,
            limit=5,
            score_threshold=0.3
        )
        
        print(f"📊 Search results: {len(results)} found")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result.score:.3f}, File: {result.payload.get('file_path', 'Unknown')}")
        
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
    print("🧪 Qdrant Access and Vector Data Test")
    print("=" * 50)
    
    # Test Qdrant access
    qdrant_ok = test_qdrant_access()
    
    # Test vector search
    search_ok = test_vector_search()
    
    print(f"\n📋 Test Results:")
    print(f"   Qdrant Access: {'✅ PASS' if qdrant_ok else '❌ FAIL'}")
    print(f"   Vector Search: {'✅ PASS' if search_ok else '❌ FAIL'}")
    
    if qdrant_ok and search_ok:
        print("\n🎉 All tests passed! Vector data is accessible.")
    else:
        print("\n⚠️ Some tests failed. Vector data may not be accessible.")
