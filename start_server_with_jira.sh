
#!/bin/bash

# CodeGates Server with JIRA Integration
# This script loads JIRA credentials and starts the server

# Load environment variables from jira.env file
if [ -f "jira.env" ]; then
    echo "📄 Loading JIRA environment variables from jira.env..."
    export $(cat jira.env | grep -v '^#' | grep -v '^$' | xargs)
else
    # Fallback to hardcoded values
    echo "⚠️ jira.env not found, using fallback values..."
    export JIRA_URL="https://roshin.atlassian.net/jira"
    export JIRA_USER="ss"
    export JIRA_TOKEN=""
fi

echo "🔧 Starting CodeGates Server with JIRA Integration..."
echo "📋 JIRA URL: $JIRA_URL"
echo "👤 JIRA User: $JIRA_USER"
echo "🔑 JIRA Token: ${JIRA_TOKEN:0:20}..."

# Kill existing server
echo "🛑 Stopping any existing server processes..."
pkill -f "run_integrated_server.py" 2>/dev/null || echo "No existing server found"
pkill -f "uvicorn.*server" 2>/dev/null || echo "No uvicorn processes found"
sleep 2

# Verify environment variables are set
if [ -z "$JIRA_URL" ] || [ -z "$JIRA_USER" ] || [ -z "$JIRA_TOKEN" ]; then
    echo "❌ ERROR: JIRA environment variables not properly set!"
    echo "Please check jira.env file or update the script"
    exit 1
fi

# Start server with environment variables
echo "🚀 Starting server with JIRA environment variables..."
echo "🌐 Server will be available at: http://localhost:8000/ui/"
python3 run_integrated_server.py 