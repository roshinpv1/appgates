#!/usr/bin/env python3
"""
Test script to verify graceful handling of missing repositories
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from utils.git_utils import GitUtils
from core.base import ScanContext


async def test_repository_handling():
    """Test repository handling scenarios"""
    
    git_utils = GitUtils()
    
    test_cases = [
        {
            "name": "Valid Repository",
            "repo_url": "https://github.com/octocat/Hello-World",
            "branch": "main",
            "should_succeed": True
        },
        {
            "name": "Repository with CD",
            "repo_url": "https://github.com/apache/fineract",
            "branch": "develop",
            "should_succeed": True
        },
        {
            "name": "Non-existent Repository",
            "repo_url": "https://github.com/nonexistent/repo",
            "branch": "main",
            "should_succeed": False
        },
        {
            "name": "Repository with Non-existent CD",
            "repo_url": "https://github.com/apache/fineract",
            "branch": "develop",
            "should_succeed": True  # Should succeed with main repo only
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"   URL: {test_case['repo_url']}")
        print(f"   Branch: {test_case['branch']}")
        
        try:
            # Test cloning
            repo_path = await git_utils.clone_repository(
                test_case['repo_url'], 
                test_case['branch']
            )
            
            if repo_path:
                print(f"   ✅ Main repository cloned successfully: {repo_path}")
                
                # Test getting repository info
                repo_info = await git_utils.get_repository_info(repo_path)
                print(f"   📊 Repository info: {repo_info.total_files} files, {repo_info.total_lines} lines")
                
                # Test CD repository
                cd_repo_url = git_utils._get_cd_repo_url(test_case['repo_url'])
                print(f"   🔍 CD repository URL: {cd_repo_url}")
                
                try:
                    cd_repo_path = await git_utils.clone_repository(
                        cd_repo_url, 
                        test_case['branch']
                    )
                    cd_repo_info = await git_utils.get_repository_info(cd_repo_path)
                    print(f"   ✅ CD repository cloned successfully: {cd_repo_path}")
                    print(f"   📊 CD repository info: {cd_repo_info.total_files} files, {cd_repo_info.total_lines} lines")
                except Exception as e:
                    print(f"   ⚠️ CD repository not found or failed: {e}")
                
            else:
                print(f"   ❌ Failed to clone repository")
                
        except Exception as e:
            print(f"   ❌ Repository handling failed: {e}")
            
            if test_case['should_succeed']:
                print(f"   ⚠️ Expected to succeed but failed")
            else:
                print(f"   ✅ Expected to fail and failed gracefully")


if __name__ == "__main__":
    asyncio.run(test_repository_handling())
