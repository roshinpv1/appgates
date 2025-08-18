#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
    print("✅ Qdrant client imported successfully")
    
    # Test Qdrant client initialization
    client = QdrantClient(path="./qdrant_data")
    print("✅ Qdrant client initialized successfully")
    
    # Test getting collections
    collections = client.get_collections()
    print(f"✅ Found {len(collections.collections)} collections")
    
    for collection in collections.collections:
        print(f"   - {collection.name}")
    
    # Test collection info
    if collections.collections:
        collection_name = collections.collections[0].name
        info = client.get_collection(collection_name)
        print(f"✅ Collection {collection_name} info:")
        print(f"   - Vector size: {info.config.params.vectors.size}")
        print(f"   - Points count: {info.points_count}")
    
except Exception as e:
    print(f"❌ Qdrant test failed: {e}")
    import traceback
    traceback.print_exc()
