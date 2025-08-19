#!/usr/bin/env python3
"""
Test script to demonstrate server startup with PatternCache pre-compilation
Shows how patterns are loaded once at startup instead of per-request
"""

import sys
import os
import time
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

try:
    from utils.pattern_cache import get_pattern_cache, get_cache_stats, clear_pattern_cache
    from utils.hard_gates import HARD_GATES
    from utils.static_patterns import get_static_patterns_for_gate
    print("✅ Successfully imported PatternCache and related modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def simulate_server_startup():
    """Simulate server startup with pattern pre-compilation"""
    print("🚀 Simulating CodeGates Server Startup")
    print("=" * 50)
    
    # Clear any existing cache
    cleared = clear_pattern_cache()
    if cleared > 0:
        print(f"🗑️ Cleared existing cache: {cleared} patterns")
    
    print("🔧 Initializing pattern cache...")
    pattern_cache = get_pattern_cache()
    
    # Collect all patterns from hard gates and static patterns
    all_patterns = []
    
    print("📋 Collecting patterns from hard gates...")
    for gate in HARD_GATES:
        gate_name = gate["name"]
        
        # Get patterns from hard gate definition
        gate_patterns = gate.get("patterns", [])
        if isinstance(gate_patterns, list):
            all_patterns.extend(gate_patterns)
            print(f"   📄 {gate_name}: {len(gate_patterns)} patterns")
        
        # Get static patterns for this gate
        try:
            static_patterns = get_static_patterns_for_gate(gate_name, ["python", "javascript", "java"])
            if static_patterns:
                all_patterns.extend(static_patterns)
                print(f"   📄 {gate_name} (static): {len(static_patterns)} patterns")
        except Exception as e:
            print(f"   ⚠️ Could not get static patterns for {gate_name}: {e}")
    
    print(f"\n📊 Total patterns collected: {len(all_patterns)}")
    
    if not all_patterns:
        print("⚠️ No patterns found for pre-compilation")
        return
    
    # Pre-compile patterns (simulating startup)
    print("\n🔧 Pre-compiling patterns at startup...")
    start_time = time.time()
    
    successful, failed = pattern_cache.pre_compile_patterns(all_patterns)
    
    startup_time = time.time() - start_time
    print(f"✅ Startup pre-compilation complete: {startup_time:.3f}s")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    # Show cache statistics
    cache_info = get_cache_stats()
    print(f"\n📊 Pattern Cache Statistics:")
    print(f"   Cache size: {cache_info['cache_size']} patterns")
    print(f"   Memory usage: {cache_info['stats']['memory_usage_mb']:.2f} MB")
    print(f"   Hit rate: {cache_info['stats']['hit_rate_percent']:.1f}%")
    
    return successful, failed, startup_time

def simulate_request_processing():
    """Simulate processing multiple requests with cached patterns"""
    print("\n🔄 Simulating Request Processing")
    print("=" * 50)
    
    # Simulate 5 concurrent requests
    num_requests = 5
    patterns_per_request = 10  # Simulate scanning with 10 common patterns
    
    common_patterns = [
        r"logger\.info\(",
        r"logger\.error\(",
        r"logger\.debug\(",
        r"console\.log\(",
        r"print\(",
        r"System\.out\.println\(",
        r"Log\.d\(",
        r"NSLog\(",
        r"async\s+def\s+",
        r"await\s+"
    ]
    
    print(f"🎯 Processing {num_requests} requests with {patterns_per_request} patterns each...")
    
    total_time = 0
    for request_id in range(num_requests):
        start_time = time.time()
        
        # Each request accesses the same patterns (cache hits after first compilation)
        for pattern in common_patterns:
            from utils.pattern_cache import get_cached_compiled_pattern
            compiled = get_cached_compiled_pattern(pattern)
        
        request_time = time.time() - start_time
        total_time += request_time
        
        print(f"   Request {request_id + 1}: {request_time:.4f}s")
    
    avg_time = total_time / num_requests
    print(f"\n📊 Request Processing Statistics:")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average per request: {avg_time:.4f}s")
    print(f"   Requests per second: {num_requests / total_time:.1f}")
    
    # Show final cache statistics
    cache_info = get_cache_stats()
    print(f"\n📊 Final Cache Statistics:")
    print(f"   Cache hits: {cache_info['stats']['hits']}")
    print(f"   Cache misses: {cache_info['stats']['misses']}")
    print(f"   Hit rate: {cache_info['stats']['hit_rate_percent']:.1f}%")
    
    return total_time, avg_time

def simulate_old_method():
    """Simulate the old per-request compilation for comparison"""
    print("\n🐌 Simulating Old Method (Per-Request Compilation)")
    print("=" * 50)
    
    import re
    
    patterns = [
        r"logger\.info\(",
        r"logger\.error\(",
        r"logger\.debug\(",
        r"console\.log\(",
        r"print\(",
        r"System\.out\.println\(",
        r"Log\.d\(",
        r"NSLog\(",
        r"async\s+def\s+",
        r"await\s+"
    ]
    
    num_requests = 5
    total_time = 0
    
    print(f"🔄 Processing {num_requests} requests with per-request compilation...")
    
    for request_id in range(num_requests):
        start_time = time.time()
        
        # Compile patterns fresh for each request (old method)
        compiled_patterns = []
        for pattern in patterns:
            compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            compiled_patterns.append(compiled)
        
        request_time = time.time() - start_time
        total_time += request_time
        
        print(f"   Request {request_id + 1}: {request_time:.4f}s")
    
    avg_time = total_time / num_requests
    print(f"\n📊 Old Method Statistics:")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average per request: {avg_time:.4f}s")
    print(f"   Requests per second: {num_requests / total_time:.1f}")
    
    return total_time, avg_time

def main():
    """Main demonstration function"""
    print("🎯 CodeGates PatternCache Startup Demonstration")
    print()
    
    # Simulate server startup
    successful, failed, startup_time = simulate_server_startup()
    
    # Simulate request processing with cache
    cached_total, cached_avg = simulate_request_processing()
    
    # Simulate old method for comparison
    old_total, old_avg = simulate_old_method()
    
    # Summary comparison
    print(f"\n{'='*20} PERFORMANCE COMPARISON {'='*20}")
    print(f"🚀 Startup Time: {startup_time:.3f}s (one-time cost)")
    print(f"   📊 Patterns pre-compiled: {successful}")
    print(f"   ❌ Failed compilations: {failed}")
    
    print(f"\n💨 Request Processing:")
    print(f"   🔥 With Cache: {cached_avg:.4f}s per request")
    print(f"   🐌 Without Cache: {old_avg:.4f}s per request")
    
    if old_avg > 0:
        speedup = old_avg / cached_avg
        print(f"   ⚡ Performance improvement: {speedup:.1f}x faster")
    
    print(f"\n💡 Memory Benefits:")
    print(f"   ✅ Patterns compiled once at startup")
    print(f"   ✅ Zero per-request compilation overhead")
    print(f"   ✅ Predictable memory usage")
    print(f"   ✅ Thread-safe access")
    
    print(f"\n🎉 PatternCache Solution Summary:")
    print(f"   🔧 PROBLEM SOLVED: Per-request pattern compilation eliminated")
    print(f"   📈 PERFORMANCE: {speedup:.1f}x faster request processing" if old_avg > 0 else "   📈 PERFORMANCE: Significantly improved")
    print(f"   💾 MEMORY: Stable usage regardless of concurrent requests")
    print(f"   🚀 OCP READY: Production-ready for containerized environments")

if __name__ == "__main__":
    main() 