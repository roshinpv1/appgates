"""
Pattern Cache Utility
Singleton cache for compiled regex patterns to prevent per-request compilation
"""

import re
import os
import threading
import time
from typing import Dict, Optional, Tuple, List
from collections import OrderedDict

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class PatternCacheStats:
    """Statistics tracking for pattern cache performance"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.compilations = 0
        self.evictions = 0
        self.memory_usage_mb = 0.0
        self.startup_time = time.time()
        
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Convert stats to dictionary for JSON serialization"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "compilations": self.compilations,
            "evictions": self.evictions,
            "hit_rate_percent": round(self.hit_rate(), 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "uptime_seconds": round(time.time() - self.startup_time, 2)
        }

class PatternCache:
    """
    Singleton cache for compiled regex patterns
    Thread-safe implementation with LRU eviction and memory monitoring
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Configuration from environment variables
        self.max_cache_size = int(os.getenv("CODEGATES_PATTERN_CACHE_SIZE", "500"))
        self.max_memory_mb = int(os.getenv("CODEGATES_PATTERN_CACHE_MAX_MEMORY_MB", "100"))
        self.enable_monitoring = os.getenv("CODEGATES_PATTERN_CACHE_MONITORING", "true").lower() == "true"
        
        # Cache storage using OrderedDict for LRU behavior
        self._compiled_patterns: OrderedDict[str, re.Pattern] = OrderedDict()
        self._access_count: Dict[str, int] = {}
        self._compilation_time: Dict[str, float] = {}
        
        # Thread safety
        self._cache_lock = threading.RLock()
        
        # Statistics
        self.stats = PatternCacheStats()
        
        # Memory monitoring
        self._last_memory_check = time.time()
        self._memory_check_interval = 30  # seconds
        
        self._initialized = True
        print(f"🔧 PatternCache initialized: max_size={self.max_cache_size}, max_memory={self.max_memory_mb}MB")
    
    def get_compiled_pattern(self, pattern: str) -> re.Pattern:
        """
        Get compiled regex pattern from cache or compile if not cached
        Thread-safe with LRU eviction and memory management
        """
        if not pattern:
            raise ValueError("Pattern cannot be empty")
        
        with self._cache_lock:
            # Check if pattern is already in cache
            if pattern in self._compiled_patterns:
                # Move to end (most recently used)
                compiled_pattern = self._compiled_patterns.pop(pattern)
                self._compiled_patterns[pattern] = compiled_pattern
                self._access_count[pattern] += 1
                self.stats.hits += 1
                return compiled_pattern
            
            # Pattern not in cache - need to compile
            self.stats.misses += 1
            
            # Check memory usage and evict if necessary
            self._check_and_manage_memory()
            
            # Compile the pattern
            start_time = time.time()
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                compilation_time = time.time() - start_time
                
                # Add to cache
                self._compiled_patterns[pattern] = compiled_pattern
                self._access_count[pattern] = 1
                self._compilation_time[pattern] = compilation_time
                self.stats.compilations += 1
                
                # Update memory usage estimate
                if self.enable_monitoring:
                    self._update_memory_usage()
                
                print(f"   ✅ Compiled and cached pattern: {pattern[:50]}... ({compilation_time:.3f}s)")
                return compiled_pattern
                
            except re.error as e:
                print(f"   ❌ Invalid regex pattern: {pattern[:50]}... - {e}")
                raise ValueError(f"Invalid regex pattern: {e}")
    
    def _check_and_manage_memory(self):
        """Check cache size and memory usage, evict if necessary"""
        # Check cache size limit
        if len(self._compiled_patterns) >= self.max_cache_size:
            self._evict_lru_patterns(count=max(1, self.max_cache_size // 10))  # Evict 10%
        
        # Check memory usage periodically
        current_time = time.time()
        if current_time - self._last_memory_check > self._memory_check_interval:
            self._last_memory_check = current_time
            
            if self.enable_monitoring:
                self._update_memory_usage()
                if self.stats.memory_usage_mb > self.max_memory_mb:
                    evict_count = max(1, len(self._compiled_patterns) // 5)  # Evict 20%
                    print(f"⚠️ Pattern cache memory usage ({self.stats.memory_usage_mb:.1f}MB) exceeds limit ({self.max_memory_mb}MB)")
                    self._evict_lru_patterns(count=evict_count)
    
    def _evict_lru_patterns(self, count: int = 1):
        """Evict least recently used patterns"""
        evicted = 0
        patterns_to_remove = []
        
        # Collect patterns to remove (from the beginning = least recently used)
        for pattern in list(self._compiled_patterns.keys()):
            if evicted >= count:
                break
            patterns_to_remove.append(pattern)
            evicted += 1
        
        # Remove collected patterns
        for pattern in patterns_to_remove:
            if pattern in self._compiled_patterns:
                del self._compiled_patterns[pattern]
                del self._access_count[pattern]
                if pattern in self._compilation_time:
                    del self._compilation_time[pattern]
                self.stats.evictions += 1
        
        if evicted > 0:
            print(f"   🗑️ Evicted {evicted} LRU patterns from cache")
    
    def _update_memory_usage(self):
        """Update memory usage statistics"""
        try:
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_info = process.memory_info()
                # Estimate cache memory usage (rough approximation)
                pattern_count = len(self._compiled_patterns)
                estimated_mb = (pattern_count * 10) / 1024  # Rough estimate: 10KB per pattern
                self.stats.memory_usage_mb = estimated_mb
            else:
                # Fallback estimation without psutil
                pattern_count = len(self._compiled_patterns)
                estimated_mb = pattern_count * 0.01  # Very rough estimate: 10KB per pattern
                self.stats.memory_usage_mb = estimated_mb
        except Exception:
            # Final fallback
            self.stats.memory_usage_mb = len(self._compiled_patterns) * 0.01
    
    def pre_compile_patterns(self, patterns: List[str]) -> Tuple[int, int]:
        """
        Pre-compile a list of patterns (e.g., at server startup)
        Returns (successful_compilations, failed_compilations)
        """
        successful = 0
        failed = 0
        
        print(f"🔧 Pre-compiling {len(patterns)} patterns...")
        
        for i, pattern in enumerate(patterns):
            try:
                self.get_compiled_pattern(pattern)
                successful += 1
                
                # Progress logging every 50 patterns
                if (i + 1) % 50 == 0:
                    print(f"   📊 Pre-compiled {i + 1}/{len(patterns)} patterns...")
                    
            except Exception as e:
                failed += 1
                print(f"   ❌ Failed to pre-compile pattern: {pattern[:30]}... - {e}")
        
        print(f"✅ Pre-compilation complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def get_cache_info(self) -> Dict:
        """Get comprehensive cache information"""
        with self._cache_lock:
            total_patterns = len(self._compiled_patterns)
            
            # Get top accessed patterns
            top_patterns = sorted(
                self._access_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            # Get compilation times
            avg_compilation_time = (
                sum(self._compilation_time.values()) / len(self._compilation_time)
                if self._compilation_time else 0.0
            )
            
            return {
                "cache_size": total_patterns,
                "max_cache_size": self.max_cache_size,
                "cache_utilization_percent": round((total_patterns / self.max_cache_size) * 100, 2),
                "stats": self.stats.to_dict(),
                "top_accessed_patterns": [
                    {"pattern": pattern[:50] + "..." if len(pattern) > 50 else pattern, "access_count": count}
                    for pattern, count in top_patterns
                ],
                "average_compilation_time_ms": round(avg_compilation_time * 1000, 2),
                "configuration": {
                    "max_cache_size": self.max_cache_size,
                    "max_memory_mb": self.max_memory_mb,
                    "monitoring_enabled": self.enable_monitoring
                }
            }
    
    def clear_cache(self) -> int:
        """Clear all cached patterns. Returns number of patterns cleared."""
        with self._cache_lock:
            count = len(self._compiled_patterns)
            self._compiled_patterns.clear()
            self._access_count.clear()
            self._compilation_time.clear()
            
            # Reset stats except startup time
            startup_time = self.stats.startup_time
            self.stats = PatternCacheStats()
            self.stats.startup_time = startup_time
            
            print(f"🗑️ Cleared pattern cache: {count} patterns removed")
            return count
    
    def resize_cache(self, new_size: int) -> bool:
        """Resize cache maximum size"""
        if new_size < 1:
            return False
            
        with self._cache_lock:
            old_size = self.max_cache_size
            self.max_cache_size = new_size
            
            # Evict patterns if new size is smaller
            if len(self._compiled_patterns) > new_size:
                evict_count = len(self._compiled_patterns) - new_size
                self._evict_lru_patterns(count=evict_count)
            
            print(f"🔧 Pattern cache resized: {old_size} → {new_size}")
            return True

# Global instance accessor
_pattern_cache_instance = None

def get_pattern_cache() -> PatternCache:
    """Get the global PatternCache instance"""
    global _pattern_cache_instance
    if _pattern_cache_instance is None:
        _pattern_cache_instance = PatternCache()
    return _pattern_cache_instance

def get_cached_compiled_pattern(pattern: str) -> re.Pattern:
    """Convenience function to get compiled pattern from global cache"""
    cache = get_pattern_cache()
    return cache.get_compiled_pattern(pattern)

def get_cache_stats() -> Dict:
    """Get pattern cache statistics"""
    cache = get_pattern_cache()
    return cache.get_cache_info()

def clear_pattern_cache() -> int:
    """Clear the pattern cache"""
    cache = get_pattern_cache()
    return cache.clear_cache() 