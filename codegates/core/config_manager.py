"""
Configuration Manager - Centralizes gate configuration loading and validation
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class ConfigManager:
    """Singleton configuration manager for gate_config.yml"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _get_config_path(self) -> Path:
        """Get configuration file path with fallback options"""
        # Try environment variable first
        env_path = os.getenv('CODEGATES_CONFIG_PATH')
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            logger.warning(f"Config path from environment not found: {env_path}")
        
        # Try common locations
        search_paths = [
            Path("codegates/core/gate_config.yml"),  # Default location
            Path("gate_config.yml"),  # Current directory
            Path("config/gate_config.yml"),  # Config directory
            Path("../codegates/core/gate_config.yml"),  # One level up
            Path(os.path.expanduser("~/.codegates/gate_config.yml")),  # User home
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        # Return default path for error messaging
        return Path("codegates/core/gate_config.yml")
    
    def _load_config(self) -> None:
        """Load and validate gate configuration"""
        config_path = self._get_config_path()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                logger.info(f"Loaded gate configuration from {config_path}")
                
                # Basic validation
                if not isinstance(self._config, dict):
                    raise ValueError("Configuration must be a dictionary")
                if 'hard_gates' not in self._config:
                    raise ValueError("Configuration missing 'hard_gates' section")
                if not isinstance(self._config['hard_gates'], list):
                    raise ValueError("'hard_gates' must be a list")
                
                # Validate each gate has required fields
                for gate in self._config['hard_gates']:
                    if not isinstance(gate, dict):
                        raise ValueError("Each gate must be a dictionary")
                    if 'id' not in gate or 'name' not in gate:
                        raise ValueError("Each gate must have 'id' and 'name' fields")
                    if 'patterns' not in gate:
                        logger.warning(f"Gate '{gate['name']}' has no patterns defined")
        
        except Exception as e:
            logger.error(f"Failed to load gate configuration from {config_path}: {e}")
            # Use empty config as fallback
            self._config = {'hard_gates': []}
            raise RuntimeError(f"Failed to load gate configuration: {e}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the loaded configuration"""
        return self._config
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self._config = None
        self._load_config()
        logger.info("Gate configuration reloaded")
    
    @lru_cache(maxsize=128)
    def get_patterns_for_gate(self, gate_name: str, language: str) -> Dict[str, Any]:
        """Get patterns for a specific gate and language"""
        if not self._config or 'hard_gates' not in self._config:
            return {}
        
        for gate in self._config['hard_gates']:
            if gate.get('name') == gate_name:
                patterns = gate.get('patterns', {})
                return patterns.get(language, {})
        
        return {}

# Global instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def reload_config() -> None:
    """Reload the global configuration"""
    if _config_manager is not None:
        _config_manager.reload() 