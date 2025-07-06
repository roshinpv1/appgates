"""
Storage Manager for CodeGates

Provides a unified interface for managing scan results with configurable backends.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from .models import ScanResultModel, StorageConfig, StorageBackend
from .backends import BaseStorageBackend, SQLiteBackend, FileBackend, PostgreSQLBackend


class StorageManager:
    """Main storage manager that coordinates different storage backends"""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig.from_env()
        self.backend: Optional[BaseStorageBackend] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the storage backend"""
        try:
            # Create appropriate backend
            if self.config.backend == StorageBackend.SQLITE:
                self.backend = SQLiteBackend(self.config)
            elif self.config.backend == StorageBackend.POSTGRESQL:
                self.backend = PostgreSQLBackend(self.config)
            elif self.config.backend == StorageBackend.FILE:
                self.backend = FileBackend(self.config)
            elif self.config.backend == StorageBackend.MEMORY:
                # Fall back to in-memory storage (no persistent backend)
                print("⚠️ Using in-memory storage (no persistence)")
                self.backend = None
                self._initialized = True
                return True
            else:
                raise ValueError(f"Unsupported storage backend: {self.config.backend}")
            
            # Initialize the backend
            if self.backend:
                success = await self.backend.initialize()
                if not success:
                    print(f"❌ Failed to initialize {self.config.backend.value} backend")
                    return False
                
                self._initialized = True
                
                # Start cleanup task if retention is configured
                if self.config.retention_days:
                    self._cleanup_task = asyncio.create_task(self._cleanup_loop())
                
                print(f"✅ Storage manager initialized with {self.config.backend.value} backend")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to initialize storage manager: {e}")
            return False
    
    async def close(self):
        """Close the storage manager and cleanup resources"""
        try:
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close backend
            if self.backend:
                await self.backend.close()
            
            self._initialized = False
            print("✅ Storage manager closed")
            
        except Exception as e:
            print(f"⚠️ Error closing storage manager: {e}")
    
    async def save_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Save a scan result"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return False
        
        if not self.backend:
            # In-memory storage fallback
            return True
        
        return await self.backend.save_scan_result(scan_result)
    
    async def get_scan_result(self, scan_id: str) -> Optional[ScanResultModel]:
        """Get a scan result by ID"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return None
        
        if not self.backend:
            # In-memory storage fallback
            return None
        
        return await self.backend.get_scan_result(scan_id)
    
    async def update_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Update an existing scan result"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return False
        
        if not self.backend:
            # In-memory storage fallback
            return True
        
        return await self.backend.update_scan_result(scan_result)
    
    async def delete_scan_result(self, scan_id: str) -> bool:
        """Delete a scan result"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return False
        
        if not self.backend:
            # In-memory storage fallback
            return True
        
        return await self.backend.delete_scan_result(scan_id)
    
    async def list_scan_results(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> List[ScanResultModel]:
        """List scan results with optional filtering"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return []
        
        if not self.backend:
            # In-memory storage fallback
            return []
        
        return await self.backend.list_scan_results(limit, offset, status_filter, repository_filter)
    
    async def count_scan_results(
        self,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> int:
        """Count scan results with optional filtering"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return 0
        
        if not self.backend:
            # In-memory storage fallback
            return 0
        
        return await self.backend.count_scan_results(status_filter, repository_filter)
    
    async def cleanup_old_results(self, older_than: Optional[datetime] = None) -> int:
        """Clean up old scan results"""
        if not self._initialized:
            print("⚠️ Storage manager not initialized")
            return 0
        
        if not self.backend:
            # In-memory storage fallback
            return 0
        
        if not older_than and self.config.retention_days:
            older_than = datetime.now() - timedelta(days=self.config.retention_days)
        
        if not older_than:
            return 0
        
        return await self.backend.cleanup_old_results(older_than)
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if not self._initialized:
            return {
                'backend': self.config.backend.value,
                'initialized': False,
                'error': 'Storage manager not initialized'
            }
        
        if not self.backend:
            return {
                'backend': 'memory',
                'initialized': True,
                'message': 'Using in-memory storage (no persistence)'
            }
        
        return await self.backend.get_storage_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check storage health"""
        if not self._initialized:
            return {
                'healthy': False,
                'message': 'Storage manager not initialized'
            }
        
        if not self.backend:
            return {
                'healthy': True,
                'message': 'In-memory storage is healthy'
            }
        
        return await self.backend.health_check()
    
    async def _cleanup_loop(self):
        """Background task for periodic cleanup"""
        try:
            while True:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)  # Convert hours to seconds
                
                try:
                    if self.config.retention_days:
                        older_than = datetime.now() - timedelta(days=self.config.retention_days)
                        deleted_count = await self.cleanup_old_results(older_than)
                        
                        if deleted_count > 0:
                            print(f"🧹 Cleaned up {deleted_count} old scan results (older than {self.config.retention_days} days)")
                        
                except Exception as e:
                    print(f"⚠️ Error during periodic cleanup: {e}")
                    
        except asyncio.CancelledError:
            print("🛑 Storage cleanup task cancelled")
            raise
        except Exception as e:
            print(f"❌ Storage cleanup task failed: {e}")
    
    def is_initialized(self) -> bool:
        """Check if storage manager is initialized"""
        return self._initialized
    
    def get_backend_type(self) -> str:
        """Get the current backend type"""
        return self.config.backend.value
    
    def get_config(self) -> StorageConfig:
        """Get storage configuration"""
        return self.config
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactional operations (if supported by backend)"""
        # This is a placeholder for future transaction support
        # For now, we just yield the manager itself
        try:
            yield self
        except Exception as e:
            # In the future, we could implement rollback logic here
            print(f"⚠️ Transaction failed: {e}")
            raise


# Global storage manager instance
_storage_manager: Optional[StorageManager] = None


async def get_storage_manager() -> StorageManager:
    """Get the global storage manager instance"""
    global _storage_manager
    
    if _storage_manager is None:
        _storage_manager = StorageManager()
        await _storage_manager.initialize()
    
    return _storage_manager


async def close_storage_manager():
    """Close the global storage manager"""
    global _storage_manager
    
    if _storage_manager:
        await _storage_manager.close()
        _storage_manager = None


# Convenience functions for direct access
async def save_scan_result(scan_result: ScanResultModel) -> bool:
    """Save a scan result using the global storage manager"""
    manager = await get_storage_manager()
    return await manager.save_scan_result(scan_result)


async def get_scan_result(scan_id: str) -> Optional[ScanResultModel]:
    """Get a scan result by ID using the global storage manager"""
    manager = await get_storage_manager()
    return await manager.get_scan_result(scan_id)


async def update_scan_result(scan_result: ScanResultModel) -> bool:
    """Update a scan result using the global storage manager"""
    manager = await get_storage_manager()
    return await manager.update_scan_result(scan_result)


async def delete_scan_result(scan_id: str) -> bool:
    """Delete a scan result using the global storage manager"""
    manager = await get_storage_manager()
    return await manager.delete_scan_result(scan_id)


async def list_scan_results(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    status_filter: Optional[str] = None,
    repository_filter: Optional[str] = None
) -> List[ScanResultModel]:
    """List scan results using the global storage manager"""
    manager = await get_storage_manager()
    return await manager.list_scan_results(limit, offset, status_filter, repository_filter) 