#!/usr/bin/env python3
"""
CodeGates API Server

Main entry point for running the CodeGates API server.
Supports development, production, and testing environments.
"""

import os
import sys
import logging
import secrets
from pathlib import Path

# Add the parent directory to the Python path to import codegates
sys.path.insert(0, str(Path(__file__).parent))

from api.app import create_app
from api.config import Config


def setup_environment():
    """Setup environment variables and paths"""
    # Set default environment if not specified
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'development'
    
    # Generate secure secret key if not provided
    if 'SECRET_KEY' not in os.environ:
        secure_key = secrets.token_urlsafe(32)
        os.environ['SECRET_KEY'] = secure_key
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'development':
            print("🔐 Generated secure SECRET_KEY for development")
        else:
            print("⚠️ No SECRET_KEY provided - generated secure random key")
    
    # Set default database URL if not specified
    if 'DATABASE_URL' not in os.environ:
        db_path = Path(__file__).parent / 'codegates.db'
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'


def main():
    """Main entry point"""
    setup_environment()
    
    # Get configuration environment
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app
    app = create_app(env)
    
    # Configure logging for development
    if env == 'development':
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Get host and port from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = env == 'development'
    
    print(f"""
🛡️  CodeGates API Server
========================
Environment: {env}
Host: {host}
Port: {port}
Debug: {debug}
API Docs: http://{host}:{port}/docs
Health Check: http://{host}:{port}/health
""")
    
    # Run the application
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 CodeGates API Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 