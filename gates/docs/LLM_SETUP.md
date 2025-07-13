# LLM Integration Setup Guide

This guide explains how to configure and use the comprehensive LLM integration in CodeGates v2.0, which supports local, enterprise, and Apigee-based LLM providers.

## Overview

CodeGates v2.0 includes a comprehensive LLM client that supports multiple providers:

- **OpenAI**: Cloud-based GPT models
- **Anthropic**: Claude models
- **Google Gemini**: Google's AI models
- **Local LLM**: OpenAI-compatible local servers (LM Studio, Ollama, etc.)
- **Ollama**: Direct Ollama integration
- **Enterprise LLM**: Custom enterprise endpoints with token management
- **Apigee Enterprise**: Enterprise LLM through Apigee proxy with advanced authentication

## Quick Start

### Auto-Detection

The system automatically detects available LLM providers based on environment variables:

```bash
# Run with auto-detection
python cli.py scan https://github.com/owner/repo
```

### Manual Provider Selection

```bash
# Use specific provider
python cli.py scan https://github.com/owner/repo --llm-provider openai --llm-model gpt-4
```

### Test LLM Integration

```bash
# Test auto-detection
python cli.py test-llm

# Test specific provider
python cli.py test-llm --llm-provider openai --verbose
```

## Provider Configuration

### 1. OpenAI

```bash
# Environment variables
export OPENAI_API_KEY="sk-your-api-key"
export OPENAI_MODEL="gpt-4"                    # Optional, default: gpt-4
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
export OPENAI_TEMPERATURE="0.1"               # Optional, default: 0.1
export OPENAI_MAX_TOKENS="4000"              # Optional, default: 4000
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider openai
```

### 2. Anthropic (Claude)

```bash
# Environment variables
export ANTHROPIC_API_KEY="sk-ant-your-api-key"
export ANTHROPIC_MODEL="claude-3-sonnet-20240229"  # Optional
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
export ANTHROPIC_TEMPERATURE="0.1"            # Optional
export ANTHROPIC_MAX_TOKENS="4000"           # Optional
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider anthropic
```

### 3. Google Gemini

```bash
# Environment variables
export GEMINI_API_KEY="your-gemini-api-key"
export GEMINI_MODEL="gemini-pro"              # Optional
export GEMINI_BASE_URL="https://generativelanguage.googleapis.com"  # Optional
export GEMINI_TEMPERATURE="0.1"              # Optional
export GEMINI_MAX_TOKENS="4000"             # Optional
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider gemini
```

### 4. Local LLM (OpenAI-compatible)

For local servers like LM Studio, Ollama in OpenAI mode, or custom local deployments:

```bash
# Environment variables
export LOCAL_LLM_URL="http://localhost:11434/v1"
export LOCAL_LLM_MODEL="meta-llama-3.1-8b-instruct"  # Optional
export LOCAL_LLM_API_KEY="not-needed"        # Optional, default: not-needed
export LOCAL_LLM_TEMPERATURE="0.1"           # Optional
export LOCAL_LLM_MAX_TOKENS="4000"          # Optional
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider local
```

### 5. Ollama (Direct)

For direct Ollama integration:

```bash
# Environment variables
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="meta-llama-3.1-8b-instruct"  # Optional
export OLLAMA_TEMPERATURE="0.1"              # Optional
export OLLAMA_NUM_PREDICT="4000"            # Optional
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider ollama
```

### 6. Enterprise LLM

For custom enterprise endpoints with token management:

```bash
# Environment variables
export ENTERPRISE_LLM_URL="https://your-enterprise-llm-endpoint"
export ENTERPRISE_LLM_TOKEN="your-initial-token"
export ENTERPRISE_LLM_MODEL="meta-llama-3.1-8b-instruct"  # Optional
export ENTERPRISE_LLM_API_KEY="your-api-key"  # Alternative to token
export ENTERPRISE_LLM_TEMPERATURE="0.1"      # Optional
export ENTERPRISE_LLM_MAX_TOKENS="4000"     # Optional

# Token refresh configuration (optional)
export ENTERPRISE_LLM_REFRESH_URL="https://your-token-refresh-endpoint"
export ENTERPRISE_LLM_CLIENT_ID="your-client-id"
export ENTERPRISE_LLM_CLIENT_SECRET="your-client-secret"
export ENTERPRISE_LLM_REFRESH_TOKEN="your-refresh-token"
export ENTERPRISE_LLM_TOKEN_EXPIRY_HOURS="24"  # Default: 24 hours

# Additional headers (optional)
export ENTERPRISE_LLM_HEADERS='{"X-Custom-Header": "value"}'
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider enterprise
```

### 7. Apigee Enterprise

For enterprise LLM through Apigee proxy with advanced authentication:

```bash
# Required Apigee configuration
export APIGEE_NONPROD_LOGIN_URL="https://your-apigee-login-url"
export APIGEE_CONSUMER_KEY="your-consumer-key"
export APIGEE_CONSUMER_SECRET="your-consumer-secret"

# Required enterprise configuration
export ENTERPRISE_BASE_URL="https://your-enterprise-base-url"
export WF_USE_CASE_ID="your-wf-use-case-id"
export WF_CLIENT_ID="your-wf-client-id"
export WF_API_KEY="your-wf-api-key"

# Optional model configuration
export APIGEE_MODEL="gpt-4"                  # Default: gpt-4
export APIGEE_TEMPERATURE="0.1"             # Default: 0.1
export APIGEE_MAX_TOKENS="4000"            # Default: 4000
```

**Usage:**
```bash
python cli.py scan https://github.com/owner/repo --llm-provider apigee
```

