#!/usr/bin/env python3
"""
Test script to verify local LLM configuration and connectivity.
This will help you ensure your local LLM is properly set up and being invoked.
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_environment_variables():
    """Test if LLM environment variables are set correctly"""
    print("🔧 Testing Environment Variables")
    print("=" * 50)
    
    # Check for local LLM configuration
    local_vars = {
        'LOCAL_LLM_URL': os.getenv('LOCAL_LLM_URL', 'http://localhost:1234/v1'),
        'LOCAL_LLM_MODEL': os.getenv('LOCAL_LLM_MODEL', 'meta-llama-3.1-8b-instruct'),
        'LOCAL_LLM_API_KEY': os.getenv('LOCAL_LLM_API_KEY', 'not-needed'),
        'LOCAL_LLM_TEMPERATURE': os.getenv('LOCAL_LLM_TEMPERATURE', '0.1'),
        'LOCAL_LLM_MAX_TOKENS': os.getenv('LOCAL_LLM_MAX_TOKENS', '4000'),
    }
    
    print("Local LLM Configuration:")
    for key, value in local_vars.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")
    
    # Check alternative configurations
    alternative_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'OLLAMA_HOST': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
        'OLLAMA_MODEL': os.getenv('OLLAMA_MODEL'),
    }
    
    print("\nAlternative LLM Configurations:")
    for key, value in alternative_vars.items():
        status = "✅" if value else "⚪"
        print(f"  {status} {key}: {value or 'Not set'}")
    
    return local_vars

def test_local_llm_service(base_url, model_name):
    """Test connectivity to local LLM service"""
    print(f"\n🌐 Testing Local LLM Service at {base_url}")
    print("=" * 50)
    
    # Test 1: Check if service is running
    try:
        # Try different endpoints that local LLM services typically expose
        endpoints_to_try = [
            f"{base_url.rstrip('/')}/models",
            f"{base_url.rstrip('/')}/v1/models", 
            f"{base_url.rstrip('/')}/health",
            f"{base_url.rstrip('/')}/api/health",
        ]
        
        service_available = False
        for endpoint in endpoints_to_try:
            try:
                print(f"   Trying: {endpoint}")
                response = requests.get(endpoint, timeout=10)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    service_available = True
                    print(f"   ✅ Service available at {endpoint}")
                    
                    # Try to parse response to see available models
                    try:
                        data = response.json()
                        if 'data' in data and isinstance(data['data'], list):
                            models = [model.get('id', 'unnamed') for model in data['data']]
                            print(f"   📋 Available models: {models}")
                            
                            if model_name in models:
                                print(f"   ✅ Target model '{model_name}' is available")
                            else:
                                print(f"   ⚠️ Target model '{model_name}' not found")
                                print(f"   💡 Suggestion: Use one of the available models")
                        elif isinstance(data, list):
                            print(f"   📋 Response: {data}")
                        else:
                            print(f"   📋 Service response: {data}")
                    except json.JSONDecodeError:
                        print(f"   📄 Non-JSON response: {response.text[:200]}...")
                    break
                    
            except requests.RequestException as e:
                print(f"   ❌ Failed: {str(e)}")
                continue
        
        if not service_available:
            print(f"   ❌ No LLM service found at {base_url}")
            print(f"   💡 Make sure your local LLM server is running")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False
    
    # Test 2: Try a simple completion request
    try:
        print(f"\n   🤖 Testing model completion...")
        completion_url = f"{base_url.rstrip('/')}/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from CodeGates!' and nothing else."}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Add API key if needed (some local services require it)
        api_key = os.getenv('LOCAL_LLM_API_KEY')
        if api_key and api_key != 'not-needed':
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.post(completion_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {}).get('content', '')
                print(f"   ✅ Model response: {message.strip()}")
                print(f"   ✅ Local LLM is working correctly!")
                return True
            else:
                print(f"   ⚠️ Unexpected response format: {result}")
                return False
        else:
            print(f"   ❌ Completion request failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Completion test failed: {e}")
        return False

def test_codegates_llm_integration():
    """Test CodeGates LLM integration"""
    print(f"\n🎯 Testing CodeGates LLM Integration")
    print("=" * 50)
    
    try:
        from codegates.utils.env_loader import EnvironmentLoader
        from codegates.core.llm_analyzer import LLMConfig, LLMProvider, LLMIntegrationManager
        
        # Load environment
        env_loader = EnvironmentLoader()
        env_loader.load_environment(force_reload=True)
        
        # Get preferred provider
        preferred_provider = env_loader.get_preferred_llm_provider()
        print(f"   📡 Preferred provider: {preferred_provider}")
        
        if not preferred_provider:
            print(f"   ❌ No LLM provider configured")
            return False
        
        # Get provider configuration
        provider_config = env_loader.get_llm_config(preferred_provider)
        print(f"   🔧 Provider config: {provider_config}")
        
        # Create LLM configuration
        if preferred_provider == 'local':
            llm_config = LLMConfig(
                provider=LLMProvider.LOCAL,
                model=provider_config['model'],
                api_key=provider_config['api_key'],
                base_url=provider_config['base_url'],
                temperature=provider_config['temperature'],
                max_tokens=provider_config['max_tokens']
            )
        elif preferred_provider == 'openai':
            llm_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=provider_config['model'],
                api_key=provider_config['api_key'],
                base_url=provider_config.get('base_url'),
                temperature=provider_config['temperature'],
                max_tokens=provider_config['max_tokens']
            )
        else:
            print(f"   ⚠️ Provider {preferred_provider} not configured for this test")
            return False
        
        # Test LLM manager
        llm_manager = LLMIntegrationManager(llm_config)
        
        if llm_manager.is_enabled():
            print(f"   ✅ LLM Integration Manager initialized successfully")
            
            # Test a simple enhancement
            test_enhancement = llm_manager.enhance_gate_validation(
                gate_name="structured_logs",
                matches=[{"match": "logger.info('test message')"}],
                language="python", 
                detected_technologies={"logging": ["python-logging"]}
            )
            
            if test_enhancement and 'enhanced_quality_score' in test_enhancement:
                print(f"   ✅ LLM enhancement successful!")
                print(f"   📊 Quality score: {test_enhancement['enhanced_quality_score']}")
                print(f"   📝 Recommendations: {len(test_enhancement.get('llm_recommendations', []))}")
                return True
            else:
                print(f"   ⚠️ LLM enhancement returned empty result")
                return False
        else:
            print(f"   ❌ LLM Integration Manager failed to initialize")
            return False
            
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print(f"   💡 Make sure CodeGates is properly installed")
        return False
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def check_common_local_llm_services():
    """Check for common local LLM services"""
    print(f"\n🔍 Checking Common Local LLM Services")
    print("=" * 50)
    
    services = [
        {"name": "LM Studio", "url": "http://localhost:1234/v1"},
        {"name": "Ollama", "url": "http://localhost:11434"},
        {"name": "text-generation-webui", "url": "http://localhost:5000"},
        {"name": "LocalAI", "url": "http://localhost:8080"},
        {"name": "Oobabooga", "url": "http://localhost:5000/v1"},
        {"name": "Custom OpenAI-compatible", "url": "http://localhost:8000/v1"},
    ]
    
    found_services = []
    
    for service in services:
        try:
            # Try to connect to the service
            response = requests.get(f"{service['url']}/models", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {service['name']} detected at {service['url']}")
                found_services.append(service)
            else:
                print(f"   ⚪ {service['name']} - no response at {service['url']}")
        except requests.RequestException:
            print(f"   ⚪ {service['name']} - not running at {service['url']}")
    
    if found_services:
        print(f"\n   🎉 Found {len(found_services)} local LLM service(s)")
        return found_services
    else:
        print(f"\n   ❌ No local LLM services detected")
        print(f"   💡 Start one of these services:")
        print(f"      - LM Studio: https://lmstudio.ai/")
        print(f"      - Ollama: https://ollama.com/")
        print(f"      - text-generation-webui: https://github.com/oobabooga/text-generation-webui")
        return []

def provide_setup_instructions():
    """Provide setup instructions for local LLM"""
    print(f"\n💡 Local LLM Setup Instructions")
    print("=" * 50)
    
    print("""
