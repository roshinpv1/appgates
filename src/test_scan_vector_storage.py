#!/usr/bin/env python3
"""
Test to verify vector storage during scan process
"""

import os
import time
from datetime import datetime
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService
from services.ast_parser_service import ASTParserService
from flow.scan_flow import ScanFlow


def test_scan_vector_storage():
    """Test vector storage during scan process"""
    
    print("🧪 Testing Vector Storage During Scan Process")
    print("=" * 50)
    
    # Configuration that matches server
    config = {
        "vector_store": {
            "use_qdrant": True,
            "qdrant_path": "./qdrant_data",
            "vector_size": 768
        },
        "embedding": {
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234",
            "batch_size": 32,
            "vector_size": 768
        },
        "ast_parser": {
            "supported_languages": [
                "python", "javascript", "typescript", "java", 
                "csharp", "go", "rust", "c", "cpp"
            ]
        },
        "llm": {
            "provider": "local",
            "model": "llama-3.2-3b-instruct",
            "base_url": "http://localhost:1234",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    }
    
    print("📊 Initializing Scan Flow...")
    scan_flow = ScanFlow(config)
    
    # Check vector service configuration
    print(f"🔗 Vector Service Configuration:")
    print(f"   Using Qdrant: {scan_flow.vector_service.use_qdrant}")
    print(f"   Qdrant Path: {config['vector_store']['qdrant_path']}")
    
    # Test with a small repository
    test_repo = "https://github.com/octocat/Hello-World"
    scan_id = f"test_vector_storage_{int(datetime.now().timestamp())}"
    
    print(f"\n🔍 Testing scan with repository: {test_repo}")
    print(f"📋 Scan ID: {scan_id}")
    
    try:
        # Run a quick scan
        result = scan_flow.run_scan(
            repo_url=test_repo,
            branch="main",
            scan_id=scan_id
        )
        
        print(f"✅ Scan completed: {result}")
        
        # Check if vector data was stored
        print(f"\n📊 Checking Vector Storage...")
        
        # Check for collections
        main_collection = f"repo_{scan_id}"
        cd_collection = f"repo_{scan_id}_cd"
        
        print(f"📁 Looking for collections:")
        print(f"   Main: {main_collection}")
        print(f"   CD: {cd_collection}")
        
        # Check if collections exist
        if scan_flow.vector_service.use_qdrant:
            try:
                main_info = scan_flow.vector_service.client.get_collection(main_collection)
                print(f"✅ Main collection found: {main_info.points_count} points")
            except Exception as e:
                print(f"❌ Main collection not found: {e}")
            
            try:
                cd_info = scan_flow.vector_service.client.get_collection(cd_collection)
                print(f"✅ CD collection found: {cd_info.points_count} points")
            except Exception as e:
                print(f"❌ CD collection not found: {e}")
        else:
            print("⚠️ Not using Qdrant, checking in-memory collections")
            if main_collection in scan_flow.vector_service.collections:
                print(f"✅ Main collection found in memory: {scan_flow.vector_service.collections[main_collection]['count']} points")
            else:
                print(f"❌ Main collection not found in memory")
        
        # Test project summary generation
        print(f"\n🔍 Testing Project Summary Generation...")
        project_info = scan_flow.vector_service.generate_project_summary(
            repo_url=test_repo,
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
            print("✅ Vector storage working correctly!")
            return True
        else:
            print("❌ No vector data found")
            return False
            
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return False


if __name__ == "__main__":
    test_scan_vector_storage()
