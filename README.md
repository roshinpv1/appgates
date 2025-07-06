# CodeGates - Code Quality Analysis Tool

CodeGates is a powerful code quality analysis tool that uses LLM (Large Language Models) to validate and improve code quality across different programming languages.

## Features

- Code quality analysis using multiple LLM providers
- Support for multiple programming languages
- Integration with Jira for issue tracking
- Customizable quality gates
- HTML report generation
- API server for remote analysis
- Enterprise-ready with token management

## Environment Variables

### LLM Configuration

#### OpenAI
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_MODEL` - Model to use (default: gpt-4)
- `OPENAI_BASE_URL` - Custom base URL for OpenAI API
- `OPENAI_TEMPERATURE` - Temperature for model responses (default: 0.1)
- `OPENAI_MAX_TOKENS` - Maximum tokens per request (default: 4000)

#### Anthropic
- `ANTHROPIC_API_KEY` - Anthropic API key
- `ANTHROPIC_MODEL` - Model to use (default: claude-3-sonnet-20240229)
- `ANTHROPIC_BASE_URL` - Custom base URL for Anthropic API
- `ANTHROPIC_TEMPERATURE` - Temperature for model responses (default: 0.1)
- `ANTHROPIC_MAX_TOKENS` - Maximum tokens per request (default: 4000)

#### Local LLM
- `LOCAL_LLM_URL` - URL for local LLM server
- `LOCAL_LLM_MODEL` - Model to use (default: meta-llama-3.1-8b-instruct)
- `LOCAL_LLM_API_KEY` - API key if required (default: not-needed)
- `LOCAL_LLM_TEMPERATURE` - Temperature for model responses (default: 0.1)
- `LOCAL_LLM_MAX_TOKENS` - Maximum tokens per request (default: 4000)

#### Ollama
- `OLLAMA_HOST` - Ollama server host (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model to use (default: meta-llama-3.1-8b-instruct)
- `OLLAMA_TEMPERATURE` - Temperature for model responses (default: 0.1)
- `OLLAMA_NUM_PREDICT` - Number of tokens to predict (default: 4000)

#### Enterprise LLM
- `ENTERPRISE_LLM_URL` - Enterprise LLM server URL
- `ENTERPRISE_LLM_MODEL` - Model to use (default: meta-llama-3.1-8b-instruct)
- `ENTERPRISE_LLM_API_KEY` - API key for enterprise LLM
- `ENTERPRISE_LLM_TOKEN` - Authentication token
- `ENTERPRISE_LLM_REFRESH_URL` - Token refresh URL
- `ENTERPRISE_LLM_CLIENT_ID` - Client ID for token refresh
- `ENTERPRISE_LLM_CLIENT_SECRET` - Client secret for token refresh
- `ENTERPRISE_LLM_HEADERS` - Additional headers as JSON (default: {})
- `ENTERPRISE_LLM_TEMPERATURE` - Temperature for model responses (default: 0.1)
- `ENTERPRISE_LLM_MAX_TOKENS` - Maximum tokens per request (default: 4000)

### API Server Configuration

- `CODEGATES_API_HOST` - API server host (default: 0.0.0.0)
- `CODEGATES_API_PORT` - API server port (default: 8000)
- `CODEGATES_API_BASE_URL` - Base URL for API (default: http://localhost:8000)
- `CODEGATES_API_VERSION_PREFIX` - API version prefix (default: /api/v1)
- `CODEGATES_API_TITLE` - API title (default: MyGates API)
- `CODEGATES_API_DESCRIPTION` - API description
- `CODEGATES_API_DOCS_ENABLED` - Enable API docs (default: true)
- `CODEGATES_API_DOCS_URL` - API docs URL (default: /docs)
- `CODEGATES_API_REDOC_URL` - ReDoc URL (default: /redoc)

### CORS Configuration

- `CODEGATES_CORS_ORIGINS` - Allowed origins
- `CODEGATES_CORS_METHODS` - Allowed methods
- `CODEGATES_CORS_HEADERS` - Allowed headers
- `CODEGATES_CORS_EXPOSE_HEADERS` - Exposed headers

### Storage Configuration

- `CODEGATES_STORAGE_BACKEND` - Storage backend (default: sqlite)
- `CODEGATES_DATABASE_URL` - Database URL
- `CODEGATES_DATABASE_PATH` - SQLite database path (default: ./data/codegates.db)
- `CODEGATES_STORAGE_DIR` - Storage directory (default: ./data/scan_results)
- `CODEGATES_MAX_CONNECTIONS` - Maximum database connections (default: 10)
- `CODEGATES_CONNECTION_TIMEOUT` - Database connection timeout (default: 30)
- `CODEGATES_RETENTION_DAYS` - Data retention period in days
- `CODEGATES_CLEANUP_INTERVAL_HOURS` - Cleanup interval in hours (default: 24)
- `CODEGATES_ENABLE_INDEXING` - Enable database indexing (default: true)
- `CODEGATES_ENABLE_COMPRESSION` - Enable data compression (default: false)

### Jira Integration

- `JIRA_URL` - Jira instance URL
- `JIRA_USERNAME` - Jira username
- `JIRA_API_TOKEN` - Jira API token
- `JIRA_PROJECT_KEY` - Jira project key
- `JIRA_ISSUE_KEY` - Jira issue key
- `JIRA_COMMENT_FORMAT` - Comment format (default: markdown)
- `JIRA_INCLUDE_DETAILS` - Include analysis details (default: true)
- `JIRA_INCLUDE_RECOMMENDATIONS` - Include recommendations (default: true)
- `JIRA_ATTACH_HTML_REPORT` - Attach HTML report (default: false)

### Timeouts

- `CODEGATES_GIT_CLONE_TIMEOUT` - Git clone timeout (default: 3000)
- `CODEGATES_GIT_LS_REMOTE_TIMEOUT` - Git ls-remote timeout (default: 300)
- `CODEGATES_API_DOWNLOAD_TIMEOUT` - API download timeout (default: 1200)
- `CODEGATES_ANALYSIS_TIMEOUT` - Analysis timeout (default: 1800)
- `CODEGATES_LLM_REQUEST_TIMEOUT` - LLM request timeout (default: 300)
- `CODEGATES_HTTP_REQUEST_TIMEOUT` - HTTP request timeout (default: 100)
- `CODEGATES_HEALTH_CHECK_TIMEOUT` - Health check timeout (default: 5)
- `CODEGATES_JIRA_REQUEST_TIMEOUT` - Jira request timeout (default: 300)
- `CODEGATES_JIRA_HEALTH_TIMEOUT` - Jira health check timeout (default: 100)
- `CODEGATES_GITHUB_CONNECT_TIMEOUT` - GitHub connection timeout (default: 300)
- `CODEGATES_GITHUB_READ_TIMEOUT` - GitHub read timeout (default: 1200)
- `CODEGATES_VSCODE_API_TIMEOUT` - VSCode API timeout (default: 3000)
- `CODEGATES_LLM_BATCH_TIMEOUT` - LLM batch processing timeout (default: 300)

### SSL Configuration

- `CODEGATES_SSL_VERIFY` - Verify SSL certificates (default: true)
- `CODEGATES_SSL_CA_BUNDLE` - Custom CA bundle path
- `CODEGATES_SSL_CLIENT_CERT` - Client certificate path
- `CODEGATES_SSL_CLIENT_KEY` - Client key path
- `CODEGATES_SSL_DISABLE_WARNINGS` - Disable SSL warnings (default: false)

## Getting Started

1. Clone the repository
2. Create a `.env` file with the required environment variables
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the API server:
   ```bash
   python -m codegates.api.server
   ```

## License

MIT License 