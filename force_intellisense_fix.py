#!/usr/bin/env python3
"""
Force IntelliSense Fix for Cursor
This script will help you manually fix the Python interpreter issue
"""

import os
import sys
from pathlib import Path

def main():
    print("🔧 FORCE IntelliSense Fix for Cursor")
    print("=" * 50)
    
    # Get the absolute path to the correct Python interpreter
    current_dir = Path(__file__).parent.absolute()
    venv_python = current_dir / ".venv" / "bin" / "python"
    
    print(f"📍 Current directory: {current_dir}")
    print(f"🐍 Correct Python: {venv_python}")
    print(f"✅ Exists: {venv_python.exists()}")
    
    if venv_python.exists():
        print("\n🎯 MANUAL FIX STEPS:")
        print("=" * 30)
        print("1. Open Cursor")
        print("2. Press Cmd+Shift+P")
        print("3. Type: 'Python: Select Interpreter'")
        print(f"4. Click 'Enter interpreter path...'")
        print(f"5. Paste this exact path:")
        print(f"   {venv_python}")
        print("6. Press Enter")
        print("7. Wait for Cursor to reload")
        print("8. Press Cmd+Shift+P again")
        print("9. Type: 'Python: Restart Language Server'")
        print("10. Press Cmd+Shift+P again")
        print("11. Type: 'Developer: Reload Window'")
        
        print("\n🔍 VERIFICATION:")
        print("After completing the steps above:")
        print("1. Open src/services/question_service.py")
        print("2. Type 'from services.' and wait for suggestions")
        print("3. Hover over 'QuestionService' to see documentation")
        print("4. Cmd+Click on 'QuestionService' to go to definition")
        
        print("\n🚨 IF STILL NOT WORKING:")
        print("1. Close Cursor completely")
        print("2. Delete .vscode/settings.json")
        print("3. Reopen Cursor")
        print("4. Follow steps 1-11 above")
        
    else:
        print(f"❌ Virtual environment not found at {venv_python}")
        print("Please run: python -m venv .venv")

if __name__ == "__main__":
    main()
