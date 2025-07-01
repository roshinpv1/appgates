#!/usr/bin/env python3
"""
MyGates API Server Entry Point

Starts the FastAPI server with JIRA integration support.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from codegates.api.server import start_server

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the API server"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Start the server
        start_server()
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        print("💡 Make sure you have all dependencies installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 