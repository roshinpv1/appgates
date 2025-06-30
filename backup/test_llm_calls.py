#!/usr/bin/env python3
"""
Test script to verify if LLM calls are actually being made
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append('.')

try:
    from codegates.core.llm_analyzer import LLMIntegrationManager, LLMConfig, LLMProvider
    from codegates.core.gate_validator import GateValidator
    from codegates.models import ScanConfig, Language
    from codegates.utils.env_loader import EnvironmentLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def test_llm_availability():
    """Test if LLM is configured and available"""
    
    print("🔍 Testing LLM Availability")
    print("=" * 50)
    
    # Load environment
    env_loader = EnvironmentLoader()
    env_loader.load_environment(force_reload=True)
    
    # Check for LLM configuration
    print("\n📋 Environment Configuration Check:")
    
    # Check for various LLM API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") 
    gemini_key = os.getenv("GEMINI_API_KEY")
    local_url = os.getenv("LOCAL_LLM_URL") or os.getenv("OPENAI_URL")
    
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Not set'}")
    print(f"   GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"   LOCAL_LLM_URL: {'✅ Set' if local_url else '❌ Not set'}")
    
    # Get preferred provider
    preferred_provider = env_loader.get_preferred_llm_provider()
    print(f"   Preferred Provider: {preferred_provider or 'None detected'}")
    
    if not preferred_provider:
        print("\n❌ No LLM provider configured!")
        print("   To enable LLM calls, set one of the following in your environment:")
        print("   - OPENAI_API_KEY=your-openai-key")
        print("   - ANTHROPIC_API_KEY=your-anthropic-key") 
        print("   - GEMINI_API_KEY=your-gemini-key")
        print("   - LOCAL_LLM_URL=http://localhost:1234/v1 (for local LLM)")
        return False
    
    # Get provider configuration
    provider_config = env_loader.get_llm_config(preferred_provider)
    
    if not provider_config:
        print(f"\n❌ Configuration not found for provider: {preferred_provider}")
        return False
    
    print(f"\n✅ LLM Provider Configuration Found:")
    print(f"   Provider: {preferred_provider}")
    print(f"   Model: {provider_config.get('model', 'Unknown')}")
    print(f"   Base URL: {provider_config.get('base_url', 'Default')}")
    print(f"   Temperature: {provider_config.get('temperature', 0.1)}")
    print(f"   Max Tokens: {provider_config.get('max_tokens', 8000)}")
    
    return True, preferred_provider, provider_config


def test_llm_manager():
    """Test LLM manager initialization and availability"""
    
    print("\n🤖 Testing LLM Manager")
    print("=" * 50)
    
    # Load environment first
    env_loader = EnvironmentLoader()
    env_loader.load_environment(force_reload=True)
    
    # Get preferred provider
    preferred_provider = env_loader.get_preferred_llm_provider()
    
    if not preferred_provider:
        print("❌ No LLM provider configured - skipping LLM manager test")
        return None
    
    # Get provider configuration
    provider_config = env_loader.get_llm_config(preferred_provider)
    
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
    elif preferred_provider == 'anthropic':
        llm_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model=provider_config['model'],
            api_key=provider_config['api_key'],
            temperature=provider_config['temperature'],
            max_tokens=provider_config['max_tokens']
        )
    else:
        print(f"❌ Provider {preferred_provider} not supported in this test")
        return None
    
    # Create LLM manager
    print(f"🔧 Creating LLM manager with {preferred_provider} provider...")
    llm_manager = LLMIntegrationManager(llm_config)
    
    # Test availability
    print("🔍 Checking LLM availability...")
    is_enabled = llm_manager.is_enabled()
    
    print(f"   LLM Enabled: {'✅ Yes' if is_enabled else '❌ No'}")
    
    if is_enabled:
        # Get detailed status
        status = llm_manager.get_availability_status()
        print(f"   Cached Result: {status.get('cached_result', 'None')}")
        print(f"   Last Check: {status.get('last_check', 'Never')}")
        print(f"   Cache Valid: {status.get('cache_valid', False)}")
        
        # Force a fresh check
        print("🔄 Forcing fresh availability check...")
        fresh_result = llm_manager.force_availability_check()
        print(f"   Fresh Check Result: {'✅ Available' if fresh_result else '❌ Unavailable'}")
    
    return llm_manager if is_enabled else None


def test_actual_llm_call():
    """Test making an actual LLM call"""
    
    print("\n🚀 Testing Actual LLM Call")
    print("=" * 50)
    
    llm_manager = test_llm_manager()
    
    if not llm_manager:
        print("❌ LLM manager not available - cannot test actual calls")
        return False
    
    print("📝 Preparing test data...")
    
    # Create a simple test case
    test_matches = [
        {
            'file_name': 'test.py',
            'line_number': 10,
            'matched_text': 'logger.info("User login successful")',
            'full_line': '    logger.info("User login successful")',
            'severity': 'LOW',
            'priority': 3,
            'category': 'logging',
            'pattern_type': 'structured_logging',
            'language': 'python',
            'suggested_fix': 'Use structured logging with context fields',
            'function_context': {
                'function_name': 'login_user',
                'line_number': 8,
                'signature': 'def login_user(username, password):'
            }
        }
    ]
    
    test_technologies = {
        'logging': ['python-logging'],
        'web_frameworks': ['flask']
    }
    
    test_recommendations = [
        "Implement structured logging with JSON format",
        "Add correlation IDs to log messages"
    ]
    
    print("🤖 Making LLM call for gate validation enhancement...")
    
    try:
        # This should make an actual LLM call
        enhancement = llm_manager.enhance_gate_validation(
            gate_name="structured_logs",
            matches=test_matches,
            language=Language.PYTHON,
            detected_technologies=test_technologies,
            base_recommendations=test_recommendations
        )
        
        print("✅ LLM call completed successfully!")
        print(f"   Enhanced Quality Score: {enhancement.get('enhanced_quality_score', 'None')}")
        print(f"   LLM Recommendations: {len(enhancement.get('llm_recommendations', []))}")
        print(f"   Security Insights: {len(enhancement.get('security_insights', []))}")
        print(f"   Technology Insights: {len(enhancement.get('technology_insights', {}))}")
        
        # Show sample recommendations
        llm_recs = enhancement.get('llm_recommendations', [])
        if llm_recs:
            print("\n📋 Sample LLM Recommendations:")
            for i, rec in enumerate(llm_recs[:3], 1):
                print(f"   {i}. {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM call failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if it's a configuration issue
        if "api_key" in str(e).lower():
            print("   This appears to be an API key issue")
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            print("   This appears to be a connection issue")
        elif "model" in str(e).lower():
            print("   This appears to be a model availability issue")
        
        return False


def main():
    """Main test function"""
    
    print("🧪 LLM Call Verification Test")
    print("=" * 60)
    
    # Test 1: Check LLM availability
    try:
        result = test_llm_availability()
        if not result:
            print("\n❌ LLM not configured - no calls will be made")
            return
    except Exception as e:
        print(f"❌ LLM availability test failed: {e}")
        return
    
    # Test 2: Test LLM manager
    try:
        llm_manager = test_llm_manager()
        if not llm_manager:
            print("\n❌ LLM manager not available - no calls will be made")
            return
    except Exception as e:
        print(f"❌ LLM manager test failed: {e}")
        return
    
    # Test 3: Test actual LLM call
    try:
        success = test_actual_llm_call()
        if success:
            print("\n🎉 LLM calls are working correctly!")
            print("   The system WILL make actual LLM calls during analysis.")
        else:
            print("\n❌ LLM calls are NOT working")
            print("   The system will fall back to static recommendations.")
    except Exception as e:
        print(f"❌ LLM call test failed: {e}")
        print("   The system will fall back to static recommendations.")


if __name__ == "__main__":
    main() 