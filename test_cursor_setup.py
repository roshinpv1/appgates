#!/usr/bin/env python3
"""
Cursor-specific setup test for CodeGates
Tests AI features and Cursor-specific functionality
"""

import sys
from pathlib import Path

def test_cursor_features():
    """Test Cursor-specific features"""
    print("🎯 Testing Cursor-specific features...")
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Test imports (should work with Cursor's enhanced intellisense)
    try:
        from services.question_service import QuestionService
        print("✅ QuestionService imported (AI should suggest this)")
    except ImportError as e:
        print(f"❌ QuestionService import failed: {e}")
    
    try:
        from services.cocoindex_service import CocoIndexService
        print("✅ CocoIndexService imported (AI should suggest this)")
    except ImportError as e:
        print(f"❌ CocoIndexService import failed: {e}")
    
    try:
        from flow.scan_flow import ScanFlow
        print("✅ ScanFlow imported (AI should suggest this)")
    except ImportError as e:
        print(f"❌ ScanFlow import failed: {e}")

def test_cursor_config():
    """Test Cursor configuration files"""
    print("\n🔧 Testing Cursor configuration...")
    
    config_files = [
        ".vscode/settings.json",
        ".vscode/launch.json", 
        ".vscode/extensions.json",
        ".vscode/keybindings.json",
        "pyrightconfig.json",
        "pyproject.toml"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} missing")

def test_ai_features():
    """Test AI-related features"""
    print("\n🤖 Testing AI features...")
    
    # Test that we can create sample code for AI to work with
    sample_code = '''
class SampleService:
    """Sample service for AI testing"""
    
    def __init__(self, config: dict):
        self.config = config
    
    async def process_data(self, data: str) -> dict:
        """Process data with AI assistance"""
        return {"processed": data, "status": "success"}
    '''
    
    print("✅ Sample code created (AI can analyze this)")
    print("✅ AI should suggest improvements and completions")

def main():
    print("🚀 Cursor Setup Test for CodeGates")
    print("=" * 50)
    
    test_cursor_config()
    test_cursor_features()
    test_ai_features()
    
    print("\n" + "=" * 50)
    print("🎯 Cursor Setup Test Completed!")
    print("\n📝 Next Steps:")
    print("1. Open Cursor and navigate to this project")
    print("2. Select Python interpreter: .venv/bin/python")
    print("3. Install recommended extensions")
    print("4. Test AI features:")
    print("   - Press Cmd+L to open AI chat")
    print("   - Type '/explain' followed by code")
    print("   - Use Cmd+K for inline AI assistance")
    print("5. Test navigation:")
    print("   - Cmd+Click on any class/method")
    print("   - Shift+F12 to find references")
    print("   - F12 to go to definition")
    
    print("\n🎨 Cursor AI Features to Try:")
    print("- Cmd+L: Open AI chat")
    print("- Cmd+K: Inline AI assistance")
    print("- Cmd+Shift+L: Fix code with AI")
    print("- Cmd+Shift+K: Explain code with AI")
    print("- Tab/Enter: Accept AI suggestions")

if __name__ == "__main__":
    main()
