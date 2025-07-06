"""
File-based Storage Backend

Implements persistent storage using JSON files in a directory structure.
"""

import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiofiles
import asyncio

from .base import BaseStorageBackend
from ..models import ScanResultModel, StorageConfig


class FileBackend(BaseStorageBackend):
    """File-based storage backend"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.storage_dir = Path(config.storage_directory or './data/scan_results')
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize file storage directory"""
        try:
            # Create storage directory
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for organization
            (self.storage_dir / 'completed').mkdir(exist_ok=True)
            (self.storage_dir / 'failed').mkdir(exist_ok=True)
            (self.storage_dir / 'running').mkdir(exist_ok=True)
            
            # Create index file if it doesn't exist
            index_file = self.storage_dir / 'index.json'
            if not index_file.exists():
                async with aiofiles.open(index_file, 'w') as f:
                    await f.write(json.dumps({'scans': {}, 'last_updated': datetime.now().isoformat()}))
            
            self._initialized = True
            print(f"✅ File storage initialized: {self.storage_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize file storage: {e}")
            return False
    
    async def close(self):
        """Close file storage (cleanup if needed)"""
        self._initialized = False
    
    def _get_file_path(self, scan_id: str, status: str = None) -> Path:
        """Get file path for a scan result"""
        if status:
            return self.storage_dir / status / f"{scan_id}.json"
        else:
            # Search in all subdirectories
            for subdir in ['completed', 'failed', 'running']:
                file_path = self.storage_dir / subdir / f"{scan_id}.json"
                if file_path.exists():
                    return file_path
            # Default to completed if not found
            return self.storage_dir / 'completed' / f"{scan_id}.json"
    
    async def _update_index(self, scan_result: ScanResultModel, operation: str = 'upsert'):
        """Update the index file"""
        index_file = self.storage_dir / 'index.json'
        
        async with self._lock:
            try:
                # Read current index
                if index_file.exists():
                    async with aiofiles.open(index_file, 'r') as f:
                        content = await f.read()
                        index_data = json.loads(content)
                else:
                    index_data = {'scans': {}, 'last_updated': datetime.now().isoformat()}
                
                # Update index
                if operation == 'upsert':
                    index_data['scans'][scan_result.scan_id] = {
                        'status': scan_result.status,
                        'score': scan_result.score,
                        'repository_url': scan_result.repository_url,
                        'branch': scan_result.branch,
                        'created_at': scan_result.created_at.isoformat(),
                        'updated_at': scan_result.updated_at.isoformat(),
                        'completed_at': scan_result.completed_at.isoformat() if scan_result.completed_at else None,
                        'file_path': str(self._get_file_path(scan_result.scan_id, scan_result.status))
                    }
                elif operation == 'delete':
                    index_data['scans'].pop(scan_result.scan_id, None)
                
                index_data['last_updated'] = datetime.now().isoformat()
                
                # Write updated index
                async with aiofiles.open(index_file, 'w') as f:
                    await f.write(json.dumps(index_data, indent=2))
                    
            except Exception as e:
                print(f"⚠️ Failed to update index: {e}")
    
    async def save_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Save a scan result to file"""
        try:
            # Get file path based on status
            file_path = self._get_file_path(scan_result.scan_id, scan_result.status)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove from old location if status changed
            for subdir in ['completed', 'failed', 'running']:
                old_path = self.storage_dir / subdir / f"{scan_result.scan_id}.json"
                if old_path.exists() and old_path != file_path:
                    old_path.unlink()
            
            # Save to new location
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(scan_result.to_dict(), indent=2))
            
            # Update index
            await self._update_index(scan_result)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save scan result {scan_result.scan_id}: {e}")
            return False
    
    async def get_scan_result(self, scan_id: str) -> Optional[ScanResultModel]:
        """Get a scan result by ID"""
        try:
            file_path = self._get_file_path(scan_id)
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)
                return ScanResultModel.from_dict(data)
                
        except Exception as e:
            print(f"❌ Failed to get scan result {scan_id}: {e}")
            return None
    
    async def update_scan_result(self, scan_result: ScanResultModel) -> bool:
        """Update an existing scan result"""
        return await self.save_scan_result(scan_result)
    
    async def delete_scan_result(self, scan_id: str) -> bool:
        """Delete a scan result"""
        try:
            file_path = self._get_file_path(scan_id)
            
            if file_path.exists():
                file_path.unlink()
            
            # Update index
            dummy_scan = ScanResultModel(scan_id=scan_id, status='', score=0)
            await self._update_index(dummy_scan, 'delete')
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete scan result {scan_id}: {e}")
            return False
    
    async def list_scan_results(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> List[ScanResultModel]:
        """List scan results with optional filtering"""
        try:
            results = []
            
            # Get all JSON files
            search_patterns = []
            if status_filter:
                search_patterns.append(str(self.storage_dir / status_filter / "*.json"))
            else:
                for subdir in ['completed', 'failed', 'running']:
                    search_patterns.append(str(self.storage_dir / subdir / "*.json"))
            
            file_paths = []
            for pattern in search_patterns:
                file_paths.extend(glob.glob(pattern))
            
            # Sort by modification time (newest first)
            file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Apply offset and limit
            if offset:
                file_paths = file_paths[offset:]
            if limit:
                file_paths = file_paths[:limit]
            
            # Load scan results
            for file_path in file_paths:
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        scan_result = ScanResultModel.from_dict(data)
                        
                        # Apply repository filter
                        if repository_filter and scan_result.repository_url:
                            if repository_filter.lower() not in scan_result.repository_url.lower():
                                continue
                        
                        results.append(scan_result)
                        
                except Exception as e:
                    print(f"⚠️ Failed to load scan result from {file_path}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to list scan results: {e}")
            return []
    
    async def count_scan_results(
        self,
        status_filter: Optional[str] = None,
        repository_filter: Optional[str] = None
    ) -> int:
        """Count scan results with optional filtering"""
        try:
            count = 0
            
            # Get all JSON files
            search_patterns = []
            if status_filter:
                search_patterns.append(str(self.storage_dir / status_filter / "*.json"))
            else:
                for subdir in ['completed', 'failed', 'running']:
                    search_patterns.append(str(self.storage_dir / subdir / "*.json"))
            
            file_paths = []
            for pattern in search_patterns:
                file_paths.extend(glob.glob(pattern))
            
            # Count matching files
            if not repository_filter:
                return len(file_paths)
            
            # Need to check repository filter
            for file_path in file_paths:
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        if data.get('repository_url') and repository_filter.lower() in data['repository_url'].lower():
                            count += 1
                            
                except Exception:
                    continue
            
            return count
            
        except Exception as e:
            print(f"❌ Failed to count scan results: {e}")
            return 0
    
    async def cleanup_old_results(self, older_than: datetime) -> int:
        """Clean up old scan results"""
        try:
            deleted_count = 0
            
            # Get all JSON files
            for subdir in ['completed', 'failed', 'running']:
                pattern = str(self.storage_dir / subdir / "*.json")
                file_paths = glob.glob(pattern)
                
                for file_path in file_paths:
                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if mtime < older_than:
                            os.remove(file_path)
                            deleted_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ Failed to delete old file {file_path}: {e}")
                        continue
            
            # Rebuild index after cleanup
            await self._rebuild_index()
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ Failed to cleanup old results: {e}")
            return 0
    
    async def _rebuild_index(self):
        """Rebuild the index file from existing scan files"""
        try:
            index_data = {'scans': {}, 'last_updated': datetime.now().isoformat()}
            
            # Scan all subdirectories
            for subdir in ['completed', 'failed', 'running']:
                pattern = str(self.storage_dir / subdir / "*.json")
                file_paths = glob.glob(pattern)
                
                for file_path in file_paths:
                    try:
                        async with aiofiles.open(file_path, 'r') as f:
                            content = await f.read()
                            data = json.loads(content)
                            
                            scan_id = data.get('scan_id')
                            if scan_id:
                                index_data['scans'][scan_id] = {
                                    'status': data.get('status'),
                                    'score': data.get('score', 0),
                                    'repository_url': data.get('repository_url'),
                                    'branch': data.get('branch'),
                                    'created_at': data.get('created_at'),
                                    'updated_at': data.get('updated_at'),
                                    'completed_at': data.get('completed_at'),
                                    'file_path': file_path
                                }
                                
                    except Exception as e:
                        print(f"⚠️ Failed to process file {file_path} during index rebuild: {e}")
                        continue
            
            # Write new index
            index_file = self.storage_dir / 'index.json'
            async with aiofiles.open(index_file, 'w') as f:
                await f.write(json.dumps(index_data, indent=2))
                
        except Exception as e:
            print(f"❌ Failed to rebuild index: {e}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {
                'backend': 'file',
                'storage_directory': str(self.storage_dir),
                'initialized': self._initialized
            }
            
            # Count files in each subdirectory
            for subdir in ['completed', 'failed', 'running']:
                pattern = str(self.storage_dir / subdir / "*.json")
                file_count = len(glob.glob(pattern))
                stats[f'{subdir}_count'] = file_count
            
            # Calculate total size
            total_size = 0
            for file_path in self.storage_dir.rglob('*.json'):
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    pass
            
            stats['total_size_bytes'] = total_size
            stats['total_files'] = sum(stats.get(f'{subdir}_count', 0) for subdir in ['completed', 'failed', 'running'])
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get storage stats: {e}")
            return {
                'backend': 'file',
                'error': str(e),
                'initialized': self._initialized
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check file backend health"""
        try:
            if not self._initialized:
                return {
                    'healthy': False,
                    'message': 'Backend not initialized'
                }
            
            # Check if storage directory exists and is writable
            if not self.storage_dir.exists():
                return {
                    'healthy': False,
                    'message': f'Storage directory does not exist: {self.storage_dir}'
                }
            
            # Try to write a test file
            test_file = self.storage_dir / '.health_check'
            try:
                async with aiofiles.open(test_file, 'w') as f:
                    await f.write('health_check')
                test_file.unlink()
            except Exception as e:
                return {
                    'healthy': False,
                    'message': f'Storage directory not writable: {e}'
                }
            
            return {
                'healthy': True,
                'message': 'File backend is healthy',
                'storage_directory': str(self.storage_dir),
                'directory_exists': self.storage_dir.exists()
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'message': f'File health check failed: {e}'
            } 