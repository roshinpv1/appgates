"""
CodeGates API Scan Routes

Handles repository scanning and analysis endpoints.
"""

import re
from flask import jsonify, request, current_app, g
from . import api_bp
from ..models import Scan, Repository
from ..services import GitHubService, ScanService
from ..utils import validate_github_token, validate_github_url
from ..decorators import auth_required, rate_limit


class ScanError(Exception):
    """Custom exception for scan errors"""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


@api_bp.route('/scan', methods=['POST'])
@auth_required
@rate_limit("5 per minute")
def start_scan():
    """
    Start a new repository scan
    
    Request body:
    {
        "repository_url": "https://github.com/owner/repo",
        "branch": "main",  # optional, defaults to main
        "github_token": "ghp_xxx",  # optional, required for private repositories
        "scan_options": {  # optional
            "threshold": 70  # optional, defaults to 70
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'repository_url' not in data:
            raise ScanError('Repository URL is required')
        
        # Validate GitHub URL format
        repo_url = data['repository_url']
        if not validate_github_url(repo_url):
            raise ScanError('Invalid GitHub repository URL format')
        
        # Get optional parameters
        github_token = data.get('github_token')
        branch = data.get('branch', 'main')
        scan_options = data.get('scan_options', {})
        threshold = scan_options.get('threshold', 70)
        
        try:
            # Initialize services with or without token
            github_service = GitHubService(github_token) if github_token else GitHubService(None)
            scan_service = ScanService()
            
            # Try to access repository
            if not github_service.can_access_repository(repo_url):
                if github_token:
                    raise ScanError('Cannot access repository. Please check if the token has access to this repository.', 403)
                else:
                    raise ScanError('Repository is private. Please provide a GitHub token with repo scope.', 401)
            
            # Create repository record
            repo = Repository.create_or_get(
                url=repo_url,
                branch=branch,
                owner=github_service.get_repo_owner(repo_url),
                name=github_service.get_repo_name(repo_url)
            )
            
            # Start scan
            scan = scan_service.start_scan(
                repository=repo,
                branch=branch,
                threshold=threshold,
                github_token=github_token
            )
            
            return jsonify({
                'scan_id': scan.id,
                'status': scan.status,
                'repository': {
                    'url': repo.url,
                    'branch': branch
                },
                'created_at': scan.created_at.isoformat(),
                'message': 'Scan started successfully'
            }), 202
            
        except ValueError as e:
            raise ScanError(str(e))
            
    except ScanError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': str(e)
        }), e.status_code
        
    except Exception as e:
        current_app.logger.error(f"Scan error: {str(e)}", 
                               extra={'request_id': g.request_id},
                               exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to start scan'
        }), 500


@api_bp.route('/scan/<scan_id>', methods=['GET'])
@auth_required
def get_scan_status(scan_id):
    """Get scan status and results"""
    try:
        scan = Scan.get_by_id(scan_id)
        if not scan:
            return jsonify({
                'error': 'Not Found',
                'message': 'Scan not found'
            }), 404
        
        return jsonify({
            'scan_id': scan.id,
            'status': scan.status,
            'score': scan.score,
            'gates': scan.gates,
            'recommendations': scan.recommendations,
            'report_url': scan.report_url,
            'created_at': scan.created_at.isoformat(),
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting scan status: {str(e)}", 
                               extra={'request_id': g.request_id},
                               exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to get scan status'
        }), 500 