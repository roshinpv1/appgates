#!/bin/bash

# CodeGates Agent Quick Start Script
# This script helps you quickly set up and run the CodeGates validation agent

set -e

echo "🚀 CodeGates Agent Quick Start"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "codegates_agent.py" ]; then
    echo "❌ Error: Please run this script from the agent directory"
    echo "   cd agent"
    echo "   ./quick_start.sh"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
echo "🔍 Checking Python version..."
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $python_version found"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install google-adk litellm requests pydantic python-dotenv

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# CodeGates Agent Configuration
# Choose your LLM provider and configure accordingly

# For Local LLM (Ollama) - Recommended for development
CODEGATES_LLM_PROVIDER=ollama
CODEGATES_LLM_MODEL=llama2
CODEGATES_LLM_BASE_URL=http://localhost:11434

# For Cloud LLM (OpenAI) - Uncomment and configure
# CODEGATES_LLM_PROVIDER=openai
# CODEGATES_LLM_MODEL=gpt-3.5-turbo
# CODEGATES_LLM_API_KEY=your-openai-api-key
# CODEGATES_LLM_BASE_URL=https://api.openai.com/v1

# For Cloud LLM (Anthropic) - Uncomment and configure
# CODEGATES_LLM_PROVIDER=anthropic
# CODEGATES_LLM_MODEL=claude-3-sonnet-20240229
# CODEGATES_LLM_API_KEY=your-anthropic-api-key

# For Cloud LLM (Google) - Uncomment and configure
# CODEGATES_LLM_PROVIDER=google
# CODEGATES_LLM_MODEL=gemini-1.5-flash
# CODEGATES_LLM_API_KEY=your-google-api-key
EOF
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file with your LLM configuration"
else
    echo "✅ .env file already exists"
fi

# Load environment variables
echo "🔧 Loading environment variables..."
set -o allexport && source .env && set +o allexport

# Test agent setup
echo "🧪 Testing agent setup..."
python3 test_agent.py

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your LLM configuration"
echo "2. Start Ollama (if using local LLM): ollama serve"
echo "3. Run the agent with ADK web: adk web ."
echo "4. Open browser to: http://localhost:8080"
echo ""
echo "Example commands to try:"
echo "- 'Validate the repository at https://github.com/company/myapp'"
echo "- 'What gates are available for validation?'"
echo "- 'Help me understand the validation process'"
echo ""
echo "For more information, see: ADK_WEB_DEPLOYMENT_GUIDE.md" 