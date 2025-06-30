"""
CodeGates API Routes Package

Contains all API route definitions organized by functionality.
"""

from flask import Blueprint

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Import all route modules to register them with the blueprint
from . import auth
from . import scan
from . import projects
from . import reports
from . import admin
from . import webhooks

__all__ = ['api_bp'] 