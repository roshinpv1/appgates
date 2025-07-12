# Enterprise LLM Integration with Apigee Authentication

This document describes how to configure and use the Enterprise LLM integration with Apigee authentication in CodeGates.

## Overview

The Enterprise LLM integration provides secure access to enterprise-grade language models through Apigee proxy authentication. This ensures that all LLM requests are properly authenticated and routed through your enterprise infrastructure.

## Features

- **Apigee Token Management**: Automatic token generation and refresh
- **Thread-Safe Caching**: Token caching with thread safety
- **Enterprise Headers**: Proper enterprise request headers and correlation IDs
- **Error Handling**: Comprehensive error handling and logging
- **SSL Support**: Support for enterprise SSL certificates

## Environment Variables

### Required Variables

```bash
# Apigee Authentication
APIGEE_NONPROD_LOGIN_URL=https://your-apigee-login-url
APIGEE_CONSUMER_KEY=your-consumer-key
APIGEE_CONSUMER_SECRET=your-consumer-secret

# Enterprise Configuration
ENTERPRISE_BASE_URL=https://your-enterprise-base-url
WF_USE_CASE_ID=your-wf-use-case-id
WF_CLIENT_ID=your-wf-client-id
WF_API_KEY=your-wf-api-key

# LLM Configuration
APIGEE_MODEL=gpt-4
APIGEE_TEMPERATURE=0.1
APIGEE_MAX_TOKENS=4000
```

### Optional Variables

```bash
# Proxy Configuration (if needed)
ENTERPRISE_LLM_PROXY=proxy.company.com:8080

# SSL Configuration
ENTERPRISE_LLM_VERIFY_SSL=false  # Set to true for production
```

## Usage

### 1. Basic Usage

```python
from codegates.core.enterprise_llm import get_enterprise_analyzer

# Get the enterprise analyzer
analyzer = get_enterprise_analyzer()

# Analyze a gate implementation
result = analyzer.analyze_gate_implementation(
    gate_name="structured_logs",
    code_samples=["logger.info('User logged in', user_id=123)"],
    language=Language.PYTHON,
    technologies={"logging": ["python-logging"]}
)
```

### 2. Direct LLM Client Usage

```python
from codegates.core.enterprise_llm import EnterpriseLLMClient

# Initialize the client
client = EnterpriseLLMClient()

# Call the LLM directly
response = client.call_enterprise_llm(
    prompt="Analyze this code for security issues...",
    model="gpt-4",
    temperature=0.1,
    max_tokens=4000
)
```

### 3. CLI Usage

```bash
# Test the Apigee LLM provider
codegates test-llm --llm-provider apigee --llm-model gpt-4

# Run a scan with Apigee LLM
codegates scan /path/to/repo --llm-provider apigee
```

## Architecture

### Components

1. **ApigeeTokenManager**: Handles token generation and refresh
2. **EnterpriseLLMClient**: Manages API calls with proper headers
3. **EnterpriseLLMAnalyzer**: Provides high-level analysis interface

### Token Flow

1. **Initial Request**: Client requests a token from Apigee
2. **Token Caching**: Token is cached with expiry tracking
3. **Automatic Refresh**: Token is refreshed before expiry
4. **API Calls**: All LLM calls use the cached token

### Request Headers

Each request includes enterprise-specific headers:

```python
headers = {
    "x-w-request-date": "2024-01-01T00:00:00Z",
    "Authorization": "Bearer <apigee_token>",
    "x-request-id": "<uuid>",
    "x-correlation-id": "<uuid>",
    "x-wf-client-id": "<client_id>",
    "x-wf-api-key": "<api_key>",
    "x-wf-usecase-id": "<use_case_id>"
}
```

## Error Handling

### Common Errors

1. **Token Generation Failed**
   - Check Apigee credentials
   - Verify network connectivity
   - Check SSL certificate configuration

2. **API Call Failed**
   - Verify enterprise base URL
   - Check request headers
   - Validate model name

3. **SSL Certificate Issues**
   - Set `verify=False` for development
   - Configure proper CA certificates for production

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **Token Security**: Tokens are cached in memory only
2. **SSL Verification**: Disabled for development, enable for production
3. **Credential Storage**: Use environment variables, never hardcode
4. **Network Security**: All requests go through enterprise proxy

## Production Deployment

1. **SSL Certificates**: Configure proper CA certificates
2. **Token Refresh**: Ensure token refresh works in production
3. **Monitoring**: Add monitoring for token refresh failures
4. **Logging**: Configure appropriate log levels

## Troubleshooting

### Token Issues

```bash
# Check environment variables
echo $APIGEE_NONPROD_LOGIN_URL
echo $APIGEE_CONSUMER_KEY
echo $APIGEE_CONSUMER_SECRET

# Test token generation
python -c "
from codegates.core.enterprise_llm import ApigeeTokenManager
manager = ApigeeTokenManager()
token = manager.get_apigee_token()
print(f'Token: {token[:20]}...')
"
```

### Network Issues

```bash
# Test connectivity
curl -k $APIGEE_NONPROD_LOGIN_URL

# Test enterprise endpoint
curl -k $ENTERPRISE_BASE_URL/health
```

## Integration with CodeGates

The Enterprise LLM integration is automatically used when:

1. `APIGEE_NONPROD_LOGIN_URL` is set in environment
2. `--llm-provider apigee` is specified in CLI
3. Enterprise LLM is selected in API configuration

The integration provides enhanced analysis capabilities while maintaining enterprise security requirements. 