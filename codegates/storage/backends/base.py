"""
Base Storage Backend Interface

Defines the interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models import ScanResultModel, StorageConfig


class BaseStorageBackend(ABC):
    """Base class for all storage backends"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the storage backend"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the storage backend and cleanup resources"""
        pass
    
    @abstractmethod
    async def save_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Save a scan result"""
        pass
    
    @abstractmethod
    async def get_scan_result(self, scan_id: str) -> Optional[ScanResultModel]:
        """Get a scan result by ID"""
        pass
    
    @abstractmethod
    async def update_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Update an existing scan result"""
        pass
    
    @abstractmethod
    async def delete_scan_result(self, scan_id: str) -> bool:
        """Delete a scan result"""
        pass
    
    @abstractmethod
    async def list_scan_results(
        self, 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> List[ScanResultModel]:
        """List scan results with optional filtering"""
        pass
    
    @abstractmethod
    async def count_scan_results(
        self,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> int:
        """Count scan results with optional filtering"""
        pass
    
    @abstractmethod
    async def cleanup_old_results(self, older_than: datetime) -> int:
        """Clean up old scan results"""
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        pass
    
    # Helper methods
    def is_initialized(self) -> bool:
        """Check if backend is initialized"""
        return self._initialized
    
    def get_config(self) -> StorageConfig:
        """Get storage configuration"""
        return self.config 