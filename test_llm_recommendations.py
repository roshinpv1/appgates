#!/usr/bin/env python3
"""
Test script for LLM recommendations integration
"""

import os
import sys
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_llm_recommendations():
    """Test LLM recommendations with a mock failed gate"""
    
    print("🧪 Testing LLM Recommendations Integration")
    print("=" * 50)
    
    try:
        # Import the ValidateGatesNode class
        from nodes import ValidateGatesNode
        
        # Create a test instance
        validator = ValidateGatesNode()
        
        # Mock shared data
        shared = {
            "request": {
                "enable_llm_recommendations": True,
                "repository_url": "https://github.com/test/repo"
            },
            "llm_config": {
                "url": "https://api.openai.com/v1",  # Base URL, not full endpoint
                "api_key": os.getenv("OPENAI_API_KEY", "test-key"),
                "model": "gpt-3.5-turbo"
            },
            "repository": {
                "metadata": {
                    "primary_languages": ["java", "python"]
                }
            }
        }
        
        # Mock failed gate results
        gate_results = [
            {
                "gate": "AVOID_LOGGING_SECRETS",
                "status": "FAIL",
                "description": "Avoid logging sensitive information like passwords, tokens, or personal data",
                "patterns": ["log.*password", "logger.*secret", "console.*token"],
                "matches": [
                    {
                        "file": "src/auth/AuthService.java",
                        "line": 45,
                        "code": 'logger.info("User login: " + user.getPassword());'
                    },
                    {
                        "file": "src/config/Config.py",
                        "line": 23,
                        "code": 'print(f"API Key: {api_key}")'
                    }
                ],
                "score": 25.0
            },
            {
                "gate": "RETRY_LOGIC",
                "status": "WARNING",
                "description": "Implement retry logic for external service calls",
                "patterns": ["@Retryable", "retry", "tenacity"],
                "matches": [
                    {
                        "file": "src/services/ApiClient.java",
                        "line": 67,
                        "code": "response = httpClient.post(url, data);"
                    }
                ],
                "score": 60.0
            }
        ]
        
        print(f"📋 Testing with {len(gate_results)} mock gates")
        print("   - AVOID_LOGGING_SECRETS (FAIL)")
        print("   - RETRY_LOGIC (WARNING)")
        print()
        
        # Test LLM recommendations generation
        print("🤖 Generating LLM recommendations...")
        validator._generate_llm_recommendations(shared, gate_results)
        
        # Check results
        print("\n📊 Results:")
        for gate in gate_results:
            gate_name = gate["gate"]
            has_recommendation = gate.get("llm_recommendation") is not None
            is_generated = gate.get("recommendation_generated", False)
            
            status_icon = "✅" if has_recommendation else "❌"
            print(f"   {status_icon} {gate_name}: {'Recommendation generated' if has_recommendation else 'No recommendation'}")
            
            if has_recommendation:
                recommendation = gate["llm_recommendation"]
                print(f"      Preview: {recommendation[:100]}...")
                print()
        
        # Summary
        successful_recommendations = len([g for g in gate_results if g.get("llm_recommendation")])
        print(f"📈 Summary: {successful_recommendations}/{len(gate_results)} gates got LLM recommendations")
        
        if successful_recommendations > 0:
            print("✅ LLM recommendations integration working!")
        else:
            print("❌ LLM recommendations integration failed")
            
        return successful_recommendations > 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_llm_client_availability():
    """Test if LLM client can be created"""
    
    print("\n🔍 Testing LLM Client Availability")
    print("=" * 40)
    
    try:
        from utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider
        
        # Test environment-based client
        print("🌍 Checking environment-based LLM client...")
        env_client = create_llm_client_from_env()
        
        if env_client:
            print(f"✅ Environment client available: {env_client.config.provider.value}")
            print(f"   Model: {env_client.config.model}")
            print(f"   Available: {env_client.is_available()}")
        else:
            print("⚠️ No environment-based LLM client found")
        
        # Test manual client creation
        print("\n🔧 Testing manual client creation...")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if openai_key:
            try:
                config = LLMConfig(
                    provider=LLMProvider.OPENAI,
                    model="gpt-3.5-turbo",
                    api_key=openai_key,
                    temperature=0.3,
                    max_tokens=100
                )
                
                manual_client = LLMClient(config)
                print(f"✅ Manual OpenAI client created")
                print(f"   Available: {manual_client.is_available()}")
                
                # Test a simple call
                if manual_client.is_available():
                    print("🧪 Testing simple LLM call...")
                    response = manual_client.call_llm("Say 'Hello from CodeGates LLM test!'")
                    print(f"   Response: {response[:100]}...")
                    return True
                    
            except Exception as e:
                print(f"❌ Manual client test failed: {e}")
        else:
            print("⚠️ OPENAI_API_KEY not set, skipping manual test")
        
        return env_client is not None
        
    except ImportError as e:
        print(f"❌ LLM client import error: {e}")
        return False
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False

if __name__ == "__main__":
    print("🤖 CodeGates LLM Recommendations Test Suite")
    print("=" * 60)
    
    # Test 1: LLM Client availability
    client_ok = test_llm_client_availability()
    
    # Test 2: LLM Recommendations integration
    recommendations_ok = test_llm_recommendations()
    
    print("\n" + "=" * 60)
    print("📋 Final Results:")
    print(f"   LLM Client: {'✅ Working' if client_ok else '❌ Failed'}")
    print(f"   Recommendations: {'✅ Working' if recommendations_ok else '❌ Failed'}")
    
    if client_ok and recommendations_ok:
        print("\n🎉 All tests passed! LLM recommendations are ready to use.")
        print("\n💡 Next steps:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Enable LLM recommendations in scan request")
        print("   3. Run a scan with failed gates to see recommendations")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        
    sys.exit(0 if (client_ok and recommendations_ok) else 1) 