"""
Git Operations Utility
Handles repository cloning and management
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import git
import requests
import zipfile
from urllib.parse import urlparse


def clone_repository(repo_url: str, branch: str = "main", 
                    github_token: Optional[str] = None,
                    target_dir: Optional[str] = None) -> str:
    """
    Clone a repository using Git or GitHub API with enterprise-aware preferences
    
    Args:
        repo_url: Repository URL
        branch: Branch to checkout
        github_token: GitHub token for private repos
        target_dir: Target directory (if None, creates temp dir)
    
    Returns:
        Path to cloned repository
    """
    
    if target_dir is None:
        target_dir = tempfile.mkdtemp(prefix="codegates_repo_")
    
    # Determine if this is GitHub Enterprise
    parsed_url = urlparse(repo_url)
    hostname = parsed_url.netloc.lower()
    is_github_enterprise = 'github' in hostname and hostname != 'github.com'
    
    if is_github_enterprise:
        # For GitHub Enterprise: Try API first (better for enterprise networks, SSL, VPN)
        print(f"🏢 GitHub Enterprise detected ({hostname}), trying API first")
        try:
            return _download_with_github_api(repo_url, branch, github_token, target_dir)
        except Exception as api_error:
            print(f"⚠️ GitHub API download failed: {api_error}")
            print(f"🔄 Falling back to Git clone...")
            
            # Fallback to Git clone
            try:
                return _clone_with_git(repo_url, branch, github_token, target_dir)
            except Exception as git_error:
                print(f"⚠️ Git clone also failed: {git_error}")
                raise Exception(f"Both API and Git clone failed. API: {api_error}, Git: {git_error}")
    else:
        # For GitHub.com or other Git servers: Try Git clone first (unlimited, no rate limits)
        print(f"🌐 GitHub.com or other Git server detected, trying Git clone first")
        try:
            return _clone_with_git(repo_url, branch, github_token, target_dir)
        except Exception as git_error:
            print(f"⚠️ Git clone failed: {git_error}")
            
            # Fallback to GitHub API if it's a GitHub repo
            if "github.com" in repo_url:
                print(f"🔄 Falling back to GitHub API...")
                try:
                    return _download_with_github_api(repo_url, branch, github_token, target_dir)
                except Exception as api_error:
                    print(f"⚠️ GitHub API download failed: {api_error}")
                    raise Exception(f"Both Git clone and API download failed. Git: {git_error}, API: {api_error}")
            else:
                raise git_error


def _clone_with_git(repo_url: str, branch: str, github_token: Optional[str], target_dir: str) -> str:
    """Clone repository using Git"""
    
    # Prepare URL with token if provided
    if github_token and "github.com" in repo_url:
        # Insert token into URL
        parsed = urlparse(repo_url)
        auth_url = f"https://{github_token}@{parsed.netloc}{parsed.path}"
    else:
        auth_url = repo_url
    
    print(f"🔄 Cloning repository with Git: {repo_url} (branch: {branch})")
    
    # Clone repository
    repo = git.Repo.clone_from(auth_url, target_dir, branch=branch, depth=1)
    
    print(f"✅ Repository cloned successfully to: {target_dir}")
    return target_dir


def _download_with_github_api(repo_url: str, branch: str, github_token: Optional[str], target_dir: str) -> str:
    """Download repository using GitHub API"""
    
    # Extract owner and repo name from URL
    owner, repo_name = _parse_github_url(repo_url)
    
    # Prepare API URL
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/zipball/{branch}"
    
    # Prepare headers
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    print(f"🔄 Downloading repository with GitHub API: {repo_url} (branch: {branch})")
    
    # Download zip file
    response = requests.get(api_url, headers=headers, stream=True)
    response.raise_for_status()
    
    # Save and extract zip file
    zip_path = os.path.join(target_dir, "repo.zip")
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Extract zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
    
    # Remove zip file
    os.remove(zip_path)
    
    # Find extracted directory (GitHub creates a directory with commit hash)
    extracted_dirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
    if not extracted_dirs:
        raise Exception("No directory found after extraction")
    
    # Move contents to target directory
    extracted_dir = os.path.join(target_dir, extracted_dirs[0])
    temp_dir = target_dir + "_temp"
    shutil.move(extracted_dir, temp_dir)
    
    # Remove old target directory and rename temp
    shutil.rmtree(target_dir)
    shutil.move(temp_dir, target_dir)
    
    print(f"✅ Repository downloaded successfully to: {target_dir}")
    return target_dir


def _parse_github_url(repo_url: str) -> Tuple[str, str]:
    """Parse GitHub URL to extract owner and repo name"""
    
    # Remove .git suffix if present
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    
    # Parse URL
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL format: {repo_url}")
    
    owner = path_parts[0]
    repo_name = path_parts[1]
    
    return owner, repo_name


def cleanup_repository(repo_path: str) -> None:
    """
    Clean up cloned repository
    
    Args:
        repo_path: Path to repository directory
    """
    
    if os.path.exists(repo_path):
        try:
            shutil.rmtree(repo_path)
            print(f"🧹 Cleaned up repository: {repo_path}")
        except Exception as e:
            print(f"⚠️ Failed to cleanup repository {repo_path}: {e}")


def get_repository_info(repo_path: str) -> dict:
    """
    Get basic information about the repository
    
    Args:
        repo_path: Path to repository directory
        
    Returns:
        Dictionary with repository information
    """
    
    info = {
        "path": repo_path,
        "exists": os.path.exists(repo_path),
        "is_git_repo": False,
        "current_branch": None,
        "commit_hash": None,
        "remote_url": None
    }
    
    try:
        if os.path.exists(os.path.join(repo_path, ".git")):
            repo = git.Repo(repo_path)
            info.update({
                "is_git_repo": True,
                "current_branch": repo.active_branch.name,
                "commit_hash": repo.head.commit.hexsha[:8],
                "remote_url": repo.remote().url if repo.remotes else None
            })
    except Exception as e:
        print(f"⚠️ Could not get Git info: {e}")
    
    return info


if __name__ == "__main__":
    # Test the git operations
    test_repo = "https://github.com/octocat/Hello-World"
    test_branch = "master"
    
    print(f"Testing git operations with {test_repo}")
    
    try:
        repo_path = clone_repository(test_repo, test_branch)
        info = get_repository_info(repo_path)
        print(f"Repository info: {info}")
        cleanup_repository(repo_path)
        print("✅ Test completed successfully")
    except Exception as e:
        print(f"❌ Test failed: {e}") 