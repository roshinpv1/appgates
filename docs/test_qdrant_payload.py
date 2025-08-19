#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import QdrantClient

print("🔧 Testing Qdrant payload...")

try:
    # Initialize Qdrant client
    client = QdrantClient(path="./qdrant_data")
    print(f"✅ Qdrant client initialized successfully")
    
    # Get collection info
    collection_name = "e1115fe93def0923"
    info = client.get_collection(collection_name)
    print(f"🔧 Collection info: {info.points_count} points")
    
    # Get all points
    points = client.scroll(
        collection_name=collection_name,
        limit=10
    )
    
    print(f"🔧 Found {len(points[0])} points")
    
    for i, point in enumerate(points[0]):
        print(f"🔧 Point {i}:")
        print(f"   ID: {point.id}")
        print(f"   Score: {point.score if hasattr(point, 'score') else 'N/A'}")
        print(f"   Payload keys: {list(point.payload.keys())}")
        
        # Check if content is in payload
        if 'content' in point.payload:
            content = point.payload['content']
            print(f"   Content length: {len(content) if content else 0}")
            print(f"   Content preview: {content[:100] if content else 'Empty'}")
        else:
            print(f"   Content: Not found in payload")
        
        # Show all payload keys
        for key, value in point.payload.items():
            if key == 'content':
                print(f"   {key}: {len(str(value))} chars")
            else:
                print(f"   {key}: {value}")
        print()
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
