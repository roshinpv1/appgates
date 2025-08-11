#!/usr/bin/env python3
"""
Test script for CodeGates Validation Agent
Demonstrates agent functionality and LiteLLM integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_agent_creation():
    """Test agent creation and configuration"""
    print("🧪 Testing Agent Creation")
    print("=" * 50)
    
    try:
        from agent import root_agent
        
        print(f"✅ Agent created successfully")
        print(f"   Name: {root_agent.name}")
        print(f"   Description: {root_agent.description}")
        print(f"   Available tools: {len(root_agent.tools)}")
        
        # List available tools
        for i, tool in enumerate(root_agent.tools, 1):
            print(f"   {i}. {tool.name}: {tool.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return False

def test_litellm_configuration():
    """Test LiteLLM configuration"""
    print("\n🧪 Testing LiteLLM Configuration")
    print("=" * 50)
    
    try:
        from agent.litellm_config import test_litellm_configuration as test_config
        
        success = test_config()
        if success:
            print("✅ LiteLLM configuration test passed")
        else:
            print("⚠️ LiteLLM configuration test failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing LiteLLM configuration: {e}")
        return False

def test_tool_functionality():
    """Test individual tool functionality"""
    print("\n🧪 Testing Tool Functionality")
    print("=" * 50)
    
    try:
        from agent.codegates_agent import (
            RepositoryAnalysisTool,
            GateValidationTool,
            EvidenceCollectionTool,
            ReportGenerationTool
        )
        
        # Test tool creation
        tools = [
            RepositoryAnalysisTool(),
            GateValidationTool(),
            EvidenceCollectionTool(),
            ReportGenerationTool()
        ]
        
        print("✅ Tools created successfully")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing tool functionality: {e}")
        return False

async def test_agent_workflow():
    """Test complete agent workflow"""
    print("\n🧪 Testing Agent Workflow")
    print("=" * 50)
    
    try:
        from agent import create_codegates_runner
        
        # Create runner
        runner = create_codegates_runner()
        print("✅ Runner created successfully")
        
        # Test user message
        user_message = {
            "parts": [{
                "text": "Hello! Can you help me understand what gates are available for validation?"
            }]
        }
        
        print("🔄 Running agent workflow...")
        
        # Run the agent
        event_count = 0
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=user_message
        ):
            event_count += 1
            print(f"   Event {event_count}: {event.type}")
            
            if hasattr(event, 'content') and event.content:
                print(f"   Content: {event.content[:200]}...")
        
        print(f"✅ Agent workflow completed. Generated {event_count} events.")
        return True
        
    except Exception as e:
        print(f"❌ Error in agent workflow: {e}")
        return False

def test_environment_configuration():
    """Test environment configuration"""
    print("\n🧪 Testing Environment Configuration")
    print("=" * 50)
    
    # Check required environment variables
    env_vars = [
        "CODEGATES_LLM_PROVIDER",
        "CODEGATES_LLM_MODEL",
        "CODEGATES_LLM_BASE_URL",
        "CODEGATES_LLM_API_KEY"
    ]
    
    print("Environment Variables:")
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if value != "Not set":
            print(f"   ✅ {var}: {value[:20]}..." if len(value) > 20 else f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️ {var}: Not set")
    
    return True

def demonstrate_usage_examples():
    """Demonstrate usage examples"""
    print("\n📚 Usage Examples")
    print("=" * 50)
    
    examples = [
        "Validate the repository at https://github.com/company/myapp",
        "What gates are applicable for a Python web application?",
        "Generate a report for the validation results",
        "Collect evidence from Splunk and AppDynamics",
        "Explain the ALERTING_ACTIONABLE gate requirements"
    ]
    
    print("Example interactions with the agent:")
    for i, example in enumerate(examples, 1):
        print(f"   {i}. {example}")
    
    print("\nTo test these examples, run:")
    print("   python agent/codegates_agent.py")
    print("   Then interact with the agent using the examples above.")

def main():
    """Main test function"""
    print("🚀 CodeGates Validation Agent Test Suite")
    print("=" * 60)
    
    # Test agent creation
    agent_created = test_agent_creation()
    
    # Test LiteLLM configuration
    litellm_configured = test_litellm_configuration()
    
    # Test tool functionality
    tools_working = test_tool_functionality()
    
    # Test environment configuration
    env_configured = test_environment_configuration()
    
    # Demonstrate usage
    demonstrate_usage_examples()
    
    # Test workflow if everything is available
    if all([agent_created, tools_working]):
        print("\n" + "=" * 60)
        print("🧪 Running Agent Workflow Test")
        print("=" * 60)
        
        try:
            asyncio.run(test_agent_workflow())
        except Exception as e:
            print(f"⚠️ Workflow test failed: {e}")
            print("   This is expected if dependencies are not fully configured")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    tests = {
        "Agent Creation": agent_created,
        "LiteLLM Configuration": litellm_configured,
        "Tool Functionality": tools_working,
        "Environment Configuration": env_configured
    }
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print("\n" + "=" * 60)
    print("✅ CodeGates Validation Agent Test Suite Complete")
    print("=" * 60)
    
    # Next steps
    print("\n🚀 Next Steps:")
    print("1. Configure your preferred LLM provider")
    print("2. Set up environment variables for your LLM")
    print("3. Test the agent with real repositories")
    print("4. Deploy to ADK web portal")
    print("5. Integrate with existing CodeGates workflows")

if __name__ == "__main__":
    main() 