#!/usr/bin/env python3
"""
Test script to verify IDE setup is working correctly
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all key modules can be imported"""
    print("🧪 Testing imports...")
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Test core imports
    try:
        from services.cocoindex_service import CocoIndexService
        print("✅ CocoIndexService imported")
    except ImportError as e:
        print(f"❌ CocoIndexService import failed: {e}")
    
    try:
        from flow.scan_flow import ScanFlow
        print("✅ ScanFlow imported")
    except ImportError as e:
        print(f"❌ ScanFlow import failed: {e}")
    
    try:
        from services.question_service import QuestionService
        print("✅ QuestionService imported")
    except ImportError as e:
        print(f"❌ QuestionService import failed: {e}")
    
    try:
        from services.prompt_templates import prompt_templates
        print("✅ PromptTemplates imported")
    except ImportError as e:
        print(f"❌ PromptTemplates import failed: {e}")
    
    try:
        from server import ScanRequest
        print("✅ ScanRequest model imported")
    except ImportError as e:
        print(f"❌ ScanRequest import failed: {e}")

def test_python_path():
    """Test Python path configuration"""
    print("\n🔍 Testing Python path...")
    src_path = Path(__file__).parent / "src"
    if str(src_path) in sys.path:
        print(f"✅ {src_path} is in Python path")
    else:
        print(f"❌ {src_path} is NOT in Python path")

def test_environment():
    """Test environment configuration"""
    print("\n🌍 Testing environment...")
    
    # Check virtual environment
    venv_path = Path(__file__).parent / ".venv"
    if venv_path.exists():
        print(f"✅ Virtual environment found at {venv_path}")
    else:
        print("❌ Virtual environment not found")
    
    # Check Python version
    print(f"✅ Python version: {sys.version}")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    print(f"✅ Current directory: {current_dir}")

if __name__ == "__main__":
    print("🚀 CodeGates IDE Setup Test")
    print("=" * 40)
    
    test_environment()
    test_python_path()
    test_imports()
    
    print("\n" + "=" * 40)
    print("🎯 Test completed!")
    print("\nIf all tests passed, your IDE setup should work correctly.")
    print("If any tests failed, check the IDE_SETUP.md guide for troubleshooting.")
