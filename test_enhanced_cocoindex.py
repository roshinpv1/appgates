#!/usr/bin/env python3
"""
Test script for Enhanced CocoIndex Service with AST-based parsing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.enhanced_cocoindex_service import EnhancedCocoIndexService

async def test_enhanced_cocoindex():
    """Test the enhanced CocoIndex service"""
    
    print("🧪 Testing Enhanced CocoIndex Service")
    print("=" * 50)
    
    # Configuration
    config = {
        "qdrant_path": "./qdrant_data",
        "chunk_size": 1000,
        "chunk_overlap": 300,
        "embedding_model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "included_patterns": [
            "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cs", 
            "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", "*.md", "*.mdx"
        ],
        "excluded_patterns": [
            ".*", "node_modules", "__pycache__", "target", "build", "dist", 
            "*.pyc", "*.class", "*.o", "*.so", "*.dylib", "*.dll"
        ]
    }
    
    try:
        # Initialize service
        print("🔧 Initializing Enhanced CocoIndex Service...")
        service = EnhancedCocoIndexService(config)
        
        # Test AST-based chunking with a sample Python file
        print("\n🔍 Testing AST-based chunking...")
        
        sample_python_code = '''
import os
import sys
from typing import Dict, List, Any

class TestClass:
    """A test class for demonstration"""
    
    def __init__(self, name: str):
        self.name = name
    
    def test_method(self, param: str) -> str:
        """A test method"""
        return f"Hello {self.name}, param: {param}"

def test_function(param: int) -> int:
    """A test function"""
    return param * 2

async def async_function():
    """An async function"""
    await asyncio.sleep(1)
    return "done"
'''
        
        # Test chunking
        chunks = service._create_ast_based_chunks(
            sample_python_code,
            Path("test_file.py"),
            Path("."),
            "test_scan",
            "python",
            "main"
        )
        
        print(f"📄 Generated {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            method = chunk["metadata"].get("chunking_method", "unknown")
            node_type = chunk["metadata"].get("node_type", "")
            print(f"  {i+1}. Method: {method}, Node Type: {node_type}, Lines: {chunk['metadata']['start_line']}-{chunk['metadata']['end_line']}")
        
        # Test language detection
        print("\n🔍 Testing language detection...")
        test_files = [
            "test.py",
            "test.js",
            "test.ts",
            "test.java",
            "test.go",
            "test.rs",
            "test.cpp",
            "test.c",
            "test.md"
        ]
        
        for file_path in test_files:
            language = service._detect_language(Path(file_path))
            print(f"  {file_path} -> {language}")
        
        # Test file filtering
        print("\n🔍 Testing file filtering...")
        test_paths = [
            "src/main.py",
            "node_modules/package.json",
            "__pycache__/test.pyc",
            "build/output.js",
            "src/components/App.tsx"
        ]
        
        for file_path in test_paths:
            should_ignore = service._should_ignore_file(Path(file_path))
            print(f"  {file_path} -> {'❌ Ignored' if should_ignore else '✅ Included'}")
        
        print("\n✅ Enhanced CocoIndex Service test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_cocoindex())
