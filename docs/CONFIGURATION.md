# CodeGates Configuration Guide

This guide explains how to configure CodeGates using environment variables for different deployment scenarios.

## 🚀 Quick Start

### 1. Interactive Setup (Recommended)

Run the interactive configuration setup script:

```bash
python setup_config.py
```

This will guide you through all configuration options and create a `.env` file.

### 2. Manual Setup

Copy the environment template and customize it:

```bash
cp codegates/config/environment.template .env
# Edit .env with your preferred settings
```

### 3. Environment-Specific Configuration

Create different configuration files for different environments:

```bash
# Development
cp .env .env.development

# Staging  
cp .env .env.staging

# Production
cp .env .env.production
```

## 📋 Configuration Sections

### API Server Configuration

Configure the core API server settings:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CODEGATES_API_HOST` | Server bind address | `0.0.0.0` | `127.0.0.1` |
| `CODEGATES_API_PORT` | Server port | `8000` | `9000` |
| `CODEGATES_API_BASE_URL` | Base URL for links | `http://localhost:8000` | `https://api.mycompany.com` |
| `CODEGATES_API_VERSION_PREFIX` | API version path | `/api/v1` | `/v2` |
| `CODEGATES_API_TITLE` | API documentation title | `MyGates API` | `Company Code Quality API` |
| `CODEGATES_API_DESCRIPTION` | API description | Auto-generated | Custom description |
| `CODEGATES_API_DOCS_ENABLED` | Enable /docs endpoint | `true` | `false` |

### CORS Configuration

Configure Cross-Origin Resource Sharing:

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEGATES_CORS_ORIGINS` | Allowed origins (comma-separated) | `vscode-webview://*,http://localhost:*,...` |
| `CODEGATES_CORS_METHODS` | Allowed HTTP methods | `GET,POST,PUT,DELETE,OPTIONS,PATCH` |
| `CODEGATES_CORS_HEADERS` | Allowed headers | Standard headers |
| `CODEGATES_CORS_EXPOSE_HEADERS` | Exposed response headers | `Content-Type,Content-Length,Date,Server` |

### LLM Configuration

Configure Language Model integration:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CODEGATES_LLM_ENABLED` | Enable LLM analysis | `false` | `true` |
| `CODEGATES_LLM_PROVIDER` | LLM provider | `local` | `openai`, `anthropic` |
| `CODEGATES_LLM_MODEL` | Model name | `meta-llama-3.1-8b-instruct` | `gpt-4` |
| `CODEGATES_LLM_TEMPERATURE` | Sampling temperature | `0.1` | `0.7` |
| `CODEGATES_LLM_MAX_TOKENS` | Maximum response tokens | `8000` | `4000` |

#### Provider-Specific Configuration

**Local LLM (LM Studio, Ollama, etc.)**:
```bash
LOCAL_LLM_URL=http://localhost:1234/v1
LOCAL_LLM_API_KEY=not-needed
LOCAL_LLM_MODEL=meta-llama-3.1-8b-instruct
```

**OpenAI**:
```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

**Anthropic**:
```bash
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Google Gemini**:
```bash
GOOGLE_API_KEY=...
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-pro
```

### GitHub Integration

Configure GitHub repository access:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GITHUB_TOKEN` | Personal access token | None | `ghp_...` |
| `GITHUB_API_BASE_URL` | GitHub API base URL | `https://api.github.com` | `https://github.company.com/api/v3` |
| `GITHUB_TIMEOUT` | Request timeout (seconds) | `300` | `600` |

### JIRA Integration

Configure JIRA comment posting:

| Variable | Description | Example |
|----------|-------------|---------|
| `JIRA_URL` | JIRA instance URL | `https://company.atlassian.net` |
| `JIRA_USERNAME` | JIRA username/email | `user@company.com` |
| `JIRA_API_TOKEN` | JIRA API token | `ATATT3xFfGF0...` |
| `JIRA_COMMENT_FORMAT` | Comment format | `markdown` or `text` |
| `JIRA_INCLUDE_DETAILS` | Include gate details | `true` |
| `JIRA_INCLUDE_RECOMMENDATIONS` | Include recommendations | `true` |

### Reports Configuration

Configure report generation and URLs:

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEGATES_REPORTS_DIR` | Reports directory | `reports` |
| `CODEGATES_REPORT_URL_BASE` | Report URL base | `http://localhost:8000/api/v1/reports` |
| `CODEGATES_HTML_REPORTS_ENABLED` | Enable HTML reports | `true` |

### VS Code Extension Configuration

Configure VS Code extension settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `VSCODE_API_BASE_URL` | Extension API URL | `http://localhost:8000/api/v1` |
| `VSCODE_API_TIMEOUT` | Request timeout | `300` |
| `VSCODE_API_RETRIES` | Retry attempts | `3` |

## 🌍 Environment-Specific Examples

### Development Environment

```bash
# Development settings
ENVIRONMENT=development
DEBUG=true

# Local API server
CODEGATES_API_HOST=127.0.0.1
CODEGATES_API_PORT=8000
CODEGATES_API_BASE_URL=http://localhost:8000

# Enable documentation
CODEGATES_API_DOCS_ENABLED=true

# Local LLM
CODEGATES_LLM_ENABLED=true
CODEGATES_LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:1234/v1

# Development CORS
CODEGATES_CORS_ORIGINS=vscode-webview://*,http://localhost:*
```

### Production Environment

