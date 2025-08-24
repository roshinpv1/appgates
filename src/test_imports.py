#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

def test_imports():
    """Test all imports"""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        print("  Testing core imports...")
        from core.base import AsyncFlow, AsyncNode, ScanContext
        print("    ✅ Core imports successful")
        
        # Test models imports
        print("  Testing models imports...")
        from models.scan_models import RepositoryInfo, CodeChunk, Pattern, GateResult
        print("    ✅ Models imports successful")
        
        # Test services imports
        print("  Testing services imports...")
        from services.vector_service import VectorService
        from services.embedding_service import EmbeddingService
        from services.ast_parser_service import ASTParserService
        from services.prompt_service import PromptService
        from services.pattern_library_service import PatternLibraryService
        print("    ✅ Services imports successful")
        
        # Test utils imports
        print("  Testing utils imports...")
        from utils.git_utils import GitUtils
        print("    ✅ Utils imports successful")
        
        # Test flow imports
        print("  Testing flow imports...")
        from flow.scan_flow import ScanFlow
        from flow.scan_nodes import RepositoryCheckoutNode
        print("    ✅ Flow imports successful")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
