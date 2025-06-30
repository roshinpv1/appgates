"""
CodeGates API Package

Contains both Flask and FastAPI server implementations.
"""

# FastAPI server (simple with JIRA integration) - Primary
try:
    from .server import app as fastapi_app, start_server
    FASTAPI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ FastAPI server not available: {e}")
    FASTAPI_AVAILABLE = False
    fastapi_app = None
    start_server = None

# Flask API (full-featured with auth) - Optional
try:
    from .app import create_app
    FLASK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Flask server not available: {e}")
    FLASK_AVAILABLE = False
    create_app = None

__all__ = [
    'fastapi_app',         # FastAPI app instance (primary)
    'start_server',        # FastAPI server starter (primary)
    'create_app',          # Flask app factory (optional)
    'FASTAPI_AVAILABLE',   # FastAPI availability flag
    'FLASK_AVAILABLE'      # Flask availability flag
] 