1. 🚀 Quick Setup with LM Studio (Recommended):
   - Download: https://lmstudio.ai/
   - Install and open LM Studio
   - Download a model (e.g., meta-llama-3.1-8b-instruct)
   - Start the local server (port 1234)
   
2. 📝 Configure Environment Variables:
   Create a .env file in your project root:
   
   LOCAL_LLM_URL=http://localhost:1234/v1
   LOCAL_LLM_MODEL=meta-llama-3.1-8b-instruct
   LOCAL_LLM_API_KEY=not-needed
   LOCAL_LLM_TEMPERATURE=0.1
   LOCAL_LLM_MAX_TOKENS=4000

3. 🦙 Alternative: Ollama Setup:
   - Install: curl -fsSL https://ollama.com/install.sh | sh
   - Pull model: ollama pull meta-llama-3.1-8b-instruct
   - Update .env:
     OLLAMA_HOST=http://localhost:11434
     OLLAMA_MODEL=meta-llama-3.1-8b-instruct

4. ✅ Verify Setup:
   - Run this test script again
   - Or run: python -m codegates.cli test-llm --llm-provider local
   
5. 🎯 Use in CodeGates:
   - API: POST /api/v1/scan (LLM will be auto-detected)
   - CLI: codegates scan . --enable-llm
""")

def main():
    """Main test function"""
    print("🤖 CodeGates Local LLM Test Suite")
    print("=" * 60)
    
    # Test 1: Environment Variables
    env_vars = test_environment_variables()
    
    # Test 2: Check for running services
    found_services = check_common_local_llm_services()
    
    # Test 3: Test specific local LLM
    base_url = env_vars['LOCAL_LLM_URL']
    model_name = env_vars['LOCAL_LLM_MODEL']
    
    service_ok = test_local_llm_service(base_url, model_name)
    
    # Test 4: Test CodeGates integration
    integration_ok = test_codegates_llm_integration()
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    print(f"Environment Variables: ✅")
    print(f"Local LLM Service: {'✅' if service_ok else '❌'}")
    print(f"CodeGates Integration: {'✅' if integration_ok else '❌'}")
    
    if service_ok and integration_ok:
        print(f"\n🎉 SUCCESS: Local LLM is properly configured and working!")
        print(f"   Your local LLM will be used for enhanced code analysis.")
        print(f"   Model: {model_name}")
        print(f"   Endpoint: {base_url}")
    else:
        print(f"\n⚠️ ISSUES DETECTED: Local LLM needs configuration")
        provide_setup_instructions()

if __name__ == "__main__":
    main() 