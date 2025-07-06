"""
Configuration Loader Utility

Loads configuration from environment variables, .env files, and provides
defaults with type conversion and validation.
"""

import os
from typing import Any, Dict, List, Optional, Union, TypeVar, Type
from pathlib import Path
import logging

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration loader with environment variable support"""
    
    def __init__(self, env_file_paths: Optional[List[str]] = None):
        """
        Initialize configuration loader
        
        Args:
            env_file_paths: List of .env file paths to load (in order of priority)
        """
        self.env_vars = {}
        self._load_env_files(env_file_paths or ['.env', 'config/.env', 'codegates/config/.env'])
        self._load_system_env()
    
    def _load_env_files(self, file_paths: List[str]):
        """Load environment variables from .env files"""
        for file_path in file_paths:
            env_path = Path(file_path)
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                # Don't override if already set (priority order)
                                if key.strip() not in self.env_vars:
                                    self.env_vars[key.strip()] = value.strip()
                    logger.info(f"Loaded environment variables from {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
    
    def _load_system_env(self):
        """Load system environment variables (highest priority)"""
        for key, value in os.environ.items():
            self.env_vars[key] = value
    
    def get(self, key: str, default: Any = None, type_class: Type[T] = str) -> T:
        """
        Get configuration value with type conversion
        
        Args:
            key: Environment variable key
            default: Default value if not found
            type_class: Type to convert the value to
            
        Returns:
            Converted value or default
        """
        value = self.env_vars.get(key)
        
        if value is None:
            return default
        
        try:
            return self._convert_type(value, type_class)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {key}={value} to {type_class.__name__}: {e}")
            return default
    
    def get_boolean(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.env_vars.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_list(self, key: str, default: Optional[List[str]] = None, separator: str = ',') -> List[str]:
        """Get list configuration value"""
        value = self.env_vars.get(key)
        if value is None:
            return default or []
        
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        return self.get(key, default, int)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        return self.get(key, default, float)
    
    def _convert_type(self, value: str, type_class: Type[T]) -> T:
        """Convert string value to specified type"""
        if type_class == str:
            return value
        elif type_class == int:
            return int(value)
        elif type_class == float:
            return float(value)
        elif type_class == bool:
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        else:
            # Try direct conversion
            return type_class(value)
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration"""
        return {
            'host': self.get('CODEGATES_API_HOST', '0.0.0.0'),
            'port': self.get_int('CODEGATES_API_PORT', 8000),
            'base_url': self.get('CODEGATES_API_BASE_URL'),  # Will be auto-generated if None
            'version_prefix': self.get('CODEGATES_API_VERSION_PREFIX', '/api/v1'),
            'title': self.get('CODEGATES_API_TITLE', 'MyGates API'),
            'description': self.get('CODEGATES_API_DESCRIPTION', 'API for validating code quality gates across different programming languages'),
            'docs_enabled': self.get_boolean('CODEGATES_API_DOCS_ENABLED', True),
            'docs_url': self.get('CODEGATES_API_DOCS_URL', '/docs'),
            'redoc_url': self.get('CODEGATES_API_REDOC_URL', '/redoc'),
        }
    
    def get_timeout_config(self) -> Dict[str, Any]:
        """Get timeout configuration for all operations"""
        return {
            # Repository operations
            'git_clone_timeout': self.get_int('CODEGATES_GIT_CLONE_TIMEOUT', 300),  # 5 minutes
            'git_ls_remote_timeout': self.get_int('CODEGATES_GIT_LS_REMOTE_TIMEOUT', 30),  # 30 seconds
            'api_download_timeout': self.get_int('CODEGATES_API_DOWNLOAD_TIMEOUT', 120),  # 2 minutes
            
            # Analysis operations
            'analysis_timeout': self.get_int('CODEGATES_ANALYSIS_TIMEOUT', 1800),  # 3 minutes
            'llm_request_timeout': self.get_int('CODEGATES_LLM_REQUEST_TIMEOUT', 300),  # 30 seconds
            
            # HTTP operations
            'http_request_timeout': self.get_int('CODEGATES_HTTP_REQUEST_TIMEOUT', 10),  # 10 seconds
            'health_check_timeout': self.get_int('CODEGATES_HEALTH_CHECK_TIMEOUT', 5),  # 5 seconds
            
            # JIRA integration
            'jira_request_timeout': self.get_int('CODEGATES_JIRA_REQUEST_TIMEOUT', 30),  # 30 seconds
            'jira_health_timeout': self.get_int('CODEGATES_JIRA_HEALTH_TIMEOUT', 10),  # 10 seconds
            
            # GitHub Enterprise
            'github_connect_timeout': self.get_int('CODEGATES_GITHUB_CONNECT_TIMEOUT', 30),  # 30 seconds
            'github_read_timeout': self.get_int('CODEGATES_GITHUB_READ_TIMEOUT', 120),  # 2 minutes
            
            # VS Code extension
            'vscode_api_timeout': self.get_int('CODEGATES_VSCODE_API_TIMEOUT', 300),  # 5 minutes
            
            # LLM batch processing
            'llm_batch_timeout': self.get_int('CODEGATES_LLM_BATCH_TIMEOUT', 30),  # 30 seconds per request
        }
    
    def get_git_config(self) -> Dict[str, Any]:
        """Get Git and repository checkout configuration"""
        timeout_config = self.get_timeout_config()
        return {
            'prefer_api_checkout': self.get_boolean('CODEGATES_PREFER_API_CHECKOUT', False),
            'enable_api_fallback': self.get_boolean('CODEGATES_ENABLE_API_FALLBACK', True),
            'git_timeout': timeout_config['git_clone_timeout'],  # Use timeout config
            'api_timeout': timeout_config['api_download_timeout'],  # Use timeout config
            'max_repo_size': self.get_int('CODEGATES_MAX_REPO_SIZE', 100),  # MB
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            'origins': self.get_list('CODEGATES_CORS_ORIGINS', [
                'vscode-webview://*',
                'http://localhost:*',
                'http://127.0.0.1:*',
                'https://localhost:*',
                'https://127.0.0.1:*'
            ]),
            'methods': self.get_list('CODEGATES_CORS_METHODS', [
                'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'
            ]),
            'headers': self.get_list('CODEGATES_CORS_HEADERS', [
                'Accept', 'Accept-Language', 'Content-Language', 'Content-Type',
                'Authorization', 'X-Requested-With', 'User-Agent', 'Origin',
                'Access-Control-Request-Method', 'Access-Control-Request-Headers'
            ]),
            'expose_headers': self.get_list('CODEGATES_CORS_EXPOSE_HEADERS', [
                'Content-Type', 'Content-Length', 'Date', 'Server'
            ])
        }
    
    def get_vscode_config(self) -> Dict[str, Any]:
        """Get VS Code extension configuration"""
        api_config = self.get_api_config()
        base_url = api_config['base_url']
        if not base_url:
            base_url = f"http://localhost:{api_config['port']}"
        
        return {
            'api_base_url': self.get('VSCODE_API_BASE_URL', f"{base_url}{api_config['version_prefix']}"),
            'api_timeout': self.get_int('VSCODE_API_TIMEOUT', 300),
            'api_retries': self.get_int('VSCODE_API_RETRIES', 3),
        }
    
    def get_reports_config(self) -> Dict[str, Any]:
        """Get reports configuration"""
        api_config = self.get_api_config()
        base_url = api_config['base_url']
        if not base_url:
            base_url = f"http://localhost:{api_config['port']}"
        
        return {
            'reports_dir': self.get('CODEGATES_REPORTS_DIR', 'reports'),
            'report_url_base': self.get('CODEGATES_REPORT_URL_BASE', f"{base_url}{api_config['version_prefix']}/reports"),
            'html_reports_enabled': self.get_boolean('CODEGATES_HTML_REPORTS_ENABLED', True),
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            'enabled': self.get_boolean('CODEGATES_LLM_ENABLED', False),
            'provider': self.get('CODEGATES_LLM_PROVIDER', 'local'),
            'model': self.get('CODEGATES_LLM_MODEL', 'meta-llama-3.1-8b-instruct'),
            'temperature': self.get_float('CODEGATES_LLM_TEMPERATURE', 0.1),
            'max_tokens': self.get_int('CODEGATES_LLM_MAX_TOKENS', 8000),
            
            # Provider-specific configs
            'local': {
                'url': self.get('LOCAL_LLM_URL', 'http://localhost:1234/v1'),
                'api_key': self.get('LOCAL_LLM_API_KEY', 'not-needed'),
                'model': self.get('LOCAL_LLM_MODEL', 'meta-llama-3.1-8b-instruct'),
                'temperature': self.get_float('LOCAL_LLM_TEMPERATURE', 0.1),
                'max_tokens': self.get_int('LOCAL_LLM_MAX_TOKENS', 8000),
            },
            'openai': {
                'api_key': self.get('OPENAI_API_KEY'),
                'base_url': self.get('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                'model': self.get('OPENAI_MODEL', 'gpt-4'),
                'temperature': self.get_float('OPENAI_TEMPERATURE', 0.1),
                'max_tokens': self.get_int('OPENAI_MAX_TOKENS', 8000),
            },
            'anthropic': {
                'api_key': self.get('ANTHROPIC_API_KEY'),
                'base_url': self.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
                'model': self.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229'),
                'temperature': self.get_float('ANTHROPIC_TEMPERATURE', 0.1),
                'max_tokens': self.get_int('ANTHROPIC_MAX_TOKENS', 8000),
            },
        }
    
    def get_ssl_config(self) -> Dict[str, Any]:
        """Get SSL/TLS configuration for GitHub Enterprise"""
        return {
            'verify_ssl': self.get_boolean('CODEGATES_SSL_VERIFY', True),
            'ca_bundle': self.get('CODEGATES_SSL_CA_BUNDLE'),  # Path to custom CA bundle
            'client_cert': self.get('CODEGATES_SSL_CLIENT_CERT'),  # Path to client certificate
            'client_key': self.get('CODEGATES_SSL_CLIENT_KEY'),  # Path to client private key
            'disable_warnings': self.get_boolean('CODEGATES_SSL_DISABLE_WARNINGS', False),
            'ignore_self_signed': self.get_boolean('CODEGATES_SSL_IGNORE_SELF_SIGNED', False),  # For dev environments
        }

    def get_github_enterprise_config(self) -> Dict[str, Any]:
        """Get GitHub Enterprise specific configuration"""
        return {
            'default_hostname': self.get('GITHUB_ENTERPRISE_HOSTNAME'),  # e.g., github.company.com
            'api_version': self.get('GITHUB_ENTERPRISE_API_VERSION', 'v3'),
            'connect_timeout': self.get_int('GITHUB_ENTERPRISE_CONNECT_TIMEOUT', 30),
            'read_timeout': self.get_int('GITHUB_ENTERPRISE_READ_TIMEOUT', 120),
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration sections"""
        return {
            'api': self.get_api_config(),
            'git': self.get_git_config(),
            'cors': self.get_cors_config(),
            'vscode': self.get_vscode_config(),
            'reports': self.get_reports_config(),
            'llm': self.get_llm_config(),
            'ssl': self.get_ssl_config(),
            'github_enterprise': self.get_github_enterprise_config(),
            'timeouts': self.get_timeout_config(),
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        api_config = self.get_api_config()
        
        # Validate API configuration
        if not (1 <= api_config['port'] <= 65535):
            issues.append(f"Invalid API port: {api_config['port']} (must be 1-65535)")
        
        if api_config['base_url'] and not api_config['base_url'].startswith(('http://', 'https://')):
            issues.append(f"Invalid API base URL: {api_config['base_url']} (must start with http:// or https://)")
        
        # Validate LLM configuration
        llm_config = self.get_llm_config()
        if llm_config['enabled']:
            provider = llm_config['provider']
            if provider not in ['openai', 'anthropic', 'local', 'gemini']:
                issues.append(f"Unsupported LLM provider: {provider}")
            
            if provider == 'openai' and not llm_config['openai']['api_key']:
                issues.append("OpenAI API key is required when using OpenAI provider")
            
            if provider == 'anthropic' and not llm_config['anthropic']['api_key']:
                issues.append("Anthropic API key is required when using Anthropic provider")
        
        return issues


# Global configuration loader instance
config_loader = ConfigLoader()


def get_config() -> ConfigLoader:
    """Get the global configuration loader instance"""
    return config_loader 