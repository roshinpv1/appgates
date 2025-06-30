"""
Environment Configuration Loader for CodeGates
Ensures consistent loading of environment variables across all components
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class EnvironmentLoader:
    """Centralized environment variable loader with .env file support"""
    
    _loaded = False
    _env_vars = {}
    
    @classmethod
    def load_environment(cls, force_reload: bool = False) -> Dict[str, Any]:
        """Load environment variables from .env files and system environment"""
        
        if cls._loaded and not force_reload:
            return cls._env_vars
        
        # Try to import python-dotenv
        try:
            from dotenv import load_dotenv, find_dotenv
            dotenv_available = True
        except ImportError:
            print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")
            dotenv_available = False
        
        # Find project root
        project_root = cls._find_project_root()
        
        # Load .env files in order of precedence
        env_files = [
            project_root / '.env.local',     # Local overrides (highest priority)
            project_root / '.env',           # Main environment file
            project_root / 'config.env',     # Config environment file
            project_root / '.env.example'    # Example file (lowest priority)
        ]
        
        print("🔧 Loading environment configuration...")
        
        if dotenv_available:
            for env_file in env_files:
                if env_file.exists():
                    print(f"   📄 Loading {env_file.name}")
                    load_dotenv(env_file, override=False)  # Don't override existing vars
        else:
            print("   ⚠️ Skipping .env files (python-dotenv not available)")
        
        # Load and validate LLM configuration
        cls._env_vars = cls._load_llm_config()
        cls._loaded = True
        
        print(f"✅ Environment loaded with {len(cls._env_vars)} LLM variables")
        return cls._env_vars
    
    @classmethod
    def _find_project_root(cls) -> Path:
        """Find the project root directory"""
        
        # Start from current file location
        current = Path(__file__).parent
        
        # Look for project indicators
        indicators = ['.git', 'pyproject.toml', 'setup.py', 'requirements.txt', '.env']
        
        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent
        
        # Fallback to current working directory
        return Path.cwd()
    
    @classmethod
    def _load_llm_config(cls) -> Dict[str, Any]:
        """Load and validate LLM configuration"""
        
        config = {}
        
        # OpenAI Configuration
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            config['openai'] = {
                'api_key': openai_key,
                'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
                'base_url': os.getenv('OPENAI_BASE_URL'),
                'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
                'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
            }
            print(f"   ✅ OpenAI configuration loaded (model: {config['openai']['model']})")
        
        # Anthropic Configuration
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            config['anthropic'] = {
                'api_key': anthropic_key,
                'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229'),
                'base_url': os.getenv('ANTHROPIC_BASE_URL'),
                'temperature': float(os.getenv('ANTHROPIC_TEMPERATURE', '0.1')),
                'max_tokens': int(os.getenv('ANTHROPIC_MAX_TOKENS', '4000'))
            }
            print(f"   ✅ Anthropic configuration loaded (model: {config['anthropic']['model']})")
        
        # Local LLM Configuration
        local_url = os.getenv('LOCAL_LLM_URL') or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
        config['local'] = {
            'base_url': local_url,
            'model': os.getenv('LOCAL_MODEL') or os.getenv('LOCAL_LLM_MODEL', 'meta-llama-3.1-8b-instruct'),
            'api_key': os.getenv('LOCAL_LLM_API_KEY', 'not-needed'),
            'temperature': float(os.getenv('LOCAL_LLM_TEMPERATURE', '0.1')),
            'max_tokens': int(os.getenv('LOCAL_LLM_MAX_TOKENS', '4000'))
        }
        print(f"   📡 Local LLM configuration: {local_url} (model: {config['local']['model']})")
        
        # Enterprise LLM Configuration
        enterprise_url = os.getenv('ENTERPRISE_LLM_URL')
        if enterprise_url:
            config['enterprise'] = {
                'url': enterprise_url,
                'model': os.getenv('ENTERPRISE_LLM_MODEL', 'meta-llama-3.1-8b-instruct'),
                'api_key': os.getenv('ENTERPRISE_LLM_API_KEY'),
                'token': os.getenv('ENTERPRISE_LLM_TOKEN'),
                'refresh_url': os.getenv('ENTERPRISE_LLM_REFRESH_URL'),
                'client_id': os.getenv('ENTERPRISE_LLM_CLIENT_ID'),
                'client_secret': os.getenv('ENTERPRISE_LLM_CLIENT_SECRET'),
                'headers': os.getenv('ENTERPRISE_LLM_HEADERS', '{}'),
                'temperature': float(os.getenv('ENTERPRISE_LLM_TEMPERATURE', '0.1')),
                'max_tokens': int(os.getenv('ENTERPRISE_LLM_MAX_TOKENS', '4000'))
            }
            print(f"   🏢 Enterprise LLM configuration loaded: {enterprise_url}")
        
        # Ollama Configuration (alternative to local)
        ollama_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        if ollama_url != 'http://localhost:11434' or os.getenv('OLLAMA_MODEL'):
            config['ollama'] = {
                'host': ollama_url,
                'model': os.getenv('OLLAMA_MODEL', 'meta-llama-3.1-8b-instruct'),
                'temperature': float(os.getenv('OLLAMA_TEMPERATURE', '0.1')),
                'num_predict': int(os.getenv('OLLAMA_NUM_PREDICT', '4000'))
            }
            print(f"   🦙 Ollama configuration loaded: {ollama_url}")
        
        return config
    
    @classmethod
    def get_llm_config(cls, provider: str) -> Optional[Dict[str, Any]]:
        """Get LLM configuration for a specific provider"""
        
        if not cls._loaded:
            cls.load_environment()
        
        return cls._env_vars.get(provider.lower())
    
    @classmethod
    def get_preferred_llm_provider(cls) -> Optional[str]:
        """Get the preferred LLM provider based on available configuration"""
        
        if not cls._loaded:
            cls.load_environment()
        
        # Priority order: OpenAI > Anthropic > Local > Enterprise > Ollama
        providers = ['openai', 'anthropic', 'local', 'enterprise', 'ollama']
        
        for provider in providers:
            if provider in cls._env_vars:
                # Additional validation for cloud providers
                if provider in ['openai', 'anthropic']:
                    if cls._env_vars[provider].get('api_key'):
                        return provider
                else:
                    return provider
        
        return None
    
    @classmethod
    def validate_environment(cls) -> Dict[str, bool]:
        """Validate environment configuration"""
        
        if not cls._loaded:
            cls.load_environment()
        
        validation = {}
        
        # Check each provider
        for provider, config in cls._env_vars.items():
            if provider == 'openai':
                validation[provider] = bool(config.get('api_key'))
            elif provider == 'anthropic':
                validation[provider] = bool(config.get('api_key'))
            elif provider == 'local':
                validation[provider] = bool(config.get('base_url'))
            elif provider == 'enterprise':
                validation[provider] = bool(config.get('url') and 
                                          (config.get('token') or config.get('api_key')))
            elif provider == 'ollama':
                validation[provider] = bool(config.get('host'))
            else:
                validation[provider] = True
        
        return validation
    
    @classmethod
    def create_sample_env_file(cls, path: Optional[Path] = None) -> Path:
        """Create a sample .env file with LLM configuration"""
        
        if path is None:
            path = cls._find_project_root() / '.env.example'
        
        sample_content = """# CodeGates LLM Configuration
