#!/usr/bin/env python3
"""
Quick verification script for IntelliSense
Run this after fixing the Python interpreter
"""

import sys
from pathlib import Path

def main():
    print("🔍 Verifying IntelliSense Setup...")
    
    # Check Python interpreter
    expected_venv = "/Users/roshinpv/Documents/next/gates/.venv/bin/python"
    current_python = sys.executable
    
    print(f"Expected: {expected_venv}")
    print(f"Current:  {current_python}")
    
    if expected_venv in current_python:
        print("✅ Python interpreter is correct!")
    else:
        print("❌ Python interpreter is wrong!")
        print("   Fix: Cmd+Shift+P → 'Python: Select Interpreter'")
        print(f"   Choose: {expected_venv}")
    
    # Test imports
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    try:
        from services.question_service import QuestionService
        print("✅ QuestionService import works")
    except ImportError as e:
        print(f"❌ QuestionService import failed: {e}")
    
    try:
        from flow.scan_flow import ScanFlow
        print("✅ ScanFlow import works")
    except ImportError as e:
        print(f"❌ ScanFlow import failed: {e}")
    
    print("\n🎯 Next Steps in Cursor:")
    print("1. Restart Python Language Server")
    print("2. Reload Window")
    print("3. Test auto-completion in a Python file")

if __name__ == "__main__":
    main()
