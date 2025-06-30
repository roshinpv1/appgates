# CodeGates - Cross-Language Hard Gate Validation & Scoring System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-green.svg)](https://github.com/yourusername/codegates)

**CodeGates** is a comprehensive, cross-language hard gate validation and scoring system designed to ensure production-ready code quality, security, and reliability across multiple programming languages.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/codegates.git
cd codegates

# Install dependencies
pip install -r requirements.txt

# Run validation on a project
python main.py scan /path/to/your/project

# Generate detailed HTML report
python main.py scan /path/to/your/project --format html --verbose
```

## 📋 Table of Contents

- [Features](#-features)
- [Hard Gates Overview](#-hard-gates-overview)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Supported Languages](#-supported-languages)
- [LLM Integration](#-llm-integration)
- [Reports](#-reports)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 **15 Production-Critical Hard Gates**
- **Structured Logging**: JSON-formatted, searchable logs
- **Secret Protection**: Prevents sensitive data exposure in logs
- **Audit Trail**: Comprehensive operation tracking
- **Error Handling**: Robust exception management
- **Reliability Patterns**: Timeouts, retries, circuit breakers
- **Testing Coverage**: Automated test validation
- **Security Monitoring**: Error tracking and alerting

### 🌐 **Multi-Language Support**
- **Java**: Spring Boot, Maven, Gradle projects
- **Python**: Django, Flask, FastAPI applications  
- **JavaScript/TypeScript**: Node.js, React, Angular projects
- **C#/.NET**: ASP.NET Core, Entity Framework applications

### 🤖 **LLM-Enhanced Analysis**
- **Intelligent Code Review**: Beyond regex pattern matching
- **Context-Aware Recommendations**: Technology-specific insights
- **Security Vulnerability Detection**: AI-powered threat analysis
- **Code Quality Assessment**: Automated best practice validation

### 📊 **Rich Reporting**
- **Interactive HTML Reports**: Beautiful, detailed analysis
- **JSON Export**: Machine-readable validation results
- **CI/CD Integration**: Automated quality gates
- **Trend Analysis**: Track improvements over time

## 🛡️ Hard Gates Overview

| Gate | Weight | Description | Criticality |
|------|--------|-------------|-------------|
| **Structured Logs** | 2.0 | JSON-formatted logging with consistent fields | 🔴 Critical |
| **Avoid Logging Secrets** | 2.0 | Prevents sensitive data in log files | 🔴 Critical |
| **Audit Trail** | 1.8 | Tracks critical business operations | 🔴 Critical |
| **Error Logs** | 1.8 | Comprehensive exception handling | 🔴 Critical |
| **Circuit Breakers** | 1.7 | Fault tolerance for external services | 🟡 High |
| **Timeouts** | 1.6 | Prevents hanging operations | 🟡 High |
| **UI Errors** | 1.5 | User-friendly error handling | 🟡 High |
| **Correlation ID** | 1.5 | Request tracing across services | 🟡 High |
| **Automated Tests** | 1.5 | Test coverage and quality | 🟡 High |
| **UI Error Tools** | 1.4 | Error monitoring integration | 🟢 Medium |
| **Retry Logic** | 1.4 | Resilient failure handling | 🟢 Medium |
| **API Logs** | 1.3 | Endpoint access logging | 🟢 Medium |
| **Throttling** | 1.3 | Rate limiting implementation | 🟢 Medium |
| **Background Jobs** | 1.2 | Async task monitoring | 🟢 Medium |
| **HTTP Codes** | 1.2 | Proper status code usage | 🟢 Medium |

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Verify Installation
```bash
python main.py --help
```

## 💻 Usage

### Basic Scanning
```bash
# Scan current directory
python main.py scan .

# Scan specific project
python main.py scan /path/to/project

# Scan with language specification
python main.py scan /path/to/project --languages java,python
```

### Advanced Options
```bash
# Generate HTML report with verbose output
python main.py scan /path/to/project --format html --verbose

# Set quality threshold
python main.py scan /path/to/project --threshold 80

# Exclude patterns
python main.py scan /path/to/project --exclude "test/**,*.test.*"

# View existing report
python main.py view-report reports/codegates_report_20231201_120000.json
```

### LLM-Enhanced Analysis
```bash
# Enable LLM analysis with OpenAI
python main.py scan /path/to/project --enable-llm --llm-provider openai

