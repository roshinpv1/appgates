#!/usr/bin/env python3
"""
Test script for Git Hash-based Collection System

This script demonstrates:
1. Creating collections based on git hash instead of scan ID
2. Deduplication of repository indexing
3. Scan ID to git hash mapping
4. Reusing existing collections for multiple scans
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from services.vector_service import VectorService
from services.embedding_service import EmbeddingService


class GitHashCollectionTester:
    """Test the git hash-based collection system"""
    
    def __init__(self):
        self.vector_service = VectorService({
            "vector_size": 768,
            "use_qdrant": False  # Use in-memory for testing
        })
        self.embedding_service = EmbeddingService({
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234",
            "vector_size": 768
        })
    
    def test_collection_naming(self):
        """Test collection naming based on git hash"""
        print("🧪 Testing Collection Naming...")
        
        # Test cases
        test_cases = [
            {
                "scan_id": "scan_001",
                "repo_hash": "abc123def456",
                "expected": "repo_abc123def456"
            },
            {
                "scan_id": "scan_002", 
                "repo_hash": None,
                "expected": "repo_scan_002"
            },
            {
                "scan_id": "scan_003",
                "repo_hash": "xyz789",
                "expected": "repo_xyz789"
            }
        ]
        
        for case in test_cases:
            collection_name = self.vector_service._get_collection_name(
                case["scan_id"], 
                case["repo_hash"]
            )
            expected = case["expected"]
            
            if collection_name == expected:
                print(f"✅ {case['scan_id']} -> {collection_name}")
            else:
                print(f"❌ {case['scan_id']} -> {collection_name} (expected: {expected})")
    
    def test_scan_mapping(self):
        """Test scan ID to git hash mapping"""
        print("\n🧪 Testing Scan Mapping...")
        
        # Store some test mappings
        test_mappings = [
            {
                "scan_id": "scan_001",
                "repo_hash": "abc123def456",
                "repo_url": "https://github.com/user/repo1",
                "branch": "main"
            },
            {
                "scan_id": "scan_002",
                "repo_hash": "abc123def456",  # Same repo, different scan
                "repo_url": "https://github.com/user/repo1",
                "branch": "main"
            },
            {
                "scan_id": "scan_003",
                "repo_hash": "xyz789",
                "repo_url": "https://github.com/user/repo2",
                "branch": "develop"
            }
        ]
        
        for mapping in test_mappings:
            self.vector_service._store_scan_mapping(
                mapping["scan_id"],
                mapping["repo_hash"],
                mapping["repo_url"],
                mapping["branch"]
            )
        
        # Test retrieval
        for mapping in test_mappings:
            retrieved = self.vector_service._get_scan_mapping(mapping["scan_id"])
            if retrieved and retrieved.get("repo_hash") == mapping["repo_hash"]:
                print(f"✅ Scan {mapping['scan_id']} -> Hash {mapping['repo_hash']}")
            else:
                print(f"❌ Failed to retrieve mapping for {mapping['scan_id']}")
        
        # Test getting all scans for a repo
        repo_scans = self.vector_service.get_scan_mappings_for_repo("abc123def456")
        print(f"📋 Repository abc123def456 has {len(repo_scans)} scans: {[s['scan_id'] for s in repo_scans]}")
    
    def test_repository_indexing_check(self):
        """Test repository indexing status check"""
        print("\n🧪 Testing Repository Indexing Check...")
        
        # Create a test collection
        test_hash = "test123hash"
        collection_name = f"repo_{test_hash}"
        
        # Should not be indexed initially
        is_indexed = self.vector_service.is_repository_indexed(test_hash)
        print(f"Repository {test_hash} indexed: {is_indexed}")
        
        # Create the collection
        self.vector_service.create_collection(collection_name)
        
        # Should be indexed now
        is_indexed = self.vector_service.is_repository_indexed(test_hash)
        print(f"Repository {test_hash} indexed after creation: {is_indexed}")
        
        # Get collection info
        info = self.vector_service.get_repository_collection_info(test_hash)
        print(f"Collection info: {info}")
    
    def test_deduplication_scenario(self):
        """Test the deduplication scenario"""
        print("\n🧪 Testing Deduplication Scenario...")
        
        # Simulate first scan of a repository
        repo_hash = "production_repo_hash"
        scan_id_1 = "scan_2024_01_01"
        
        print(f"🔍 First scan: {scan_id_1} for repo {repo_hash}")
        
        # Check if already indexed
        if self.vector_service.is_repository_indexed(repo_hash):
            print("🔄 Repository already indexed - skipping vectorization")
        else:
            print("📝 Repository not indexed - creating new collection")
            collection_name = self.vector_service._get_collection_name(scan_id_1, repo_hash)
            self.vector_service.create_collection(collection_name)
            
            # Store some dummy vectors
            dummy_vectors = [
                {
                    "id": "chunk_1",
                    "vector": [0.1] * 768,
                    "payload": {"content": "test content 1", "file_path": "test1.java"}
                },
                {
                    "id": "chunk_2", 
                    "vector": [0.2] * 768,
                    "payload": {"content": "test content 2", "file_path": "test2.java"}
                }
            ]
            self.vector_service.upsert_vectors(collection_name, dummy_vectors)
        
        # Store scan mapping
        self.vector_service._store_scan_mapping(
            scan_id_1, repo_hash, "https://github.com/user/prod-repo", "main"
        )
        
        # Simulate second scan of the same repository
        scan_id_2 = "scan_2024_01_15"
        
        print(f"\n🔍 Second scan: {scan_id_2} for repo {repo_hash}")
        
        # Check if already indexed
        if self.vector_service.is_repository_indexed(repo_hash):
            print("🔄 Repository already indexed - reusing existing collection")
            collection_name = self.vector_service._get_collection_name(scan_id_2, repo_hash)
            print(f"📊 Using collection: {collection_name}")
            
            # Get collection stats
            stats = self.vector_service.get_collection_stats(collection_name)
            print(f"📈 Collection stats: {stats}")
        else:
            print("📝 Repository not indexed - creating new collection")
        
        # Store scan mapping for second scan
        self.vector_service._store_scan_mapping(
            scan_id_2, repo_hash, "https://github.com/user/prod-repo", "main"
        )
        
        # Show all scans for this repository
        all_scans = self.vector_service.get_scan_mappings_for_repo(repo_hash)
        print(f"\n📋 All scans for repository {repo_hash}:")
        for scan in all_scans:
            print(f"  - {scan['scan_id']} ({scan['created_at']})")
    
    def test_different_repositories(self):
        """Test different repositories getting different collections"""
        print("\n🧪 Testing Different Repositories...")
        
        repos = [
            {
                "hash": "repo_a_hash",
                "url": "https://github.com/user/repo-a",
                "scans": ["scan_a_1", "scan_a_2"]
            },
            {
                "hash": "repo_b_hash", 
                "url": "https://github.com/user/repo-b",
                "scans": ["scan_b_1"]
            }
        ]
        
        for repo in repos:
            print(f"\n📁 Repository: {repo['hash']}")
            
            # Create collection for this repo
            collection_name = f"repo_{repo['hash']}"
            self.vector_service.create_collection(collection_name)
            
            # Store scan mappings
            for scan_id in repo['scans']:
                self.vector_service._store_scan_mapping(
                    scan_id, repo['hash'], repo['url'], "main"
                )
            
            # Verify collection
            is_indexed = self.vector_service.is_repository_indexed(repo['hash'])
            info = self.vector_service.get_repository_collection_info(repo['hash'])
            scans = self.vector_service.get_scan_mappings_for_repo(repo['hash'])
            
            print(f"  Collection: {info['collection_name']}")
            print(f"  Indexed: {is_indexed}")
            print(f"  Scans: {len(scans)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Git Hash-based Collection System Tests")
        print("=" * 60)
        
        self.test_collection_naming()
        self.test_scan_mapping()
        self.test_repository_indexing_check()
        self.test_deduplication_scenario()
        self.test_different_repositories()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        
        # Show final state
        print("\n📊 Final System State:")
        print(f"Total collections: {len(self.vector_service.collections)}")
        for collection_name, vectors in self.vector_service.collections.items():
            print(f"  - {collection_name}: {len(vectors)} items")


async def main():
    """Main test function"""
    tester = GitHashCollectionTester()
    tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
