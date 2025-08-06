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
import time
import urllib3
import subprocess
import signal
import threading
from contextlib import contextmanager

# Configuration for git operation timeouts
GIT_CLONE_TIMEOUT = int(os.getenv("CODEGATES_GIT_CLONE_TIMEOUT", "300"))  # 5 minutes default
GIT_FETCH_TIMEOUT = int(os.getenv("CODEGATES_GIT_FETCH_TIMEOUT", "180"))  # 3 minutes default
GITHUB_API_TIMEOUT = int(os.getenv("CODEGATES_GITHUB_API_TIMEOUT", "120"))  # 2 minutes default

class GitTimeoutError(Exception):
    """Custom exception for git operation timeouts"""
    pass

@contextmanager
def timeout_context(seconds: int, operation_name: str = "Git operation"):
    """Context manager for timing out git operations"""
    def timeout_handler(signum, frame):
        raise GitTimeoutError(f"{operation_name} timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the old signal handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def run_git_command_with_timeout(cmd: list, timeout: int, cwd: str = None, env: dict = None) -> subprocess.CompletedProcess:
    """Run git command with timeout using subprocess"""
    try:
        print(f"🔄 Running git command with {timeout}s timeout: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result
        
    except subprocess.TimeoutExpired as e:
        print(f"⏰ Git command timed out after {timeout} seconds: {' '.join(cmd)}")
        raise GitTimeoutError(f"Git command timed out after {timeout} seconds")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e.stderr}")
        raise Exception(f"Git command failed: {e.stderr}")
    except Exception as e:
        print(f"❌ Git command error: {e}")
        raise Exception(f"Git command error: {e}")


def clone_repository(repo_url: str, branch: str = "main", 
                    github_token: Optional[str] = None,
                    target_dir: Optional[str] = None) -> str:
    """
    Clone a repository using Git or GitHub API with enterprise-aware preferences and timeout handling
    
    Args:
        repo_url: Repository URL
        branch: Branch to checkout
        github_token: GitHub token for private repos
        target_dir: Target directory (if None, creates temp dir)
    
    Returns:
        Path to cloned repository
        
    Raises:
        GitTimeoutError: If git operations exceed configured timeouts
        Exception: For other git-related errors
    """
    
    print(f"🔧 Git timeout configuration:")
    timeout_status = get_git_timeout_status()
    for name, config in timeout_status.items():
        print(f"   {name}: {config['value']}s (env: {config['env_var']})")
    
    if target_dir is None:
        try:
            target_dir = tempfile.mkdtemp(prefix="codegates_repo_", suffix="_temp")
            print(f"📁 Created temp directory: {target_dir}")
        except Exception as e:
            raise Exception(f"Failed to create temporary directory: {e}")
    
    # Ensure target directory exists and is writable
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create target directory {target_dir}: {e}")
    
    # Verify directory is writable
    if not os.access(target_dir, os.W_OK):
        raise Exception(f"Target directory is not writable: {target_dir}")
    
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
            except GitTimeoutError as git_timeout_error:
                print(f"⏰ Git clone timed out: {git_timeout_error}")
                # Clean up temp directory on timeout
                if target_dir and target_dir.startswith(tempfile.gettempdir()):
                    cleanup_repository(target_dir)
                raise GitTimeoutError(f"Both API and Git clone failed due to timeout. API: {api_error}, Git: {git_timeout_error}")
            except Exception as git_error:
                print(f"⚠️ Git clone also failed: {git_error}")
                # Clean up temp directory on failure
                if target_dir and target_dir.startswith(tempfile.gettempdir()):
                    cleanup_repository(target_dir)
                raise Exception(f"Both API and Git clone failed. API: {api_error}, Git: {git_error}")
    else:
        # For GitHub.com and other Git servers: Try Git clone first
        print(f"🌐 Public repository detected, trying Git clone first")
        try:
            return _clone_with_git(repo_url, branch, github_token, target_dir)
        except GitTimeoutError as git_timeout_error:
            print(f"⏰ Git clone timed out: {git_timeout_error}")
            # Clean up temp directory on timeout
            if target_dir and target_dir.startswith(tempfile.gettempdir()):
                cleanup_repository(target_dir)
            raise git_timeout_error
        except Exception as git_error:
            print(f"⚠️ Git clone failed: {git_error}")
            
            # Fallback to GitHub API if it's GitHub.com
            if "github.com" in repo_url:
                print(f"🔄 Falling back to GitHub API...")
                try:
                    return _download_with_github_api(repo_url, branch, github_token, target_dir)
                except Exception as api_error:
                    print(f"⚠️ GitHub API also failed: {api_error}")
                    # Clean up temp directory on failure
                    if target_dir and target_dir.startswith(tempfile.gettempdir()):
                        cleanup_repository(target_dir)
                    raise Exception(f"Both Git clone and API failed. Git: {git_error}, API: {api_error}")
            else:
                # Clean up temp directory on failure
                if target_dir and target_dir.startswith(tempfile.gettempdir()):
                    cleanup_repository(target_dir)
                raise git_error


def _clone_with_git(repo_url: str, branch: str, github_token: Optional[str], target_dir: str) -> str:
    """Clone repository using Git with enterprise support and timeout"""
    
    # Parse repository URL to determine if it's enterprise
    parsed_url = urlparse(repo_url)
    hostname = parsed_url.netloc.lower()
    is_github_enterprise = 'github' in hostname and hostname != 'github.com'
    
    # Prepare URL with token if provided
    if github_token:
        if is_github_enterprise or "github.com" in repo_url:
            # Insert token into URL for GitHub authentication
            auth_url = f"https://{github_token}@{hostname}{parsed_url.path}"
        else:
            # For other Git servers, use the original URL
            auth_url = repo_url
    else:
        auth_url = repo_url
    
    print(f"🔄 Cloning repository with Git (timeout: {GIT_CLONE_TIMEOUT}s): {repo_url} (branch: {branch})")
    
    # Configure Git environment for enterprise scenarios
    env = os.environ.copy()
    
    if is_github_enterprise:
        print(f"🏢 Configuring Git SSL settings for GitHub Enterprise: {hostname}")
        
        # Enterprise-specific Git configurations
        disable_ssl = os.getenv('GITHUB_ENTERPRISE_DISABLE_SSL', 'true').lower() == 'true'
        ca_bundle = os.getenv('GITHUB_ENTERPRISE_CA_BUNDLE')
        
        if disable_ssl:
            env['GIT_SSL_NO_VERIFY'] = 'true'
            print("⚠️ SSL verification disabled for Git clone (via GITHUB_ENTERPRISE_DISABLE_SSL)")
        elif ca_bundle and os.path.exists(ca_bundle):
            env['GIT_SSL_CAINFO'] = ca_bundle
            print(f"🔐 Using custom CA bundle for Git: {ca_bundle}")
        else:
            print("🔐 Using default SSL verification for Git (set GITHUB_ENTERPRISE_DISABLE_SSL=true if you have certificate issues)")
    
    # Prepare git clone command
    git_cmd = [
        "git", "clone",
        "--depth", "1",
        "--branch", branch,
        "--single-branch",
        auth_url,
        target_dir
    ]
    
    # First attempt with current SSL settings
    ssl_retry_attempted = False
    
    try:
        # Clone repository with timeout
        result = run_git_command_with_timeout(
            git_cmd, 
            timeout=GIT_CLONE_TIMEOUT,
            env=env
        )
        
        print(f"✅ Repository cloned successfully to: {target_dir}")
        return target_dir
        
    except GitTimeoutError as e:
        print(f"⏰ Git clone timed out: {e}")
        raise Exception(f"Git clone operation timed out after {GIT_CLONE_TIMEOUT} seconds. Repository might be too large or network is slow.")
        
    except Exception as e:
        error_msg = str(e)
        
        # Handle SSL certificate errors with auto-retry
        if "ssl certificate problem" in error_msg.lower() or "certificate verify failed" in error_msg.lower():
            if is_github_enterprise and not ssl_retry_attempted:
                print(f"⚠️ Git SSL certificate verification failed: {e}")
                print("🔄 Retrying Git clone with SSL verification disabled...")
                
                # Retry with SSL disabled
                env['GIT_SSL_NO_VERIFY'] = 'true'
                ssl_retry_attempted = True
                
                try:
                    result = run_git_command_with_timeout(
                        git_cmd,
                        timeout=GIT_CLONE_TIMEOUT,
                        env=env
                    )
                    print(f"✅ Repository cloned successfully to: {target_dir} (SSL verification disabled)")
                    return target_dir
                except GitTimeoutError as retry_timeout_error:
                    raise Exception(f"Git clone timed out even with SSL disabled: {retry_timeout_error}")
                except Exception as retry_error:
                    raise Exception(f"Git clone failed even with SSL disabled: {retry_error}")
            else:
                raise Exception(f"SSL certificate issue. For enterprise GitHub, try setting GITHUB_ENTERPRISE_DISABLE_SSL=true or provide a CA bundle.")
        elif "authentication failed" in error_msg.lower():
            raise Exception(f"Git authentication failed. Check your GitHub token and permissions.")
        elif "repository not found" in error_msg.lower():
            raise Exception(f"Repository not found or access denied: {repo_url}")
        elif "connection refused" in error_msg.lower():
            raise Exception(f"Connection refused. Check network connectivity and repository URL.")
        elif "timeout" in error_msg.lower():
            raise Exception(f"Git clone timeout. The repository might be too large or network is slow.")
        else:
            raise Exception(f"Git clone failed: {error_msg}")
    
    except Exception as e:
        raise Exception(f"Failed to clone repository: {str(e)}")


def _download_with_github_api(repo_url: str, branch: str, github_token: Optional[str], target_dir: str) -> str:
    """Download repository using GitHub API with enterprise support"""
    
    # Parse repository URL to determine if it's enterprise
    parsed_url = urlparse(repo_url)
    hostname = parsed_url.netloc.lower()
    is_github_enterprise = 'github' in hostname and hostname != 'github.com'
    
    # Extract owner and repo name from URL
    owner, repo_name = _parse_github_url(repo_url)
    
    # Construct API URL based on repository type
    if is_github_enterprise:
        # For GitHub Enterprise: use enterprise API endpoint
        api_url = f"https://{hostname}/api/v3/repos/{owner}/{repo_name}/zipball/{branch}"
        print(f"🏢 Using GitHub Enterprise API: {api_url}")
    else:
        # For GitHub.com: use public API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/zipball/{branch}"
        print(f"🌐 Using GitHub.com API: {api_url}")
    
    # Prepare headers
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CodeGates/1.0"
    }
    
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    print(f"🔄 Downloading repository with GitHub API: {repo_url} (branch: {branch})")
    
    # Configure request session with enterprise-friendly settings
    session = requests.Session()
    session.headers.update(headers)
    
    # Enterprise-specific configurations with configurable timeout
    request_kwargs = {
        "stream": True,
        "timeout": (30, GITHUB_API_TIMEOUT),  # (connect_timeout, read_timeout) - now configurable
        "allow_redirects": True
    }
    
    print(f"🔄 Using GitHub API timeout: {GITHUB_API_TIMEOUT} seconds")
    
    # Handle SSL verification for enterprise environments
    if is_github_enterprise:
        print(f"🏢 Configuring SSL settings for GitHub Enterprise: {hostname}")
        
        # Check multiple environment variables for SSL bypass
        disable_ssl = (
            os.getenv('GITHUB_ENTERPRISE_DISABLE_SSL', 'true').lower() == 'true' or
            os.getenv('CODEGATES_DISABLE_SSL', 'true').lower() == 'true' or
            os.getenv('DISABLE_SSL_VERIFICATION', 'true').lower() == 'true'
        )
        ca_bundle = os.getenv('GITHUB_ENTERPRISE_CA_BUNDLE') or os.getenv('SSL_CA_BUNDLE')
        
        if disable_ssl:
            request_kwargs["verify"] = False
            print("⚠️ SSL verification disabled for GitHub Enterprise")
            print("   Set via: GITHUB_ENTERPRISE_DISABLE_SSL=true")
            print("   Or: CODEGATES_DISABLE_SSL=true")
            print("   Or: DISABLE_SSL_VERIFICATION=true")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        elif ca_bundle and os.path.exists(ca_bundle):
            request_kwargs["verify"] = ca_bundle
            print(f"🔐 Using custom CA bundle: {ca_bundle}")
        else:
            print("🔐 Using default SSL verification")
            print("   To disable SSL: export GITHUB_ENTERPRISE_DISABLE_SSL=true")
            print("   To use custom CA: export GITHUB_ENTERPRISE_CA_BUNDLE=/path/to/ca-bundle.crt")
    else:
        # For GitHub.com, also check for global SSL bypass
        disable_ssl = (
            os.getenv('CODEGATES_DISABLE_SSL', 'false').lower() == 'true' or
            os.getenv('DISABLE_SSL_VERIFICATION', 'false').lower() == 'true'
        )
        
        if disable_ssl:
            request_kwargs["verify"] = False
            print("⚠️ SSL verification disabled for GitHub.com")
            print("   Set via: CODEGATES_DISABLE_SSL=true")
            print("   Or: DISABLE_SSL_VERIFICATION=true")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # First attempt with current SSL settings
    ssl_retry_attempted = False
    
    try:
        # Download zip file with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = session.get(api_url, **request_kwargs)
                response.raise_for_status()
                break
            except requests.exceptions.SSLError as e:
                # Handle SSL certificate errors specifically
                ssl_error_msg = str(e).lower()
                if any(ssl_issue in ssl_error_msg for ssl_issue in [
                    "certificate verify failed", 
                    "self-signed certificate",
                    "certificate has expired",
                    "hostname mismatch",
                    "ssl certificate",
                    "certificate error"
                ]):
                    if not ssl_retry_attempted:
                        print(f"⚠️ SSL certificate verification failed: {e}")
                        print("🔄 Retrying with SSL verification disabled...")
                        
                        # Retry with SSL disabled
                        request_kwargs["verify"] = False
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        ssl_retry_attempted = True
                        continue
                    else:
                        raise Exception(f"SSL certificate verification failed even with SSL disabled. Error: {e}")
                else:
                    raise
            except requests.exceptions.ConnectionError as e:
                connection_error_msg = str(e).lower()
                if any(conn_issue in connection_error_msg for conn_issue in [
                    "connection reset by peer",
                    "connection refused",
                    "connection timeout",
                    "network is unreachable"
                ]) and attempt < max_retries - 1:
                    print(f"⚠️ Connection error: {e}")
                    print(f"🔄 Retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Request timeout, retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise
    
        # Save and extract zip file
        zip_path = os.path.join(target_dir, "repo.zip")
        
        try:
            # Ensure we can write to the target directory
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            
            # Write the zip file
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
            
            # Verify the zip file was created and has content
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                raise Exception("Downloaded zip file is empty or was not created")
            
            print(f"📦 Downloaded {os.path.getsize(zip_path)} bytes to {zip_path}")
            
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
            
            # Ensure temp_dir doesn't already exist
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            shutil.move(extracted_dir, temp_dir)
            
            # Remove old target directory and rename temp
            shutil.rmtree(target_dir)
            shutil.move(temp_dir, target_dir)
            
            print(f"✅ Repository downloaded successfully to: {target_dir}")
            return target_dir
            
        except zipfile.BadZipFile as e:
            # Clean up the bad zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise Exception(f"Downloaded file is not a valid zip file: {e}")
        
        except Exception as e:
            # Clean up any partial files
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise Exception(f"Failed to extract repository: {e}")
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise Exception(f"Repository not found or access denied: {repo_url}")
        elif e.response.status_code == 401:
            raise Exception(f"Authentication failed. Check your GitHub token.")
        elif e.response.status_code == 403:
            raise Exception(f"Access forbidden. Check repository permissions and token scopes.")
        else:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
    
    except requests.exceptions.ConnectionError as e:
        if "Connection reset by peer" in str(e):
            raise Exception(f"Connection reset by peer. This often happens with enterprise GitHub due to network/SSL issues. Try: 1) Check SSL settings 2) Use git clone instead 3) Contact your IT team")
        else:
            raise Exception(f"Connection error: {str(e)}")
    
    except requests.exceptions.Timeout as e:
        raise Exception(f"Request timeout. The repository might be too large or the network is slow: {str(e)}")
    
    except Exception as e:
        raise Exception(f"Failed to download repository via API: {str(e)}")
    
    finally:
        session.close()


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


def configure_git_timeouts(
    clone_timeout: Optional[int] = None,
    fetch_timeout: Optional[int] = None, 
    api_timeout: Optional[int] = None
) -> dict:
    """
    Configure git operation timeouts dynamically
    
    Args:
        clone_timeout: Timeout for git clone operations (seconds)
        fetch_timeout: Timeout for git fetch operations (seconds)
        api_timeout: Timeout for GitHub API operations (seconds)
    
    Returns:
        Dictionary with current timeout values
    """
    global GIT_CLONE_TIMEOUT, GIT_FETCH_TIMEOUT, GITHUB_API_TIMEOUT
    
    if clone_timeout is not None:
        GIT_CLONE_TIMEOUT = max(30, min(clone_timeout, 1800))  # Between 30s and 30 minutes
        print(f"🔧 Git clone timeout set to: {GIT_CLONE_TIMEOUT} seconds")
    
    if fetch_timeout is not None:
        GIT_FETCH_TIMEOUT = max(30, min(fetch_timeout, 900))  # Between 30s and 15 minutes
        print(f"🔧 Git fetch timeout set to: {GIT_FETCH_TIMEOUT} seconds")
    
    if api_timeout is not None:
        GITHUB_API_TIMEOUT = max(30, min(api_timeout, 600))  # Between 30s and 10 minutes
        print(f"🔧 GitHub API timeout set to: {GITHUB_API_TIMEOUT} seconds")
    
    return get_git_timeout_status()

def get_git_timeout_status() -> dict:
    """
    Get current git timeout configuration
    
    Returns:
        Dictionary with current timeout values and their sources
    """
    return {
        "git_clone_timeout": {
            "value": GIT_CLONE_TIMEOUT,
            "default": 300,
            "env_var": "CODEGATES_GIT_CLONE_TIMEOUT",
            "description": "Timeout for git clone operations"
        },
        "git_fetch_timeout": {
            "value": GIT_FETCH_TIMEOUT,
            "default": 180,
            "env_var": "CODEGATES_GIT_FETCH_TIMEOUT", 
            "description": "Timeout for git fetch operations"
        },
        "github_api_timeout": {
            "value": GITHUB_API_TIMEOUT,
            "default": 120,
            "env_var": "CODEGATES_GITHUB_API_TIMEOUT",
            "description": "Timeout for GitHub API operations"
        }
    }

def set_ocp_optimized_timeouts():
    """
    Set timeouts optimized for OpenShift Container Platform environments
    These are conservative values to prevent hanging in resource-constrained environments
    """
    return configure_git_timeouts(
        clone_timeout=180,  # 3 minutes for clone
        fetch_timeout=120,  # 2 minutes for fetch
        api_timeout=90      # 1.5 minutes for API
    )

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