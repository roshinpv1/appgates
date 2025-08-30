#!/usr/bin/env python3
"""
Debug script to verify virtual environment and Python path
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 Debug Environment Verification")
    print("=" * 50)
    
    # Check Python executable
    print(f"🐍 Python Executable: {sys.executable}")
    print(f"📦 Python Version: {sys.version}")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"🔧 In Virtual Environment: {in_venv}")
    
    # Check sys.path
    print(f"\n📁 Python Path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    # Check environment variables
    print(f"\n🌍 Environment Variables:")
    print(f"  PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"  VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
    
    # Check if src is in path
    src_path = Path(__file__).parent / "src"
    print(f"\n📂 Source Path Check:")
    print(f"  src path: {src_path}")
    print(f"  src exists: {src_path.exists()}")
    print(f"  src in sys.path: {str(src_path) in sys.path}")
    
    # Test imports
    print(f"\n🧪 Import Tests:")
    try:
        sys.path.insert(0, str(src_path))
        from services.question_service import QuestionService
        print("  ✅ QuestionService import: SUCCESS")
    except Exception as e:
        print(f"  ❌ QuestionService import: FAILED - {e}")
    
    try:
        from flow.scan_flow import ScanFlow
        print("  ✅ ScanFlow import: SUCCESS")
    except Exception as e:
        print(f"  ❌ ScanFlow import: FAILED - {e}")
    
    try:
        import uvicorn
        print("  ✅ uvicorn import: SUCCESS")
    except Exception as e:
        print(f"  ❌ uvicorn import: FAILED - {e}")
    
    print(f"\n🎯 Debug Configuration:")
    print("1. In VS Code, press F5 or go to Run → Start Debugging")
    print("2. Select 'Debug CodeGates Server' configuration")
    print("3. Set breakpoints in your code")
    print("4. The debugger should now use the correct virtual environment")

if __name__ == "__main__":
    main()
