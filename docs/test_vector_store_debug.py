#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.vector_store import VectorStore

# Test configuration
config = {
    "use_qdrant": True,
    "qdrant_path": "./qdrant_data",
    "vector_size": 768
}

print("🔧 Testing VectorStore initialization...")
print(f"🔧 Config: {config}")

try:
    vector_store = VectorStore(config)
    print(f"✅ VectorStore initialized successfully")
    print(f"🔧 use_qdrant flag: {vector_store.use_qdrant}")
    print(f"🔧 vector_size: {vector_store.vector_size}")
    
    # Test health check
    health = vector_store.health_check()
    print(f"🔧 Health check: {health}")
    
    # Test collection exists
    exists = vector_store.collection_exists("e1115fe93def0923")
    print(f"🔧 Collection exists: {exists}")
    
    # Test get collection stats
    stats = vector_store.get_collection_stats("e1115fe93def0923")
    print(f"🔧 Collection stats: {stats}")
    
except Exception as e:
    print(f"❌ VectorStore test failed: {e}")
    import traceback
    traceback.print_exc()