# Use local LLM server
python main.py scan /path/to/project --enable-llm \
  --llm-provider local \
  --llm-base-url http://localhost:1234/v1 \
  --llm-model meta-llama-3.1-8b-instruct

# Test LLM connection
python main.py test-llm --llm-provider openai
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# LLM Configuration
CODEGATES_LLM_ENABLED=true
CODEGATES_LLM_PROVIDER=openai
CODEGATES_LLM_API_KEY=your-api-key
CODEGATES_LLM_MODEL=gpt-4

# Scan Configuration  
CODEGATES_SCAN_THRESHOLD=70.0
CODEGATES_DEFAULT_LANGUAGES=python,java,javascript,typescript,csharp
CODEGATES_MAX_WORKERS=4

# Report Configuration
CODEGATES_REPORTS_DIR=reports
CODEGATES_REPORT_FORMATS=json,html
CODEGATES_INCLUDE_LLM_INSIGHTS=true
```

### Configuration File
Create `codegates.json`:

```json
{
  "scan": {
    "threshold": 80.0,
    "languages": ["java", "python", "typescript"],
    "exclude_patterns": ["test/**", "*.test.*", "node_modules/**"]
  },
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.1
  },
  "gates": {
    "structured_logs": {"weight": 2.0, "threshold": 80},
    "avoid_logging_secrets": {"weight": 2.0, "threshold": 0},
    "audit_trail": {"weight": 1.8, "threshold": 70}
  }
}
```

## 🌍 Supported Languages

### Java
- **Frameworks**: Spring Boot, Spring MVC, Jersey
- **Build Tools**: Maven, Gradle
- **Testing**: JUnit, TestNG, Mockito
- **Logging**: SLF4J, Logback, Log4j

### Python  
- **Frameworks**: Django, Flask, FastAPI
- **Testing**: pytest, unittest
- **Logging**: Python logging, structlog, loguru
- **Async**: asyncio, aiohttp

### JavaScript/TypeScript
- **Runtime**: Node.js, Deno
- **Frameworks**: Express, NestJS, Koa
- **Frontend**: React, Vue, Angular
- **Testing**: Jest, Mocha, Cypress
- **Logging**: Winston, Pino, Bunyan

### C#/.NET
- **Frameworks**: ASP.NET Core, .NET 6+
- **Testing**: xUnit, NUnit, MSTest
- **Logging**: Serilog, NLog, ILogger
- **ORM**: Entity Framework Core

## 🤖 LLM Integration

CodeGates supports multiple LLM providers for enhanced code analysis:

### Supported Providers
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3 models
- **Google**: Gemini Pro
- **Ollama**: Local models
- **Custom**: OpenAI-compatible APIs

### Enhanced Capabilities
- **Semantic Code Analysis**: Understanding code intent
- **Security Vulnerability Detection**: AI-powered threat identification
- **Technology-Specific Recommendations**: Framework-aware suggestions
- **Code Quality Assessment**: Beyond pattern matching

## 📊 Reports

### HTML Reports
- Interactive, filterable results
- Detailed gate analysis
- Technology detection
- LLM insights and recommendations
- Trend visualization

### JSON Reports
- Machine-readable format
- CI/CD integration friendly
- Programmatic analysis
- Historical comparison

### Report Structure
```
codegates/
├── codegates/
│   ├── __init__.py
│   ├── cli.py
│   ├── models.py
│   ├── reports.py
│   ├── core/
│   │   ├── gate_validator.py
│   │   ├── language_detector.py
│   │   ├── llm_analyzer.py
│   │   └── gate_validators/
│   └── utils/
└── reports/
    ├── codegates_report_20231201_120000.html
    └── codegates_report_20231201_120000.json
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/yourusername/codegates.git
cd codegates
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Run CodeGates on itself
python main.py scan . --enable-llm --format html
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: support@codegates.dev
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/codegates/issues)
- 📖 Docs: [Documentation](https://codegates.dev/docs)

## 🏆 Acknowledgments

- Hard Gates methodology inspired by production engineering best practices
- Multi-language support designed for modern polyglot architectures
- LLM integration leveraging state-of-the-art AI for code analysis

---

**CodeGates** - Ensuring your code meets production-grade standards across all languages and frameworks. 