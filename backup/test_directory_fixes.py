#!/usr/bin/env python3
"""
Test script to verify fixes for "directory is not empty" issues

This script tests:
1. Unique temporary directory creation with collision avoidance
2. Safe archive extraction with robust error handling
3. Proper cleanup of extraction artifacts
4. Race condition prevention
"""

import os
import sys
import asyncio
import tempfile
import shutil
import zipfile
import io
import time
import threading
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_unique_directory_creation():
    """Test unique temporary directory creation"""
    print("=" * 60)
    print("🧪 Testing Unique Directory Creation")
    print("=" * 60)
    
    try:
        from codegates.api.server import create_unique_temp_directory, cleanup_temp_directory
        
        # Test 1: Create multiple directories rapidly
        print("   🔧 Test 1: Creating multiple directories rapidly")
        directories = []
        for i in range(10):
            try:
                temp_dir = create_unique_temp_directory("test_rapid_", f"rapid test directory {i}")
                directories.append(temp_dir)
                print(f"      Created: {os.path.basename(temp_dir)}")
            except Exception as e:
                print(f"      ❌ Failed to create directory {i}: {e}")
                return False
        
        # Verify all directories are unique
        unique_names = set(os.path.basename(d) for d in directories)
        if len(unique_names) == len(directories):
            print(f"   ✅ All {len(directories)} directories have unique names")
        else:
            print(f"   ❌ Directory name collision detected: {len(directories)} created, {len(unique_names)} unique")
            return False
        
        # Cleanup
        for temp_dir in directories:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Test 2: Concurrent directory creation
        print("   🔧 Test 2: Concurrent directory creation")
        concurrent_dirs = []
        lock = threading.Lock()
        
        def create_concurrent_dir(index):
            try:
                temp_dir = create_unique_temp_directory("test_concurrent_", f"concurrent test directory {index}")
                with lock:
                    concurrent_dirs.append(temp_dir)
                    print(f"      Thread {index}: Created {os.path.basename(temp_dir)}")
            except Exception as e:
                print(f"      ❌ Thread {index} failed: {e}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_concurrent_dir, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify concurrent creation results
        if len(concurrent_dirs) == 5:
            unique_concurrent = set(os.path.basename(d) for d in concurrent_dirs)
            if len(unique_concurrent) == 5:
                print(f"   ✅ Concurrent creation successful: {len(concurrent_dirs)} directories, all unique")
            else:
                print(f"   ❌ Concurrent name collision: {len(concurrent_dirs)} created, {len(unique_concurrent)} unique")
                return False
        else:
            print(f"   ❌ Concurrent creation failed: expected 5, got {len(concurrent_dirs)}")
            return False
        
        # Cleanup concurrent directories
        for temp_dir in concurrent_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        print("   ✅ Unique directory creation tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_safe_archive_extraction():
    """Test safe archive extraction"""
    print("\n" + "=" * 60)
    print("🧪 Testing Safe Archive Extraction")
    print("=" * 60)
    
    try:
        from codegates.api.server import safe_extract_archive, create_unique_temp_directory
        
        # Create a test ZIP archive with GitHub-like structure
        print("   🔧 Creating test ZIP archive with GitHub structure")
        
        # Create temporary directory for the test
        test_base = create_unique_temp_directory("test_extract_", "extraction test")
        
        # Create a mock repository structure
        repo_content = {
            'owner-repo-abcd1234/README.md': 'This is a test repository',
            'owner-repo-abcd1234/src/main.py': 'print("Hello, World!")',
            'owner-repo-abcd1234/src/__init__.py': '',
            'owner-repo-abcd1234/tests/test_main.py': 'import unittest',
            'owner-repo-abcd1234/.gitignore': '*.pyc\n__pycache__/',
        }
        
        # Create ZIP archive in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, content in repo_content.items():
                zip_file.writestr(file_path, content)
        
        zip_content = zip_buffer.getvalue()
        print(f"   📦 Created test archive ({len(zip_content)} bytes, {len(repo_content)} files)")
        
        # Test extraction
        print("   🔧 Testing safe extraction")
        extraction_dir = create_unique_temp_directory("test_extraction_", "extraction target")
        
        try:
            result_dir = safe_extract_archive(zip_content, extraction_dir)
            
            # Verify extraction results
            if result_dir == extraction_dir:
                print(f"   ✅ Extraction completed to: {result_dir}")
                
                # Check if files were extracted correctly
                expected_files = ['README.md', 'src/main.py', 'src/__init__.py', 'tests/test_main.py', '.gitignore']
                extracted_files = []
                
                for root, dirs, files in os.walk(result_dir):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), result_dir)
                        extracted_files.append(rel_path)
                
                print(f"   📁 Expected files: {len(expected_files)}")
                print(f"   📁 Extracted files: {len(extracted_files)}")
                
                missing_files = set(expected_files) - set(extracted_files)
                extra_files = set(extracted_files) - set(expected_files)
                
                if not missing_files and not extra_files:
                    print("   ✅ All files extracted correctly")
                    
                    # Test extraction with existing content (should handle conflicts)
                    print("   🔧 Testing extraction with existing content")
                    
                    # Create a conflicting file
                    conflict_file = os.path.join(extraction_dir, 'README.md')
                    with open(conflict_file, 'w') as f:
                        f.write("This is a conflicting file")
                    
                    # Extract again
                    try:
                        result_dir2 = safe_extract_archive(zip_content, extraction_dir)
                        print("   ✅ Re-extraction with conflicts handled successfully")
                    except Exception as e:
                        print(f"   ❌ Re-extraction failed: {e}")
                        return False
                    
                else:
                    if missing_files:
                        print(f"   ❌ Missing files: {missing_files}")
                    if extra_files:
                        print(f"   ❌ Extra files: {extra_files}")
                    return False
                
            else:
                print(f"   ❌ Unexpected result directory: {result_dir}")
                return False
                
        finally:
            # Cleanup
            try:
                shutil.rmtree(test_base, ignore_errors=True)
                shutil.rmtree(extraction_dir, ignore_errors=True)
            except Exception:
                pass
        
        print("   ✅ Safe archive extraction tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def test_directory_cleanup_robustness():
    """Test robust directory cleanup"""
    print("\n" + "=" * 60)
    print("🧪 Testing Directory Cleanup Robustness")
    print("=" * 60)
    
    try:
        from codegates.api.server import create_unique_temp_directory, cleanup_temp_directory
        
        # Test 1: Cleanup directory with permission issues
        print("   🔧 Test 1: Cleanup with permission issues")
        
        test_dir = create_unique_temp_directory("test_cleanup_", "cleanup test")
        
        # Create files with different permissions
        normal_file = os.path.join(test_dir, 'normal.txt')
        readonly_file = os.path.join(test_dir, 'readonly.txt')
        subdir = os.path.join(test_dir, 'subdir')
        subfile = os.path.join(subdir, 'subfile.txt')
        
        with open(normal_file, 'w') as f:
            f.write('normal file')
        
        with open(readonly_file, 'w') as f:
            f.write('readonly file')
        
        os.makedirs(subdir)
        with open(subfile, 'w') as f:
            f.write('subfile')
        
        # Make some files readonly
        try:
            os.chmod(readonly_file, 0o444)  # Read-only
            os.chmod(subdir, 0o555)  # Read + execute only
        except OSError:
            print("   ⚠️ Cannot set file permissions (Windows or restricted environment)")
        
        # Test cleanup
        cleanup_success = await cleanup_temp_directory(test_dir, "permission test directory")
        
        if cleanup_success and not os.path.exists(test_dir):
            print("   ✅ Cleanup with permission issues successful")
        else:
            print(f"   ❌ Cleanup failed: success={cleanup_success}, exists={os.path.exists(test_dir)}")
            return False
        
        # Test 2: Cleanup deeply nested structure
        print("   🔧 Test 2: Cleanup deeply nested structure")
        
        nested_dir = create_unique_temp_directory("test_nested_", "nested cleanup test")
        
        # Create deeply nested structure
        current_path = nested_dir
        for i in range(10):
            current_path = os.path.join(current_path, f'level_{i}')
            os.makedirs(current_path)
            
            # Add some files at each level
            for j in range(3):
                file_path = os.path.join(current_path, f'file_{j}.txt')
                with open(file_path, 'w') as f:
                    f.write(f'Content at level {i}, file {j}')
        
        # Test cleanup
        cleanup_success = await cleanup_temp_directory(nested_dir, "nested test directory")
        
        if cleanup_success and not os.path.exists(nested_dir):
            print("   ✅ Cleanup of deeply nested structure successful")
        else:
            print(f"   ❌ Nested cleanup failed: success={cleanup_success}, exists={os.path.exists(nested_dir)}")
            return False
        
        print("   ✅ Directory cleanup robustness tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def main():
    """Run all directory fix tests"""
    print("🧪 Directory Fixes Test Suite")
    print("=" * 60)
    
    tests = [
        ("Unique Directory Creation", test_unique_directory_creation()),
        ("Safe Archive Extraction", test_safe_archive_extraction()),
        ("Directory Cleanup Robustness", test_directory_cleanup_robustness())
    ]
    
    results = []
    for test_name, test_result in tests:
        print(f"\n🔄 Running: {test_name}")
        try:
            if asyncio.iscoroutine(test_result):
                result = await test_result
            else:
                result = test_result
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Directory Fixes Test Results")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All directory fixes working properly!")
        print("\n🔧 Key improvements:")
        print("   • Unique temporary directory creation prevents collisions")
        print("   • Safe archive extraction handles GitHub structure properly")
        print("   • Robust cleanup handles permission and nesting issues")
        print("   • Race condition prevention in concurrent operations")
        return True
    else:
        print("⚠️ Some tests failed. Review the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 