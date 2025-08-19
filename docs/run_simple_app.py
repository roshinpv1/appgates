#!/usr/bin/env python3
"""
Simple CodeGates App Launcher
Launches the simple FastAPI + Streamlit app with APP ID workflow
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import fastapi
        import uvicorn
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install streamlit fastapi uvicorn requests")
        return False

def wait_for_server():
    """Wait for the server to be ready"""
    print("⏳ Waiting for server to start...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
    
    print("⚠️ Server may not be ready")
    return False

def main():
    """Main launcher function"""
    print("🚀 CodeGates Simple App Launcher")
    print("=" * 50)
    print("APP ID → Repository → Branch → Scan Workflow")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start the simple server
    print("🚀 Starting simple server...")
    try:
        process = subprocess.Popen([
            sys.executable, "simple_server.py"
        ])
        
        # Wait for server to be ready
        if wait_for_server():
            print("\n🎉 Simple app is running!")
            print("📱 Access the application at: http://localhost:8000")
            print("🎨 UI Interface at: http://localhost:8000/ui")
            print("🔧 API Documentation at: http://localhost:8000/docs")
            print("🚀 Direct Streamlit at: http://localhost:8501")
            print()
            print("✨ Features:")
            print("   • Select APP ID from predefined list")
            print("   • Choose repository based on APP ID")
            print("   • Select branch from available branches")
            print("   • Configure GitHub token and scan settings")
            print("   • Real-time scan progress monitoring")
            print("   • View HTML and JSON reports")
            print()
            print("Press Ctrl+C to stop the server")
        else:
            print("⚠️ Server may not be fully ready, but you can try accessing it")
            print("📱 Try accessing: http://localhost:8000")
        
        # Keep running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n👋 Stopping simple app...")
            process.terminate()
            process.wait()
            print("✅ Server stopped")
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 