#!/usr/bin/env python3
"""
Debug script to test vectorization step directly
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow.scan_nodes import VectorizationNode
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService
from services.ast_parser_service import ASTParserService

async def debug_vectorization():
    """Debug vectorization step directly"""
    
    print("🔍 Debugging Vectorization Step")
    print("=" * 40)
    
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
    
    # Initialize services
    print("1. Initializing services...")
    vector_service = VectorService(config["vector_store"])
    embedding_service = EmbeddingService(config["embedding"])
    ast_parser_service = ASTParserService(config)
    
    # Create vectorization node
    vectorization_node = VectorizationNode(vector_service, embedding_service, ast_parser_service)
    
    # Mock repository data
    repo_path = "/tmp/test_repo"
    scan_id = "test_vectorization_debug"
    
    # Create a test file
    os.makedirs(repo_path, exist_ok=True)
    test_file = Path(repo_path) / "test.py"
    test_file.write_text("""
def hello_world():
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.name = "test"
    
    def test_method(self):
        return self.name
""")
    
    # Mock metadata
    metadata = {
        "scan_id": scan_id,
        "main_repo": {
            "repo_url": "https://github.com/test/repo",
            "branch": "main",
            "commit_hash": "abc123",
            "total_files": 1,
            "total_lines": 10,
            "languages": ["python"],
            "dependencies": {},
            "build_files": [],
            "config_files": []
        }
    }
    
    # Test preparation
    print("2. Testing preparation...")
    prep_res = {
        "repo_path": repo_path,
        "cd_repo_path": None,
        "metadata": metadata
    }
    
    # Test execution
    print("3. Testing execution...")
    try:
        result = await vectorization_node.exec_async(prep_res)
        print(f"Execution result: {result}")
        
        # Check if collections were created
        print("4. Checking collections...")
        if hasattr(vector_service, 'client') and vector_service.client:
            collections = vector_service.client.get_collections()
            print(f"Collections found: {[c.name for c in collections.collections]}")
        else:
            print("Using in-memory storage - collections not persisted")
            print(f"In-memory collections: {list(vector_service.collections.keys())}")
        
        # Check collection info
        main_collection = f"repo_{scan_id}"
        if hasattr(vector_service, 'client') and vector_service.client:
            try:
                info = vector_service.client.get_collection(main_collection)
                print(f"Main collection info: {info}")
                
                # Get sample points
                points = vector_service.client.scroll(
                    collection_name=main_collection,
                    limit=5
                )
                print(f"Sample points: {len(points[0])}")
                
                if points[0]:
                    sample_point = points[0][0]
                    print(f"Sample point ID: {sample_point.id}")
                    print(f"Sample point payload keys: {list(sample_point.payload.keys())}")
                    print(f"Sample point content preview: {sample_point.payload.get('content', '')[:100]}...")
                    
                    # Check metadata
                    metadata_keys = [k for k in sample_point.payload.keys() if k != 'content']
                    print(f"Metadata keys: {metadata_keys}")
                    
                    for key in metadata_keys:
                        value = sample_point.payload.get(key)
                        print(f"  {key}: {value}")
            except Exception as e:
                print(f"❌ Failed to get collection info: {e}")
        else:
            # Check in-memory storage
            if main_collection in vector_service.vectors:
                vectors = vector_service.vectors[main_collection]
                print(f"In-memory vectors: {len(vectors)}")
                if vectors:
                    sample_vector = vectors[0]
                    print(f"Sample vector ID: {sample_vector['id']}")
                    print(f"Sample vector payload keys: {list(sample_vector['payload'].keys())}")
                    print(f"Sample vector content preview: {sample_vector['payload'].get('content', '')[:100]}...")
                    
                    # Check metadata
                    metadata_keys = [k for k in sample_vector['payload'].keys() if k != 'content']
                    print(f"Metadata keys: {metadata_keys}")
                    
                    for key in metadata_keys:
                        value = sample_vector['payload'].get(key)
                        print(f"  {key}: {value}")
            else:
                print(f"Collection {main_collection} not found in memory")
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("5. Cleanup...")
    try:
        import shutil
        shutil.rmtree(repo_path)
        print("✅ Test repository cleaned up")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(debug_vectorization())
