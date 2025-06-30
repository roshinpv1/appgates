# 🤖 LLM Integration Guide

## Overview

CodeGates now supports **LLM-enhanced analysis** that goes beyond traditional regex-based pattern matching to provide intelligent, context-aware code analysis and recommendations.

## 🚀 Quick Start

### Basic Usage

```bash
# Enable LLM with OpenAI
codegates scan . --enable-llm --llm-provider openai

# Use with custom configuration
codegates scan . --enable-llm \
  --llm-provider anthropic \
  --llm-model claude-3-sonnet \
  --llm-temperature 0.2

# Local LLM server
codegates scan . --enable-llm \
  --llm-provider local \
  --llm-base-url http://localhost:1234/v1 \
  --llm-model meta-llama-3.1-8b-instruct
```

### Configuration File

Create `codegates-llm.json`:

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.1,
    "max_tokens": 8000
  }
}
```

## 🔧 Provider Setup

### OpenAI

```bash
export OPENAI_API_KEY="your-api-key"
codegates scan . --enable-llm --llm-provider openai --format html
```

### Anthropic (Claude)

```bash
export ANTHROPIC_API_KEY="your-api-key"
codegates scan . --enable-llm --llm-provider anthropic --verbose
```

### Google Gemini

```bash
export GOOGLE_API_KEY="your-api-key"
codegates scan . --enable-llm --llm-provider gemini --threshold 80
```

## 📋 Available Commands

### Test LLM Connection

```bash
# Test OpenAI
codegates test-llm --llm-provider openai

# Test Anthropic with specific model
codegates test-llm --llm-provider anthropic --llm-model claude-3-haiku

# Test local Ollama
codegates test-llm --llm-provider ollama --llm-model llama2
```

### Enhanced Scanning

```bash
# Full LLM-enhanced scan
codegates scan /path/to/project \
  --enable-llm \
  --llm-provider openai \
  --llm-model gpt-4 \
  --format html \
  --verbose

# With custom temperature
codegates scan . \
  --enable-llm \
  --llm-temperature 0.3 \
  --llm-max-tokens 3000
```

### Local LLM Setup (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull codellama

# Use with CodeGates
codegates scan . --enable-llm --llm-provider ollama --llm-model codellama
```

## 🐍 Python API

```python
from codegates.core.llm_analyzer import LLMConfig, LLMProvider, LLMIntegrationManager

# Configure LLM
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    api_key="your-key",
    temperature=0.1
)

# Initialize manager
llm_manager = LLMIntegrationManager(config)

# Test connection
if llm_manager.test_connection():
    print("✅ LLM connection successful")
```

## 🧪 Testing

### Test Commands

```bash
# Test OpenAI connection
codegates test-llm --llm-provider openai

# Test with verbose output
codegates test-llm --llm-provider anthropic --llm-model claude-3-haiku

# Test local model
codegates test-llm --llm-provider ollama --llm-model llama2
```

### Integration Testing

```bash
# Run with LLM on test project
codegates scan tests/sample-projects/java-spring \
  --enable-llm \
  --llm-provider openai \
  --format json

# Compare with/without LLM
codegates scan . --format json > baseline.json
codegates scan . --enable-llm --format json > enhanced.json
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```bash
   export OPENAI_API_KEY="your-key"
   ```

2. **Model Not Found**
   ```bash
   # List available models
   codegates test-llm --llm-provider openai
   ```

3. **Connection Timeout**
   ```bash
   # Increase timeout
   codegates scan . --enable-llm --llm-timeout 60
   ```

### Debug Mode

```bash
# Enable debug logging
codegates scan . --enable-llm --verbose --debug
```

## ⚙️ Advanced Configuration

### Environment Variables

```bash
# LLM Configuration
export CODEGATES_LLM_ENABLED=true
export CODEGATES_LLM_PROVIDER=openai
export CODEGATES_LLM_MODEL=gpt-4
export CODEGATES_LLM_TEMPERATURE=0.1
export CODEGATES_LLM_MAX_TOKENS=8000

# Provider Keys
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export GOOGLE_API_KEY=your-google-key
```

### Custom Prompts

CodeGates uses optimized prompts for each gate type. You can customize them by:

1. Creating custom prompt templates
2. Extending the LLM analyzer
3. Using configuration overrides

### Performance Tuning

```bash
# Faster analysis with smaller model
codegates scan . --enable-llm \
  --llm-model gpt-3.5-turbo \
  --llm-temperature 0.0

# Parallel processing
codegates scan . --enable-llm --max-workers 8
```

## 🏗️ Architecture

### LLM Integration Flow

```
1. Gate Validation → 2. Code Extraction → 3. LLM Analysis → 4. Enhanced Results
```

### Key Components

- **LLMAnalyzer**: Core analysis engine
- **LLMIntegrationManager**: Coordination and fallbacks
- **Provider Adapters**: OpenAI, Anthropic, Gemini, Ollama
- **Prompt Templates**: Gate-specific analysis prompts

## 📊 Cost Optimization

### Token Usage

- **Average per gate**: 500-1500 tokens
- **Full project scan**: 5,000-15,000 tokens
- **Cost estimate**: $0.01-0.05 per scan (GPT-4)

### Optimization Tips

1. Use smaller models for development
2. Cache results for repeated scans
3. Filter code samples by relevance
4. Use local models for frequent testing

## 🔒 Security & Privacy

### Data Handling

- Code samples are sent to LLM providers
- No persistent storage of code
- API keys handled securely
- Optional local-only processing

### Local Processing

```bash
# Use local Ollama for privacy
ollama pull codellama
codegates scan . --enable-llm --llm-provider ollama
```

## 🎯 Best Practices

1. **Start with test projects** before production use
2. **Use appropriate models** for your use case
3. **Monitor token usage** and costs
4. **Combine with traditional analysis** for comprehensive coverage
5. **Review LLM recommendations** before implementation

---

**🚀 Ready to enhance your code analysis with AI? Start with a simple test:**

```bash
codegates test-llm --llm-provider openai
``` 