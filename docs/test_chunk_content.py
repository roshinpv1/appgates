#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.indexing import CodeIndexer
from gates.advanced_llm.embedding import EmbeddingService
from gates.advanced_llm.ast_parser import ASTParser
from gates.advanced_llm.vector_store import VectorStore
from gates.advanced_llm.core import IndexingConfig

print("🔧 Testing chunk content generation...")

try:
    # Initialize dependencies
    vector_store = VectorStore({"use_qdrant": False})  # Use in-memory for testing
    embedding_service = EmbeddingService({"provider": "local", "model": "nomic-embed-text"})
    ast_parser = ASTParser({})
    
    # Create config object
    config = IndexingConfig(
        chunk_size=800,
        overlap_size=120,
        supported_languages=["python", "javascript", "typescript", "java", "csharp", "go", "rust"],
        enable_ast_parsing=True,
        enable_symbol_extraction=True,
        batch_size=64
    )
    
    # Initialize code indexer
    indexer = CodeIndexer(vector_store, embedding_service, ast_parser, config)
    print(f"✅ CodeIndexer initialized successfully")
    
    # Test content
    test_content = """# Hello World

This is a simple Hello World repository.

## Features

- Simple and clean
- Easy to understand
- Perfect for beginners

## Usage

Just run the code and see "Hello World" printed.
"""
    
    print(f"🔧 Test content length: {len(test_content)}")
    print(f"🔧 Test content: {repr(test_content)}")
    
    # Create chunks
    chunks = indexer._create_sliding_chunks(
        repo_id="test",
        file_path="/test/README.md",
        content=test_content,
        language="markdown",
        file_info={"mtime": 1234567890}
    )
    
    print(f"🔧 Created {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"🔧 Chunk {i}:")
        print(f"   Type: {chunk['type']}")
        print(f"   Content length: {len(chunk['content'])}")
        print(f"   Content: {repr(chunk['content'])}")
        print(f"   Metadata: {chunk['metadata']}")
        print()
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
