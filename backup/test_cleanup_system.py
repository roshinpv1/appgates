#!/usr/bin/env python3
"""
Test script to verify the enhanced cleanup system for MyGates API

This script tests:
1. Temporary directory creation and registration
2. Cleanup after successful operations
3. Cleanup after failed operations  
4. Orphaned directory detection and cleanup
5. Manual cleanup functionality
6. Application shutdown cleanup
"""

import os
import sys
import asyncio
import tempfile
import shutil
import time
import requests
import json
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_temp_directory_management():
    """Test the managed temporary directory system"""
    print("=" * 60)
    print("🧪 Testing Temporary Directory Management")
    print("=" * 60)
    
    try:
        # Import the cleanup functions
        from codegates.api.server import (
            managed_temp_directory, 
            cleanup_temp_directory,
            cleanup_all_temp_directories,
            register_temp_directory,
            _TEMP_DIRECTORIES
        )
        
        print(f"📝 Initial registered directories: {len(_TEMP_DIRECTORIES)}")
        
        # Test 1: Managed temp directory context manager
        print("\n🔧 Test 1: Managed temp directory context manager")
        
        temp_dirs_created = []
        
        async with managed_temp_directory("test_managed_", "test directory") as temp_dir:
            print(f"   ✅ Created managed directory: {temp_dir}")
            print(f"   📝 Directory exists: {os.path.exists(temp_dir)}")
            print(f"   📝 Registered directories: {len(_TEMP_DIRECTORIES)}")
            temp_dirs_created.append(temp_dir)
            
            # Create some test files
            test_file = os.path.join(temp_dir, "test_file.txt")
            with open(test_file, 'w') as f:
                f.write("Test content")
            
            print(f"   📝 Test file created: {os.path.exists(test_file)}")
        
        # After context manager, directory should be cleaned up
        print(f"   🧹 After context: Directory exists: {os.path.exists(temp_dirs_created[0])}")
        print(f"   📝 Registered directories: {len(_TEMP_DIRECTORIES)}")
        
        # Test 2: Manual registration and cleanup
        print("\n🔧 Test 2: Manual registration and cleanup")
        
        manual_temp = tempfile.mkdtemp(prefix="test_manual_")
        print(f"   📁 Created manual directory: {manual_temp}")
        
        register_temp_directory(manual_temp)
        print(f"   📝 Registered directories: {len(_TEMP_DIRECTORIES)}")
        
        # Create test content
        test_file = os.path.join(manual_temp, "manual_test.txt")
        with open(test_file, 'w') as f:
            f.write("Manual test content")
        
        # Manual cleanup
        cleanup_success = await cleanup_temp_directory(manual_temp, "manual test directory")
        print(f"   🧹 Manual cleanup success: {cleanup_success}")
        print(f"   📝 Directory exists after cleanup: {os.path.exists(manual_temp)}")
        
        # Test 3: Cleanup all registered directories
        print("\n🔧 Test 3: Cleanup all registered directories")
        
        # Create multiple directories
        test_dirs = []
        for i in range(3):
            temp_dir = tempfile.mkdtemp(prefix=f"test_bulk_{i}_")
            register_temp_directory(temp_dir)
            test_dirs.append(temp_dir)
            
            # Add some content
            with open(os.path.join(temp_dir, f"file_{i}.txt"), 'w') as f:
                f.write(f"Content {i}")
        
        print(f"   📁 Created {len(test_dirs)} test directories")
        print(f"   📝 Registered directories: {len(_TEMP_DIRECTORIES)}")
        
        # Cleanup all
        await cleanup_all_temp_directories()
        print(f"   🧹 After cleanup all - Registered directories: {len(_TEMP_DIRECTORIES)}")
        
        # Check if directories were actually removed
        removed_count = sum(1 for d in test_dirs if not os.path.exists(d))
        print(f"   ✅ Directories actually removed: {removed_count}/{len(test_dirs)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_orphaned_directory_cleanup():
    """Test orphaned directory detection and cleanup"""
    print("\n" + "=" * 60)
    print("🧪 Testing Orphaned Directory Cleanup")
    print("=" * 60)
    
    try:
        from codegates.api.server import cleanup_orphaned_temp_directories
        
        # Create some fake orphaned directories
        temp_bases = ['./temp', '/tmp']
        orphaned_dirs = []
        
        for temp_base in temp_bases:
            if not os.path.exists(temp_base):
                try:
                    os.makedirs(temp_base, exist_ok=True)
                except (OSError, PermissionError):
                    continue
            
            # Create an old directory (simulate by setting old timestamp)
            orphaned_dir = os.path.join(temp_base, "mygates_orphaned_test_123")
            try:
                os.makedirs(orphaned_dir, exist_ok=True)
                
                # Create some content
                with open(os.path.join(orphaned_dir, "orphaned_file.txt"), 'w') as f:
                    f.write("Orphaned content")
                
                # Set old timestamp (2 hours ago)
                old_time = time.time() - 7200  # 2 hours ago
                os.utime(orphaned_dir, (old_time, old_time))
                
                orphaned_dirs.append(orphaned_dir)
                print(f"   📁 Created orphaned test directory: {orphaned_dir}")
                
            except (OSError, PermissionError) as e:
                print(f"   ⚠️ Cannot create test directory in {temp_base}: {e}")
                continue
        
        print(f"   📝 Created {len(orphaned_dirs)} orphaned test directories")
        
        # Run cleanup
        cleanup_orphaned_temp_directories()
        
        # Check results
        removed_count = sum(1 for d in orphaned_dirs if not os.path.exists(d))
        print(f"   ✅ Orphaned directories removed: {removed_count}/{len(orphaned_dirs)}")
        
        # Cleanup any remaining test directories
        for orphaned_dir in orphaned_dirs:
            if os.path.exists(orphaned_dir):
                try:
                    shutil.rmtree(orphaned_dir, ignore_errors=True)
                except Exception:
                    pass
        
        return removed_count > 0
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def test_api_cleanup_endpoints():
    """Test the API cleanup endpoints"""
    print("\n" + "=" * 60)
    print("🧪 Testing API Cleanup Endpoints")
    print("=" * 60)
    
    try:
        # Check if API server is running
        api_base = "http://localhost:8000"
        
        try:
            response = requests.get(f"{api_base}/api/v1/health", timeout=5)
            if response.status_code != 200:
                print("   ⚠️ API server not running, skipping API tests")
                return True
        except requests.RequestException:
            print("   ⚠️ API server not accessible, skipping API tests")
            return True
        
        # Test temp status endpoint
        print("   🔧 Testing /api/v1/system/temp-status")
        response = requests.get(f"{api_base}/api/v1/system/temp-status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   📝 Registered directories: {status_data.get('registered_directories', 0)}")
            print(f"   📝 Orphaned check locations: {len(status_data.get('orphaned_check', {}))}")
            print("   ✅ Temp status endpoint working")
        else:
            print(f"   ❌ Temp status endpoint failed: {response.status_code}")
        
        # Test manual cleanup endpoint
        print("   🔧 Testing /api/v1/system/cleanup")
        response = requests.get(f"{api_base}/api/v1/system/cleanup")
        if response.status_code == 200:
            cleanup_data = response.json()
            print(f"   📝 Cleanup status: {cleanup_data.get('status')}")
            print(f"   📝 Cleanup message: {cleanup_data.get('message')}")
            print("   ✅ Manual cleanup endpoint working")
        else:
            print(f"   ❌ Manual cleanup endpoint failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False

async def test_scan_cleanup_integration():
    """Test cleanup integration with actual scan operations"""
    print("\n" + "=" * 60)
    print("🧪 Testing Scan Cleanup Integration")
    print("=" * 60)
    
    try:
        # Check if API server is running
        api_base = "http://localhost:8000"
        
        try:
            response = requests.get(f"{api_base}/api/v1/health", timeout=5)
            if response.status_code != 200:
                print("   ⚠️ API server not running, skipping scan integration tests")
                return True
        except requests.RequestException:
            print("   ⚠️ API server not accessible, skipping scan integration tests")
            return True
        
        # Get initial temp status
        response = requests.get(f"{api_base}/api/v1/system/temp-status")
        if response.status_code == 200:
            initial_status = response.json()
            initial_count = initial_status.get('registered_directories', 0)
            print(f"   📝 Initial registered directories: {initial_count}")
        else:
            initial_count = 0
        
        # Start a scan that will fail (invalid repo)
        print("   🔧 Testing cleanup after failed scan")
        scan_request = {
            "repository_url": "https://github.com/nonexistent/invalid-repo-12345",
            "branch": "main",
            "scan_options": {
                "threshold": 70,
                "enable_api_fallback": True
            }
        }
        
        response = requests.post(f"{api_base}/api/v1/scan", json=scan_request)
        if response.status_code == 200:
            scan_data = response.json()
            scan_id = scan_data.get('scan_id')
            print(f"   📝 Started scan: {scan_id}")
            
            # Wait a bit for the scan to fail
            await asyncio.sleep(10)
            
            # Check status
            response = requests.get(f"{api_base}/api/v1/scan/{scan_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"   📝 Scan status: {status_data.get('status')}")
                print(f"   📝 Scan message: {status_data.get('message', '')[:100]}...")
            
            # Check temp directories after scan
            response = requests.get(f"{api_base}/api/v1/system/temp-status")
            if response.status_code == 200:
                final_status = response.json()
                final_count = final_status.get('registered_directories', 0)
                print(f"   📝 Final registered directories: {final_count}")
                
                if final_count <= initial_count:
                    print("   ✅ Cleanup working properly after failed scan")
                else:
                    print("   ⚠️ Some directories may not have been cleaned up")
            
        else:
            print(f"   ❌ Failed to start test scan: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Scan integration test failed: {e}")
        return False

async def main():
    """Run all cleanup system tests"""
    print("🧪 MyGates Cleanup System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Temporary Directory Management", test_temp_directory_management()),
        ("Orphaned Directory Cleanup", test_orphaned_directory_cleanup()),
        ("API Cleanup Endpoints", test_api_cleanup_endpoints()),
        ("Scan Cleanup Integration", test_scan_cleanup_integration())
    ]
    
    results = []
    for test_name, test_coroutine in tests:
        print(f"\n🔄 Running: {test_name}")
        try:
            if asyncio.iscoroutine(test_coroutine):
                result = await test_coroutine
            else:
                result = test_coroutine
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cleanup system tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Review the cleanup system implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 