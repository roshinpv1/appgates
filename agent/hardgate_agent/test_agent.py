#!/usr/bin/env python3
"""
Test Script for HardGate Agent
Tests the HardGate agent functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from hardgate_agent import (
    hardgate_agent,
    analyze_repository,
    validate_gates,
    perform_security_scan,
    collect_evidence,
    run_complete_analysis
)


async def test_agent_initialization():
    """Test agent initialization"""
    print("🧪 Testing Agent Initialization...")
    
    if hardgate_agent.agent:
        print("✅ Agent initialized successfully")
        print(f"📋 Agent name: {hardgate_agent.agent.name}")
        print(f"📋 Agent description: {hardgate_agent.agent.description}")
        print(f"🔧 Tools available: {len(hardgate_agent.agent.tools)}")
        return True
    else:
        print("❌ Agent initialization failed")
        return False


async def test_repository_analysis():
    """Test repository analysis functionality"""
    print("\n🧪 Testing Repository Analysis...")
    
    # Test with a sample repository (you can replace with a real one)
    result = await analyze_repository(
        repository_url="https://github.com/example/security-app",
        branch="main"
    )
    
    if result["success"]:
        print("✅ Repository analysis completed")
        print(f"📊 Analysis result: {result['analysis_result']}")
        return True
    else:
        print(f"❌ Repository analysis failed: {result['error']}")
        return False


async def test_gate_validation():
    """Test gate validation functionality"""
    print("\n🧪 Testing Gate Validation...")
    
    # Test with a sample repository path
    result = await validate_gates(
        repository_path="/tmp/test-repo",
        gates=["STRUCTURED_LOGS", "AUTHENTICATION", "AUTHORIZATION"]
    )
    
    if result["success"]:
        print("✅ Gate validation completed")
        print(f"📊 Validation result: {result['validation_result']}")
        return True
    else:
        print(f"❌ Gate validation failed: {result['error']}")
        return False


async def test_security_scanning():
    """Test security scanning functionality"""
    print("\n🧪 Testing Security Scanning...")
    
    # Test with a sample repository path
    result = await perform_security_scan(
        repository_path="/tmp/test-repo",
        scan_type="comprehensive"
    )
    
    if result["success"]:
        print("✅ Security scanning completed")
        print(f"📊 Scan result: {result['scan_result']}")
        return True
    else:
        print(f"❌ Security scanning failed: {result['error']}")
        return False


async def test_evidence_collection():
    """Test evidence collection functionality"""
    print("\n🧪 Testing Evidence Collection...")
    
    # Test evidence collection
    result = await collect_evidence(
        app_id="test-app-123",
        sources=["splunk", "appdynamics"],
        time_range="24h"
    )
    
    if result["success"]:
        print("✅ Evidence collection completed")
        print(f"📊 Evidence result: {result['evidence_result']}")
        return True
    else:
        print(f"❌ Evidence collection failed: {result['error']}")
        return False


async def test_complete_analysis():
    """Test complete analysis workflow"""
    print("\n🧪 Testing Complete Analysis Workflow...")
    
    # Test complete analysis
    result = await run_complete_analysis(
        repository_url="https://github.com/example/security-app",
        branch="main",
        app_id="test-app-123"
    )
    
    if result["success"]:
        print("✅ Complete analysis workflow completed")
        print(f"📊 Workflow results: {result['workflow_results']}")
        return True
    else:
        print(f"❌ Complete analysis workflow failed: {result['error']}")
        return False


async def test_configuration():
    """Test configuration functionality"""
    print("\n🧪 Testing Configuration...")
    
    try:
        from hardgate_agent.config import config
        
        # Test configuration loading
        litellm_config = config.get_litellm_config()
        agent_config = config.get_agent_config()
        security_config = config.get_security_config()
        
        print("✅ Configuration loaded successfully")
        print(f"📋 LiteLLM Model: {litellm_config.get('model')}")
        print(f"📋 Agent Name: {agent_config.get('name')}")
        print(f"📋 Default Gates: {len(security_config.get('default_gates', []))}")
        
        # Test configuration validation
        validation = config.validate_configuration()
        if validation["valid"]:
            print("✅ Configuration validation passed")
        else:
            print(f"⚠️ Configuration validation issues: {validation['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_tools():
    """Test individual tools"""
    print("\n🧪 Testing Individual Tools...")
    
    try:
        from hardgate_agent.tools import (
            RepositoryAnalysisTool,
            GateValidationTool,
            CodeScanningTool,
            EvidenceCollectionTool,
            SecurityAnalysisTool,
            ComplianceCheckTool,
            LLMAnalysisTool,
            ReportGenerationTool
        )
        
        # Test tool instantiation
        tools = [
            RepositoryAnalysisTool(),
            GateValidationTool(),
            CodeScanningTool(),
            EvidenceCollectionTool(),
            SecurityAnalysisTool(),
            ComplianceCheckTool(),
            LLMAnalysisTool(),
            ReportGenerationTool()
        ]
        
        print(f"✅ All {len(tools)} tools instantiated successfully")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting HardGate Agent Tests")
    print("=" * 50)
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Configuration", test_configuration),
        ("Tools", test_tools),
        ("Repository Analysis", test_repository_analysis),
        ("Gate Validation", test_gate_validation),
        ("Security Scanning", test_security_scanning),
        ("Evidence Collection", test_evidence_collection),
        ("Complete Analysis", test_complete_analysis)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! HardGate Agent is ready to use.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the configuration and dependencies.")
        return False


def main():
    """Main test function"""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 