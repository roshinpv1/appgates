#!/usr/bin/env python3
"""
Pattern Loader - Loads gate patterns from gate_config.yml and provides them to validators
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from functools import lru_cache
import logging

from ..models import Language, GateType
from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


class PatternLoader:
    """Loads and manages gate validation patterns from configuration"""
    
    def __init__(self):
        """Initialize pattern loader"""
        self._pattern_cache = {}
        self._config_manager = get_config_manager()
    
    def reload_config(self) -> None:
        """Reload configuration"""
        self._pattern_cache.clear()
        self._config_manager.reload()
        logger.info("Gate configuration reloaded")
    
    @lru_cache(maxsize=128)
    def get_patterns_for_gate(self, gate_name: str, language: str) -> List[str]:
        """Get patterns for a specific gate and language"""
        gate_config = self._find_gate_by_name(gate_name)
        if not gate_config:
            logger.warning(f"No configuration found for gate: {gate_name}")
            return []
        
        patterns = gate_config.get('patterns', {})
        
        # Try exact language match first
        if language in patterns:
            return patterns[language]
        
        # Try language variations
        language_mappings = {
            'csharp': 'dotnet',
            'dotnet': 'csharp',
            'js': 'javascript',
            'ts': 'typescript'
        }
        
        alt_language = language_mappings.get(language.lower())
        if alt_language and alt_language in patterns:
            return patterns[alt_language]
        
        # Fall back to all_languages patterns
        if 'all_languages' in patterns:
            return patterns['all_languages']
        
        logger.debug(f"No patterns found for gate '{gate_name}' and language '{language}'")
        return []
    
    def get_patterns_for_gate_type(self, gate_type: GateType, language: Language) -> Dict[str, List[str]]:
        """Get patterns for a gate type and language, organized by pattern category"""
        gate_name = self._gate_type_to_name(gate_type)
        gate_config = self._find_gate_by_name(gate_name)
        
        if not gate_config:
            return {}
        
        patterns = gate_config.get('patterns', {})
        language_str = language.value.lower()
        
        # Get patterns for the specific language
        lang_patterns = self.get_patterns_for_gate(gate_name, language_str)
        
        # Organize patterns by category based on gate type
        categorized_patterns = self._categorize_patterns(gate_type, lang_patterns)
        
        return categorized_patterns
    
    def _find_gate_by_name(self, gate_name: str) -> Optional[Dict[str, Any]]:
        """Find gate configuration by name"""
        config = self._config_manager.config
        if not config or 'hard_gates' not in config:
            return None
        
        for gate_config in config['hard_gates']:
            if gate_config.get('name') == gate_name:
                return gate_config
        
        # Try fuzzy matching
        gate_name_lower = gate_name.lower()
        for gate_config in config['hard_gates']:
            config_name = gate_config.get('name', '').lower()
            if gate_name_lower in config_name or config_name in gate_name_lower:
                return gate_config
        
        return None
    
    def get_all_gates(self) -> List[Dict[str, Any]]:
        """Get all gate configurations"""
        config = self._config_manager.config
        if not config or 'hard_gates' not in config:
            return []
        
        return config['hard_gates']
    
    def get_gate_by_id(self, gate_id: int) -> Optional[Dict[str, Any]]:
        """Get gate configuration by ID"""
        for gate_config in self.get_all_gates():
            if gate_config.get('id') == gate_id:
                return gate_config
        return None
    
    def get_supported_languages(self, gate_name: str) -> List[str]:
        """Get list of supported languages for a gate"""
        gate_config = self._find_gate_by_name(gate_name)
        if not gate_config:
            return []
        
        patterns = gate_config.get('patterns', {})
        return list(patterns.keys())
    
    def validate_patterns(self, gate_name: str, language: str) -> List[str]:
        """Validate regex patterns for a gate/language combination"""
        patterns = self.get_patterns_for_gate(gate_name, language)
        invalid_patterns = []
        
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                invalid_patterns.append(f"Pattern '{pattern}': {str(e)}")
        
        return invalid_patterns
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded patterns"""
        stats = {
            'total_gates': 0,
            'total_patterns': 0,
            'languages_supported': set(),
            'gates_by_language': {},
            'patterns_by_gate': {}
        }
        
        for gate_config in self.get_all_gates():
            gate_name = gate_config.get('name', 'Unknown')
            patterns = gate_config.get('patterns', {})
            
            stats['total_gates'] += 1
            stats['patterns_by_gate'][gate_name] = {}
            
            for language, lang_patterns in patterns.items():
                stats['languages_supported'].add(language)
                pattern_count = len(lang_patterns)
                stats['total_patterns'] += pattern_count
                stats['patterns_by_gate'][gate_name][language] = pattern_count
                
                if language not in stats['gates_by_language']:
                    stats['gates_by_language'][language] = 0
                stats['gates_by_language'][language] += 1
        
        stats['languages_supported'] = list(stats['languages_supported'])
        return stats
    
    def _gate_type_to_name(self, gate_type: GateType) -> str:
        """Convert GateType enum to gate name for lookup"""
        gate_type_mappings = {
            GateType.STRUCTURED_LOGS: "Logs Searchable/Available",
            GateType.AVOID_LOGGING_SECRETS: "Avoid Logging Confidential Data",
            GateType.AUDIT_TRAIL: "Create Audit Trail Logs",  # Updated to match YAML
            GateType.ERROR_LOGS: "Error Logs",  # Updated to match YAML
            GateType.RETRY_LOGIC: "Retry Logic",
            GateType.TIMEOUTS: "Timeouts in IO Ops",
            GateType.CIRCUIT_BREAKERS: "Circuit Breakers",
            GateType.THROTTLING: "Throttling & Drop Request",
            GateType.CORRELATION_ID: "Correlation ID",
            GateType.AUTOMATED_TESTS: "Automated Tests",
            GateType.LOG_API_CALLS: "Log API Calls",
            GateType.LOG_BACKGROUND_JOBS: "Log Background Jobs",  # Updated to match YAML
            GateType.UI_ERRORS: "Client UI Errors Logged",
            GateType.UI_ERROR_TOOLS: "Client Error Tracking",
            GateType.HTTP_CODES: "HTTP Status Codes"  # Updated to match YAML
        }
        
        return gate_type_mappings.get(gate_type, gate_type.value)
    
    def _categorize_patterns(self, gate_type: GateType, patterns: List[str]) -> Dict[str, List[str]]:
        """Categorize patterns based on gate type"""
        
        # Define pattern categories for each gate type
        category_mappings = {
            GateType.STRUCTURED_LOGS: {
                'structured_logging': [p for p in patterns if any(term in p.lower() for term in ['logger', 'log', 'json', 'structured'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['xml', 'conf', 'config', 'properties'])]
            },
            GateType.AVOID_LOGGING_SECRETS: {
                'secret_patterns': patterns  # All patterns are secret detection patterns
            },
            GateType.AUDIT_TRAIL: {
                'audit_patterns': [p for p in patterns if any(term in p.lower() for term in ['audit', 'trail', 'track'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.ERROR_LOGS: {
                'error_patterns': [p for p in patterns if any(term in p.lower() for term in ['error', 'exception', 'catch', 'throw'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.RETRY_LOGIC: {
                'retry_patterns': [p for p in patterns if any(term in p.lower() for term in ['retry', 'attempt', 'backoff'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.TIMEOUTS: {
                'timeout_patterns': [p for p in patterns if any(term in p.lower() for term in ['timeout', 'delay', 'wait'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.CIRCUIT_BREAKERS: {
                'circuit_breaker_patterns': [p for p in patterns if any(term in p.lower() for term in ['circuit', 'breaker', 'hystrix', 'polly'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.THROTTLING: {
                'throttling_patterns': [p for p in patterns if any(term in p.lower() for term in ['throttle', 'rate', 'limit'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.CORRELATION_ID: {
                'correlation_patterns': [p for p in patterns if any(term in p.lower() for term in ['correlation', 'request', 'trace', 'uuid'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.AUTOMATED_TESTS: {
                'test_patterns': [p for p in patterns if any(term in p.lower() for term in ['test', 'assert', 'expect', 'describe', 'it'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config', 'ini', 'json'])]
            },
            GateType.LOG_API_CALLS: {
                'api_log_patterns': [p for p in patterns if any(term in p.lower() for term in ['api', 'endpoint', 'request', 'response'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.LOG_BACKGROUND_JOBS: {
                'job_log_patterns': [p for p in patterns if any(term in p.lower() for term in ['job', 'task', 'worker', 'background', 'async'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.UI_ERRORS: {
                'ui_error_patterns': [p for p in patterns if any(term in p.lower() for term in ['error', 'boundary', 'catch', 'ui'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.UI_ERROR_TOOLS: {
                'error_tool_patterns': [p for p in patterns if any(term in p.lower() for term in ['sentry', 'rollbar', 'bugsnag', 'airbrake'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            },
            GateType.HTTP_CODES: {
                'http_code_patterns': [p for p in patterns if any(term in p.lower() for term in ['status', 'http', 'response', 'code'])],
                'config_patterns': [p for p in patterns if any(term in p.lower() for term in ['conf', 'config'])]
            }
        }
        
        return category_mappings.get(gate_type, {'patterns': patterns})
    
    def add_pattern(self, gate_name: str, language: str, pattern: str) -> bool:
        """Add a new pattern to a gate/language combination"""
        gate_config = self._find_gate_by_name(gate_name)
        if not gate_config:
            logger.error(f"Gate '{gate_name}' not found")
            return False
        
        # Validate pattern syntax
        try:
            re.compile(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return False
        
        # Add pattern to config
        if 'patterns' not in gate_config:
            gate_config['patterns'] = {}
        
        if language not in gate_config['patterns']:
            gate_config['patterns'][language] = []
        
        if pattern not in gate_config['patterns'][language]:
            gate_config['patterns'][language].append(pattern)
            self._config_manager.save() # Save the entire config after adding a pattern
            logger.info(f"Added pattern '{pattern}' to gate '{gate_name}' for language '{language}'")
            return True
        
        logger.warning(f"Pattern '{pattern}' already exists for gate '{gate_name}' and language '{language}'")
        return False
    
    def remove_pattern(self, gate_name: str, language: str, pattern: str) -> bool:
        """Remove a pattern from a gate/language combination"""
        gate_config = self._find_gate_by_name(gate_name)
        if not gate_config:
            logger.error(f"Gate '{gate_name}' not found")
            return False
        
        patterns = gate_config.get('patterns', {}).get(language, [])
        if pattern in patterns:
            patterns.remove(pattern)
            self._config_manager.save() # Save the entire config after removing a pattern
            logger.info(f"Removed pattern '{pattern}' from gate '{gate_name}' for language '{language}'")
            return True
        
        logger.warning(f"Pattern '{pattern}' not found for gate '{gate_name}' and language '{language}'")
        return False
    
    def save_config(self, backup: bool = True) -> bool:
        """Save current configuration back to YAML file"""
        try:
            if backup:
                backup_path = Path("codegates/core/gate_config.yml").with_suffix('.yml.backup')
                if Path("codegates/core/gate_config.yml").exists():
                    import shutil
                    shutil.copy2("codegates/core/gate_config.yml", backup_path)
                    logger.info(f"Created backup at {backup_path}")
            
            # The config_manager handles saving, so we just reload to ensure consistency
            self._config_manager.reload()
            
            logger.info(f"Saved configuration to {Path('codegates/core/gate_config.yml')}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _clear_cache(self) -> None:
        """Clear pattern cache"""
        self._pattern_cache.clear()
        # Clear LRU cache
        self.get_patterns_for_gate.cache_clear()


# Global pattern loader instance
_pattern_loader = None


def get_pattern_loader() -> PatternLoader:
    """Get the global pattern loader instance"""
    global _pattern_loader
    if _pattern_loader is None:
        _pattern_loader = PatternLoader()
    return _pattern_loader


def reload_patterns() -> None:
    """Reload patterns from configuration file"""
    global _pattern_loader
    if _pattern_loader is not None:
        _pattern_loader.reload_config()


# Convenience functions for backward compatibility
def get_patterns_for_gate(gate_name: str, language: str) -> List[str]:
    """Get patterns for a specific gate and language"""
    return get_pattern_loader().get_patterns_for_gate(gate_name, language)


def get_patterns_for_gate_type(gate_type: GateType, language: Language) -> Dict[str, List[str]]:
    """Get patterns for a gate type and language"""
    return get_pattern_loader().get_patterns_for_gate_type(gate_type, language)


def validate_pattern_syntax(gate_name: str, language: str) -> List[str]:
    """Validate regex patterns for a gate/language combination"""
    return get_pattern_loader().validate_patterns(gate_name, language) 