#!/usr/bin/env python3
"""
Test script to verify LLM timeout fixes
"""

import asyncio
import os
from services.llm_service import LLMService


async def test_llm_timeout_fixes():
    """Test the LLM timeout fixes"""
    
    print("🧪 Testing LLM Timeout Fixes")
    print("=" * 50)
    
    # Test 1: Mock mode
    print("\n📝 Test 1: Mock Mode")
    print("-" * 30)
    
    llm_service = LLMService({
        "provider": "local",
        "model": "llama-3.2-3b-instruct",
        "base_url": "http://localhost:1234"
    })
    
    # Test with mock mode enabled
    mock_response = await llm_service.generate(
        "Generate patterns for security analysis",
        use_mock=True,
        scan_id="test_scan_123",
        node_name="TestNode"
    )
    
    print(f"✅ Mock response received: {len(mock_response)} characters")
    print(f"Response preview: {mock_response[:100]}...")
    
    # Test 2: Environment variable mock mode
    print("\n📝 Test 2: Environment Variable Mock Mode")
    print("-" * 30)
    
    # Set environment variable
    os.environ["LLM_USE_MOCK"] = "true"
    
    env_mock_response = await llm_service.generate(
        "Analyze code quality and provide recommendations",
        scan_id="test_scan_456",
        node_name="TestNode"
    )
    
    print(f"✅ Environment mock response received: {len(env_mock_response)} characters")
    print(f"Response preview: {env_mock_response[:100]}...")
    
    # Reset environment variable
    os.environ["LLM_USE_MOCK"] = "false"
    
    # Test 3: Timeout configuration
    print("\n📝 Test 3: Timeout Configuration")
    print("-" * 30)
    
    # Test with custom timeout
    try:
        timeout_response = await llm_service.generate(
            "Test prompt with custom timeout",
            timeout=10,  # Short timeout
            scan_id="test_scan_789",
            node_name="TestNode"
        )
        print(f"✅ Timeout test response: {len(timeout_response)} characters")
    except Exception as e:
        print(f"⚠️ Expected timeout or connection error: {e}")
    
    # Test 4: Fallback to mock on failure
    print("\n📝 Test 4: Fallback to Mock on Failure")
    print("-" * 30)
    
    # This should fail and fall back to mock
    fallback_response = await llm_service.generate(
        "Test fallback behavior",
        scan_id="test_scan_fallback",
        node_name="TestNode"
    )
    
    print(f"✅ Fallback response received: {len(fallback_response)} characters")
    print(f"Response preview: {fallback_response[:100]}...")
    
    # Test 5: Check logs
    print("\n📊 Test 5: Check LLM Logs")
    print("-" * 30)
    
    from services.llm_logger import LLMLogger
    
    llm_logger = LLMLogger()
    
    # Check logs for test scans
    for scan_id in ["test_scan_123", "test_scan_456", "test_scan_789", "test_scan_fallback"]:
        logs = llm_logger.get_scan_logs(scan_id)
        if logs:
            print(f"✅ Found {len(logs)} log entries for {scan_id}")
            for log in logs:
                print(f"   - {log['node_name']}: {log.get('error', 'Success')}")
        else:
            print(f"⚠️ No logs found for {scan_id}")
    
    print("\n🎉 LLM Timeout Fix Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_llm_timeout_fixes())
