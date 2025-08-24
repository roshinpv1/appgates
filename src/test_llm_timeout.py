
#!/usr/bin/env python3
"""
Test script to check LLM timeout issues
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from services.llm_service import LLMService


async def test_llm_timeout():
    """Test LLM service with timeout"""
    
    # Test configuration
    config = {
        "provider": "local",
        "model": "gpt-3.5-turbo",
        "base_url": "http://localhost:11434/v1",  # Ollama default
        "temperature": 0.3,
        "max_tokens": 1000,
        "timeout": 10,  # 10 second timeout
        "max_retries": 1
    }
    
    print("🧪 Testing LLM Service Timeout")
    print(f"   Config: {config}")
    
    try:
        # Initialize LLM service
        llm_service = LLMService(config)
        
        # Test simple prompt
        test_prompt = "Hello, please respond with a short message."
        
        print(f"   📞 Calling LLM with prompt: '{test_prompt}'")
        print(f"   ⏱️  Timeout set to: {config['timeout']} seconds")
        
        start_time = time.time()
        
        # Call LLM with timeout
        response = await asyncio.wait_for(
            llm_service.generate(test_prompt),
            timeout=config['timeout'] + 5  # Add 5 seconds buffer
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"   ✅ LLM response received in {elapsed_time:.2f}s")
        print(f"   📝 Response: {response[:100]}...")
        
        return True
        
    except asyncio.TimeoutError:
        print(f"   ❌ LLM call timed out after {config['timeout']} seconds")
        return False
    except Exception as e:
        print(f"   ❌ LLM call failed: {e}")
        return False


async def test_llm_with_fallback():
    """Test LLM with fallback to mock response"""
    
    print("\n🧪 Testing LLM with fallback")
    
    # Test configuration with very short timeout
    config = {
        "provider": "local",
        "model": "gpt-3.5-turbo",
        "base_url": "http://localhost:11434/v1",
        "temperature": 0.3,
        "max_tokens": 1000,
        "timeout": 2,  # Very short timeout
        "max_retries": 1
    }
    
    try:
        llm_service = LLMService(config)
        
        # Test prompt that might take long
        test_prompt = """
        Analyze the following project and generate applicable security, performance, and quality patterns:
        
        Project Summary:
        - Repository: https://github.com/apache/fineract
        - Branch: develop
        - Total Files: 6211
        - Total Lines: 977899
        - Languages: java, xml, properties
        - Dependencies: maven, spring
        - Build Files: pom.xml, build.gradle
        - Config Files: application.properties, logback.xml
        
        Please generate patterns in JSON format.
        """
        
        print(f"   📞 Calling LLM with complex prompt")
        print(f"   ⏱️  Timeout set to: {config['timeout']} seconds")
        
        start_time = time.time()
        
        response = await asyncio.wait_for(
            llm_service.generate(test_prompt),
            timeout=config['timeout'] + 5
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"   ✅ LLM response received in {elapsed_time:.2f}s")
        print(f"   📝 Response length: {len(response)} characters")
        
        return True
        
    except asyncio.TimeoutError:
        print(f"   ❌ LLM call timed out after {config['timeout']} seconds")
        print(f"   💡 Consider using a mock response or shorter timeout")
        return False
    except Exception as e:
        print(f"   ❌ LLM call failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting LLM Timeout Tests")
    
    # Test 1: Simple prompt
    result1 = asyncio.run(test_llm_timeout())
    
    # Test 2: Complex prompt with fallback
    result2 = asyncio.run(test_llm_with_fallback())
    
    print(f"\n📊 Test Results:")
    print(f"   Simple prompt: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"   Complex prompt: {'✅ PASS' if result2 else '❌ FAIL'}")
    
    if not result1 or not result2:
        print(f"\n💡 Recommendations:")
        print(f"   - Check if Ollama is running on localhost:11434")
        print(f"   - Consider increasing timeout in LLM config")
        print(f"   - Use mock responses for development")
        print(f"   - Check network connectivity")
