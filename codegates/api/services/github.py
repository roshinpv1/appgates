"""
GitHub Service

Handles GitHub API interactions and repository operations.
"""

import os
from urllib.parse import urlparse
import requests
from github import Github
from github.GithubException import GithubException


class GitHubService:
    """Service for interacting with GitHub repositories"""
    
    def __init__(self, token=None):
        """
        Initialize GitHub service
        
        Args:
            token (str, optional): GitHub personal access token
        """
        self.token = token
        self.client = Github(token) if token else Github()
        
    def can_access_repository(self, repo_url):
        """
        Check if the repository is accessible
        
        Args:
            repo_url (str): GitHub repository URL
            
        Returns:
            bool: True if accessible, False otherwise
        """
        try:
            owner, name = self.parse_repo_url(repo_url)
            repo = self.client.get_repo(f"{owner}/{name}")
            # Try to access basic repo info to verify permissions
            _ = repo.name
            return True
        except GithubException as e:
            if e.status == 404:  # Repository not found
                return False
            if e.status == 401 and not self.token:  # Unauthorized, no token provided
                return False
            if e.status == 403:  # Forbidden, invalid token or private repo without token
                return False
            return False
        except Exception:
            return False
            
    def get_repo_owner(self, repo_url):
        """Get repository owner from URL"""
        owner, _ = self.parse_repo_url(repo_url)
        return owner
        
    def get_repo_name(self, repo_url):
        """Get repository name from URL"""
        _, name = self.parse_repo_url(repo_url)
        return name
        
    def parse_repo_url(self, repo_url):
        """
        Parse owner and name from repository URL
        
        Args:
            repo_url (str): GitHub repository URL
            
        Returns:
            tuple: (owner, name)
            
        Raises:
            ValueError: If URL format is invalid
        """
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) != 2:
                raise ValueError("Invalid repository URL format")
                
            return path_parts[0], path_parts[1]
            
        except Exception as e:
            raise ValueError(f"Failed to parse repository URL: {str(e)}")
            
    def get_default_branch(self, repo_url):
        """Get repository's default branch"""
        try:
            owner, name = self.parse_repo_url(repo_url)
            repo = self.client.get_repo(f"{owner}/{name}")
            return repo.default_branch
        except Exception as e:
            raise ValueError(f"Failed to get default branch: {str(e)}")
            
    def clone_repository(self, repo_url, branch, target_dir):
        """
        Clone repository to target directory
        
        Args:
            repo_url (str): GitHub repository URL
            branch (str): Branch to clone
            target_dir (str): Target directory path
            
        Returns:
            str: Path to cloned repository
        """
        try:
            # Create clone URL with or without token
            parsed = urlparse(repo_url)
            if self.token:
                clone_url = f"https://{self.token}@{parsed.netloc}{parsed.path}.git"
            else:
                clone_url = f"https://{parsed.netloc}{parsed.path}.git"
            
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Clone repository
            repo_path = os.path.join(target_dir, self.get_repo_name(repo_url))
            os.system(f"git clone -b {branch} {clone_url} {repo_path}")
            
            return repo_path
            
        except Exception as e:
            raise ValueError(f"Failed to clone repository: {str(e)}")
            
    def cleanup_repository(self, repo_path):
        """Clean up cloned repository"""
        try:
            if os.path.exists(repo_path):
                os.system(f"rm -rf {repo_path}")
        except Exception:
            pass  # Ignore cleanup errors 