"""
Optimized File Processor Utility
High-performance file processing with chunk-based reading, batch pattern matching, and parallel processing
"""

import os
import mmap
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

class FileProcessorStats:
    """Statistics tracking for file processing performance"""
    
    def __init__(self):
        self.files_processed = 0
        self.files_skipped = 0
        self.files_failed = 0
        self.total_processing_time = 0.0
        self.total_bytes_processed = 0
        self.matches_found = 0
        self.parallel_threads_used = 0
        self.memory_mapped_files = 0
        self.chunk_processed_files = 0
        self.streaming_processed_files = 0
        self.start_time = time.time()
        
    def to_dict(self) -> Dict:
        """Convert stats to dictionary for JSON serialization"""
        total_time = time.time() - self.start_time
        return {
            "files_processed": self.files_processed,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "total_processing_time_seconds": round(self.total_processing_time, 3),
            "total_runtime_seconds": round(total_time, 3),
            "total_bytes_processed": self.total_bytes_processed,
            "matches_found": self.matches_found,
            "parallel_threads_used": self.parallel_threads_used,
            "memory_mapped_files": self.memory_mapped_files,
            "chunk_processed_files": self.chunk_processed_files,
            "streaming_processed_files": self.streaming_processed_files,
            "throughput_files_per_second": round(self.files_processed / total_time, 2) if total_time > 0 else 0,
            "throughput_mb_per_second": round((self.total_bytes_processed / (1024*1024)) / total_time, 2) if total_time > 0 else 0
        }

