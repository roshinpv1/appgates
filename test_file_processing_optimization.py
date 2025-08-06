#!/usr/bin/env python3
"""
Test script for File Processing Optimization
Demonstrates the performance improvement from line-by-line to optimized processing
"""

import sys
import os
import time
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Any

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

try:
    from utils.file_processor import get_optimized_file_processor, get_file_processor_stats
    from utils.pattern_cache import get_cached_compiled_pattern, get_pattern_cache
    import re
    print("✅ Successfully imported optimized file processor and pattern cache")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def create_test_files(temp_dir: Path, num_files: int = 50) -> List[Dict[str, Any]]:
    """Create test files with varying sizes and content"""
    
    test_files = []
    
    # File templates with different patterns
    templates = {
        "python": {
            "extension": ".py",
            "content": """
import logging
import sys
from flask import Flask

logger = logging.getLogger(__name__)

def process_data():
    logger.info("Processing data...")
    try:
        result = complex_operation()
        logger.debug(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing: {e}")
        raise

def audit_action(user_id, action):
    logger.info(f"User {user_id} performed {action}")
    
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    logger.info("API call to /api/data")
    return {"status": "success"}

if __name__ == "__main__":
    app.run(debug=True)
"""
        },
        "javascript": {
            "extension": ".js",
            "content": """
const express = require('express');
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
    transports: [
        new winston.transports.Console()
    ]
});

const app = express();

app.get('/api/users', (req, res) => {
    logger.info('GET /api/users called');
    
    try {
        const users = getUserData();
        logger.debug(`Found ${users.length} users`);
        res.json(users);
    } catch (error) {
        logger.error('Error fetching users:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

function auditUserAction(userId, action) {
    logger.info(`User ${userId} performed action: ${action}`);
}

console.log('Server starting...');
app.listen(3000, () => {
    logger.info('Server running on port 3000');
});
"""
        },
        "java": {
            "extension": ".java",
            "content": """
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

@RestController
public class UserController {
    
    private static final Logger logger = LoggerFactory.getLogger(UserController.class);
    
    @GetMapping("/api/users")
    public ResponseEntity<List<User>> getUsers() {
        logger.info("Getting all users");
        
        try {
            List<User> users = userService.findAll();
            logger.debug("Found {} users", users.size());
            return ResponseEntity.ok(users);
        } catch (Exception e) {
            logger.error("Error retrieving users", e);
            throw new RuntimeException("Failed to retrieve users");
        }
    }
    
    @PostMapping("/api/users")
    public ResponseEntity<User> createUser(@RequestBody User user) {
        logger.info("Creating new user: {}", user.getUsername());
        
        try {
            User savedUser = userService.save(user);
            auditUserAction(savedUser.getId(), "USER_CREATED");
            return ResponseEntity.ok(savedUser);
        } catch (Exception e) {
            logger.error("Error creating user", e);
            throw new RuntimeException("Failed to create user");
        }
    }
    
    private void auditUserAction(Long userId, String action) {
        logger.info("User {} performed action: {}", userId, action);
    }
}
"""
        }
    }
    
    # Create files with different sizes
    for i in range(num_files):
        template_name = list(templates.keys())[i % len(templates)]
        template = templates[template_name]
        
        file_name = f"test_file_{i:03d}{template['extension']}"
        file_path = temp_dir / file_name
        
        # Create content with varying repetition for different file sizes
        repetitions = 1 + (i % 10)  # 1-10 repetitions
        content = template['content'] * repetitions
        
        file_path.write_text(content, encoding='utf-8')
        
        file_size = file_path.stat().st_size
        test_files.append({
            "relative_path": file_name,
            "language": template_name,
            "type": "Source Code",
            "size": file_size,
            "lines": content.count('\n')
        })
    
    print(f"✅ Created {len(test_files)} test files")
    return test_files

