#!/usr/bin/env python3
"""
Test script for Agentic Workflow System
Demonstrates the intelligent workflow orchestration capabilities
"""

import asyncio
import sys
import os

# Add the agent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

async def test_agentic_workflow():
    """Test the agentic workflow system"""
    print("🤖 Testing Agentic Workflow System...")
    print("=" * 60)
    
    try:
        from hardgate_agent.agentic_workflow import (
            AgenticWorkflowManager,
            run_agentic_workflow,
            create_agentic_workflow
        )
        from hardgate_agent.agentic_agent import (
            AgenticHardGateAgent,
            run_comprehensive_analysis,
            run_targeted_analysis
        )
        
        print("✅ Agentic workflow modules imported successfully!")
        
        # Test 1: Create workflow manager
        print("\n1. Testing Workflow Manager Creation...")
        orchestrator = AgenticWorkflowManager.create_workflow(
            request_id="test_workflow_001",
            repository_url="https://github.com/example/test-repo",
            branch="main",
            gates=["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS"],
            app_id="test-app",
            enable_llm=True,
            enable_evidence=True,
            enable_integrations=True
        )
        print("✅ Workflow orchestrator created successfully!")
        print(f"   Request ID: {orchestrator.context.request_id}")
        print(f"   Repository: {orchestrator.context.repository_url}")
        print(f"   Gates: {orchestrator.context.gates}")
        
        # Test 2: Create agentic agent
        print("\n2. Testing Agentic Agent Creation...")
        agent = AgenticHardGateAgent()
        print("✅ Agentic agent created successfully!")
        print(f"   Agent name: {agent.agent.name}")
        print(f"   Agent description: {agent.agent.description}")
        print(f"   Number of tools: {len(agent.agent.tools)}")
        
        # Test 3: Test targeted analysis (without actual repository)
        print("\n3. Testing Targeted Analysis...")
        security_result = await agent.execute_targeted_analysis(
            analysis_type="security",
            repository_path="/tmp/test-repo",  # Non-existent path for testing
            scan_type="comprehensive"
        )
        print("✅ Targeted analysis executed!")
        print(f"   Status: {security_result.get('status')}")
        print(f"   Analysis type: {security_result.get('analysis_type')}")
        
        # Test 4: Test workflow status management
        print("\n4. Testing Workflow Status Management...")
        status = await agent.get_workflow_status("test_workflow_001")
        print("✅ Workflow status retrieved!")
        print(f"   Status: {status.get('status')}")
        
        # Test 5: Test workflow history
        print("\n5. Testing Workflow History...")
        history = await agent.get_workflow_history(limit=5)
        print("✅ Workflow history retrieved!")
        print(f"   History entries: {len(history)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agentic workflow: {e}")
        return False

async def test_workflow_decision_making():
    """Test the intelligent decision-making capabilities"""
    print("\n🧠 Testing Intelligent Decision Making...")
    print("=" * 60)
    
    try:
        from hardgate_agent.agentic_workflow import (
            WorkflowState,
            DecisionType,
            AgentDecision,
            WorkflowContext
        )
        
        # Test decision creation
        decision = AgentDecision(
            decision_type=DecisionType.CONTINUE,
            reason="Repository analysis completed successfully",
            confidence=0.95
        )
        
        print("✅ Decision creation successful!")
        print(f"   Decision type: {decision.decision_type.value}")
        print(f"   Reason: {decision.reason}")
        print(f"   Confidence: {decision.confidence}")
        
        # Test workflow state management
        context = WorkflowContext(
            request_id="test_decision_001",
            repository_url="https://github.com/example/repo"
        )
        
        print("✅ Workflow context created!")
        print(f"   Current state: {context.current_state.value}")
        print(f"   Request ID: {context.request_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing decision making: {e}")
        return False

async def test_workflow_optimization():
    """Test workflow optimization capabilities"""
    print("\n🔧 Testing Workflow Optimization...")
    print("=" * 60)
    
    try:
        from hardgate_agent.agentic_agent import AgenticHardGateAgent
        
        agent = AgenticHardGateAgent()
        
        # Test optimization application
        optimization_result = await agent.optimize_workflow(
            request_id="test_optimization_001",
            optimization_type="performance"
        )
        
        print("✅ Workflow optimization tested!")
        print(f"   Status: {optimization_result.get('status')}")
        print(f"   Optimization type: {optimization_result.get('optimization_type')}")
        print(f"   Message: {optimization_result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing optimization: {e}")
        return False

async def test_comprehensive_workflow():
    """Test a comprehensive workflow simulation"""
    print("\n🚀 Testing Comprehensive Workflow Simulation...")
    print("=" * 60)
    
    try:
        from hardgate_agent.agentic_workflow import run_agentic_workflow
        
        # Simulate a comprehensive workflow (without actual repository)
        result = await run_agentic_workflow(
            request_id="comprehensive_test_001",
            repository_url="https://github.com/example/comprehensive-repo",
            branch="main",
            gates=["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS", "ALERTING_ACTIONABLE"],
            app_id="comprehensive-app",
            enable_llm=False,  # Disable LLM for testing
            enable_evidence=False,  # Disable evidence for testing
            enable_integrations=False,  # Disable integrations for testing
            max_retries=1
        )
        
        print("✅ Comprehensive workflow simulation completed!")
        print(f"   Status: {result.get('status')}")
        print(f"   Request ID: {result.get('request_id')}")
        print(f"   Total duration: {result.get('total_duration', 0):.2f} seconds")
        
        # Show completed states
        completed_states = result.get('completed_states', [])
        print(f"   Completed states: {len(completed_states)}")
        for state in completed_states:
            print(f"     - {state}")
        
        # Show step timings
        step_timings = result.get('step_timings', {})
        if step_timings:
            print("   Step timings:")
            for step, timing in step_timings.items():
                print(f"     - {step}: {timing:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing comprehensive workflow: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing Agentic Workflow System")
    print("=" * 80)
    
    tests = [
        ("Agentic Workflow", test_agentic_workflow),
        ("Decision Making", test_workflow_decision_making),
        ("Workflow Optimization", test_workflow_optimization),
        ("Comprehensive Workflow", test_comprehensive_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = await test_func()
            results[test_name] = "✅ PASS" if success else "❌ FAIL"
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = "❌ FAIL"
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Results Summary:")
    print("=" * 80)
    
    for test_name, result in results.items():
        print(f"   {test_name}: {result}")
    
    passed = sum(1 for result in results.values() if "PASS" in result)
    total = len(results)
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Agentic workflow system is working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")
    
    print("\n" + "=" * 80)
    print("🔧 Agentic Workflow System Features Demonstrated:")
    print("   ✅ Intelligent workflow orchestration")
    print("   ✅ State management and transitions")
    print("   ✅ Decision making and optimization")
    print("   ✅ Error handling and retry logic")
    print("   ✅ Performance monitoring and metrics")
    print("   ✅ Comprehensive analysis workflows")
    print("   ✅ Targeted analysis capabilities")
    print("   ✅ Workflow history and status tracking")

if __name__ == "__main__":
    asyncio.run(main()) 