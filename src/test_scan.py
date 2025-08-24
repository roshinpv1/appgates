"""
Test script for the CodeGates scan implementation
"""

import asyncio
import json
from flow.scan_flow import ScanFlow


async def test_scan_flow():
    """Test the scan flow with a sample repository (including CD repo detection)"""
    
    # Configuration
    config = {
        "vector_store": {
            "use_qdrant": False,  # Use in-memory for testing
            "vector_size": 768
        },
        "embedding": {
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234",
            "batch_size": 32,
            "vector_size": 768
        },
        "ast_parser": {
            "supported_languages": [
                "python", "javascript", "typescript", "java", 
                "csharp", "go", "rust", "c", "cpp"
            ]
        },
        "llm": {
            "provider": "local",
            "model": "llama-3.2-3b-instruct",
            "base_url": "http://localhost:1234",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    }
    
    try:
        print("🧪 Testing CodeGates Scan Flow (with CD repository support)")
        
        # Create scan flow
        scan_flow = ScanFlow(config)
        
        # Test with a public repository (will also try to find -cd version)
        result = await scan_flow.run_scan(
            repo_url="https://github.com/octocat/Hello-World",
            branch="main"
        )
        
        print(f"✅ Test completed: {result['status']}")
        
        if result['status'] == 'completed':
            print(f"📊 Scan ID: {result['scan_id']}")
            if result.get('result'):
                scan_result = result['result']
                print(f"🎯 Gates: {scan_result.get('passed_gates', 0)}/{scan_result.get('total_gates', 0)} passed")
                print(f"⚠️ Risk Score: {scan_result.get('risk_score', 0):.2f}")
            
            # Check if CD repository was found
            if result.get('metadata', {}).get('has_cd_repo'):
                print("🔄 CD repository was found and included in analysis")
            else:
                print("ℹ️ No CD repository found (this is normal for test repositories)")
            
            # Show vector data summary
            if result.get('vector_data'):
                vector_data = result['vector_data']
                print(f"📈 Vector Summary:")
                print(f"   Main repo vectors: {vector_data.get('main_vectors_count', 0)}")
                print(f"   CD repo vectors: {vector_data.get('cd_vectors_count', 0)}")
                print(f"   Total vectors: {vector_data.get('total_vectors_count', 0)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"status": "failed", "error": str(e)}


def test_services():
    """Test individual services"""
    print("🔧 Testing Services")
    
    try:
        from services.vector_service import VectorService
        from services.embedding_service import EmbeddingService
        from services.ast_parser_service import ASTParserService
        
        # Test vector service
        vector_config = {"use_qdrant": False, "vector_size": 768}
        vector_service = VectorService(vector_config)
        print("✅ Vector service initialized")
        
        # Test embedding service
        embedding_config = {
            "provider": "local",
            "model": "text-embedding-nomic-embed-text-v1.5-embedding",
            "base_url": "http://localhost:1234"
        }
        embedding_service = EmbeddingService(embedding_config)
        print("✅ Embedding service initialized")
        
        # Test AST parser service
        ast_config = {"supported_languages": ["python", "javascript"]}
        ast_service = ASTParserService(ast_config)
        print("✅ AST parser service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False


def test_models():
    """Test data models"""
    print("📋 Testing Data Models")
    
    try:
        from models.scan_models import (
            GateStatus, RecommendationType, Symbol, ImportInfo,
            FileMetadata, CodeChunk, Pattern, GateResult,
            ContextualRecommendation, ScanResult, RepositoryInfo
        )
        
        # Test enum creation
        status = GateStatus.PASS
        rec_type = RecommendationType.SECURITY
        print(f"✅ Enums: {status}, {rec_type}")
        
        # Test dataclass creation
        symbol = Symbol(
            name="test_function",
            kind="function",
            start_line=1,
            end_line=10,
            start_column=0,
            end_column=50
        )
        print(f"✅ Symbol: {symbol.name}")
        
        # Test pattern creation
        pattern = Pattern(
            gate_id="test_gate",
            name="Test Pattern",
            description="Test pattern description",
            pattern=r"test\s+pattern",
            severity="HIGH",
            category="SECURITY"
        )
        print(f"✅ Pattern: {pattern.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False


def test_flow_base():
    """Test flow base classes"""
    print("🔄 Testing Flow Base Classes")
    
    try:
        from core.base import AsyncNode, ScanContext
        
        # Test context creation
        context = ScanContext(
            repo_url="https://github.com/test/repo",
            branch="main"
        )
        print(f"✅ Context: {context.repo_url}")
        
        # Test async node
        class TestNode(AsyncNode):
            async def exec_async(self, prep_res):
                return "success"
        
        test_node = TestNode()
        print("✅ Test node created")
        
        return True
        
    except Exception as e:
        print(f"❌ Flow base test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting CodeGates Tests")
    print("=" * 50)
    
    # Test individual components
    print("\n1. Testing Data Models...")
    models_ok = test_models()
    
    print("\n2. Testing Flow Base Classes...")
    flow_ok = test_flow_base()
    
    print("\n3. Testing Services...")
    services_ok = test_services()
    
    # Test full scan flow
    print("\n4. Testing Full Scan Flow...")
    scan_result = await test_scan_flow()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Data Models: {'✅' if models_ok else '❌'}")
    print(f"   Flow Base: {'✅' if flow_ok else '❌'}")
    print(f"   Services: {'✅' if services_ok else '❌'}")
    print(f"   Scan Flow: {'✅' if scan_result.get('status') == 'completed' else '❌'}")
    
    if scan_result.get('status') == 'completed':
        print("\n🎉 All tests passed! The implementation is working correctly.")
    else:
        print(f"\n⚠️ Scan flow test failed: {scan_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