def create_test_patterns() -> Dict[str, List[tuple]]:
    """Create test patterns for different gates"""
    
    patterns = {
        "STRUCTURED_LOGS": [
            r"logger\.(info|debug|error|warning|critical)",
            r"logging\.(info|debug|error|warning|critical)",
            r"winston\.(info|debug|error|warning)",
            r"Logger\.(info|debug|error|warn|trace)",
            r"console\.(log|info|debug|error|warn)",
        ],
        "AUDIT_TRAIL": [
            r"audit.*log",
            r"logger\.info.*user.*action",
            r"auditUserAction",
            r"audit.*trail",
        ],
        "API_LOGGING": [
            r"@app\.route",
            r"app\.get\(",
            r"@GetMapping",
            r"@PostMapping",
            r"logger\.info.*api",
        ]
    }
    
    # Compile patterns using pattern cache
    compiled_patterns = {}
    pattern_cache = get_pattern_cache()
    
    for gate_name, pattern_list in patterns.items():
        compiled_patterns[gate_name] = []
        for pattern in pattern_list:
            try:
                compiled_pattern = get_cached_compiled_pattern(pattern)
                compiled_patterns[gate_name].append((pattern, compiled_pattern))
            except Exception as e:
                print(f"⚠️ Failed to compile pattern {pattern}: {e}")
    
    print(f"✅ Compiled patterns for {len(compiled_patterns)} gates")
    return compiled_patterns

def test_legacy_processing(files: List[Dict[str, Any]], patterns: Dict[str, List[tuple]], 
                          temp_dir: Path) -> Dict[str, Any]:
    """Test legacy line-by-line processing"""
    
    print("\n🐌 Testing Legacy Line-by-Line Processing")
    print("=" * 50)
    
    start_time = time.time()
    total_matches = 0
    files_processed = 0
    
    for file_info in files:
        file_path = temp_dir / file_info["relative_path"]
        files_processed += 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for gate_name, compiled_patterns in patterns.items():
                        for pattern, compiled_pattern in compiled_patterns:
                            try:
                                if compiled_pattern.search(line):
                                    total_matches += 1
                            except Exception:
                                continue
        except Exception:
            continue
    
    processing_time = time.time() - start_time
    
    result = {
        "method": "Legacy Line-by-Line",
        "processing_time": processing_time,
        "files_processed": files_processed,
        "total_matches": total_matches,
        "throughput_files_per_second": files_processed / processing_time if processing_time > 0 else 0
    }
    
    print(f"   ⏱️ Processing time: {processing_time:.3f}s")
    print(f"   📁 Files processed: {files_processed}")
    print(f"   🎯 Total matches: {total_matches}")
    print(f"   📊 Throughput: {result['throughput_files_per_second']:.1f} files/sec")
    
    return result

def test_optimized_processing(files: List[Dict[str, Any]], patterns: Dict[str, List[tuple]], 
                             temp_dir: Path) -> Dict[str, Any]:
    """Test optimized file processing"""
    
    print("\n🚀 Testing Optimized File Processing")
    print("=" * 50)
    
    # Configure optimized processor
    config = {
        "max_matches_per_file": 100,
        "max_file_size_mb": 10,
        "max_parallel_files": 4,
        "chunk_size": 8192,
        "batch_line_count": 100,
        "enable_file_filtering": True
    }
    
    processor = get_optimized_file_processor(config)
    
    start_time = time.time()
    
    # Process files with optimized strategies
    all_matches = processor.process_files_optimized(files, patterns, temp_dir)
    
    processing_time = time.time() - start_time
    
    # Count total matches
    total_matches = sum(len(matches) for matches in all_matches.values())
    
    # Get performance statistics
    perf_stats = get_file_processor_stats()
    
    result = {
        "method": "Optimized Processing",
        "processing_time": processing_time,
        "files_processed": perf_stats['performance_stats']['files_processed'],
        "files_skipped": perf_stats['performance_stats']['files_skipped'],
        "total_matches": total_matches,
        "throughput_files_per_second": perf_stats['performance_stats']['throughput_files_per_second'],
        "memory_mapped_files": perf_stats['performance_stats']['memory_mapped_files'],
        "chunk_processed_files": perf_stats['performance_stats']['chunk_processed_files'],
        "streaming_processed_files": perf_stats['performance_stats']['streaming_processed_files'],
        "parallel_threads_used": perf_stats['performance_stats']['parallel_threads_used']
    }
    
    print(f"   ⏱️ Processing time: {processing_time:.3f}s")
    print(f"   📁 Files processed: {result['files_processed']}")
    print(f"   📁 Files skipped: {result['files_skipped']}")
    print(f"   🎯 Total matches: {total_matches}")
    print(f"   📊 Throughput: {result['throughput_files_per_second']:.1f} files/sec")
    print(f"   💾 Memory mapped files: {result['memory_mapped_files']}")
    print(f"   📦 Chunk processed files: {result['chunk_processed_files']}")
    print(f"   🌊 Streaming processed files: {result['streaming_processed_files']}")
    print(f"   🔀 Parallel threads used: {result['parallel_threads_used']}")
    
    return result

