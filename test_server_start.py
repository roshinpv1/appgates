#!/usr/bin/env python3
"""
Simple test to check if the server can start
"""

import sys
import os

# Add the gates directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gates'))

try:
    # Try to import the server
    from server import app
    print("✅ Server imports successfully")
    
    # Try to import nodes
    from nodes import GenerateReportNode
    print("✅ Nodes import successfully")
    
    print("✅ All imports successful - server should start")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing server startup...") 