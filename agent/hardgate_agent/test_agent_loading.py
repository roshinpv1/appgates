#!/usr/bin/env python3
"""
Test script to verify HardGate Agent loading
Tests that all tools can be instantiated without BaseTool initialization errors
"""

import sys
import os
from pathlib import Path

# Add the hardgate_agent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_loading():
    """Test that the HardGate Agent can be loaded without errors"""
    try:
        print("🔍 Testing HardGate Agent loading...")
        
        # Test importing the agent directly from the hardgate_agent directory
        from agent import HardGateAgent
        print("✅ HardGate Agent imported successfully")
        
        # Test agent initialization
        agent = HardGateAgent()
        print("✅ HardGate Agent instantiated successfully")
        
        # Test that agent has the expected attributes
        if hasattr(agent, 'agent'):
            print("✅ Agent has 'agent' attribute")
        else:
            print("❌ Agent missing 'agent' attribute")
            return False
        
        # Test that the underlying Google ADK agent is properly configured
        adk_agent = agent.agent
        if hasattr(adk_agent, 'tools') and len(adk_agent.tools) > 0:
            print(f"✅ Agent has {len(adk_agent.tools)} tools configured")
        else:
            print("❌ Agent has no tools configured")
            return False
        
        # Test individual tool loading
        print("\n🔍 Testing individual tool loading...")
        from tools.repository_analysis import RepositoryAnalysisTool
        from tools.gate_validation import GateValidationTool
        from tools.evidence_collection import EvidenceCollectionTool
        from tools.report_generation import ReportGenerationTool
        from tools.code_scanning import CodeScanningTool
        from tools.security_analysis import SecurityAnalysisTool
        from tools.compliance_check import ComplianceCheckTool
        from tools.llm_analysis import LLMAnalysisTool
        
        tools_to_test = [
            ("RepositoryAnalysisTool", RepositoryAnalysisTool),
            ("GateValidationTool", GateValidationTool),
            ("EvidenceCollectionTool", EvidenceCollectionTool),
            ("ReportGenerationTool", ReportGenerationTool),
            ("CodeScanningTool", CodeScanningTool),
            ("SecurityAnalysisTool", SecurityAnalysisTool),
            ("ComplianceCheckTool", ComplianceCheckTool),
            ("LLMAnalysisTool", LLMAnalysisTool)
        ]
        
        for tool_name, tool_class in tools_to_test:
            try:
                tool_instance = tool_class()
                print(f"✅ {tool_name} instantiated successfully")
                
                # Test that tool has required attributes
                if hasattr(tool_instance, 'name') and hasattr(tool_instance, 'description'):
                    print(f"   - Name: {tool_instance.name}")
                    print(f"   - Description: {tool_instance.description[:50]}...")
                else:
                    print(f"❌ {tool_name} missing required attributes")
                    return False
                    
            except Exception as e:
                print(f"❌ {tool_name} failed to instantiate: {str(e)}")
                return False
        
        print("\n🎉 All tests passed! HardGate Agent is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure all dependencies are installed and paths are correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_litellm_configuration():
    """Test that LiteLLM is properly configured"""
    try:
        print("\n🔍 Testing LiteLLM configuration...")
        
        from tools.llm_analysis import LLMAnalysisTool
        
        llm_tool = LLMAnalysisTool()
        
        # Check that model configuration is set
        if hasattr(llm_tool, 'model_config'):
            config = llm_tool.model_config
            print(f"✅ LiteLLM configured with:")
            print(f"   - Model: {config.get('model', 'N/A')}")
            print(f"   - Base URL: {config.get('base_url', 'N/A')}")
            print(f"   - Provider: {config.get('provider', 'N/A')}")
        else:
            print("❌ LiteLLM model configuration not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LiteLLM configuration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 HardGate Agent Loading Test")
    print("=" * 50)
    
    # Test agent loading
    agent_ok = test_agent_loading()
    
    # Test LiteLLM configuration
    litellm_ok = test_litellm_configuration()
    
    print("\n" + "=" * 50)
    if agent_ok and litellm_ok:
        print("🎉 All tests passed! HardGate Agent is ready for use.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 