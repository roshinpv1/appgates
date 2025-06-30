"""
CodeGates API Utilities

Common utility functions for the API.
"""

import re
import uuid
import requests
from urllib.parse import urlparse


def generate_request_id():
    """Generate a unique request ID"""
    return str(uuid.uuid4())


def validate_github_url(url):
    """
    Validate GitHub repository URL format
    
    Args:
        url (str): GitHub repository URL
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        
        # Check basic URL format
        if not all([parsed.scheme, parsed.netloc, parsed.path]):
            return False
            
        # Check if it's a GitHub URL
        if not parsed.netloc.endswith('github.com'):
            return False
            
        # Check path format (should be /owner/repo)
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 2:
            return False
            
        return True
        
    except Exception:
        return False


def validate_github_token(token):
    """
    Validate GitHub token by making a test API call
    
    Args:
        token (str): GitHub personal access token
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Make a test API call to get user info
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(
            'https://api.github.com/user',
            headers=headers,
            timeout=5
        )
        
        # Check if token is valid and has required scopes
        if response.status_code == 200:
            scopes = response.headers.get('X-OAuth-Scopes', '').split(',')
            required_scopes = {'repo', 'read:user'}
            
            # Check if token has required scopes
            token_scopes = {scope.strip() for scope in scopes}
            return bool(required_scopes & token_scopes)
            
        return False
        
    except Exception:
        return False


def setup_logging(app):
    """Configure application logging"""
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        # Ensure log directory exists
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Configure file handler
        file_handler = RotatingFileHandler(
            'logs/codegates.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d] '
            'request_id=%(request_id)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Set base logging level
        app.logger.setLevel(logging.INFO)
        app.logger.info('CodeGates API startup') 