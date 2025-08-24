#!/usr/bin/env python3
"""
Production startup script for CodeGates Scan API Server
Disables reload to avoid Qdrant concurrency issues
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
    """Main function to start the production server"""
    
    # Configuration for production
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    workers = int(os.getenv("WORKERS", "1"))  # Single worker to avoid Qdrant conflicts
    
    # Initialize scan flow
    print("🔧 Initializing CodeGates Scan Flow...")
    success = initialize_scan_flow(DEFAULT_CONFIG)
    
    if not success:
        print("❌ Failed to initialize scan flow. Check your configuration.")
        sys.exit(1)
    
    print("✅ Scan flow initialized successfully")
    print(f"🚀 Starting CodeGates Scan API Server (Production) on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print(f"🔧 Workers: {workers} (reload disabled for Qdrant compatibility)")
    
    # Start server with production settings
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,  # Disable reload to avoid Qdrant concurrency issues
        log_level=log_level,
        access_log=True,
        workers=workers
    )


if __name__ == "__main__":
    main()
