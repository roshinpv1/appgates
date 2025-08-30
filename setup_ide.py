#!/usr/bin/env python3
"""
IDE Setup Script for CodeGates
This script helps configure the development environment for proper intellisense.
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 Setting up CodeGates IDE configuration...")
    
    # Get project root
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    # Add src to Python path
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"✅ Added {src_path} to Python path")
    
    # Check virtual environment
    venv_path = project_root / ".venv"
    if venv_path.exists():
        print(f"✅ Virtual environment found at {venv_path}")
    else:
        print("⚠️ Virtual environment not found")
    
    # Test imports
    try:
        import fastapi
        print(f"✅ FastAPI imported successfully: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
    
    try:
        import qdrant_client
        print("✅ Qdrant client imported successfully")
    except ImportError as e:
        print(f"❌ Qdrant client import failed: {e}")
    
    try:
        from services.cocoindex_service import CocoIndexService
        print("✅ CocoIndexService imported successfully")
    except ImportError as e:
        print(f"❌ CocoIndexService import failed: {e}")
    
    try:
        from flow.scan_flow import ScanFlow
        print("✅ ScanFlow imported successfully")
    except ImportError as e:
        print(f"❌ ScanFlow import failed: {e}")
    
    print("\n🎯 IDE Setup Complete!")
    print("📝 Next steps:")
    print("1. Restart your IDE/editor")
    print("2. Select Python interpreter: .venv/bin/python")
    print("3. Reload the window if using VS Code")
    print("4. Check that intellisense is working")

if __name__ == "__main__":
    main()
