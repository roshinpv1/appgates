# CodeGates v2.0 - PocketFlow Implementation

A comprehensive hard gate validation system built with [PocketFlow](https://the-pocket.github.io/PocketFlow/) for enterprise security and reliability standards.

## 🚀 Features

- **15 Enterprise Hard Gates**: Comprehensive validation of security, reliability, and compliance standards
- **AI-Powered Pattern Generation**: Dynamic LLM-driven pattern creation for accurate validation
- **Comprehensive LLM Support**: OpenAI, Anthropic, Google Gemini, Local LLM, Ollama, Enterprise, and Apigee
- **Multiple Interfaces**: CLI, Web API, and programmatic access
- **Comprehensive Reports**: HTML and JSON reports with detailed analysis
- **Repository Support**: GitHub, GitLab, and other Git repositories
- **Language Support**: Python, Java, JavaScript/TypeScript, C#, Go, Ruby, PHP, and more
- **Enterprise Ready**: Token management, proxy support, and advanced authentication

## 🤖 LLM Integration

CodeGates v2.0 includes comprehensive LLM integration supporting multiple providers:

### Supported Providers

- **☁️ Cloud Providers**: OpenAI (GPT-4), Anthropic (Claude), Google Gemini
- **🏠 Local Providers**: Local LLM servers, Ollama direct integration
- **🏢 Enterprise Providers**: Custom enterprise endpoints with token management
- **🔐 Apigee Enterprise**: Advanced enterprise authentication through Apigee proxy

### Quick LLM Setup

```bash
# Auto-detection (recommended)
python cli.py scan https://github.com/owner/repo

# Specific provider
python cli.py scan https://github.com/owner/repo --llm-provider openai --llm-model gpt-4

# Test LLM integration
python cli.py test-llm --verbose
```

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-your-api-key"

# Local LLM
export LOCAL_LLM_URL="http://localhost:11434/v1"

# Apigee Enterprise
export APIGEE_NONPROD_LOGIN_URL="https://your-apigee-url"
export APIGEE_CONSUMER_KEY="your-key"
export APIGEE_CONSUMER_SECRET="your-secret"
export ENTERPRISE_BASE_URL="https://your-enterprise-url"
```

See [LLM Setup Guide](docs/LLM_SETUP.md) for complete configuration details.

## 📋 Hard Gates Validated

1. **Logs Searchable/Available** - Structured logging implementation
2. **Avoid Logging Confidential Data** - Security compliance for sensitive data
3. **Create Audit Trail Logs** - Compliance logging for critical operations
4. **Tracking ID for Logs** - Correlation IDs for distributed tracing
5. **Log REST API Calls** - API request/response logging
6. **Log Application Messages** - Application state and event logging
7. **Client UI Errors Logged** - Frontend error capture
8. **Retry Logic** - Resilient operation patterns
9. **Timeouts in IO Ops** - I/O operation timeout handling
10. **Throttling & Drop Request** - Rate limiting implementation
11. **Circuit Breakers** - Fault tolerance patterns
12. **Log System Errors** - Comprehensive error logging
13. **HTTP Error Codes** - Proper API status code usage
14. **Client Error Tracking** - Error monitoring tool integration
15. **Automated Tests** - Test coverage and quality

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd gates

# Install dependencies
pip install -r requirements.txt

# Optional: Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

## 🎯 Quick Start

### Command Line Interface

```bash
# Scan a public repository
python cli.py scan https://github.com/owner/repo

# Scan with custom settings
python cli.py scan https://github.com/owner/repo \
  --branch develop \
  --threshold 80 \
  --output ./my-reports \
  --format html

# Scan private repository
python cli.py scan https://github.com/owner/private-repo \
  --token ghp_your_token_here

# List available gates
python cli.py gates

# View generated report
python cli.py view ./reports/codegates_report_*.html
```

### Web API Server

```bash
# Start the API server
python server.py

# Or with uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000/api/v1/

### Programmatic Usage

```python
from flow import create_validation_flow
from utils.hard_gates import HARD_GATES
import tempfile
import uuid

# Initialize shared store
shared = {
    "request": {
        "repository_url": "https://github.com/owner/repo",
        "branch": "main",
        "github_token": None,
        "threshold": 70,
        "scan_id": str(uuid.uuid4())
    },
    "repository": {"local_path": None, "metadata": {}},
    "config": {"build_files": {}, "config_files": {}, "dependencies": []},
    "llm": {"prompt": None, "response": None, "patterns": {}},
    "validation": {"gate_results": [], "overall_score": 0.0},
    "reports": {"html_path": None, "json_path": None},
    "hard_gates": HARD_GATES,
    "temp_dir": tempfile.mkdtemp(prefix="codegates_"),
    "errors": []
}

# Run validation flow
flow = create_validation_flow()
flow.run(shared)

# Access results
print(f"Overall Score: {shared['validation']['overall_score']:.1f}%")
print(f"Report: {shared['reports']['html_path']}")
```

## 🔧 Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_URL=http://localhost:11434/v1/chat/completions  # Local LLM server
LLM_API_KEY=your_api_key_here                       # API key if required

# GitHub Configuration  
GITHUB_TOKEN=ghp_your_token_here                    # For private repositories

# Report Configuration
REPORTS_DIR=./reports                               # Output directory
DEFAULT_THRESHOLD=70                                # Default quality threshold
```

### LLM Integration

CodeGates supports various LLM providers:

- **Local LLM** (Ollama, LM Studio): Set `LLM_URL` to your local endpoint
- **OpenAI**: Use OpenAI-compatible endpoints
- **Custom LLM**: Any OpenAI-compatible API

If no LLM is configured, the system uses intelligent fallback patterns based on detected technologies.

## 📊 API Usage Examples

### Start a Scan

```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/owner/repo",
    "branch": "main",
    "threshold": 70
  }'
