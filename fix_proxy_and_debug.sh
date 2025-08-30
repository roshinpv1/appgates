#!/bin/bash
# Fix proxy issues and setup debugger environment

echo "🔧 Fixing proxy and debugger setup..."

# Unset proxy variables
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

# Verify virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install essential packages
echo "📦 Installing essential packages..."
pip install fastapi uvicorn requests qdrant-client pydantic

# Test the setup
echo "🧪 Testing setup..."
python debug_venv_test.py

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Open Cursor/VS Code"
echo "2. Press Cmd+Shift+P"
echo "3. Type: 'Python: Select Interpreter'"
echo "4. Select: /Users/roshinpv/Documents/next/gates/.venv/bin/python"
echo "5. Press F5 to start debugging"