## Installation

### Base Requirements

```bash
pip install -r requirements.txt
```

### Provider-Specific Dependencies

Install only the dependencies you need for your specific LLM provider:

```bash
# OpenAI
pip install openai>=1.0.0

# Anthropic
pip install anthropic>=0.25.0

# Google Gemini
pip install google-generativeai>=0.3.0

# Ollama
pip install ollama>=0.1.0

# Apigee (requires httpx)
pip install httpx>=0.24.0

# For all providers
pip install openai anthropic google-generativeai ollama httpx
```

## Programmatic Usage

### Basic Usage

```python
from utils.llm_client import create_llm_client_from_env

# Auto-detect and create client
client = create_llm_client_from_env()

if client:
    response = client.call_llm("Analyze this code for security issues...")
    print(response)
```

### Manual Configuration

```python
from utils.llm_client import LLMClient, LLMConfig, LLMProvider

# Create specific configuration
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    api_key="sk-your-api-key",
    temperature=0.1,
    max_tokens=4000
)

client = LLMClient(config)
response = client.call_llm("Your prompt here...")
```

## Priority Order

When using auto-detection, the system checks providers in this order:

1. **OpenAI** (if `OPENAI_API_KEY` is set)
2. **Anthropic** (if `ANTHROPIC_API_KEY` is set)
3. **Google Gemini** (if `GEMINI_API_KEY` is set)
4. **Apigee** (if `APIGEE_NONPROD_LOGIN_URL` is set)
5. **Enterprise** (if `ENTERPRISE_LLM_URL` is set)
6. **Local** (if `LOCAL_LLM_URL` is set)
7. **Ollama** (if `OLLAMA_HOST` is set)

## Fallback Behavior

If no LLM provider is available or if the LLM call fails, the system automatically falls back to built-in pattern generation based on the hard gate definitions. This ensures that CodeGates always works, even without LLM integration.

## Advanced Configuration

### Custom Models

You can specify custom models for any provider:

```bash
# OpenAI with custom model
python cli.py scan https://github.com/owner/repo --llm-provider openai --llm-model gpt-4-turbo

# Local LLM with custom model
python cli.py scan https://github.com/owner/repo --llm-provider local --llm-model codellama:7b
```

### Temperature and Token Limits

```bash
# Adjust creativity and response length
python cli.py scan https://github.com/owner/repo \
  --llm-provider openai \
  --llm-temperature 0.3 \
  --llm-max-tokens 8000
```

### Multiple Configurations

You can set up multiple configurations and switch between them:

```bash
# Development environment
export OPENAI_API_KEY="sk-dev-key"
export LOCAL_LLM_URL="http://localhost:11434/v1"

# Production environment
export APIGEE_NONPROD_LOGIN_URL="https://prod-apigee-url"
export ENTERPRISE_BASE_URL="https://prod-enterprise-url"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install openai anthropic google-generativeai ollama httpx
   ```

2. **Authentication Failures**
   ```bash
   # Check API keys
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   
   # Test authentication
   python cli.py test-llm --llm-provider openai --verbose
   ```

3. **Network Issues**
   ```bash
   # Test connectivity
   curl -I https://api.openai.com/v1/models
   curl -I http://localhost:11434/api/tags
   ```

4. **Apigee Token Issues**
   ```bash
   # Check Apigee configuration
   echo $APIGEE_NONPROD_LOGIN_URL
   echo $APIGEE_CONSUMER_KEY
   echo $ENTERPRISE_BASE_URL
   
   # Test token generation
   python -c "
   from utils.llm_client import ApigeeTokenManager
   manager = ApigeeTokenManager()
   token = manager.get_apigee_token()
   print(f'Token: {token[:20]}...')
   "
   ```

### Debug Mode

Enable verbose logging for debugging:

```bash
python cli.py scan https://github.com/owner/repo --llm-provider openai --verbose
```

### Testing Individual Providers

```bash
# Test all providers
python cli.py test-llm --verbose

# Test specific provider
python cli.py test-llm --llm-provider apigee --verbose
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files for development
3. **Token Management**: Enterprise tokens are cached in memory only
4. **SSL Verification**: Apigee uses `verify=False` for development; enable for production
5. **Network Security**: All requests go through appropriate proxies and authentication

## Performance Tips

1. **Model Selection**: Smaller models are faster but may be less accurate
2. **Temperature**: Lower values (0.1) for consistent results, higher for creativity
3. **Token Limits**: Balance between comprehensive analysis and response time
4. **Caching**: Apigee and enterprise tokens are automatically cached
5. **Fallback**: Always available even without LLM integration

## Examples

### Complete Setup Examples

#### Local Development with Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.1:8b

# Configure environment
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama3.1:8b"

# Run scan
python cli.py scan https://github.com/owner/repo --llm-provider ollama
```

#### Enterprise Production with Apigee
```bash
# Configure Apigee
export APIGEE_NONPROD_LOGIN_URL="https://company-apigee.com/oauth/token"
export APIGEE_CONSUMER_KEY="your-consumer-key"
export APIGEE_CONSUMER_SECRET="your-consumer-secret"

# Configure enterprise endpoint
export ENTERPRISE_BASE_URL="https://company-llm.com/v1"
export WF_USE_CASE_ID="codegates-validation"
export WF_CLIENT_ID="your-client-id"
export WF_API_KEY="your-api-key"

# Run scan
python cli.py scan https://github.com/owner/repo --llm-provider apigee
```

This comprehensive LLM integration ensures that CodeGates can work with any LLM provider, from simple local setups to complex enterprise architectures with advanced authentication and token management. 