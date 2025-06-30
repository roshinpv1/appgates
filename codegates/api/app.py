"""
CodeGates API Application Factory

Creates and configures the Flask application with all necessary
middleware, error handlers, and route registration.
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
import jwt
from functools import wraps

from .config import Config
from .routes import api_bp
from .models import init_db
from .middleware import RequestMiddleware, SecurityMiddleware
from .utils import setup_logging, generate_request_id


def create_app(config_name='development'):
    """
    Application factory pattern for creating Flask app instances
    
    Args:
        config_name: Configuration environment ('development', 'production', 'testing')
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config_class = Config.get_config(config_name)
    app.config.from_object(config_class)
    
    # Setup logging
    setup_logging(app)
    
    # Trust proxy headers in production
    if config_name == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize database
    init_db(app)
    
    # Register middleware
    register_middleware(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add health check endpoint
    register_health_check(app)
    
    # Add request context processors
    register_context_processors(app)
    
    return app


def init_extensions(app):
    """Initialize Flask extensions"""
    
    # CORS configuration
    CORS(app, 
         origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
         supports_credentials=True,
         expose_headers=['X-Request-ID', 'X-Rate-Limit-Remaining'])
    
    # Rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=app.config.get('RATE_LIMITS', ["100 per hour", "10 per minute"]),
        storage_uri=app.config.get('REDIS_URL', 'memory://'),
        headers_enabled=True
    )
    
    app.limiter = limiter


def register_middleware(app):
    """Register custom middleware"""
    
    # Request ID middleware
    @app.before_request
    def before_request():
        g.request_id = generate_request_id()
        g.start_time = datetime.utcnow()
        
        # Log request
        app.logger.info(f"Request started: {request.method} {request.path}", 
                       extra={'request_id': g.request_id})
    
    @app.after_request
    def after_request(response):
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.request_id
        
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # Log response
        app.logger.info(f"Request completed: {response.status_code}", 
                       extra={'request_id': g.request_id})
        
        return response
    
    # Security middleware
    SecurityMiddleware(app)
    RequestMiddleware(app)


def register_blueprints(app):
    """Register application blueprints"""
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if error.description else 'Invalid request',
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Insufficient permissions',
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'Resource not found',
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': str(error.description),
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat(),
            'retry_after': error.retry_after
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}", 
                        extra={'request_id': getattr(g, 'request_id', None)})
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}", 
                        extra={'request_id': getattr(g, 'request_id', None)},
                        exc_info=True)
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'request_id': getattr(g, 'request_id', None),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


def register_health_check(app):
    """Register health check endpoints"""
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': app.config.get('VERSION', '1.0.0'),
            'environment': app.config.get('ENV', 'development')
        })
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with dependency status"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': app.config.get('VERSION', '1.0.0'),
            'environment': app.config.get('ENV', 'development'),
            'dependencies': {}
        }
        
        # Check database connection
        try:
            # Add database health check here
            health_status['dependencies']['database'] = 'healthy'
        except Exception as e:
            health_status['dependencies']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check Redis connection (if configured)
        if app.config.get('REDIS_URL'):
            try:
                # Add Redis health check here
                health_status['dependencies']['redis'] = 'healthy'
            except Exception as e:
                health_status['dependencies']['redis'] = f'unhealthy: {str(e)}'
                health_status['status'] = 'degraded'
        
        # Check LLM providers
        try:
            # Add LLM provider health checks here
            health_status['dependencies']['llm_providers'] = 'healthy'
        except Exception as e:
            health_status['dependencies']['llm_providers'] = f'degraded: {str(e)}'
            if health_status['status'] == 'healthy':
                health_status['status'] = 'degraded'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code


def register_context_processors(app):
    """Register template context processors"""
    
    @app.context_processor
    def inject_config():
        return {
            'app_name': app.config.get('APP_NAME', 'CodeGates API'),
            'version': app.config.get('VERSION', '1.0.0'),
            'environment': app.config.get('ENV', 'development')
        }


def auth_required(f):
    """Authentication decorator for protected endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode JWT token
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            g.current_user = payload
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function 