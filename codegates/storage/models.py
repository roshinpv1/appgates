"""
Storage Models for CodeGates

Defines data models for persistent storage of scan results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json


class StorageBackend(Enum):
    """Available storage backends"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    FILE = "file"
    MEMORY = "memory"  # Fallback to in-memory


@dataclass
class StorageConfig:
    """Configuration for storage backend"""
    backend: StorageBackend = StorageBackend.SQLITE
    
    # Database connection settings
    database_url: Optional[str] = None
    database_path: Optional[str] = None  # For SQLite
    
    # File storage settings
    storage_directory: Optional[str] = None
    
    # Connection pool settings
    max_connections: int = 10
    connection_timeout: int = 30
    
    # Retention settings
    retention_days: Optional[int] = None  # None = keep forever
    cleanup_interval_hours: int = 24
    
    # Performance settings
    enable_indexing: bool = True
    enable_compression: bool = False
    
    @classmethod
    def from_env(cls) -> 'StorageConfig':
        """Create configuration from environment variables"""
        import os
        
        # Determine backend
        backend_str = os.getenv('CODEGATES_STORAGE_BACKEND', 'sqlite').lower()
        try:
            backend = StorageBackend(backend_str)
        except ValueError:
            print(f"⚠️ Invalid storage backend '{backend_str}', using SQLite")
            backend = StorageBackend.SQLITE
        
        # Get database configuration
        database_url = os.getenv('CODEGATES_DATABASE_URL')
        database_path = os.getenv('CODEGATES_DATABASE_PATH', './data/codegates.db')
        storage_directory = os.getenv('CODEGATES_STORAGE_DIR', './data/scan_results')
        
        # Connection settings
        max_connections = int(os.getenv('CODEGATES_MAX_CONNECTIONS', '10'))
        connection_timeout = int(os.getenv('CODEGATES_CONNECTION_TIMEOUT', '30'))
        
        # Retention settings
        retention_days = None
        if os.getenv('CODEGATES_RETENTION_DAYS'):
            retention_days = int(os.getenv('CODEGATES_RETENTION_DAYS'))
        cleanup_interval_hours = int(os.getenv('CODEGATES_CLEANUP_INTERVAL_HOURS', '24'))
        
        # Performance settings
        enable_indexing = os.getenv('CODEGATES_ENABLE_INDEXING', 'true').lower() == 'true'
        enable_compression = os.getenv('CODEGATES_ENABLE_COMPRESSION', 'false').lower() == 'true'
        
        return cls(
            backend=backend,
            database_url=database_url,
            database_path=database_path,
            storage_directory=storage_directory,
            max_connections=max_connections,
            connection_timeout=connection_timeout,
            retention_days=retention_days,
            cleanup_interval_hours=cleanup_interval_hours,
            enable_indexing=enable_indexing,
            enable_compression=enable_compression
        )


@dataclass
class GateResultModel:
    """Model for individual gate results"""
    name: str
    status: str
    score: float
    details: List[str] = field(default_factory=list)
    expected: Optional[int] = None
    found: Optional[int] = None
    coverage: Optional[float] = None
    quality_score: Optional[float] = None
    matches: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'status': self.status,
            'score': self.score,
            'details': self.details,
            'expected': self.expected,
            'found': self.found,
            'coverage': self.coverage,
            'quality_score': self.quality_score,
            'matches': self.matches
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateResultModel':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            status=data['status'],
            score=data['score'],
            details=data.get('details', []),
            expected=data.get('expected'),
            found=data.get('found'),
            coverage=data.get('coverage'),
            quality_score=data.get('quality_score'),
            matches=data.get('matches', [])
        )


@dataclass
class ScanResultModel:
    """Model for complete scan results"""
    scan_id: str
    status: str
    score: float
    gates: List[GateResultModel] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    repository_url: Optional[str] = None
    branch: Optional[str] = None
    github_token_used: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Additional data
    message: Optional[str] = None
    error: Optional[str] = None
    report_url: Optional[str] = None
    report_file: Optional[str] = None
    
    # Analysis metadata
    llm_enhanced: bool = False
    total_files: int = 0
    total_lines: int = 0
    languages_detected: List[str] = field(default_factory=list)
    checkout_method: Optional[str] = None
    
    # JIRA integration
    jira_result: Optional[Dict[str, Any]] = None
    
    # Comments
    comments: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'scan_id': self.scan_id,
            'status': self.status,
            'score': self.score,
            'gates': [gate.to_dict() for gate in self.gates],
            'recommendations': self.recommendations,
            'repository_url': self.repository_url,
            'branch': self.branch,
            'github_token_used': self.github_token_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'message': self.message,
            'error': self.error,
            'report_url': self.report_url,
            'report_file': self.report_file,
            'llm_enhanced': self.llm_enhanced,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'languages_detected': self.languages_detected,
            'checkout_method': self.checkout_method,
            'jira_result': self.jira_result,
            'comments': self.comments
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanResultModel':
        """Create from dictionary"""
        # Parse timestamps
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        completed_at = None
        if data.get('completed_at'):
            completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))
        
        # Parse gates
        gates = []
        for gate_data in data.get('gates', []):
            gates.append(GateResultModel.from_dict(gate_data))
        
        return cls(
            scan_id=data['scan_id'],
            status=data['status'],
            score=data['score'],
            gates=gates,
            recommendations=data.get('recommendations', []),
            repository_url=data.get('repository_url'),
            branch=data.get('branch'),
            github_token_used=data.get('github_token_used', False),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            completed_at=completed_at,
            message=data.get('message'),
            error=data.get('error'),
            report_url=data.get('report_url'),
            report_file=data.get('report_file'),
            llm_enhanced=data.get('llm_enhanced', False),
            total_files=data.get('total_files', 0),
            total_lines=data.get('total_lines', 0),
            languages_detected=data.get('languages_detected', []),
            checkout_method=data.get('checkout_method'),
            jira_result=data.get('jira_result'),
            comments=data.get('comments', {})
        )
    
    def update_status(self, status: str, message: Optional[str] = None):
        """Update scan status"""
        self.status = status
        self.updated_at = datetime.now()
        if message:
            self.message = message
        if status == "completed":
            self.completed_at = datetime.now()
    
    def add_gate_result(self, gate: GateResultModel):
        """Add a gate result"""
        self.gates.append(gate)
        self.updated_at = datetime.now()
    
    def set_error(self, error: str):
        """Set error and update status"""
        self.error = error
        self.status = "failed"
        self.updated_at = datetime.now()
        self.completed_at = datetime.now()
    
    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            'scan_id': self.scan_id,
            'status': self.status,
            'score': self.score,
            'gates': [gate.to_dict() for gate in self.gates],
            'recommendations': self.recommendations,
            'report_url': self.report_url,
            'jira_result': self.jira_result
        } 