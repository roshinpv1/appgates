#!/bin/bash

# CodeGates Scan API Server Startup Script

echo "🚀 Starting CodeGates Scan API Server..."

# Set default values
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"8000"}
RELOAD=${RELOAD:-"true"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

# Check if we're in the right directory
if [ ! -f "run_server.py" ]; then
    echo "❌ Error: run_server.py not found. Please run this script from the src directory."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip3 install -r requirements.txt

# Start the server
echo "🌐 Starting server on $HOST:$PORT"
echo "📖 API Documentation: http://$HOST:$PORT/docs"
echo "🔍 Health Check: http://$HOST:$PORT/health"
echo ""

python3 run_server.py