class OptimizedFileProcessor:
    """
    High-performance file processor with multiple optimization strategies
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the optimized file processor"""
        self.config = config or {}
        
        # Configuration from environment or defaults
        self.chunk_size = int(os.getenv("CODEGATES_CHUNK_SIZE", self.config.get("chunk_size", 8192)))
        self.max_parallel_files = int(os.getenv("CODEGATES_MAX_PARALLEL_FILES", self.config.get("max_parallel_files", 4)))
        self.use_memory_mapping = os.getenv("CODEGATES_USE_MEMORY_MAPPING", "true").lower() == "true"
        self.buffer_size = int(os.getenv("CODEGATES_BUFFER_SIZE", self.config.get("buffer_size", 65536)))
        self.batch_line_count = int(os.getenv("CODEGATES_BATCH_LINE_COUNT", self.config.get("batch_line_count", 100)))
        self.enable_file_filtering = os.getenv("CODEGATES_ENABLE_FILE_FILTERING", "true").lower() == "true"
        self.max_matches_per_file = self.config.get("max_matches_per_file", 50)
        self.max_file_size_mb = self.config.get("max_file_size_mb", 5)
        
        # Performance thresholds for strategy selection
        self.small_file_threshold = 10 * 1024  # 10KB
        self.medium_file_threshold = 1024 * 1024  # 1MB
        self.large_file_threshold = 10 * 1024 * 1024  # 10MB
        
        # Statistics
        self.stats = FileProcessorStats()
        
        # Thread safety
        self._stats_lock = threading.Lock()
        
        print(f"🚀 OptimizedFileProcessor initialized:")
        print(f"   📊 Chunk size: {self.chunk_size} bytes")
        print(f"   🔀 Max parallel files: {self.max_parallel_files}")
        print(f"   💾 Memory mapping: {self.use_memory_mapping}")
        print(f"   📦 Batch line count: {self.batch_line_count}")
    
    def process_files_optimized(self, files: List[Dict[str, Any]], all_compiled_patterns: Dict[str, List[tuple]], 
                               repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process files using optimized strategies based on file characteristics
        """
        print(f"🔄 Processing {len(files)} files with optimized strategies...")
        
        # Smart file filtering
        if self.enable_file_filtering:
            filtered_files = self._smart_file_filtering(files, all_compiled_patterns)
            print(f"   🎯 Filtered to {len(filtered_files)} relevant files ({len(files) - len(filtered_files)} skipped)")
        else:
            filtered_files = files
        
        # Initialize results
        all_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        # Group files by processing strategy
        file_groups = self._group_files_by_strategy(filtered_files, repo_path)
        
        # Process each group with appropriate strategy
        for strategy, file_list in file_groups.items():
            if not file_list:
                continue
                
            print(f"   📁 Processing {len(file_list)} files with {strategy} strategy...")
            
            if strategy == "parallel":
                matches = self._process_files_parallel(file_list, all_compiled_patterns, repo_path)
            else:
                matches = self._process_files_sequential(file_list, all_compiled_patterns, repo_path, strategy)
            
            # Merge results
            for gate_name, gate_matches in matches.items():
                all_matches[gate_name].extend(gate_matches)
        
        # Update final statistics
        with self._stats_lock:
            for gate_matches in all_matches.values():
                self.stats.matches_found += len(gate_matches)
        
        print(f"✅ File processing complete: {self.stats.files_processed} files, {self.stats.matches_found} matches")
        return all_matches
    
    def _group_files_by_strategy(self, files: List[Dict[str, Any]], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Group files by optimal processing strategy"""
        
        groups = {
            "parallel": [],
            "memory_mapped": [],
            "chunk_processing": [],
            "streaming": [],
            "simple_read": []
        }
        
        for file_info in files:
            file_path = repo_path / file_info["relative_path"]
            
            try:
                file_size = file_path.stat().st_size
                strategy = self._choose_processing_strategy(file_path, file_size)
                
                # Use parallel processing for medium-sized files
                if (strategy in ["chunk_processing", "streaming"] and 
                    len(groups["parallel"]) < self.max_parallel_files * 10):
                    groups["parallel"].append(file_info)
                else:
                    groups[strategy].append(file_info)
                    
            except Exception:
                # Default to simple read for problematic files
                groups["simple_read"].append(file_info)
        
        return groups
    
    def _choose_processing_strategy(self, file_path: Path, file_size: int) -> str:
        """Choose optimal processing strategy based on file characteristics"""
        
        if file_size < self.small_file_threshold:
            return "simple_read"
        elif file_size < self.medium_file_threshold:
            return "chunk_processing"
        elif file_size < self.large_file_threshold:
            return "streaming"
        else:
            return "memory_mapped" if self.use_memory_mapping else "streaming"
    
    def _process_files_parallel(self, files: List[Dict[str, Any]], all_compiled_patterns: Dict[str, List[tuple]], 
                               repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Process files in parallel for better CPU utilization"""
        
        all_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        def process_single_file(file_info):
            """Worker function for parallel processing"""
            file_path = repo_path / file_info["relative_path"]
            
            try:
                file_size = file_path.stat().st_size
                strategy = self._choose_processing_strategy(file_path, file_size)
                
                start_time = time.time()
                result = self._process_single_file_optimized(file_path, file_info, all_compiled_patterns, strategy)
                processing_time = time.time() - start_time
                
                # Update statistics
                with self._stats_lock:
                    self.stats.files_processed += 1
                    self.stats.total_processing_time += processing_time
                    self.stats.total_bytes_processed += file_size
                    
                    if strategy == "memory_mapped":
                        self.stats.memory_mapped_files += 1
                    elif strategy == "chunk_processing":
                        self.stats.chunk_processed_files += 1
                    elif strategy == "streaming":
                        self.stats.streaming_processed_files += 1
                
                return result
                
            except Exception as e:
                with self._stats_lock:
                    self.stats.files_failed += 1
                print(f"⚠️ Error processing {file_info['relative_path']}: {e}")
                return {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        # Use ThreadPoolExecutor for I/O bound operations
        with ThreadPoolExecutor(max_workers=self.max_parallel_files) as executor:
            self.stats.parallel_threads_used = self.max_parallel_files
            
            # Submit all file processing tasks
            future_to_file = {
                executor.submit(process_single_file, file_info): file_info 
                for file_info in files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                try:
                    file_matches = future.result()
                    
                    # Merge results
                    for gate_name, matches in file_matches.items():
                        all_matches[gate_name].extend(matches)
                        
                except Exception as e:
                    file_info = future_to_file[future]
                    print(f"⚠️ Parallel processing error for {file_info['relative_path']}: {e}")
        
        return all_matches
    
    def _process_files_sequential(self, files: List[Dict[str, Any]], all_compiled_patterns: Dict[str, List[tuple]], 
                                 repo_path: Path, strategy: str) -> Dict[str, List[Dict[str, Any]]]:
        """Process files sequentially with specified strategy"""
        
        all_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        for file_info in files:
            file_path = repo_path / file_info["relative_path"]
            
            try:
                start_time = time.time()
                file_matches = self._process_single_file_optimized(file_path, file_info, all_compiled_patterns, strategy)
                processing_time = time.time() - start_time
                
                # Merge results
                for gate_name, matches in file_matches.items():
                    all_matches[gate_name].extend(matches)
                
                # Update statistics
                file_size = file_path.stat().st_size
                self.stats.files_processed += 1
                self.stats.total_processing_time += processing_time
                self.stats.total_bytes_processed += file_size
                
                if strategy == "memory_mapped":
                    self.stats.memory_mapped_files += 1
                elif strategy == "chunk_processing":
                    self.stats.chunk_processed_files += 1
                elif strategy == "streaming":
                    self.stats.streaming_processed_files += 1
                    
            except Exception as e:
                self.stats.files_failed += 1
                print(f"⚠️ Error processing {file_info['relative_path']}: {e}")
        
        return all_matches
    
    def _process_single_file_optimized(self, file_path: Path, file_info: Dict[str, Any], 
                                      all_compiled_patterns: Dict[str, List[tuple]], strategy: str) -> Dict[str, List[Dict[str, Any]]]:
        """Process a single file using the specified optimization strategy"""
        
        if strategy == "memory_mapped":
            return self._process_file_memory_mapped(file_path, file_info, all_compiled_patterns)
        elif strategy == "chunk_processing":
            return self._process_file_chunked(file_path, file_info, all_compiled_patterns)
        elif strategy == "streaming":
            return self._process_file_streaming_optimized(file_path, file_info, all_compiled_patterns)
        else:  # simple_read
            return self._process_file_simple(file_path, file_info, all_compiled_patterns)
    
    def _process_file_memory_mapped(self, file_path: Path, file_info: Dict[str, Any], 
                                   all_compiled_patterns: Dict[str, List[tuple]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process file using memory mapping for large files"""
        
        file_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Use memory mapping for better performance
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    content = mmapped_file.read().decode('utf-8', errors='ignore')
            
            return self._batch_pattern_matching(content, all_compiled_patterns, file_info)
            
        except Exception as e:
            print(f"⚠️ Memory mapping error for {file_path}: {e}")
            # Fallback to simple read
            return self._process_file_simple(file_path, file_info, all_compiled_patterns)
    
    def _process_file_chunked(self, file_path: Path, file_info: Dict[str, Any], 
                             all_compiled_patterns: Dict[str, List[tuple]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process file in chunks for better memory utilization"""
        
        file_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                chunk_buffer = ""
                line_offset = 0
                
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # Combine with buffer to handle line boundaries
                    chunk_buffer += chunk
                    
                    # Process complete lines in the chunk
                    lines = chunk_buffer.split('\n')
                    chunk_buffer = lines[-1]  # Keep incomplete line for next chunk
                    
                    # Process complete lines in batch
                    if len(lines) > 1:
                        complete_lines = lines[:-1]
                        line_batch_text = '\n'.join(complete_lines)
                        
                        batch_matches = self._batch_pattern_matching_with_line_nums(
                            line_batch_text, all_compiled_patterns, file_info, line_offset
                        )
                        
                        # Merge batch results
                        for gate_name, matches in batch_matches.items():
                            file_matches[gate_name].extend(matches)
                            
                            # Respect match limits
                            if len(file_matches[gate_name]) >= self.max_matches_per_file:
                                file_matches[gate_name] = file_matches[gate_name][:self.max_matches_per_file]
                    
                    line_offset += len(lines) - 1
                
                # Process final incomplete line
                if chunk_buffer:
                    final_matches = self._batch_pattern_matching_with_line_nums(
                        chunk_buffer, all_compiled_patterns, file_info, line_offset
                    )
                    
                    for gate_name, matches in final_matches.items():
                        if len(file_matches[gate_name]) < self.max_matches_per_file:
                            remaining_slots = self.max_matches_per_file - len(file_matches[gate_name])
                            file_matches[gate_name].extend(matches[:remaining_slots])
        
        except Exception as e:
            print(f"⚠️ Error in chunk processing {file_path}: {e}")
        
        return file_matches
    
    def _process_file_streaming_optimized(self, file_path: Path, file_info: Dict[str, Any], 
                                         all_compiled_patterns: Dict[str, List[tuple]]) -> Dict[str, List[Dict[str, Any]]]:
        """Optimized streaming processing with intelligent buffering"""
        
        file_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore', buffering=self.buffer_size) as f:
                line_buffer = []
                line_offset = 0
                
                # Read lines in batches
                for line in f:
                    line_buffer.append(line.rstrip('\n\r'))
                    
                    # Process when buffer is full
                    if len(line_buffer) >= self.batch_line_count:
                        self._process_line_batch(line_buffer, line_offset, all_compiled_patterns, 
                                               file_info, file_matches)
                        line_offset += len(line_buffer)
                        line_buffer.clear()
                        
                        # Check if we've reached match limits for all gates
                        if all(len(file_matches[gate_name]) >= self.max_matches_per_file 
                               for gate_name in file_matches):
                            break
                
                # Process remaining lines
                if line_buffer:
                    self._process_line_batch(line_buffer, line_offset, all_compiled_patterns, 
                                           file_info, file_matches)
        
        except Exception as e:
            print(f"⚠️ Error in streaming processing {file_path}: {e}")
        
        return file_matches
    
    def _process_file_simple(self, file_path: Path, file_info: Dict[str, Any], 
                            all_compiled_patterns: Dict[str, List[tuple]]) -> Dict[str, List[Dict[str, Any]]]:
        """Simple file processing for small files"""
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return self._batch_pattern_matching(content, all_compiled_patterns, file_info)
        except Exception as e:
            print(f"⚠️ Error in simple processing {file_path}: {e}")
            return {gate_name: [] for gate_name in all_compiled_patterns.keys()}
    
    def _batch_pattern_matching(self, content: str, all_compiled_patterns: Dict[str, List[tuple]], 
                               file_info: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Apply all patterns to content using batch processing"""
        
        file_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        # Apply patterns gate by gate (better cache locality)
        for gate_name, compiled_patterns in all_compiled_patterns.items():
            for pattern, compiled_pattern in compiled_patterns:
                if len(file_matches[gate_name]) >= self.max_matches_per_file:
                    break
                
                try:
                    # Use finditer on entire content for better performance
                    for match in compiled_pattern.finditer(content):
                        line_num = content[:match.start()].count('\n') + 1
                        
                        file_matches[gate_name].append({
                            "file": file_info["relative_path"],
                            "pattern": pattern,
                            "match": match.group(),
                            "line": line_num,
                            "language": file_info.get("language", ""),
                            "source": "batch_optimized"
                        })
                        
                        # Respect match limits
                        if len(file_matches[gate_name]) >= self.max_matches_per_file:
                            break
                            
                except Exception:
                    continue  # Skip problematic patterns
        
        return file_matches
    
    def _batch_pattern_matching_with_line_nums(self, content: str, all_compiled_patterns: Dict[str, List[tuple]], 
                                              file_info: Dict[str, Any], line_offset: int) -> Dict[str, List[Dict[str, Any]]]:
        """Batch pattern matching with line number offset calculation"""
        
        file_matches = {gate_name: [] for gate_name in all_compiled_patterns.keys()}
        
        for gate_name, compiled_patterns in all_compiled_patterns.items():
            for pattern, compiled_pattern in compiled_patterns:
                try:
                    for match in compiled_pattern.finditer(content):
                        relative_line = content[:match.start()].count('\n')
                        absolute_line = line_offset + relative_line + 1
                        
                        file_matches[gate_name].append({
                            "file": file_info["relative_path"],
                            "pattern": pattern,
                            "match": match.group(),
                            "line": absolute_line,
                            "language": file_info.get("language", ""),
                            "source": "chunk_optimized"
                        })
                        
                        if len(file_matches[gate_name]) >= self.max_matches_per_file:
                            break
                            
                except Exception:
                    continue
        
        return file_matches
    
    def _process_line_batch(self, lines: List[str], line_offset: int, all_compiled_patterns: Dict[str, List[tuple]], 
                           file_info: Dict[str, Any], file_matches: Dict[str, List[Dict[str, Any]]]):
        """Process a batch of lines efficiently"""
        
        # Combine lines for pattern matching (better for multi-line patterns)
        combined_text = '\n'.join(lines)
        
        for gate_name, compiled_patterns in all_compiled_patterns.items():
            if len(file_matches[gate_name]) >= self.max_matches_per_file:
                continue
                
            for pattern, compiled_pattern in compiled_patterns:
                try:
                    # Find all matches in the batch
                    for match in compiled_pattern.finditer(combined_text):
                        # Calculate line number within the batch
                        relative_line = combined_text[:match.start()].count('\n')
                        absolute_line = line_offset + relative_line + 1
                        
                        file_matches[gate_name].append({
                            "file": file_info["relative_path"],
                            "pattern": pattern,
                            "match": match.group(),
                            "line": absolute_line,
                            "language": file_info.get("language", ""),
                            "source": "streaming_optimized"
                        })
                        
                        if len(file_matches[gate_name]) >= self.max_matches_per_file:
                            break
                            
                except Exception:
                    continue
    
    def _smart_file_filtering(self, files: List[Dict[str, Any]], all_compiled_patterns: Dict[str, List[tuple]]) -> List[Dict[str, Any]]:
        """Filter files intelligently based on patterns and file types"""
        
        filtered_files = []
        
        # Define file extensions that are unlikely to contain code patterns
        binary_extensions = {'.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll', 
                           '.ico', '.bmp', '.svg', '.mp4', '.avi', '.mp3', '.wav', '.doc', '.docx'}
        
        # Define extensions likely to contain relevant patterns
        code_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', 
                          '.rs', '.ts', '.jsx', '.tsx', '.vue', '.kt', '.scala', '.sh', '.ps1'}
        
        for file_info in files:
            file_path = Path(file_info["relative_path"])
            file_ext = file_path.suffix.lower()
            
            # Skip binary files
            if file_ext in binary_extensions:
                self.stats.files_skipped += 1
                continue
            
            # Calculate priority for processing order
            priority = 0
            if file_ext in code_extensions:
                priority += 10
            
            # Boost priority for certain file names
            file_name = file_path.name.lower()
            if any(keyword in file_name for keyword in ['config', 'setting', 'env', 'properties']):
                priority += 5
            
            file_info["priority"] = priority
            filtered_files.append(file_info)
        
        # Sort by priority (process high-priority files first)
        filtered_files.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        return filtered_files
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "processor_config": {
                "chunk_size": self.chunk_size,
                "max_parallel_files": self.max_parallel_files,
                "use_memory_mapping": self.use_memory_mapping,
                "buffer_size": self.buffer_size,
                "batch_line_count": self.batch_line_count,
                "enable_file_filtering": self.enable_file_filtering
            },
            "performance_stats": self.stats.to_dict()
        }

# Global instance accessor
_file_processor_instance = None

def get_optimized_file_processor(config: Optional[Dict[str, Any]] = None) -> OptimizedFileProcessor:
    """Get the global OptimizedFileProcessor instance"""
    global _file_processor_instance
    if _file_processor_instance is None:
        _file_processor_instance = OptimizedFileProcessor(config)
    return _file_processor_instance

def get_file_processor_stats() -> Dict[str, Any]:
    """Get file processor performance statistics"""
    processor = get_optimized_file_processor()
    return processor.get_performance_stats() 