# Choose one or more LLM providers

# OpenAI Configuration (Cloud)
# OPENAI_API_KEY=your-openai-api-key-here
# OPENAI_MODEL=gpt-4
# OPENAI_TEMPERATURE=0.1
# OPENAI_MAX_TOKENS=4000

# Anthropic Configuration (Cloud)
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# ANTHROPIC_MODEL=claude-3-sonnet-20240229
# ANTHROPIC_TEMPERATURE=0.1
# ANTHROPIC_MAX_TOKENS=4000

# Local LLM Configuration (Free, Private)
LOCAL_LLM_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=meta-llama-3.1-8b-instruct
LOCAL_LLM_API_KEY=not-needed
LOCAL_LLM_TEMPERATURE=0.1
LOCAL_LLM_MAX_TOKENS=4000

# Ollama Configuration (Alternative Local)
# OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=meta-llama-3.1-8b-instruct
# OLLAMA_TEMPERATURE=0.1
# OLLAMA_NUM_PREDICT=4000

# Enterprise LLM Configuration
# ENTERPRISE_LLM_URL=https://your-enterprise-llm-endpoint
# ENTERPRISE_LLM_MODEL=meta-llama-3.1-8b-instruct
# ENTERPRISE_LLM_API_KEY=your-enterprise-api-key
# ENTERPRISE_LLM_TOKEN=your-enterprise-token
# ENTERPRISE_LLM_REFRESH_URL=https://your-token-refresh-endpoint
# ENTERPRISE_LLM_CLIENT_ID=your-client-id
# ENTERPRISE_LLM_CLIENT_SECRET=your-client-secret
# ENTERPRISE_LLM_HEADERS={}
# ENTERPRISE_LLM_TEMPERATURE=0.1
# ENTERPRISE_LLM_MAX_TOKENS=4000

# CodeGates Configuration
# CODEGATES_LOG_LEVEL=INFO
# CODEGATES_MAX_FILE_SIZE=1048576
# CODEGATES_EXCLUDE_PATTERNS=node_modules/**,.git/**,**/__pycache__/**
"""
        
        with open(path, 'w') as f:
            f.write(sample_content)
        
        print(f"✅ Sample environment file created: {path}")
        return path
    
    @classmethod
    def install_dotenv_if_needed(cls) -> bool:
        """Install python-dotenv if not available"""
        
        try:
            import dotenv
            return True
        except ImportError:
            try:
                import subprocess
                import sys
                
                print("📦 Installing python-dotenv...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'python-dotenv'
                ], check=True, capture_output=True)
                
                print("✅ python-dotenv installed successfully")
                return True
            except Exception as e:
                print(f"❌ Failed to install python-dotenv: {e}")
                return False


# Auto-load environment when module is imported
EnvironmentLoader.load_environment() 