```bash
# Production settings
ENVIRONMENT=production
DEBUG=false

# Production API server
CODEGATES_API_HOST=0.0.0.0
CODEGATES_API_PORT=8000
CODEGATES_API_BASE_URL=https://codegates.company.com

# Disable documentation in production
CODEGATES_API_DOCS_ENABLED=false

# Cloud LLM
CODEGATES_LLM_ENABLED=true
CODEGATES_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Production CORS
CODEGATES_CORS_ORIGINS=https://app.company.com,https://dashboard.company.com

# GitHub Enterprise
GITHUB_API_BASE_URL=https://github.company.com/api/v3
GITHUB_TOKEN=ghp_...

# JIRA integration
JIRA_URL=https://company.atlassian.net
JIRA_USERNAME=codegates@company.com
JIRA_API_TOKEN=ATATT3xFfGF0...
```

### Docker Environment

```bash
# Docker-specific settings
CODEGATES_API_HOST=0.0.0.0
CODEGATES_API_PORT=8000
CODEGATES_API_BASE_URL=http://localhost:8000

# Use environment variables for secrets
OPENAI_API_KEY=${OPENAI_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}
JIRA_API_TOKEN=${JIRA_API_TOKEN}

# Docker networking
CODEGATES_CORS_ORIGINS=http://localhost:*,http://host.docker.internal:*
```

## 🔧 Loading Configuration

CodeGates loads configuration from multiple sources in this order (highest priority first):

1. **System environment variables**
2. **`.env` file in project root**
3. **`config/.env` file**
4. **`codegates/config/.env` file**
5. **Default values**

### Loading Custom Environment Files

```python
from codegates.utils.config_loader import ConfigLoader

# Load from custom location
config = ConfigLoader(['/path/to/custom.env'])

# Get configuration
api_config = config.get_api_config()
```

## 🧪 Testing Configuration

### Validate Configuration

```bash
python -c "
from codegates.utils.config_loader import get_config
config = get_config()
issues = config.validate_config()
if issues:
    print('Configuration issues:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('✅ Configuration is valid')
"
```

### Test API Server

```bash
# Start server with custom configuration
CODEGATES_API_PORT=9000 python start_server.py

# Test different environments
ENVIRONMENT=staging python start_server.py
```

### Test VS Code Extension

Update VS Code settings:

```json
{
  "codegates.apiUrl": "http://localhost:9000/api/v1",
  "codegates.apiTimeout": 300,
  "codegates.apiRetries": 3
}
```

## 🔍 Troubleshooting

### Common Issues

**1. Configuration not loading**:
```bash
# Check if .env file exists
ls -la .env

# Verify environment variables
python -c "import os; print(os.getenv('CODEGATES_API_PORT', 'NOT SET'))"
```

**2. API server not accessible**:
```bash
# Check host binding
netstat -an | grep 8000

# Test connection
curl http://localhost:8000/api/v1/health
```

**3. CORS issues**:
```bash
# Check CORS origins
python -c "
from codegates.utils.config_loader import get_config
config = get_config()
print('CORS Origins:', config.get_cors_config()['origins'])
"
```

**4. LLM connection issues**:
```bash
# Test LLM configuration
python test_local_llm.py
```

### Debug Mode

Enable debug logging:

```bash
DEBUG=true python start_server.py
```

This will show:
- Configuration loading details
- Environment variable resolution
- API request/response details
- LLM interaction logs

## 📚 Advanced Configuration

### Using Configuration Loader Programmatically

```python
from codegates.utils.config_loader import ConfigLoader

# Create custom config loader
config = ConfigLoader(['.env.production', '.env.local'])

# Get typed configuration
api_port = config.get_int('CODEGATES_API_PORT', 8000)
llm_enabled = config.get_boolean('CODEGATES_LLM_ENABLED', False)
cors_origins = config.get_list('CODEGATES_CORS_ORIGINS')

# Get structured configuration
all_config = config.get_all_config()
print(all_config['api'])
```

### Custom Configuration Validation

```python
from codegates.utils.config_loader import get_config

config = get_config()

# Add custom validation
issues = config.validate_config()

# Custom checks
if config.get_boolean('CODEGATES_LLM_ENABLED'):
    provider = config.get('CODEGATES_LLM_PROVIDER')
    if provider == 'openai' and not config.get('OPENAI_API_KEY'):
        issues.append("OpenAI API key required when using OpenAI provider")

if issues:
    for issue in issues:
        print(f"❌ {issue}")
else:
    print("✅ Configuration valid")
```

### Runtime Configuration Updates

```python
# Update configuration at runtime
import os
os.environ['CODEGATES_API_PORT'] = '9000'

# Reload configuration
from codegates.utils.config_loader import ConfigLoader
config = ConfigLoader()  # Will reload with new values
```

## 🔒 Security Best Practices

### Environment Variables

- **Never commit `.env` files** to version control
- **Use separate `.env` files** for each environment
- **Restrict file permissions**: `chmod 600 .env`
- **Use secrets management** in production (AWS Secrets Manager, Azure Key Vault, etc.)

### API Keys and Tokens

```bash
# Use environment-specific secrets
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id openai-key --query SecretString --output text)
export GITHUB_TOKEN=$(kubectl get secret github-token -o jsonpath='{.data.token}' | base64 -d)
```

### Production Considerations

- **Disable API documentation** (`CODEGATES_API_DOCS_ENABLED=false`)
- **Use HTTPS** for `CODEGATES_API_BASE_URL`
- **Restrict CORS origins** to known domains
- **Enable proper logging** but avoid logging sensitive data
- **Use reverse proxy** for SSL termination and load balancing

---

For more information, see:
- [API Deployment Guide](API_DEPLOYMENT.md)
- [JIRA Integration](JIRA_INTEGRATION.md)
- [Development Setup](../README.md) 