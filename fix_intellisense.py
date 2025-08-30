#!/usr/bin/env python3
"""
IntelliSense Fix Script for Cursor
Diagnoses and fixes common IntelliSense issues
"""

import os
import sys
import json
from pathlib import Path

def check_python_environment():
    """Check Python environment and paths"""
    print("🔍 Checking Python Environment...")
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    venv_path = Path("/Users/roshinpv/Documents/next/gates/.venv/bin/python")
    if venv_path.exists():
        print(f"✅ Virtual environment exists: {venv_path}")
    else:
        print(f"❌ Virtual environment not found: {venv_path}")
    
    print("\nPython path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")

def test_imports():
    """Test key imports for IntelliSense"""
    print("\n📦 Testing Key Imports...")
    
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    test_imports = [
        "server",
        "services.question_service",
        "services.cocoindex_service", 
        "flow.scan_flow",
        "models.scan_models",
        "utils.git_utils"
    ]
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")

def main():
    print("🚀 IntelliSense Diagnostic for Cursor")
    print("=" * 50)
    
    check_python_environment()
    test_imports()
    
    print("\n🔧 Fix Commands for Cursor:")
    print("1. Cmd+Shift+P → 'Python: Restart Language Server'")
    print("2. Cmd+Shift+P → 'Developer: Reload Window'")
    print("3. Cmd+Shift+P → 'Python: Select Interpreter'")
    print("   Choose: /Users/roshinpv/Documents/next/gates/.venv/bin/python")
    print("4. Install Python and Pylance extensions")
    print("5. Check View → Output → Python for errors")

if __name__ == "__main__":
    main()
