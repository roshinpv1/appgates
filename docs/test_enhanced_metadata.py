#!/usr/bin/env python3
"""
Test enhanced metadata storage in embeddings
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_enhanced_metadata():
    """Test enhanced metadata storage"""
    print("🔍 Testing enhanced metadata storage...")

    try:
        from advanced_llm.vector_store import VectorStore
        from advanced_llm.embedding import EmbeddingService
        from advanced_llm.indexing import CodeIndexer, ChunkMetadata

        # Initialize components
        vector_store = VectorStore({
            "use_qdrant": True,
            "qdrant_path": "./qdrant_metadata_test",
            "vector_size": 768
        })

        embedding_service = EmbeddingService({
            "provider": "local",
            "model": "nomic-embed-text",
            "batch_size": 32
        })

        # Test collection
        collection_name = "metadata_test"
        vector_store.create_collection(collection_name)
        print(f"✅ Created collection: {collection_name}")

        # Create test metadata
        test_metadata = ChunkMetadata(
            repo_id="test_repo",
            file_path="/path/to/test/file.py",
            relative_path="src/test/file.py",
            filename="file.py",
            directory="src/test",
            file_extension=".py",
            file_size=1024,
            total_lines=50,
            is_binary=False,
            file_type="source",
            language="python",
            start_line=1,
            end_line=20,
            chunk_size=800,
            overlap_size=100,
            imports=["os", "sys", "pathlib"],
            references=["MyClass", "my_function"],
            symbol_name="test_function",
            symbol_kind="function",
            content_hash="abc123",
            mtime=1234567890,
            encoding="utf-8",
            permissions="644",
            git_status="modified",
            git_tracked=True,
            complexity_score=2.5,
            cyclomatic_complexity=3
        )

        # Test content
        test_content = """
def test_function():
    \"\"\"Test function with enhanced metadata\"\"\"
    import os
    import sys
    
    result = "Hello World"
    return result
"""

        # Generate embedding
        embedding = embedding_service.embed_single(test_content)
        print(f"✅ Generated embedding: {len(embedding)} dimensions")

        # Create vector data with enhanced metadata
        vector_data = {
            "id": "test_enhanced_metadata_1",
            "vector": embedding,
            "payload": {
                # Repository information
                "repo_id": test_metadata.repo_id,
                
                # File path information
                "file_path": test_metadata.file_path,
                "relative_path": test_metadata.relative_path,
                "filename": test_metadata.filename,
                "directory": test_metadata.directory,
                "file_extension": test_metadata.file_extension,
                
                # File characteristics
                "file_size": test_metadata.file_size,
                "total_lines": test_metadata.total_lines,
                "is_binary": test_metadata.is_binary,
                "file_type": test_metadata.file_type,
                "language": test_metadata.language,
                
                # Chunk information
                "start_line": test_metadata.start_line,
                "end_line": test_metadata.end_line,
                "chunk_size": test_metadata.chunk_size,
                "overlap_size": test_metadata.overlap_size,
                
                # Code analysis
                "symbol_name": test_metadata.symbol_name,
                "symbol_kind": test_metadata.symbol_kind,
                "imports": test_metadata.imports,
                "references": test_metadata.references,
                
                # File metadata
                "content_hash": test_metadata.content_hash,
                "mtime": test_metadata.mtime,
                "encoding": test_metadata.encoding,
                "permissions": test_metadata.permissions,
                
                # Git information
                "git_status": test_metadata.git_status,
                "git_tracked": test_metadata.git_tracked,
                
                # Code complexity metrics
                "complexity_score": test_metadata.complexity_score,
                "cyclomatic_complexity": test_metadata.cyclomatic_complexity,
                
                # Chunk type and content
                "chunk_type": "test",
                "content": test_content
            }
        }

        # Store vector
        success = vector_store.upsert_vectors(collection_name, [vector_data])
        print(f"✅ Stored vector with enhanced metadata: {success}")

        # Retrieve and verify metadata
        results = vector_store.search_similar(
            collection_name=collection_name,
            query_vector=embedding,
            limit=1,
            score_threshold=0.0
        )

        if results:
            result = results[0]
            payload = result.payload
            
            print(f"✅ Retrieved vector with enhanced metadata:")
            print(f"   File: {payload.get('filename')} ({payload.get('file_extension')})")
            print(f"   Path: {payload.get('relative_path')}")
            print(f"   Directory: {payload.get('directory')}")
            print(f"   Type: {payload.get('file_type')} ({payload.get('language')})")
            print(f"   Size: {payload.get('file_size')} bytes, {payload.get('total_lines')} lines")
            print(f"   Binary: {payload.get('is_binary')}")
            print(f"   Lines: {payload.get('start_line')}-{payload.get('end_line')}")
            print(f"   Symbol: {payload.get('symbol_name')} ({payload.get('symbol_kind')})")
            print(f"   Imports: {payload.get('imports')}")
            print(f"   References: {payload.get('references')}")
            print(f"   Encoding: {payload.get('encoding')}")
            print(f"   Permissions: {payload.get('permissions')}")
            print(f"   Git: {payload.get('git_status')} (tracked: {payload.get('git_tracked')})")
            print(f"   Complexity: {payload.get('complexity_score')} (cyclomatic: {payload.get('cyclomatic_complexity')})")
            print(f"   Hash: {payload.get('content_hash')}")
            print(f"   Modified: {payload.get('mtime')}")
            
            # Verify all metadata fields are present
            expected_fields = [
                'repo_id', 'file_path', 'relative_path', 'filename', 'directory',
                'file_extension', 'file_size', 'total_lines', 'is_binary', 'file_type',
                'language', 'start_line', 'end_line', 'chunk_size', 'overlap_size',
                'symbol_name', 'symbol_kind', 'imports', 'references', 'content_hash',
                'mtime', 'encoding', 'permissions', 'git_status', 'git_tracked',
                'complexity_score', 'cyclomatic_complexity', 'chunk_type', 'content'
            ]
            
            missing_fields = [field for field in expected_fields if field not in payload]
            if missing_fields:
                print(f"❌ Missing metadata fields: {missing_fields}")
                return False
            else:
                print(f"✅ All enhanced metadata fields present!")
                return True
        else:
            print("❌ No results found")
            return False

    except Exception as e:
        print(f"❌ Enhanced metadata test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Testing Enhanced Metadata Storage")
    print("=" * 50)
    
    success = test_enhanced_metadata()
    
    if success:
        print("\n✅ All enhanced metadata tests passed!")
    else:
        print("\n❌ Some enhanced metadata tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
