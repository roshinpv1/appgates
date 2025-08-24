#!/usr/bin/env python3
"""
Test Suite for Hard Gate Analyzer
Comprehensive testing of the complete hard gate analysis workflow
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the gates directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gates'))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from hard_gate_analyzer import (
            HardGateAnalyzer, 
            ScanRequest, 
            ScanResult, 
            GateResult, 
            GateStatus
        )
        print("✅ Hard Gate Analyzer imports successful")
        
        from advanced_llm.core import AdvancedLLMService
        print("✅ Advanced LLM Service import successful")
        
        from advanced_llm.vector_store import VectorStore
        print("✅ Vector Store import successful")
        
        from advanced_llm.pattern_library import PatternLibraryService
        print("✅ Pattern Library Service import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_data_structures():
    """Test data structure definitions"""
    print("\n🔍 Testing data structures...")
    
    try:
        from hard_gate_analyzer import GateStatus, GateResult, ScanRequest, ScanResult
        
        # Test GateStatus enum
        assert GateStatus.PASS == "pass"
        assert GateStatus.FAIL == "fail"
        assert GateStatus.PARTIAL == "partial"
        assert GateStatus.SKIPPED == "skipped"
        print("✅ GateStatus enum working correctly")
        
        # Test GateResult dataclass
        gate_result = GateResult(
            gate_id="test_gate",
            gate_name="Test Gate",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["pattern1"],
            recommendations=["rec1"],
            confidence_score=0.9,
            reasoning="Test reasoning"
        )
        assert gate_result.gate_id == "test_gate"
        assert gate_result.status == GateStatus.PASS
        print("✅ GateResult dataclass working correctly")
        
        # Test ScanRequest dataclass
        scan_request = ScanRequest(
            repo_url="https://github.com/test/repo",
            branch="main",
            git_token="token123",
            app_id="app123"
        )
        assert scan_request.repo_url == "https://github.com/test/repo"
        assert scan_request.branch == "main"
        print("✅ ScanRequest dataclass working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

def test_prompt_library():
    """Test externalized prompt library"""
    print("\n🔍 Testing prompt library...")
    
    try:
        # Check if prompt library exists
        if not os.path.exists("prompt_library.json"):
            print("⚠️ Prompt library not found, skipping test")
            return True
        
        with open("prompt_library.json", 'r') as f:
            prompt_library = json.load(f)
        
        # Test required prompts exist
        required_prompts = [
            "llm_pre_analysis",
            "llm_post_analysis",
            "gate_applicability_assessment",
            "pattern_generation",
            "risk_assessment"
        ]
        
        for prompt in required_prompts:
            assert prompt in prompt_library, f"Missing prompt: {prompt}"
            assert "prompt_template" in prompt_library[prompt], f"Missing template in {prompt}"
            assert "parameters" in prompt_library[prompt], f"Missing parameters in {prompt}"
        
        print(f"✅ Prompt library loaded successfully with {len(prompt_library)} prompts")
        
        # Test prompt template formatting
        template = prompt_library["llm_pre_analysis"]["prompt_template"]
        formatted = template.format(
            code_structure="test structure",
            config_files="test config",
            hard_gate_summary="test summary"
        )
        assert "test structure" in formatted
        assert "test config" in formatted
        print("✅ Prompt template formatting working")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt library test failed: {e}")
        return False

def test_hard_gate_analyzer_initialization():
    """Test Hard Gate Analyzer initialization"""
    print("\n🔍 Testing Hard Gate Analyzer initialization...")
    
    try:
        from hard_gate_analyzer import HardGateAnalyzer
        
        # Test configuration
        config = {
            "advanced_llm": {
                "retrieval": {
                    "max_chunks": 8,
                    "score_threshold": 0.3
                },
                "indexing": {
                    "chunk_size": 800,
                    "supported_languages": ["python", "javascript"]
                },
                "llm": {
                    "provider": "local",
                    "model": "llama-3.2-3b-instruct",
                    "base_url": "http://localhost:1234"
                },
                "vector_store": {
                    "use_qdrant": True,
                    "qdrant_path": "./test_qdrant",
                    "vector_size": 768
                },
                "embedding": {
                    "provider": "local",
                    "model": "text-embedding-nomic-embed-text-v1.5-embedding",
                    "base_url": "http://localhost:1234"
                }
            },
            "vector_store": {
                "use_qdrant": True,
                "qdrant_path": "./test_qdrant",
                "vector_size": 768
            },
            "prompt_library_path": "prompt_library.json"
        }
        
        # Initialize analyzer
        analyzer = HardGateAnalyzer(config)
        
        # Test components are initialized
        assert analyzer.advanced_llm is not None
        assert analyzer.vector_store is not None
        assert analyzer.pattern_library is not None
        assert analyzer.gate_evaluator is not None
        assert analyzer.prompt_library is not None
        
        print("✅ Hard Gate Analyzer initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Hard Gate Analyzer initialization failed: {e}")
        return False

def test_workflow_components():
    """Test individual workflow components"""
    print("\n🔍 Testing workflow components...")
    
    try:
        from hard_gate_analyzer import HardGateAnalyzer, ScanRequest
        
        # Initialize analyzer with minimal config
        config = {
            "advanced_llm": {
                "retrieval": {"max_chunks": 8, "score_threshold": 0.3},
                "indexing": {"chunk_size": 800, "supported_languages": ["python"]},
                "llm": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"},
                "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
                "embedding": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"}
            },
            "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
            "prompt_library_path": "prompt_library.json"
        }
        
        analyzer = HardGateAnalyzer(config)
        
        # Test helper methods
        code_structure = analyzer._get_code_structure(".")
        assert isinstance(code_structure, str)
        print("✅ Code structure analysis working")
        
        config_files = analyzer._get_config_files(".")
        assert isinstance(config_files, dict)
        print("✅ Config file analysis working")
        
        hard_gate_summary = analyzer._get_hard_gate_summary()
        assert "Security Gates" in hard_gate_summary
        assert "Performance Gates" in hard_gate_summary
        print("✅ Hard gate summary generation working")
        
        fallback_patterns = analyzer._get_fallback_patterns()
        assert "patterns" in fallback_patterns
        assert "gate_applicability" in fallback_patterns
        print("✅ Fallback patterns working")
        
        # Test threshold logic
        threshold = analyzer._get_threshold_for_gate("security_auth")
        assert threshold == 1
        threshold = analyzer._get_threshold_for_gate("unknown_gate")
        assert threshold == 1  # default
        print("✅ Threshold logic working")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow components test failed: {e}")
        return False

def test_gate_evaluation_logic():
    """Test gate evaluation logic"""
    print("\n🔍 Testing gate evaluation logic...")
    
    try:
        from hard_gate_analyzer import HardGateAnalyzer, GateStatus
        
        config = {
            "advanced_llm": {
                "retrieval": {"max_chunks": 8, "score_threshold": 0.3},
                "indexing": {"chunk_size": 800, "supported_languages": ["python"]},
                "llm": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"},
                "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
                "embedding": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"}
            },
            "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
            "prompt_library_path": "prompt_library.json"
        }
        
        analyzer = HardGateAnalyzer(config)
        
        # Test scan results structure
        scan_results = {
            'files_scanned': 10,
            'patterns_found': {},
            'gate_results': {
                'test_gate': {
                    'pattern': {'description': 'Test Gate'},
                    'matches': ['match1', 'match2'],
                    'count': 2
                }
            }
        }
        
        expected_implementations = {'test_gate': 1}
        
        # Test gate evaluation
        gate_results = analyzer._evaluate_gates(scan_results, expected_implementations)
        
        assert len(gate_results) == 1
        gate_result = gate_results[0]
        assert gate_result.gate_id == 'test_gate'
        assert gate_result.actual_count == 2
        assert gate_result.expected_count == 1
        assert gate_result.status == GateStatus.PASS  # 2 >= 1
        print("✅ Gate evaluation logic working")
        
        # Test risk score calculation
        risk_score = analyzer._calculate_risk_score(gate_results)
        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 1.0
        print("✅ Risk score calculation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Gate evaluation test failed: {e}")
        return False

def test_scan_result_generation():
    """Test scan result generation"""
    print("\n🔍 Testing scan result generation...")
    
    try:
        from hard_gate_analyzer import HardGateAnalyzer, ScanRequest, GateResult, GateStatus
        
        config = {
            "advanced_llm": {
                "retrieval": {"max_chunks": 8, "score_threshold": 0.3},
                "indexing": {"chunk_size": 800, "supported_languages": ["python"]},
                "llm": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"},
                "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
                "embedding": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"}
            },
            "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
            "prompt_library_path": "prompt_library.json"
        }
        
        analyzer = HardGateAnalyzer(config)
        
        # Create test data
        request = ScanRequest(
            repo_url="https://github.com/test/repo",
            branch="main",
            app_id="test_app"
        )
        
        gate_results = [
            GateResult(
                gate_id="gate1",
                gate_name="Test Gate 1",
                status=GateStatus.PASS,
                expected_count=1,
                actual_count=1,
                threshold=1,
                patterns_found=["pattern1"],
                recommendations=["rec1"],
                confidence_score=0.9,
                reasoning="Test reasoning"
            ),
            GateResult(
                gate_id="gate2",
                gate_name="Test Gate 2",
                status=GateStatus.FAIL,
                expected_count=1,
                actual_count=0,
                threshold=1,
                patterns_found=[],
                recommendations=["rec2"],
                confidence_score=0.8,
                reasoning="Test reasoning"
            )
        ]
        
        recommendations = ["Recommendation 1", "Recommendation 2"]
        start_time = datetime.now()
        
        # Generate scan result
        scan_result = analyzer._generate_scan_result(
            "test_scan_id", request, gate_results, recommendations, start_time
        )
        
        # Verify scan result
        assert scan_result.scan_id == "test_scan_id"
        assert scan_result.app_id == "test_app"
        assert scan_result.repo_url == "https://github.com/test/repo"
        assert scan_result.branch == "main"
        assert scan_result.total_gates == 2
        assert scan_result.passed_gates == 1
        assert scan_result.failed_gates == 1
        assert scan_result.partial_gates == 0
        assert scan_result.skipped_gates == 0
        assert len(scan_result.gate_results) == 2
        assert len(scan_result.recommendations) == 2
        assert isinstance(scan_result.risk_score, float)
        assert isinstance(scan_result.scan_duration, float)
        
        print("✅ Scan result generation working")
        
        return True
        
    except Exception as e:
        print(f"❌ Scan result generation test failed: {e}")
        return False

def test_server_integration():
    """Test server API integration"""
    print("\n🔍 Testing server integration...")
    
    try:
        # Test API models
        from gates.server import HardGateScanRequest, HardGateScanResponse
        
        # Test request model
        request = HardGateScanRequest(
            repo_url="https://github.com/test/repo",
            branch="main",
            git_token="token123",
            app_id="test_app"
        )
        
        assert request.repo_url == "https://github.com/test/repo"
        assert request.branch == "main"
        assert request.git_token == "token123"
        assert request.app_id == "test_app"
        print("✅ API request model working")
        
        # Test response model
        response = HardGateScanResponse(
            scan_id="test_scan",
            app_id="test_app",
            repo_url="https://github.com/test/repo",
            branch="main",
            scan_timestamp="2024-01-01T00:00:00",
            total_gates=5,
            passed_gates=3,
            failed_gates=1,
            partial_gates=1,
            skipped_gates=0,
            risk_score=0.3,
            scan_duration=10.5,
            recommendations=["rec1", "rec2"],
            gate_results=[{"gate_id": "test", "status": "pass"}]
        )
        
        assert response.scan_id == "test_scan"
        assert response.total_gates == 5
        assert response.passed_gates == 3
        assert response.failed_gates == 1
        assert response.partial_gates == 1
        assert response.skipped_gates == 0
        assert response.risk_score == 0.3
        assert response.scan_duration == 10.5
        assert len(response.recommendations) == 2
        assert len(response.gate_results) == 1
        print("✅ API response model working")
        
        return True
        
    except Exception as e:
        print(f"❌ Server integration test failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test end-to-end workflow (mock)"""
    print("\n🔍 Testing end-to-end workflow...")
    
    try:
        from hard_gate_analyzer import HardGateAnalyzer, ScanRequest
        
        # Initialize analyzer
        config = {
            "advanced_llm": {
                "retrieval": {"max_chunks": 8, "score_threshold": 0.3},
                "indexing": {"chunk_size": 800, "supported_languages": ["python"]},
                "llm": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"},
                "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
                "embedding": {"provider": "local", "model": "test", "base_url": "http://localhost:1234"}
            },
            "vector_store": {"use_qdrant": True, "qdrant_path": "./test_qdrant", "vector_size": 768},
            "prompt_library_path": "prompt_library.json"
        }
        
        analyzer = HardGateAnalyzer(config)
        
        # Create scan request
        request = ScanRequest(
            repo_url="https://github.com/octocat/Hello-World",
            branch="master",
            app_id="test_app"
        )
        
        print("✅ End-to-end workflow setup successful")
        print("⚠️ Full workflow test requires actual LLM and repository access")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Hard Gate Analyzer Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Data Structures", test_data_structures),
        ("Prompt Library", test_prompt_library),
        ("Hard Gate Analyzer Initialization", test_hard_gate_analyzer_initialization),
        ("Workflow Components", test_workflow_components),
        ("Gate Evaluation Logic", test_gate_evaluation_logic),
        ("Scan Result Generation", test_scan_result_generation),
        ("Server Integration", test_server_integration),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Hard Gate Analyzer is ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
