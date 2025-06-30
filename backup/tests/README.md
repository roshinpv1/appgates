# CodeGates Test Suite

This directory contains all test files for the CodeGates project, organized for easy maintenance and execution.

## Test Files

### Core Functionality Tests

- **`test_local_llm.py`** - Local LLM integration and functionality tests
  - Tests LLM configuration loading
  - Tests model availability checking
  - Tests LLM provider integration (OpenAI, Local, etc.)
  - Tests enterprise LLM configurations

- **`test_cors.py`** - CORS configuration testing
  - Tests API CORS settings
  - Tests allowed origins and methods
  - Tests VS Code extension compatibility

### Git Integration Tests

- **`test_git_validation.py`** - Git repository validation tests
  - Tests repository cloning
  - Tests branch validation
  - Tests local git operations

- **`test_github_validation.py`** - GitHub API integration tests
  - Tests GitHub API authentication
  - Tests repository access validation
  - Tests public/private repository handling

- **`test_github_enterprise_integration.py`** - GitHub Enterprise integration tests
  - Tests GitHub Enterprise server connections
  - Tests enterprise authentication flows
  - Tests custom GitHub Enterprise configurations

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/

# With verbose output
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=codegates --cov-report=html
```

### Run Individual Tests
```bash
# Run specific test file
python tests/test_local_llm.py

# Run specific test with pytest
python -m pytest tests/test_local_llm.py -v
```

### Run Tests by Category
```bash
# Run all LLM tests
python -m pytest tests/test_local_llm.py

# Run all GitHub tests
python -m pytest tests/test_github*.py

# Run all Git tests
python -m pytest tests/test_git*.py
```

## Test Dependencies

Make sure you have the required dependencies installed:

```bash
pip install pytest pytest-cov
```

## Environment Setup

Some tests require environment variables or services:

1. **LLM Tests**: Require `CODEGATES_LLM_ENABLED=true` and a running LLM service
2. **GitHub Tests**: May require `GITHUB_TOKEN` for API access
3. **CORS Tests**: Test the API server configuration

## Contributing

When adding new tests:

1. Follow the naming convention: `test_*.py`
2. Add appropriate docstrings
3. Update this README if adding new test categories
4. Ensure tests can run independently
5. Mock external services when possible

## Test Structure

```
tests/
├── __init__.py          # Package initialization
├── README.md           # This file
├── test_cors.py        # CORS testing
├── test_git_validation.py       # Git operations
├── test_github_validation.py    # GitHub API
├── test_github_enterprise_integration.py  # GitHub Enterprise
└── test_local_llm.py   # LLM functionality
``` 