"""
CodeGates Storage Module

Provides persistent storage solutions for scan results with configurable backends.
"""

from .storage_manager import StorageManager
from .models import ScanResultModel, StorageConfig
from .backends import SQLiteBackend, PostgreSQLBackend, FileBackend

__all__ = [
    'StorageManager',
    'ScanResultModel', 
    'StorageConfig',
    'SQLiteBackend',
    'PostgreSQLBackend', 
    'FileBackend'
] 