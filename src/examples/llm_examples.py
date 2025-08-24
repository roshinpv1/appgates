#!/usr/bin/env python3
"""
Examples of using LLM services and utilities in CodeGates
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from services.llm_service import LLMService, create_llm_service_from_env
from services.prompt_service import PromptService
from utils.llm_utils import (
    format_prompt_with_context, extract_json_from_response, 
    clean_llm_response, validate_llm_config, create_system_prompt
)


async def example_basic_llm_usage():
    """Basic LLM service usage example"""
    print("🔍 Example 1: Basic LLM Usage")
    
    # Create LLM service with local configuration
    config = {
        "provider": "local",
        "model": "llama-3.2-3b-instruct",
        "base_url": "http://localhost:1234",
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    llm_service = LLMService(config)
    
    # Test basic generation
    prompt = "Explain what code quality means in 2-3 sentences."
    try:
        response = await llm_service.generate(prompt)
        print(f"  Prompt: {prompt}")
        print(f"  Response: {clean_llm_response(response)}")
    except Exception as e:
        print(f"  ⚠️ LLM call failed: {e}")
    
    # Get provider info
    info = llm_service.get_provider_info()
    print(f"  Provider Info: {info}")
    print()


async def example_prompt_service_integration():
    """Example using prompt service with LLM"""
    print("🔍 Example 2: Prompt Service Integration")
    
    # Create services
    prompt_service = PromptService()
    llm_service = LLMService({"provider": "local", "base_url": "http://localhost:1234"})
    
    # Get a prompt template
    prompt_template = prompt_service.get_prompt("risk_assessment")
    if prompt_template:
        print(f"  Using prompt: {prompt_template.description}")
        
        # Format with sample data
        sample_context = {
            "failed_gates": ["STRUCTURED_LOGS", "INPUT_VALIDATION"],
            "partial_gates": ["TESTING_INFRASTRUCTURE"],
            "repo_context": "Python web application with Flask framework"
        }
        
        formatted_prompt = format_prompt_with_context(
            prompt_template.prompt_template, 
            sample_context
        )
        
        try:
            response = await llm_service.generate(formatted_prompt)
            print(f"  Response: {clean_llm_response(response)[:200]}...")
        except Exception as e:
            print(f"  ⚠️ LLM call failed: {e}")
    
    print()


def example_config_validation():
    """Example of LLM configuration validation"""
    print("🔍 Example 3: Configuration Validation")
    
    # Valid configuration
    valid_config = {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "sk-test-key",
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    errors = validate_llm_config(valid_config)
    print(f"  Valid config errors: {errors}")
    
    # Invalid configuration
    invalid_config = {
        "provider": "openai",
        # Missing api_key
        "temperature": 2.5,  # Out of range
        "max_tokens": -100   # Invalid
    }
    
    errors = validate_llm_config(invalid_config)
    print(f"  Invalid config errors: {errors}")
    print()


def example_response_processing():
    """Example of processing LLM responses"""
    print("🔍 Example 4: Response Processing")
    
    # Mock JSON response
    json_response = '''
    Here's the analysis:
    ```json
    {
        "risk_score": 7.5,
        "categories": ["security", "quality"],
        "recommendations": ["Implement input validation", "Add structured logging"]
    }
    ```
    That's the complete assessment.
    '''
    
    # Extract JSON
    extracted_json = extract_json_from_response(json_response)
    print(f"  Extracted JSON: {extracted_json}")
    
    # Clean response
    messy_response = "Here's what I think: The code quality is good overall. Let me know if you need clarification."
    cleaned = clean_llm_response(messy_response)
    print(f"  Original: {messy_response}")
    print(f"  Cleaned: {cleaned}")
    print()


def example_system_prompt_creation():
    """Example of creating structured system prompts"""
    print("🔍 Example 5: System Prompt Creation")
    
    task = "Analyze code for security vulnerabilities"
    output_format = "JSON with fields: vulnerabilities (array), risk_level (string), recommendations (array)"
    examples = [
        "Input: SQL query without parameterization → Output: {vulnerabilities: ['SQL Injection'], risk_level: 'high'}",
        "Input: Password stored in plain text → Output: {vulnerabilities: ['Plain Text Password'], risk_level: 'critical'}"
    ]
    
    system_prompt = create_system_prompt(task, output_format, examples)
    print(f"  System Prompt:\n{system_prompt}")
    print()


async def example_environment_config():
    """Example using environment-based configuration"""
    print("🔍 Example 6: Environment Configuration")
    
    # Try to create LLM service from environment
    try:
        llm_service = create_llm_service_from_env()
        if llm_service:
            info = llm_service.get_provider_info()
            print(f"  Environment LLM: {info}")
        else:
            print("  No environment LLM configuration found")
    except Exception as e:
        print(f"  Environment setup failed: {e}")
    
    print()


def example_multi_provider_setup():
    """Example showing multiple provider configurations"""
    print("🔍 Example 7: Multi-Provider Setup")
    
    providers_config = {
        "openai": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "your-openai-key",
            "temperature": 0.3
        },
        "anthropic": {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "api_key": "your-anthropic-key",
            "temperature": 0.3
        },
        "local": {
            "provider": "local",
            "model": "llama-3.2-3b-instruct",
            "base_url": "http://localhost:1234",
            "temperature": 0.3
        },
        "ollama": {
            "provider": "ollama",
            "model": "llama3.1",
            "base_url": "http://localhost:11434",
            "temperature": 0.3
        },
        "enterprise": {
            "provider": "enterprise",
            "model": "enterprise-model",
            "base_url": "http://enterprise.example.com",
            "temperature": 0.3
        }
    }
    
    for name, config in providers_config.items():
        try:
            llm_service = LLMService(config)
            info = llm_service.get_provider_info()
            print(f"  {name.capitalize()}: {info['model']} ({info['provider']})")
        except Exception as e:
            print(f"  {name.capitalize()}: Setup failed - {e}")
    
    print()


async def main():
    """Run all examples"""
    print("🚀 CodeGates LLM Service Examples")
    print("=" * 50)
    
    await example_basic_llm_usage()
    await example_prompt_service_integration()
    example_config_validation()
    example_response_processing()
    example_system_prompt_creation()
    await example_environment_config()
    example_multi_provider_setup()
    
    print("✅ All examples completed!")
    print("\n📖 Notes:")
    print("  - Local LLM examples require a running LM Studio or compatible server")
    print("  - OpenAI/Anthropic examples require valid API keys")
    print("  - Ollama examples require Ollama installation and running models")
    print("  - Enterprise LLM examples require enterprise token configuration")


if __name__ == "__main__":
    asyncio.run(main())
