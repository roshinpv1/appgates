#!/usr/bin/env python3
"""
Test script for CodeGates PocketFlow implementation
"""

import sys
import os
import tempfile
import uuid
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        from flow import create_validation_flow
        from utils.hard_gates import HARD_GATES
        from utils.git_operations import clone_repository
        from utils.file_scanner import scan_directory
        from utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
        from nodes import (
            FetchRepositoryNode, ProcessCodebaseNode, ExtractConfigNode,
            GeneratePromptNode, CallLLMNode, ValidateGatesNode,
            GenerateReportNode, CleanupNode
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_hard_gates():
    """Test hard gates definition"""
    print("🧪 Testing hard gates...")
    
    try:
        from utils.hard_gates import HARD_GATES, get_gate_by_name
        
        assert len(HARD_GATES) == 15, f"Expected 15 gates, got {len(HARD_GATES)}"
        
        # Test specific gate
        structured_logs = get_gate_by_name("STRUCTURED_LOGS")
        assert structured_logs is not None, "STRUCTURED_LOGS gate not found"
        assert structured_logs["display_name"] == "Logs Searchable/Available"
        
        print(f"✅ Hard gates test passed ({len(HARD_GATES)} gates)")
        return True
    except Exception as e:
        print(f"❌ Hard gates test failed: {e}")
        return False


def test_file_scanner():
    """Test file scanner utility"""
    print("🧪 Testing file scanner...")
    
    try:
        from utils.file_scanner import scan_directory
        
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "main.py").write_text("print('hello world')\n# This is a comment\n")
            (temp_path / "app.js").write_text("console.log('hello');\nfunction test() {}\n")
            (temp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
            
            # Create subdirectory
            sub_dir = temp_path / "src"
            sub_dir.mkdir()
            (sub_dir / "utils.py").write_text("def helper():\n    return True\n")
            
            # Scan directory
            metadata = scan_directory(str(temp_path))
            
            assert metadata["total_files"] >= 4, f"Expected at least 4 files, got {metadata['total_files']}"
            assert "Python" in metadata["languages"], "Python not detected"
            assert "JavaScript" in metadata["languages"], "JavaScript not detected"
            assert metadata["total_lines"] > 0, "No lines counted"
            
        print("✅ File scanner test passed")
        return True
    except Exception as e:
        print(f"❌ File scanner test failed: {e}")
        return False


def test_llm_client():
    """Test LLM client functionality"""
    print("🧪 Testing LLM client...")
    
    try:
        from utils.llm_client import LLMClient, LLMConfig, LLMProvider, create_llm_client_from_env
        
        # Test LLM config creation
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="test-model",
            base_url="http://localhost:11434/v1",
            api_key="not-needed"
        )
        
        assert config.provider == LLMProvider.LOCAL
        assert config.model == "test-model"
        assert config.base_url == "http://localhost:11434/v1"
        
        # Test LLM client creation
        client = LLMClient(config)
        assert client.config.provider == LLMProvider.LOCAL
        
        # Test auto-detection (should not fail even if no LLM is configured)
        auto_client = create_llm_client_from_env()
        # auto_client can be None if no LLM is configured, which is fine
        
        print("✅ LLM client test passed")
        return True
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False


def test_flow_creation():
    """Test flow creation"""
    print("🧪 Testing flow creation...")
    
    try:
        from flow import create_validation_flow
        
        flow = create_validation_flow()
        assert flow is not None, "Flow creation returned None"
        
        print("✅ Flow creation test passed")
        return True
    except Exception as e:
        print(f"❌ Flow creation test failed: {e}")
        return False


def test_shared_store_structure():
    """Test shared store structure"""
    print("🧪 Testing shared store structure...")
    
    try:
        from utils.hard_gates import HARD_GATES
        
        # Create test shared store
        shared = {
            "request": {
                "repository_url": "https://github.com/octocat/Hello-World",
                "branch": "master",
                "github_token": None,
                "threshold": 70,
                "scan_id": str(uuid.uuid4())
            },
            "llm_config": {
                "provider": "auto",
                "model": None,
                "url": None,
                "api_key": None,
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "repository": {"local_path": None, "metadata": {}},
            "config": {"build_files": {}, "config_files": {}, "dependencies": []},
            "llm": {"prompt": None, "response": None, "patterns": {}, "source": "unknown", "model": "unknown"},
            "validation": {"gate_results": [], "overall_score": 0.0},
            "reports": {"html_path": None, "json_path": None},
            "hard_gates": HARD_GATES,
            "temp_dir": tempfile.mkdtemp(prefix="test_codegates_"),
            "errors": []
        }
        
        # Validate structure
        assert "request" in shared
        assert "llm_config" in shared
        assert "repository" in shared
        assert "config" in shared
        assert "llm" in shared
        assert "validation" in shared
        assert "reports" in shared
        assert "hard_gates" in shared
        assert len(shared["hard_gates"]) == 15
        
        # Validate LLM config structure
        assert "provider" in shared["llm_config"]
        assert "model" in shared["llm_config"]
        assert "url" in shared["llm_config"]
        assert "api_key" in shared["llm_config"]
        assert "temperature" in shared["llm_config"]
        assert "max_tokens" in shared["llm_config"]
        
        # Validate LLM store structure
        assert "source" in shared["llm"]
        assert "model" in shared["llm"]
        
        # Cleanup
        import shutil
        if os.path.exists(shared["temp_dir"]):
            shutil.rmtree(shared["temp_dir"])
        
        print("✅ Shared store structure test passed")
        return True
    except Exception as e:
        print(f"❌ Shared store structure test failed: {e}")
        return False


def test_node_creation():
    """Test individual node creation"""
    print("🧪 Testing node creation...")
    
    try:
        from nodes import (
            FetchRepositoryNode, ProcessCodebaseNode, ExtractConfigNode,
            GeneratePromptNode, CallLLMNode, ValidateGatesNode,
            GenerateReportNode, CleanupNode
        )
        
        # Create all nodes
        nodes = [
            FetchRepositoryNode(),
            ProcessCodebaseNode(),
            ExtractConfigNode(),
            GeneratePromptNode(),
            CallLLMNode(),
            ValidateGatesNode(),
            GenerateReportNode(),
            CleanupNode()
        ]
        
        assert len(nodes) == 8, f"Expected 8 nodes, got {len(nodes)}"
        
        for i, node in enumerate(nodes):
            assert hasattr(node, 'prep'), f"Node {i} missing prep method"
            assert hasattr(node, 'exec'), f"Node {i} missing exec method"
            assert hasattr(node, 'post'), f"Node {i} missing post method"
        
        print("✅ Node creation test passed")
        return True
    except Exception as e:
        print(f"❌ Node creation test failed: {e}")
        return False


def test_llm_providers():
    """Test LLM provider enumeration"""
    print("🧪 Testing LLM providers...")
    
    try:
        from utils.llm_client import LLMProvider
        
        # Test all expected providers exist
        expected_providers = [
            "openai", "anthropic", "gemini", "ollama", 
            "local", "enterprise", "apigee"
        ]
        
        for provider_name in expected_providers:
            provider = LLMProvider(provider_name)
            assert provider.value == provider_name, f"Provider {provider_name} has wrong value"
        
        print(f"✅ LLM providers test passed ({len(expected_providers)} providers)")
        return True
    except Exception as e:
        print(f"❌ LLM providers test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("🚀 Running CodeGates PocketFlow Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_hard_gates,
        test_file_scanner,
        test_llm_client,
        test_flow_creation,
        test_shared_store_structure,
        test_node_creation,
        test_llm_providers
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The PocketFlow implementation is ready.")
        return True
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 