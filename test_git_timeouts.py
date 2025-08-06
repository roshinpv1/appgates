#!/usr/bin/env python3
"""
Test script for Git Timeout Functionality
Demonstrates the timeout handling for git operations
"""

import sys
import os
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

try:
    from utils.git_operations import (
        clone_repository, 
        configure_git_timeouts, 
        get_git_timeout_status,
        set_ocp_optimized_timeouts,
        GitTimeoutError
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_timeout_configuration():
    """Test timeout configuration functionality"""
    print("🧪 Testing Timeout Configuration")
    print("=" * 50)
    
    # Get current status
    print("📊 Current timeout status:")
    status = get_git_timeout_status()
    for name, config in status.items():
        print(f"   {name}: {config['value']}s (default: {config['default']}s)")
    
    print("\n🔧 Configuring custom timeouts...")
    configure_git_timeouts(
        clone_timeout=120,  # 2 minutes
        api_timeout=60      # 1 minute
    )
    
    print("\n📊 Updated timeout status:")
    status = get_git_timeout_status()
    for name, config in status.items():
        print(f"   {name}: {config['value']}s")
    
    print("\n🏢 Setting OCP-optimized timeouts...")
    ocp_status = set_ocp_optimized_timeouts()
    
    return True

def test_git_operations_with_timeout():
    """Test git operations with timeout"""
    print("\n🧪 Testing Git Operations with Timeout")
    print("=" * 50)
    
    # Test with a small public repository
    test_repos = [
        {
            "url": "https://github.com/fastapi/fastapi",
            "branch": "main",
            "description": "FastAPI Repository (should succeed)"
        }
    ]
    
    for repo in test_repos:
        print(f"\n🔄 Testing: {repo['description']}")
        print(f"   URL: {repo['url']}")
        print(f"   Branch: {repo['branch']}")
        
        try:
            # Configure short timeout for demonstration
            configure_git_timeouts(clone_timeout=180, api_timeout=90)
            
            repo_path = clone_repository(
                repo_url=repo['url'],
                branch=repo['branch']
            )
            
            print(f"✅ Successfully cloned to: {repo_path}")
            
            # Quick verification
            if os.path.exists(repo_path):
                files = list(os.listdir(repo_path))[:5]  # First 5 files
                print(f"   📁 Contains {len(os.listdir(repo_path))} items")
                print(f"   📄 Sample files: {files}")
                
                # Cleanup
                import shutil
                shutil.rmtree(repo_path)
                print(f"   🧹 Cleaned up temp directory")
            
        except GitTimeoutError as e:
            print(f"⏰ Timeout occurred: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_timeout_environment_variables():
    """Test timeout configuration via environment variables"""
    print("\n🧪 Testing Environment Variable Configuration")
    print("=" * 50)
    
    # Set environment variables
    test_env_vars = {
        "CODEGATES_GIT_CLONE_TIMEOUT": "240",
        "CODEGATES_GIT_FETCH_TIMEOUT": "150", 
        "CODEGATES_GITHUB_API_TIMEOUT": "90"
    }
    
    print("🔧 Setting environment variables:")
    for var, value in test_env_vars.items():
        os.environ[var] = value
        print(f"   {var}={value}")
    
    # Reload the module to pick up new environment variables
    print("\n📊 Environment-based timeout status:")
    
    # Import with fresh environment
    import importlib
    from utils import git_operations
    importlib.reload(git_operations)
    
    status = git_operations.get_git_timeout_status()
    for name, config in status.items():
        print(f"   {name}: {config['value']}s (env: {config['env_var']})")
    
    # Clean up environment
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]

def main():
    """Main test function"""
    print("🎯 Git Timeout Functionality Tests")
    print()
    
    tests = [
        ("Timeout Configuration", test_timeout_configuration),
        ("Git Operations with Timeout", test_git_operations_with_timeout),
        ("Environment Variables", test_timeout_environment_variables)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"❌ Test {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Git timeout functionality is working correctly.")
        print("\n💡 Quick Setup for OCP:")
        print("   • Set CODEGATES_GIT_CLONE_TIMEOUT=180")
        print("   • Set CODEGATES_GITHUB_API_TIMEOUT=90") 
        print("   • Call set_ocp_optimized_timeouts() in your code")
    else:
        print(f"\n⚠️ {len(results) - passed} tests failed.")

if __name__ == "__main__":
    main() 