#!/usr/bin/env python3
"""
Startup script for CodeGates Scan API Server
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from server import app, initialize_scan_flow, DEFAULT_CONFIG


def main():
    """Main function to start the server"""
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    

    
    # Initialize scan flow
    print("🔧 Initializing CodeGates Scan Flow...")
    success = initialize_scan_flow(DEFAULT_CONFIG)
    
    if not success:
        print("❌ Failed to initialize scan flow. Check your configuration.")
        sys.exit(1)
    
    print("✅ Scan flow initialized successfully")
    print(f"🚀 Starting CodeGates Scan API Server on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    
    # Start server
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()