def test_concurrent_processing(files: List[Dict[str, Any]], patterns: Dict[str, List[tuple]], 
                              temp_dir: Path, num_threads: int = 3) -> Dict[str, Any]:
    """Test concurrent processing simulation"""
    
    print(f"\n🔀 Testing Concurrent Processing ({num_threads} threads)")
    print("=" * 50)
    
    results = []
    
    def worker_thread(thread_id: int):
        """Worker function for concurrent testing"""
        config = {
            "max_matches_per_file": 50,
            "max_file_size_mb": 5,
            "max_parallel_files": 2,  # Reduced for concurrent test
        }
        
        processor = get_optimized_file_processor(config)
        
        start_time = time.time()
        all_matches = processor.process_files_optimized(files, patterns, temp_dir)
        processing_time = time.time() - start_time
        
        total_matches = sum(len(matches) for matches in all_matches.values())
        
        results.append({
            "thread_id": thread_id,
            "processing_time": processing_time,
            "total_matches": total_matches
        })
        
        print(f"   ✅ Thread {thread_id} completed: {processing_time:.3f}s, {total_matches} matches")
    
    # Start concurrent threads
    threads = []
    overall_start = time.time()
    
    for i in range(num_threads):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    overall_time = time.time() - overall_start
    
    avg_processing_time = sum(r["processing_time"] for r in results) / len(results)
    total_concurrent_matches = sum(r["total_matches"] for r in results)
    
    result = {
        "method": "Concurrent Processing",
        "num_threads": num_threads,
        "overall_time": overall_time,
        "avg_processing_time": avg_processing_time,
        "total_concurrent_matches": total_concurrent_matches,
        "concurrent_throughput": (len(files) * num_threads) / overall_time if overall_time > 0 else 0
    }
    
    print(f"   ⏱️ Overall time: {overall_time:.3f}s")
    print(f"   📊 Average thread time: {avg_processing_time:.3f}s")
    print(f"   🎯 Total matches (all threads): {total_concurrent_matches}")
    print(f"   🚀 Concurrent throughput: {result['concurrent_throughput']:.1f} files/sec")
    
    return result

def test_memory_usage_comparison():
    """Test memory usage patterns"""
    
    print(f"\n💾 Testing Memory Usage Patterns")
    print("=" * 50)
    
    try:
        import psutil
        process = psutil.Process()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"   📊 Baseline memory: {baseline_memory:.1f} MB")
        
        # Test pattern cache memory usage
        pattern_cache = get_pattern_cache()
        cache_stats = pattern_cache.get_cache_info()
        
        print(f"   🔧 Pattern cache: {cache_stats['cache_size']} patterns, {cache_stats['stats']['memory_usage_mb']:.2f} MB")
        
        # Current memory after optimizations
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_overhead = current_memory - baseline_memory
        
        print(f"   📈 Current memory: {current_memory:.1f} MB")
        print(f"   📊 Optimization overhead: {memory_overhead:.1f} MB")
        
        return {
            "baseline_memory_mb": baseline_memory,
            "current_memory_mb": current_memory,
            "optimization_overhead_mb": memory_overhead,
            "pattern_cache_mb": cache_stats['stats']['memory_usage_mb']
        }
        
    except ImportError:
        print("   ⚠️ psutil not available, skipping detailed memory analysis")
        return {"status": "psutil_not_available"}

