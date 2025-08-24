#!/usr/bin/env python3
"""
Script to find existing collections and scan IDs
"""

import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vector_service import VectorService

def find_existing_collections():
    """Find existing collections and scan IDs"""
    
    # Configuration
    config = {
        "vector_size": 768,
        "distance_metric": "cosine",
        "use_qdrant": True,
        "qdrant_path": "./qdrant_data"
    }
    
    print("🔍 Finding Existing Collections")
    print("=" * 40)
    
    try:
        # Initialize vector service
        vector_service = VectorService(config)
        
        # List all collections
        if vector_service.use_qdrant:
            try:
                collections = vector_service.client.get_collections()
                print(f"Total collections found: {len(collections.collections)}")
                
                if collections.collections:
                    print("\n📋 Available Collections:")
                    for i, collection in enumerate(collections.collections, 1):
                        print(f"{i}. {collection.name}")
                        
                        # Get collection info
                        try:
                            info = vector_service.get_collection_info(collection.name)
                            if info:
                                print(f"   - Vector size: {info.get('vector_size', 'Unknown')}")
                                print(f"   - Points count: {info.get('count', 'Unknown')}")
                        except Exception as e:
                            print(f"   - Error getting info: {e}")
                        
                        # Extract scan ID from collection name
                        if collection.name.startswith("repo_"):
                            scan_id = collection.name[5:]  # Remove "repo_" prefix
                            print(f"   - Scan ID: {scan_id}")
                        
                        print()
                else:
                    print("❌ No collections found in Qdrant")
                    
                    # Check if Qdrant is running
                    print("\n🔧 Checking Qdrant status...")
                    try:
                        # Try to create a test collection
                        test_collection = "test_collection"
                        vector_service.create_collection(test_collection)
                        print("✅ Qdrant is running and accessible")
                        
                        # Clean up test collection
                        vector_service.delete_collection(test_collection)
                        print("✅ Test collection cleaned up")
                        
                    except Exception as e:
                        print(f"❌ Qdrant issue: {e}")
                        
            except Exception as e:
                print(f"❌ Failed to list collections: {e}")
        else:
            print("Using in-memory storage")
            print(f"Collections: {list(vector_service.collections.keys())}")
        
        # Check for recent scan reports
        print("\n📁 Checking for recent scan reports...")
        reports_dir = "../reports"
        if os.path.exists(reports_dir):
            scan_dirs = [d for d in os.listdir(reports_dir) if d.startswith("scan_")]
            scan_dirs.sort(reverse=True)  # Most recent first
            
            print(f"Found {len(scan_dirs)} scan directories:")
            for scan_dir in scan_dirs[:10]:  # Show last 10
                scan_path = os.path.join(reports_dir, scan_dir)
                files = os.listdir(scan_path) if os.path.isdir(scan_path) else []
                print(f"  {scan_dir}: {len(files)} files")
                
                # Check if this scan has vector data
                expected_collection = f"repo_{scan_dir}"
                if vector_service.use_qdrant:
                    try:
                        info = vector_service.get_collection_info(expected_collection)
                        if info:
                            print(f"    ✅ Vector collection exists: {info.get('count', 0)} points")
                        else:
                            print(f"    ❌ No vector collection found")
                    except:
                        print(f"    ❌ No vector collection found")
        
        # Check qdrant data directory
        print("\n📂 Checking Qdrant data directory...")
        qdrant_path = "./qdrant_data"
        if os.path.exists(qdrant_path):
            print(f"Qdrant data directory exists: {qdrant_path}")
            contents = os.listdir(qdrant_path)
            print(f"Contents: {contents}")
        else:
            print(f"❌ Qdrant data directory not found: {qdrant_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_existing_collections()
