#!/usr/bin/env python3
"""
CodeGates Integrated Server Launcher
Runs both FastAPI backend and Streamlit UI on the same port
"""

import sys
import os
import signal
import time
from pathlib import Path

def main():
    """Launch the integrated CodeGates server"""
    
    print("🚀 Starting CodeGates Integrated Server")
    print("=" * 50)
    
    # Add current directory to path
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir))
    
    try:
        # Import and run the server
        from gates.server import app, SERVER_HOST, SERVER_PORT
        import uvicorn
        
        print(f"🎯 True Same-Port Integration: http://localhost:{SERVER_PORT}")
        print(f"🎨 Direct UI accessible at: http://localhost:{SERVER_PORT}/ui/")
        print(f"📊 API Documentation at: http://localhost:{SERVER_PORT}/docs")
        print()
        print("✅ Features Available:")
        print("   • Complete CodeGates scanning workflow")
        print("   • Direct HTML UI integration (no iframe)")
        print("   • Individual gate PDFs for JIRA tickets")
        print("   • Advanced filtering and download management")
        print("   • Real-time scan monitoring")
        print("   • Single-port architecture (no subprocesses)")
        print()
        print("🏗️ Architecture Benefits:")
        print("   • No separate Streamlit process")
        print("   • Direct HTML rendering for faster loading")
        print("   • No cross-origin or iframe issues")
        print("   • Simplified deployment and maintenance")
        print()
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the server
        uvicorn.run(
            app,
            host=SERVER_HOST,
            port=SERVER_PORT,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down CodeGates server...")
        print("✅ Server stopped successfully")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 