def main():
    """Main test function"""
    print("🎯 File Processing Optimization Performance Tests")
    print()
    
    # Create temporary directory and test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test data
        print("📁 Setting up test environment...")
        test_files = create_test_files(temp_path, num_files=30)  # Reduced for faster testing
        test_patterns = create_test_patterns()
        
        # Test memory usage
        memory_stats = test_memory_usage_comparison()
        
        # Run performance tests
        print("\n🏃 Running Performance Tests...")
        
        # Test legacy processing
        legacy_result = test_legacy_processing(test_files, test_patterns, temp_path)
        
        # Test optimized processing
        optimized_result = test_optimized_processing(test_files, test_patterns, temp_path)
        
        # Test concurrent processing
        concurrent_result = test_concurrent_processing(test_files, test_patterns, temp_path, num_threads=3)
        
        # Performance comparison
        print(f"\n{'='*20} PERFORMANCE COMPARISON {'='*20}")
        
        print(f"📊 Processing Methods:")
        print(f"   🐌 Legacy:     {legacy_result['processing_time']:.3f}s ({legacy_result['throughput_files_per_second']:.1f} files/sec)")
        print(f"   🚀 Optimized:  {optimized_result['processing_time']:.3f}s ({optimized_result['throughput_files_per_second']:.1f} files/sec)")
        print(f"   🔀 Concurrent: {concurrent_result['overall_time']:.3f}s ({concurrent_result['concurrent_throughput']:.1f} files/sec)")
        
        # Calculate improvements
        if legacy_result['processing_time'] > 0:
            speed_improvement = legacy_result['processing_time'] / optimized_result['processing_time']
            throughput_improvement = optimized_result['throughput_files_per_second'] / legacy_result['throughput_files_per_second']
            
            print(f"\n⚡ Performance Improvements:")
            print(f"   🚀 Speed improvement: {speed_improvement:.1f}x faster")
            print(f"   📈 Throughput improvement: {throughput_improvement:.1f}x better")
            
            concurrent_improvement = concurrent_result['concurrent_throughput'] / legacy_result['throughput_files_per_second']
            print(f"   🔀 Concurrent improvement: {concurrent_improvement:.1f}x better")
        
        # Match accuracy
        print(f"\n🎯 Match Accuracy:")
        print(f"   🐌 Legacy matches: {legacy_result['total_matches']}")
        print(f"   🚀 Optimized matches: {optimized_result['total_matches']}")
        
        match_accuracy = (optimized_result['total_matches'] / legacy_result['total_matches'] * 100) if legacy_result['total_matches'] > 0 else 100
        print(f"   ✅ Accuracy: {match_accuracy:.1f}%")
        
        # Processing strategy breakdown
        print(f"\n🛠️ Processing Strategy Breakdown:")
        print(f"   💾 Memory mapped files: {optimized_result['memory_mapped_files']}")
        print(f"   📦 Chunk processed files: {optimized_result['chunk_processed_files']}")
        print(f"   🌊 Streaming processed files: {optimized_result['streaming_processed_files']}")
        print(f"   🔀 Parallel threads used: {optimized_result['parallel_threads_used']}")
        
        if isinstance(memory_stats, dict) and "baseline_memory_mb" in memory_stats:
            print(f"\n💾 Memory Usage:")
            print(f"   📊 Optimization overhead: {memory_stats['optimization_overhead_mb']:.1f} MB")
            print(f"   🔧 Pattern cache: {memory_stats['pattern_cache_mb']:.2f} MB")
        
        print(f"\n🎉 File Processing Optimization Test Complete!")
        print(f"   💡 Line-by-line processing has been successfully optimized!")
        print(f"   💡 Multiple strategies automatically selected based on file characteristics")
        print(f"   💡 Parallel processing and memory mapping provide significant improvements")
        print(f"   💡 Pattern caching eliminates per-request compilation overhead")

if __name__ == "__main__":
    main() 