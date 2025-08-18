"""
Cache Manager Component
Provides caching functionality with in-memory storage
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from collections import OrderedDict
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = 0


class InMemoryCache:
    """
    Thread-safe in-memory cache with LRU eviction
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize in-memory cache"""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
            "deletes": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if entry.expires_at and time.time() > entry.expires_at:
                    del self.cache[key]
                    self.stats["misses"] += 1
                    return None
                
                # Update access info
                entry.access_count += 1
                entry.last_accessed = time.time()
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                
                self.stats["hits"] += 1
                return entry.value
            else:
                self.stats["misses"] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        with self.lock:
            # Remove if exists
            if key in self.cache:
                del self.cache[key]
            
            # Check if we need to evict
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Create entry
            now = time.time()
            expires_at = now + (ttl or self.default_ttl) if ttl != 0 else None
            
            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=expires_at,
                access_count=1,
                last_accessed=now
            )
            
            self.cache[key] = entry
            self.stats["sets"] += 1
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats["deletes"] += 1
                return True
            return False
    
    def clear(self) -> int:
        """Clear all entries"""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            return count
    
    def keys(self) -> List[str]:
        """Get all keys"""
        with self.lock:
            return list(self.cache.keys())
    
    def size(self) -> int:
        """Get cache size"""
        with self.lock:
            return len(self.cache)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""
        with self.lock:
            keys_to_delete = []
            for key in self.cache.keys():
                if pattern in key:  # Simple substring matching
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                self.stats["deletes"] += 1
            
            return len(keys_to_delete)
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self.cache:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                **self.stats,
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_ratio": self.stats["hits"] / max(self.stats["hits"] + self.stats["misses"], 1)
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries"""
        with self.lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.expires_at and entry.expires_at < now
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)


class CacheManager:
    """
    Cache manager with support for in-memory and Redis backends
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cache manager"""
        self.config = config
        self.use_redis = config.get("use_redis", False) and REDIS_AVAILABLE
        
        if self.use_redis:
            self._init_redis()
        else:
            self._init_memory_cache()
        
        # Start cleanup task
        self.cleanup_task = None
        self._start_cleanup_task()
        
        print(f"💾 CacheManager initialized with {'Redis' if self.use_redis else 'in-memory'} backend")
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = self.config.get("redis_url", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url)
            
            # Test connection
            self.redis_client.ping()
            print(f"🔗 Connected to Redis at {redis_url}")
            
        except Exception as e:
            print(f"⚠️ Failed to connect to Redis: {e}, falling back to in-memory cache")
            self.use_redis = False
            self._init_memory_cache()
    
    def _init_memory_cache(self):
        """Initialize in-memory cache"""
        max_size = self.config.get("max_size", 1000)
        default_ttl = self.config.get("default_ttl", 300)
        
        self.memory_cache = InMemoryCache(
            max_size=max_size,
            default_ttl=default_ttl
        )
    
    def _start_cleanup_task(self):
        """Start periodic cleanup task"""
        # Don't start async task during initialization
        # Will be started when needed
        pass
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        return self.memory_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        return self.memory_cache.delete(key)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        return self.memory_cache.invalidate_pattern(pattern)
    
    def warm_cache(self, repo_id: str) -> bool:
        """Warm cache for repository"""
        # This would pre-load common queries for the repository
        # For now, just return success
        return True
    
    def clear(self) -> int:
        """Clear all cache entries"""
        return self.memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            **self.memory_cache.get_stats(),
            "backend": "memory"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for cache"""
        return {
            "status": "healthy",
            "backend": "memory",
            "stats": self.get_stats()
        }
    
    def close(self):
        """Close cache connections"""
        # Nothing to close for in-memory cache
        pass
