#!/usr/bin/env python3
"""
Test server configuration to verify embedded Qdrant is being used
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_server_config():
    """Test the exact server configuration"""
    print("🔍 Testing Server Configuration...")
    
    try:
        # Import the exact configuration from server.py
        from server import advanced_config
        
        print("✅ Server configuration loaded")
        print(f"   Vector store config: {advanced_config.get('vector_store', {})}")
        
        # Test vector store initialization with server config
        from advanced_llm.vector_store import VectorStore
        
        vector_config = advanced_config.get("vector_store", {})
        vector_store = VectorStore(vector_config)
        
        # Check health
        health = vector_store.health_check()
        print(f"   Vector store health: {health}")
        
        # Test collection creation
        success = vector_store.create_collection("test-server-config")
        print(f"   Collection creation: {'✅ Success' if success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run test"""
    print("🚀 Testing server configuration...\n")
    
    result = test_server_config()
    
    if result:
        print("\n✅ Server configuration test passed!")
    else:
        print("\n❌ Server configuration test failed!")

if __name__ == "__main__":
    main()
