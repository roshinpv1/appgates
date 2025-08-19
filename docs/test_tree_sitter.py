#!/usr/bin/env python3
"""
Test Tree-sitter language grammars
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_tree_sitter_grammars():
    """Test Tree-sitter language grammars"""
    print("🔍 Testing Tree-sitter language grammars...")
    
    try:
        # Test Python grammar
        import tree_sitter_python
        print("✅ Python grammar available")
        
        # Test JavaScript grammar
        import tree_sitter_javascript
        print("✅ JavaScript grammar available")
        
        # Test Java grammar
        import tree_sitter_java
        print("✅ Java grammar available")
        
        # Test C grammar
        import tree_sitter_c
        print("✅ C grammar available")
        
        # Test C++ grammar
        import tree_sitter_cpp
        print("✅ C++ grammar available")
        
        # Test Go grammar
        import tree_sitter_go
        print("✅ Go grammar available")
        
        # Test Rust grammar
        import tree_sitter_rust
        print("✅ Rust grammar available")
        
        return True
        
    except Exception as e:
        print(f"❌ Tree-sitter grammar test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ast_parser():
    """Test AST parser with Tree-sitter"""
    print("🔍 Testing AST parser with Tree-sitter...")
    
    try:
        from advanced_llm.ast_parser import ASTParser
        
        # Test configuration
        config = {
            "supported_languages": ["python", "javascript", "java", "c", "cpp", "go", "rust"]
        }
        
        # Initialize AST parser
        ast_parser = ASTParser(config)
        print("✅ AST parser initialized")
        
        # Test Python parsing
        python_code = """
def hello_world():
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
"""
        
        result = ast_parser.parse_file(python_code, "python")
        print(f"✅ Python parsing result: {len(result.get('symbols', []))} symbols found")
        
        # Test JavaScript parsing
        js_code = """
function greet(name) {
    console.log("Hello, " + name);
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
"""
        
        result = ast_parser.parse_file(js_code, "javascript")
        print(f"✅ JavaScript parsing result: {len(result.get('symbols', []))} symbols found")
        
        return True
        
    except Exception as e:
        print(f"❌ AST parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Testing Tree-sitter language grammars...\n")
    
    tests = [
        ("Tree-sitter Grammars", test_tree_sitter_grammars),
        ("AST Parser", test_ast_parser)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} test...")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
