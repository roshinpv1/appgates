"""
CodeGates Utilities Package
Contains utility functions for the PocketFlow-based CodeGates application
"""

from .hard_gates import HARD_GATES, get_gate_by_name, get_gates_by_category
from .git_operations import clone_repository, cleanup_repository
from .file_scanner import scan_directory
from .llm_client import create_llm_client_from_env, LLMClient, LLMConfig, LLMProvider

# Import pattern cache if available
try:
    from .pattern_cache import (
        get_pattern_cache, 
        get_cached_compiled_pattern, 
        get_cache_stats, 
        clear_pattern_cache
    )
    PATTERN_CACHE_AVAILABLE = True
    __all__ = [
        'HARD_GATES',
        'get_gate_by_name', 
        'get_gates_by_category',
        'clone_repository',
        'cleanup_repository', 
        'scan_directory',
        'create_llm_client_from_env',
        'LLMClient',
        'LLMConfig',
        'LLMProvider',
        'get_pattern_cache',
        'get_cached_compiled_pattern',
        'get_cache_stats',
        'clear_pattern_cache'
    ]
except ImportError:
    PATTERN_CACHE_AVAILABLE = False
    __all__ = [
        'HARD_GATES',
        'get_gate_by_name', 
        'get_gates_by_category',
        'clone_repository',
        'cleanup_repository', 
        'scan_directory',
        'create_llm_client_from_env',
        'LLMClient',
        'LLMConfig',
        'LLMProvider'
    ] 