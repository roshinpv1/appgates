#!/usr/bin/env python3
"""
Debug server configuration issue
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def test_server_advanced_llm():
    """Test if the server is using advanced LLM service"""
    print("🔍 Testing server advanced LLM service...")
    
    try:
        # Import the server module to check if advanced_llm_service is available
        import server
        
        if hasattr(server, 'advanced_llm_service') and server.advanced_llm_service is not None:
            print("✅ Server has advanced_llm_service")
            
            # Check vector store configuration
            vector_store = server.advanced_llm_service.vector_store
            health = vector_store.health_check()
            print(f"   Vector store health: {health}")
            
            # Check if it's using embedded Qdrant
            if hasattr(vector_store, 'use_qdrant') and vector_store.use_qdrant:
                print("✅ Server is using embedded Qdrant")
            else:
                print("❌ Server is NOT using embedded Qdrant")
                
            return True
        else:
            print("❌ Server does not have advanced_llm_service")
            return False
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_llm_import():
    """Test if advanced LLM can be imported in server context"""
    print("🔍 Testing advanced LLM import in server context...")
    
    try:
        # Test the exact import that the server uses
        from advanced_llm import AdvancedLLMService
        print("✅ Advanced LLM import successful")
        
        # Test configuration
        config = {
            "vector_store": {
                "use_qdrant": True,
                "qdrant_path": ":memory:",
                "vector_size": 1536
            }
        }
        
        service = AdvancedLLMService(config)
        health = service.vector_store.health_check()
        print(f"   Vector store health: {health}")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced LLM import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🚀 Debugging server configuration...\n")
    
    tests = [
        ("Advanced LLM Import", test_advanced_llm_import),
        ("Server Advanced LLM", test_server_advanced_llm)
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
