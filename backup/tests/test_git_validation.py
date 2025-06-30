#!/usr/bin/env python3
"""
Test script to validate Git-based repository access checking.
This tests the new approach that uses git ls-remote instead of GitHub API.
"""

import subprocess
import os
import tempfile
from urllib.parse import urlparse

def test_git_ls_remote(repo_url, token=None):
    """Test git ls-remote command for repository access validation"""
    
    print(f"🔍 Testing git ls-remote for: {repo_url}")
    
    try:
        # Parse repository URL
        parsed_url = urlparse(repo_url)
        
        # Build the Git URL for testing
        if token:
            test_url = f"https://{token}@{parsed_url.netloc}{parsed_url.path}"
        else:
            test_url = f"https://{parsed_url.netloc}{parsed_url.path}"
        
        # Ensure URL ends with .git
        if not test_url.endswith('.git'):
            test_url += '.git'
        
        print(f"   Git URL: {parsed_url.netloc}{parsed_url.path}")
        
        # Use git ls-remote to test repository access
        cmd = ["git", "ls-remote", "--heads", test_url]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30,
            env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}  # Disable interactive prompts
        )
        
        if result.returncode == 0:
            print(f"   ✅ SUCCESS: Repository accessible")
            # Show first few references
            refs = result.stdout.strip().split('\n')[:3]
            for ref in refs:
                if ref.strip():
                    parts = ref.split('\t')
                    if len(parts) >= 2:
                        print(f"      {parts[1]} -> {parts[0][:8]}...")
            return True
        else:
            print(f"   ❌ FAILED: {result.stderr.strip()}")
            
            # Parse error for specific issues
            error_output = result.stderr.lower()
            if 'authentication failed' in error_output:
                print("   💡 Suggestion: Repository may be private. Try with a GitHub token.")
            elif 'repository not found' in error_output:
                print("   💡 Suggestion: Check if the repository URL is correct.")
            elif 'ssl certificate' in error_output:
                print("   💡 Suggestion: SSL certificate issue (common with GitHub Enterprise).")
            elif 'permission denied' in error_output:
                print("   💡 Suggestion: Token may not have sufficient permissions.")
            
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ TIMEOUT: Repository access test timed out")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def test_git_clone(repo_url, branch="main", token=None):
    """Test actual git clone to verify the repository can be cloned"""
    
    print(f"\n📦 Testing git clone for: {repo_url}")
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="git_test_")
        
        # Parse repository URL
        parsed_url = urlparse(repo_url)
        
        # Build clone URL
        if token:
            clone_url = f"https://{token}@{parsed_url.netloc}{parsed_url.path}.git"
        else:
            clone_url = f"https://{parsed_url.netloc}{parsed_url.path}.git"
        
        print(f"   Clone URL: {parsed_url.netloc}{parsed_url.path}")
        print(f"   Branch: {branch}")
        print(f"   Temp dir: {temp_dir}")
        
        # Clone repository
        cmd = ["git", "clone", "-b", branch, "--depth", "1", clone_url, temp_dir]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,
            env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}
        )
        
        if result.returncode == 0:
            print(f"   ✅ SUCCESS: Repository cloned successfully")
            
            # Check if directory has content
            files = os.listdir(temp_dir)
            print(f"   📁 Files: {len(files)} items")
            
            # Show some sample files
            sample_files = [f for f in files if not f.startswith('.')][:5]
            if sample_files:
                print(f"   📄 Sample files: {', '.join(sample_files)}")
            
            return True
        else:
            print(f"   ❌ FAILED: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ TIMEOUT: Clone operation timed out")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print(f"   🧹 Cleaned up temp directory")
            except Exception as e:
                print(f"   ⚠️ Failed to cleanup temp directory: {e}")

def main():
    """Test Git-based repository validation"""
    
    print("🚀 Git-based Repository Validation Test")
    print("=" * 60)
    
    # Test repositories (using well-known public repos)
    test_repos = [
        {
            "url": "https://github.com/octocat/Hello-World",
            "description": "GitHub.com public repository",
            "should_work": True
        },
        {
            "url": "https://github.com/microsoft/vscode",
            "description": "GitHub.com large public repository",
            "should_work": True
        }
    ]
    
    # Note: For GitHub Enterprise testing, users would need to provide their own URLs
    print("\n📋 Testing public repositories (GitHub.com)...")
    
    success_count = 0
    total_tests = 0
    
    for i, repo in enumerate(test_repos, 1):
        print(f"\n{i}. {repo['description']}")
        print(f"   URL: {repo['url']}")
        
        # Test git ls-remote
        ls_remote_success = test_git_ls_remote(repo['url'])
        
        # Test git clone if ls-remote succeeded
        if ls_remote_success:
            clone_success = test_git_clone(repo['url'])
            if clone_success:
                success_count += 1
        
        total_tests += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {success_count}/{total_tests} repositories accessible")
    
    if success_count == total_tests:
        print("🎉 All tests PASSED! Git-based validation is working correctly.")
    else:
        print("⚠️ Some tests failed. Check network connectivity and repository URLs.")
    
    print("\n💡 For GitHub Enterprise testing:")
    print("   1. Replace test URLs with your GitHub Enterprise URLs")
    print("   2. Provide appropriate tokens for private repositories")
    print("   3. Ensure network connectivity to your GitHub Enterprise instance")

if __name__ == "__main__":
    main() 