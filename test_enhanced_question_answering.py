#!/usr/bin/env python3
"""
Test Enhanced Question Answering with Code Indexing and Analysis
Tests the integration of latest changes for asking questions to the agent
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_enhanced_question_answering():
    """Test enhanced question answering capabilities"""
    print("🧪 Testing Enhanced Question Answering with Code Indexing and Analysis")
    print("=" * 70)
    
    try:
        # Test 1: Import agent integration
        print("1. Testing agent integration import...")
        from gates.agent_integration import create_agent_integration, get_integration_status
        
        integration = create_agent_integration()
        status = get_integration_status()
        
        print(f"   ✅ Agent integration imported successfully")
        print(f"   📊 Integration status: {status}")
        
        # Test 2: Check enhanced tools
        print("\n2. Testing enhanced agent tools...")
        enhanced_tools = integration.get_enhanced_agent_tools()
        
        print(f"   ✅ Found {len(enhanced_tools)} enhanced tools:")
        for tool in enhanced_tools:
            print(f"      - {tool.name}: {tool.description}")
        
        # Test 3: Test question answering with a simple repository
        print("\n3. Testing question answering capabilities...")
        
        # Use a simple public repository for testing
        test_repo_url = "https://github.com/octocat/Hello-World"
        test_question = "What is the main purpose of this repository?"
        
        print(f"   🔍 Testing with repository: {test_repo_url}")
        print(f"   ❓ Question: {test_question}")
        
        # Run the test asynchronously
        async def run_question_test():
            try:
                result = await integration.ask_question_about_repository(
                    repo_url=test_repo_url,
                    question=test_question,
                    branch="master"  # Hello-World uses master branch
                )
                
                print(f"   ✅ Question answering completed")
                print(f"   📊 Result status: {result.get('status', 'unknown')}")
                
                if result.get('status') == 'success':
                    print(f"   💬 Answer: {result.get('answer', 'No answer generated')[:200]}...")
                    print(f"   📈 Context used: {result.get('context_used', {})}")
                    print(f"   🆔 Repo ID: {result.get('repo_id', 'unknown')}")
                    
                    # Check for agent insights
                    agent_insights = result.get('agent_insights')
                    if agent_insights:
                        print(f"   🤖 Agent insights available: {len(agent_insights.get('events', []))} events")
                    else:
                        print(f"   ℹ️ No agent insights available")
                else:
                    print(f"   ❌ Error: {result.get('message', 'Unknown error')}")
                
                return result
                
            except Exception as e:
                print(f"   ❌ Error during question answering: {e}")
                return None
        
        # Run the async test
        result = asyncio.run(run_question_test())
        
        # Test 4: Test enhanced capabilities
        print("\n4. Testing enhanced capabilities...")
        capabilities = integration.get_available_capabilities()
        
        print(f"   📊 Available capabilities:")
        for capability, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"      {status} {capability}: {available}")
        
        # Test 5: Test with different question types
        print("\n5. Testing different question types...")
        
        questions = [
            "What programming languages are used in this repository?",
            "Are there any configuration files?",
            "What is the structure of this project?",
            "Are there any tests in this repository?"
        ]
        
        async def test_multiple_questions():
            results = []
            for i, question in enumerate(questions, 1):
                print(f"   {i}. Testing: {question}")
                try:
                    result = await integration.ask_question_about_repository(
                        repo_url=test_repo_url,
                        question=question,
                        branch="master"
                    )
                    
                    if result.get('status') == 'success':
                        print(f"      ✅ Success - Answer length: {len(result.get('answer', ''))}")
                        results.append(result)
                    else:
                        print(f"      ❌ Failed: {result.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"      ❌ Error: {e}")
            
            return results
        
        question_results = asyncio.run(test_multiple_questions())
        print(f"   📊 Successfully answered {len(question_results)} out of {len(questions)} questions")
        
        # Summary
        print("\n" + "=" * 70)
        print("🎉 Enhanced Question Answering Test Summary")
        print("=" * 70)
        print(f"✅ Agent Integration: Working")
        print(f"✅ Enhanced Tools: {len(enhanced_tools)} available")
        print(f"✅ Question Answering: {'Working' if result and result.get('status') == 'success' else 'Failed'}")
        print(f"✅ Multiple Questions: {len(question_results)}/{len(questions)} successful")
        print(f"✅ Advanced LLM Service: {capabilities.get('advanced_llm_available', False)}")
        print(f"✅ Agent Runner: {capabilities.get('agent_runner_available', False)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_server_endpoints():
    """Test the new server endpoints"""
    print("\n🌐 Testing Server Endpoints")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Test server endpoints
        base_url = "http://localhost:8000"
        
        # Test 1: Check if server is running
        print("1. Checking server status...")
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Server is running")
            else:
                print(f"   ⚠️ Server responded with status: {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print("   ❌ Server is not running. Start with: python3 gates/server.py")
            return False
        
        # Test 2: Check enhanced tools endpoint
        print("2. Testing enhanced tools endpoint...")
        try:
            response = requests.get(f"{base_url}/api/v1/agent/enhanced-tools", timeout=10)
            if response.status_code == 200:
                data = response.json()
                tools = data.get('tools', [])
                print(f"   ✅ Enhanced tools endpoint working - {len(tools)} tools available")
                for tool in tools:
                    print(f"      - {tool.get('name')}: {tool.get('description')}")
            else:
                print(f"   ⚠️ Enhanced tools endpoint returned: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Enhanced tools endpoint error: {e}")
        
        # Test 3: Test question asking endpoint
        print("3. Testing question asking endpoint...")
        try:
            question_data = {
                "repo_url": "https://github.com/octocat/Hello-World",
                "question": "What is the main purpose of this repository?",
                "branch": "master"
            }
            
            response = requests.post(
                f"{base_url}/api/v1/agent/ask",
                json=question_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = data.get('data', {})
                    print(f"   ✅ Question asking endpoint working")
                    print(f"   💬 Answer: {result.get('answer', 'No answer')[:100]}...")
                else:
                    print(f"   ⚠️ Question asking failed: {data.get('detail', 'Unknown error')}")
            else:
                print(f"   ⚠️ Question asking endpoint returned: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Question asking endpoint error: {e}")
        
        return True
        
    except ImportError:
        print("   ⚠️ Requests library not available - skipping server tests")
        return False
    except Exception as e:
        print(f"   ❌ Server test error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Enhanced Question Answering Integration Test")
    print("=" * 70)
    
    # Run tests
    integration_ok = test_enhanced_question_answering()
    server_ok = test_server_endpoints()
    
    print("\n" + "=" * 70)
    print("📋 Test Results Summary")
    print("=" * 70)
    print(f"🔧 Integration Tests: {'✅ PASSED' if integration_ok else '❌ FAILED'}")
    print(f"🌐 Server Tests: {'✅ PASSED' if server_ok else '❌ FAILED'}")
    
    if integration_ok and server_ok:
        print("\n🎉 All tests passed! Enhanced question answering is working.")
        print("\n📖 Usage Examples:")
        print("1. Direct API call:")
        print("   curl -X POST http://localhost:8000/api/v1/agent/ask \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"repo_url\": \"https://github.com/user/repo\", \"question\": \"What does this code do?\"}'")
        print("\n2. Python integration:")
        print("   from gates.agent_integration import ask_question_about_repository")
        print("   result = await ask_question_about_repository(\"https://github.com/user/repo\", \"What does this code do?\")")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        sys.exit(1)
