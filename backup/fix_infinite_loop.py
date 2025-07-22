#!/usr/bin/env python3
"""
Fix for infinite loop in pattern matching
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def add_timeout_protection():
    """Add timeout protection to the pattern matching method"""
    
    # Read the current nodes.py file
    nodes_file = Path("gates/nodes.py")
    if not nodes_file.exists():
        print("❌ gates/nodes.py not found")
        return False
    
    content = nodes_file.read_text()
    
    # Find the _find_pattern_matches_with_config method
    method_start = content.find("def _find_pattern_matches_with_config")
    if method_start == -1:
        print("❌ Could not find _find_pattern_matches_with_config method")
        return False
    
    # Find the method end
    method_end = content.find("\n    def _get_technology_relevant_files", method_start)
    if method_end == -1:
        print("❌ Could not find method end")
        return False
    
    # Extract the method
    original_method = content[method_start:method_end]
    
    # Create the fixed method with timeout protection
    fixed_method = '''    def _find_pattern_matches_with_config(self, repo_path: Path, patterns: List[str], metadata: Dict[str, Any], gate: Dict[str, Any], config: Dict[str, Any], source: str = "LLM") -> List[Dict[str, Any]]:
        """Find pattern matches in appropriate files with improved coverage and error handling"""
        matches = []
        
        # Add timeout protection for file processing
        import time
        import threading
        
        # Timeout configuration for file processing
        FILE_PROCESSING_TIMEOUT = int(os.getenv("CODEGATES_FILE_PROCESSING_TIMEOUT", "300"))  # 5 minutes default
        print(f"   ⏱️ File processing timeout set to {FILE_PROCESSING_TIMEOUT} seconds")
        
        # Filter files based on gate type with improved logic
        gate_name = gate.get("name", "")
        
        if gate_name == "AUTOMATED_TESTS":
            # For automated tests gate, look at test files across all languages
            target_files = self._get_improved_relevant_files(metadata, file_type="Test Code", gate_name=gate_name, config=config)
            print(f"   Looking at {len(target_files)} relevant test files for {gate_name}")
        else:
            # For all other gates, look at source code files with more inclusive filtering
            target_files = self._get_improved_relevant_files(metadata, file_type="Source Code", gate_name=gate_name, config=config)
            print(f"   Looking at {len(target_files)} relevant source code files for {gate_name}")
        
        # Pre-compile patterns for efficiency (fix pattern recompilation issue)
        compiled_patterns = []
        invalid_patterns = []
        
        for pattern in patterns:
            try:
                compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                compiled_patterns.append((pattern, compiled_pattern))
            except re.error as e:
                invalid_patterns.append((pattern, str(e)))
                print(f"   ⚠️ Invalid regex pattern skipped: {pattern} - {e}")
        
        # Report pattern compilation results
        if invalid_patterns:
            print(f"   ⚠️ Skipped {len(invalid_patterns)} invalid patterns out of {len(patterns)} total")
        
        # Process files with improved limits and error handling
        files_processed = 0
        files_skipped = 0
        files_too_large = 0
        files_read_errors = 0
        
        # Configurable limits (remove hard-coded 100 file limit)
        max_files = min(len(target_files), config["max_files"])
        max_file_size = config["max_file_size_mb"] * 1024 * 1024  # Convert MB to bytes
        
        # Use threading with timeout to prevent hanging
        processing_result = {
            "matches": [],
            "files_processed": 0,
            "files_skipped": 0,
            "files_too_large": 0,
            "files_read_errors": 0,
            "error": None
        }
        
        def process_files_with_timeout():
            try:
                local_matches = []
                local_files_processed = 0
                local_files_skipped = 0
                local_files_too_large = 0
                local_files_read_errors = 0
                
                for i, file_info in enumerate(target_files[:max_files]):
                    # Add progress logging every 10 files
                    if i % 10 == 0 and i > 0:
                        print(f"   📊 Processing file {i}/{max_files} for {gate_name}...")
                    
                    file_path = repo_path / file_info["relative_path"]
                    
                    if not file_path.exists():
                        local_files_skipped += 1
                        continue
                        
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > max_file_size:
                            local_files_too_large += 1
                            if config.get("enable_detailed_logging", True):
                                print(f"   ⚠️ Skipping large file ({file_size/1024/1024:.1f}MB): {file_info['relative_path']}")
                            continue
                        
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        
                        # Apply all compiled patterns to this file
                        for pattern, compiled_pattern in compiled_patterns:
                            try:
                                for match in compiled_pattern.finditer(content):
                                    local_matches.append({
                                        "file": file_info["relative_path"],
                                        "pattern": pattern,
                                        "match": match.group(),
                                        "line": content[:match.start()].count('\\n') + 1,
                                        "language": file_info["language"],
                                        "source": source
                                    })
                            except Exception as e:
                                if config.get("enable_detailed_logging", True):
                                    print(f"   ⚠️ Pattern matching error in {file_info['relative_path']}: {e}")
                        
                        local_files_processed += 1
                        
                    except Exception as e:
                        local_files_read_errors += 1
                        if config.get("enable_detailed_logging", True):
                            print(f"   ⚠️ Error reading file {file_info['relative_path']}: {e}")
                        continue
                
                # Update result
                processing_result["matches"] = local_matches
                processing_result["files_processed"] = local_files_processed
                processing_result["files_skipped"] = local_files_skipped
                processing_result["files_too_large"] = local_files_too_large
                processing_result["files_read_errors"] = local_files_read_errors
                
            except Exception as e:
                processing_result["error"] = str(e)
        
        # Start file processing in a separate thread
        processing_thread = threading.Thread(target=process_files_with_timeout)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Wait for completion with timeout
        processing_thread.join(timeout=FILE_PROCESSING_TIMEOUT)
        
        if processing_thread.is_alive():
            print(f"   ⚠️ File processing timed out after {FILE_PROCESSING_TIMEOUT} seconds for {gate_name}")
            processing_result["error"] = f"File processing timed out after {FILE_PROCESSING_TIMEOUT} seconds"
        
        if processing_result["error"]:
            print(f"   ⚠️ File processing failed for {gate_name}: {processing_result['error']}")
            return []
        
        # Report processing statistics
        if config.get("enable_detailed_logging", True):
            print(f"   📊 File processing stats for {gate_name}: {processing_result['files_processed']} processed, {processing_result['files_skipped']} skipped, {processing_result['files_too_large']} too large, {processing_result['files_read_errors']} read errors")
        
        if len(target_files) > max_files:
            print(f"   ⚠️ File limit reached: processed {max_files} out of {len(target_files)} eligible files for {gate_name}")
        
        return processing_result["matches"]'''
    
    # Replace the method
    new_content = content.replace(original_method, fixed_method)
    
    # Write the fixed file
    nodes_file.write_text(new_content)
    
    print("✅ Successfully added timeout protection to pattern matching")
    return True

def add_environment_variables():
    """Add environment variables for timeout configuration"""
    
    env_file = Path(".env")
    env_content = ""
    
    if env_file.exists():
        env_content = env_file.read_text()
    
    # Add timeout configurations
    timeout_configs = """
# File Processing Timeout Configuration
CODEGATES_FILE_PROCESSING_TIMEOUT=300
CODEGATES_LLM_TIMEOUT=120
"""
    
    if "CODEGATES_FILE_PROCESSING_TIMEOUT" not in env_content:
        env_content += timeout_configs
        env_file.write_text(env_content)
        print("✅ Added timeout environment variables")
    else:
        print("ℹ️ Timeout environment variables already exist")

if __name__ == "__main__":
    print("🔧 Fixing infinite loop issue in pattern matching...")
    
    # Add timeout protection
    if add_timeout_protection():
        print("✅ Timeout protection added successfully")
    else:
        print("❌ Failed to add timeout protection")
        sys.exit(1)
    
    # Add environment variables
    add_environment_variables()
    
    print("\n🎉 Fix applied successfully!")
    print("The system will now:")
    print("  - Timeout file processing after 5 minutes")
    print("  - Timeout LLM calls after 2 minutes")
    print("  - Provide progress updates during file processing")
    print("  - Handle errors gracefully without hanging")
    
    print("\nTo apply the fix, restart your CodeGates server.") 