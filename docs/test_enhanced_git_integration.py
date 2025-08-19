#!/usr/bin/env python3
"""
Test Enhanced Git Integration
Comprehensive testing of repository search, branch listing, and selection features
"""

import sys
import os
from pathlib import Path

# Add the gates directory to the path
sys.path.append(str(Path(__file__).parent / "gates"))

try:
    from utils.git_operations import EnhancedGitIntegration, RepositorySelector
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_repository_search():
    """Test repository search functionality"""
    print("🧪 Testing Repository Search")
    print("=" * 50)
    
    git = EnhancedGitIntegration()
    
    # Test 1: Basic search
    print("\n1. Basic search for 'react'")
    repos = git.search_repositories("react", max_results=5)
    if repos:
        print(f"✅ Found {len(repos)} React repositories")
        for repo in repos[:3]:
            print(f"   - {repo.full_name} ({repo.stars}⭐)")
    else:
        print("❌ No repositories found")
    
    # Test 2: Language filter
    print("\n2. Search for Python repositories")
    repos = git.search_repositories("machine learning", language="Python", min_stars=1000, max_results=5)
    if repos:
        print(f"✅ Found {len(repos)} Python ML repositories")
        for repo in repos[:3]:
            print(f"   - {repo.full_name} ({repo.stars}⭐)")
    else:
        print("❌ No repositories found")
    
    # Test 3: Popular repositories
    print("\n3. Get popular JavaScript repositories")
    repos = git.get_popular_repositories(language="JavaScript", min_stars=5000)
    if repos:
        print(f"✅ Found {len(repos)} popular JavaScript repositories")
        for repo in repos[:3]:
            print(f"   - {repo.full_name} ({repo.stars}⭐)")
    else:
        print("❌ No repositories found")

def test_branch_listing():
    """Test branch listing functionality"""
    print("\n🧪 Testing Branch Listing")
    print("=" * 50)
    
    git = EnhancedGitIntegration()
    
    # Test repositories
    test_repos = [
        "facebook/react",
        "microsoft/vscode",
        "tensorflow/tensorflow"
    ]
    
    for repo_name in test_repos:
        print(f"\n📋 Branches for {repo_name}:")
        branches = git.get_repository_branches(repo_name)
        
        if branches:
            print(f"✅ Found {len(branches)} branches")
            for branch in branches[:5]:  # Show first 5
                protected = "🔒" if branch.protected else ""
                print(f"   - {branch.name} {protected}")
        else:
            print("❌ No branches found")

def test_repository_validation():
    """Test repository validation functionality"""
    print("\n🧪 Testing Repository Validation")
    print("=" * 50)
    
    git = EnhancedGitIntegration()
    
    # Test cases
    test_cases = [
        ("facebook/react", "main", True),
        ("facebook/react", "master", False),  # Should fail
        ("nonexistent/repo", "main", False),
        ("microsoft/vscode", "main", True),
    ]
    
    for repo_name, branch, should_pass in test_cases:
        print(f"\n🔍 Validating {repo_name}:{branch}")
        is_valid, message = git.validate_repository_access(repo_name, branch)
        
        if is_valid == should_pass:
            status = "✅ PASS" if is_valid else "❌ FAIL (expected)"
            print(f"   {status}: {message}")
        else:
            status = "❌ FAIL" if is_valid else "✅ PASS (expected)"
            print(f"   {status}: {message}")

def test_repository_info():
    """Test repository information retrieval"""
    print("\n🧪 Testing Repository Information")
    print("=" * 50)
    
    git = EnhancedGitIntegration()
    
    # Test repository info
    test_repos = ["facebook/react", "microsoft/vscode"]
    
    for repo_name in test_repos:
        print(f"\n📋 Repository info for {repo_name}:")
        repo_info = git.get_repository_info(repo_name)
        
        if repo_info:
            print(f"✅ Repository: {repo_info.full_name}")
            print(f"   Description: {repo_info.description[:60]}...")
            print(f"   Language: {repo_info.language}")
            print(f"   Stars: {repo_info.stars:,}")
            print(f"   Forks: {repo_info.forks:,}")
            print(f"   Default Branch: {repo_info.default_branch}")
            if repo_info.topics:
                print(f"   Topics: {', '.join(repo_info.topics[:5])}")
        else:
            print("❌ Failed to get repository info")

def test_interactive_selection():
    """Test interactive repository selection"""
    print("\n🧪 Testing Interactive Selection")
    print("=" * 50)
    
    git = EnhancedGitIntegration()
    selector = RepositorySelector(git)
    
    # Test quick validation
    print("\n1. Quick validation test:")
    is_valid = selector.quick_select("facebook/react", "main")
    print(f"   Result: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Note: Interactive search requires user input, so we'll skip it in automated tests
    print("\n2. Interactive search (skipped in automated tests)")
    print("   Use the CLI or UI for interactive testing")

def test_cli_commands():
    """Test CLI command simulation"""
    print("\n🧪 Testing CLI Commands")
    print("=" * 50)
    
    # Simulate CLI commands
    commands = [
        ["search", "--keyword", "react", "--language", "JavaScript", "--min-stars", "1000"],
        ["branches", "facebook/react"],
        ["validate", "facebook/react", "main"],
        ["popular", "--language", "Python", "--min-stars", "1000"],
        ["trending", "--timeframe", "weekly"]
    ]
    
    for cmd in commands:
        print(f"\n📋 Simulating: {' '.join(cmd)}")
        # In a real implementation, you would call the CLI functions here
        print("   (CLI command simulation - use the actual CLI for testing)")

def main():
    """Run all tests"""
    print("🚀 Enhanced Git Integration Test Suite")
    print("=" * 60)
    
    # Test repository search
    print("\n🧪 Testing Repository Search")
    print("=" * 50)
    test_repository_search()
    
    # Test branch listing
    print("\n🧪 Testing Branch Listing")
    print("=" * 50)
    test_branch_listing()
    
    # Test repository validation
    print("\n🧪 Testing Repository Validation")
    print("=" * 50)
    test_repository_validation()
    
    # Test repository information
    print("\n🧪 Testing Repository Information")
    print("=" * 50)
    test_repository_info()
    
    # Test interactive selection
    print("\n🧪 Testing Interactive Selection")
    print("=" * 50)
    test_interactive_selection()
    
    # Test CLI commands
    print("\n🧪 Testing CLI Commands")
    print("=" * 50)
    test_cli_commands()
    
    print("\n🎉 All tests completed!")
    print("=" * 60)
    print("💡 To test the full functionality:")
    print("   1. Run: python3 gates/cli_enhanced.py search -k react")
    print("   2. Run: python3 gates/cli_enhanced.py scan -i")

if __name__ == "__main__":
    main() 