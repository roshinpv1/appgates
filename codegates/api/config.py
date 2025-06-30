"""
CodeGates API Configuration

Environment-specific configuration classes for the CodeGates API.
Supports development, production, and testing environments.
"""

import os
from datetime import timedelta
import secrets


class BaseConfig:
    """Base configuration with common settings"""
    
    # Application settings
    APP_NAME = 'CodeGates API'
    VERSION = '1.0.0'
    
    # Generate a secure random secret key if not provided
    _default_secret = secrets.token_urlsafe(32)
    SECRET_KEY = os.environ.get('SECRET_KEY') or _default_secret
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///codegates.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Redis settings (for caching and rate limiting)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
    
    # Rate limiting
    RATE_LIMITS = [
        "1000 per hour",
        "100 per minute",
        "10 per second"
    ]
    
    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Container-friendly upload directory with fallbacks
    _upload_fallbacks = [
        os.environ.get('UPLOAD_FOLDER'),
        '/app/uploads',       # Common container path
        './uploads',          # Local fallback
        '/tmp/codegates-uploads'  # Traditional fallback
    ]
    UPLOAD_FOLDER = next((path for path in _upload_fallbacks if path), './uploads')
    
    ALLOWED_EXTENSIONS = {'.py', '.java', '.js', '.ts', '.cs', '.zip', '.tar.gz'}
    
    # Celery settings (for background tasks)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/1'
    
    # LLM settings
    LLM_PROVIDERS = {
        'openai': {
            'api_key': os.environ.get('OPENAI_API_KEY'),
            'base_url': os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            'default_model': 'gpt-4',
            'timeout': 60
        },
        'anthropic': {
            'api_key': os.environ.get('ANTHROPIC_API_KEY'),
            'base_url': os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
            'default_model': 'claude-3-sonnet-20240229',
            'timeout': 60
        },
        'gemini': {
            'api_key': os.environ.get('GEMINI_API_KEY'),
            'base_url': os.environ.get('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com'),
            'default_model': 'gemini-pro',
            'timeout': 60
        },
        'ollama': {
            'base_url': os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
            'default_model': 'llama2',
            'timeout': 120
        },
        'local': {
            'base_url': os.environ.get('LOCAL_LLM_URL', 'http://localhost:8000'),
            'api_key': os.environ.get('LOCAL_LLM_API_KEY'),
            'default_model': os.environ.get('LOCAL_MODEL'),
            'timeout': 120
        }
    }
    
    # Security settings
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'"
    }
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE')
    
    # Git settings - container-friendly temporary directories
    GIT_TIMEOUT = int(os.environ.get('GIT_TIMEOUT', '300'))  # 5 minutes
    
    # Try multiple temp directory options for container compatibility
    _temp_repo_options = [
        os.environ.get('TEMP_REPO_DIR'),
        '/app/temp',              # Container app temp
        './temp',                 # Local relative temp
        '/tmp/codegates-repos'    # Traditional temp
    ]
    TEMP_REPO_DIR = next((path for path in _temp_repo_options if path), './temp')
    
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    
    # API settings
    API_TITLE = 'CodeGates API'
    API_DESCRIPTION = 'Production-ready hard gate validation and code quality analysis'
    API_VERSION = 'v1'
    API_DOCS_URL = '/docs'
    API_REDOC_URL = '/redoc'
    
    # Cache settings
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Background job settings
    JOB_TIMEOUT = int(os.environ.get('JOB_TIMEOUT', '3600'))  # 1 hour
    MAX_CONCURRENT_JOBS = int(os.environ.get('MAX_CONCURRENT_JOBS', '10'))
    
    # Webhook settings
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
    WEBHOOK_TIMEOUT = int(os.environ.get('WEBHOOK_TIMEOUT', '30'))


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    ENV = 'development'
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = True
    
    # Relaxed rate limits for development
    RATE_LIMITS = [
        "10000 per hour",
        "1000 per minute",
        "100 per second"
    ]
    
    # Disable some security features for easier development
    SECURITY_HEADERS = {}
    
    # Allow all origins in development
    CORS_ORIGINS = ['*']


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Warning if SECRET_KEY not provided in production
    def __init__(self):
        if not os.environ.get('SECRET_KEY'):
            import warnings
            warnings.warn(
                "⚠️ SECRET_KEY environment variable not set in production. "
                "Using auto-generated key. For session persistence across restarts, "
                "set SECRET_KEY environment variable.",
                RuntimeWarning,
                stacklevel=2
            )
            print("⚠️ Production Warning: SECRET_KEY not set - using auto-generated key")
    
    # Database connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # Stricter rate limits
    RATE_LIMITS = [
        "500 per hour",
        "50 per minute",
        "5 per second"
    ]
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    LOG_FILE = '/var/log/codegates/api.log'
    
    # Enhanced security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production cache settings
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    ENV = 'testing'
    DEBUG = True
    TESTING = True
    
    # In-memory database for testing
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Disable rate limiting for tests
    RATE_LIMITS = []
    
    # Use memory cache for testing
    CACHE_TYPE = 'simple'
    
    # Shorter timeouts for faster tests
    GIT_TIMEOUT = 30
    JOB_TIMEOUT = 60
    
    # Disable external API calls in tests
    LLM_PROVIDERS = {}


class Config:
    """Configuration factory"""
    
    _configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    @classmethod
    def get_config(cls, config_name=None):
        """Get configuration class by name"""
        if config_name is None:
            config_name = os.environ.get('FLASK_ENV', 'development')
        
        config_class = cls._configs.get(config_name)
        if not config_class:
            raise ValueError(f"Unknown configuration: {config_name}")
        
        return config_class
    
    @classmethod
    def get_available_configs(cls):
        """Get list of available configuration names"""
        return list(cls._configs.keys()) 