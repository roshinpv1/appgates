#!/usr/bin/env python3
import sys
import os
from pathlib import Path

print("🔍 Quick IntelliSense Diagnostic")
print("=" * 40)

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

# Check if src is in path
src_path = Path(__file__).parent / "src"
print(f"src path: {src_path}")
print(f"src exists: {src_path.exists()}")
print(f"src in sys.path: {str(src_path) in sys.path}")

# Test imports
try:
    sys.path.insert(0, str(src_path))
    from services.question_service import QuestionService
    print("✅ QuestionService import works")
except Exception as e:
    print(f"❌ QuestionService import failed: {e}")

print("\n🎯 In Cursor, check:")
print("1. Bottom-left corner - should show Python 3.13.5")
print("2. Cmd+Shift+P → 'Python: Select Interpreter'")
print("3. Should show: /Users/roshinpv/Documents/next/gates/.venv/bin/python")