```

### Check Scan Status

```bash
curl "http://localhost:8000/api/v1/scan/{scan_id}"
```

### Get HTML Report

```bash
curl "http://localhost:8000/api/v1/scan/{scan_id}/report/html"
```

### Get JSON Report

```bash
curl "http://localhost:8000/api/v1/scan/{scan_id}/report/json"
```

## 🏗️ Architecture

CodeGates v2.0 is built using the PocketFlow framework with a clean, modular architecture:

```
Flow: Repository → Process → Extract → Prompt → LLM → Validate → Report → Cleanup
```

### Key Components

- **FetchRepositoryNode**: Clones repositories using Git or GitHub API
- **ProcessCodebaseNode**: Extracts file metadata and statistics
- **ExtractConfigNode**: Extracts build and configuration file contents
- **GeneratePromptNode**: Creates comprehensive LLM prompts
- **CallLLMNode**: Generates validation patterns using LLM
- **ValidateGatesNode**: Applies patterns to codebase (Map-Reduce)
- **GenerateReportNode**: Creates HTML and JSON reports
- **CleanupNode**: Removes temporary files

### Utilities

- **git_operations.py**: Repository cloning and management
- **file_scanner.py**: File metadata extraction
- **hard_gates.py**: Gate definitions and patterns
- **llm_client.py**: LLM integration (planned)
- **report_builder.py**: Report generation (planned)

## 🔍 How It Works

1. **Repository Checkout**: Clone or download the target repository
2. **Analyze Repository**: Extract file metadata, detect languages, count LOC
3. **Extract Config**: Read build files (package.json, pom.xml, etc.) and config files
4. **Generate Prompt**: Create comprehensive LLM prompt with codebase context
5. **LLM Pattern Generation**: Use AI to generate validation patterns specific to the codebase
6. **Validate Gates**: Apply patterns to source code using Map-Reduce approach
7. **Generate Reports**: Create detailed HTML and JSON reports
8. **Cleanup**: Remove temporary files and directories

## 🎨 Report Features

### HTML Reports
- Interactive dashboard with gate status
- Detailed match information
- Recommendations for improvement
- Technology stack analysis
- Color-coded status indicators

### JSON Reports
- Machine-readable format
- Complete validation data
- API integration friendly
- Structured metadata

## 🧪 Testing

```bash
# Run a test scan on a sample repository
python main.py

# Test individual components
python utils/git_operations.py
python utils/file_scanner.py

# Test the complete flow
python -c "
from flow import create_validation_flow
flow = create_validation_flow()
print('Flow created successfully')
"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following PocketFlow patterns
4. Add tests for new functionality
5. Submit a pull request

### Adding New Gates

1. Add gate definition to `utils/hard_gates.py`
2. Update validation logic in `ValidateGatesNode`
3. Add gate-specific patterns and scoring
4. Update documentation

### Adding New Utilities

1. Create utility in `utils/` directory
2. Follow the pattern: simple functions with clear input/output
3. Add tests and documentation
4. Import and use in relevant nodes

## 📚 Documentation

- **Design Document**: [docs/design.md](docs/design.md)
- **PocketFlow Guide**: https://the-pocket.github.io/PocketFlow/guide.html
- **API Documentation**: Available at `/docs` when server is running

## 🚨 Troubleshooting

### Common Issues

**Repository Clone Fails**
```bash
# Check network connectivity and token permissions
git clone https://github.com/owner/repo
```

**LLM Call Timeout**
```bash
# Check LLM server status
curl http://localhost:11434/api/tags
```

**Permission Denied**
```bash
# Ensure proper GitHub token permissions
# Token needs 'repo' scope for private repositories
```

**Missing Dependencies**
```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
```

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- Built with [PocketFlow](https://the-pocket.github.io/PocketFlow/) framework
- Inspired by enterprise security and reliability best practices
- Thanks to the open source community for tools and libraries used

---

**CodeGates v2.0** - Making enterprise code validation simple, comprehensive, and AI-powered. 🚀 