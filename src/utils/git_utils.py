"""
Enhanced Git utilities for repository operations
Includes enterprise support, timeout handling, and advanced error recovery
"""

import os
import shutil
import subprocess
import tempfile
import requests
import zipfile
import urllib3
import signal
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from contextlib import contextmanager

from models.scan_models import RepositoryInfo


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


class GitUtils:
    """Enhanced Git operations utility with enterprise support"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "codegates_scan"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def clone_repository(self, repo_url: str, branch: str = "main", 
                             git_token: Optional[str] = None) -> str:
        """
        Clone repository to auto-generated directory
        
        Args:
            repo_url: Repository URL
            branch: Branch to checkout
            git_token: GitHub token for private repos
        
        Returns:
            Path to cloned repository
        """
        # Create unique directory for this clone
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_dir = self.temp_dir / f"{repo_name}_{timestamp}"
        
        # Use the new clone_repository_to_path method
        return await self.clone_repository_to_path(repo_url, branch, git_token, str(clone_dir))
    
    async def clone_repository_to_path(self, repo_url: str, branch: str = "main", 
                                      git_token: Optional[str] = None, target_path: str = None) -> str:
        """
        Clone repository to a specific path
        
        Args:
            repo_url: Repository URL
            branch: Branch to checkout
            git_token: GitHub token for private repos
            target_path: Specific path where to clone the repository
        
        Returns:
            Path to cloned repository
        """
        print(f"🔧 Git timeout configuration:")
        timeout_status = self.get_git_timeout_status()
        for name, config in timeout_status.items():
            print(f"   {name}: {config['value']}s (env: {config['env_var']})")
        
        # Use provided target path
        if not target_path:
            raise ValueError("target_path is required for clone_repository_to_path")
        
        clone_dir = Path(target_path)
        
        # Ensure target directory exists and is writable
        if not os.path.exists(clone_dir):
            try:
                os.makedirs(clone_dir, exist_ok=True)
            except Exception as e:
                raise Exception(f"Failed to create target directory {clone_dir}: {e}")
        
        # Verify directory is writable
        if not os.access(clone_dir, os.W_OK):
            raise Exception(f"Target directory is not writable: {clone_dir}")
        
        # Determine if this is GitHub Enterprise
        parsed_url = urlparse(repo_url)
        hostname = parsed_url.netloc.lower()
        is_github_enterprise = 'github' in hostname and hostname != 'github.com'
        
        if is_github_enterprise:
            # For GitHub Enterprise: Use API
            print(f"🏢 GitHub Enterprise detected ({hostname}), using API")
            return await self._download_with_github_api(repo_url, branch, git_token, str(clone_dir))
        else:
            # For GitHub.com and other Git servers: Use Git clone
            print(f"🌐 Public repository detected, using Git clone")
            return await self._clone_with_git(repo_url, branch, git_token, str(clone_dir))
    
    async def _clone_with_git(self, repo_url: str, branch: str, git_token: Optional[str], target_dir: str) -> str:
        """Clone repository using Git with enterprise support and timeout"""
        
        # Parse repository URL to determine if it's enterprise
        parsed_url = urlparse(repo_url)
        hostname = parsed_url.netloc.lower()
        is_github_enterprise = 'github' in hostname and hostname != 'github.com'
        
        # Prepare URL with token if provided
        if git_token:
            if is_github_enterprise or "github.com" in repo_url:
                # Insert token into URL for GitHub authentication
                auth_url = f"https://{git_token}@{hostname}{parsed_url.path}"
            else:
                # For other Git servers, use the original URL
                auth_url = repo_url
        else:
            auth_url = repo_url
        
        print(f"🔄 Cloning repository with Git (timeout: {GIT_CLONE_TIMEOUT}s): {repo_url} (branch: {branch})")
        
        # Configure Git environment for enterprise scenarios
        env = os.environ.copy()
        
        # Clear proxy environment for git operations
        env.pop('HTTP_PROXY', None)
        env.pop('HTTPS_PROXY', None)
        env.pop('NO_PROXY', None)
        
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
    
    async def _download_with_github_api(self, repo_url: str, branch: str, git_token: Optional[str], target_dir: str) -> str:
        """Download repository using GitHub API with enterprise support"""
        
        # Parse repository URL to determine if it's enterprise
        parsed_url = urlparse(repo_url)
        hostname = parsed_url.netloc.lower()
        is_github_enterprise = 'github' in hostname and hostname != 'github.com'
        
        # Extract owner and repo name from URL
        owner, repo_name = self._parse_github_url(repo_url)
        
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
        
        if git_token:
            headers["Authorization"] = f"token {git_token}"
        
        print(f"🔄 Downloading repository with GitHub API: {repo_url} (branch: {branch})")
        
        # Configure request session with enterprise-friendly settings
        session = requests.Session()
        session.headers.update(headers)
        
        # Enterprise-specific configurations with configurable timeout
        request_kwargs = {
            "stream": True,
            "timeout": (30, GITHUB_API_TIMEOUT),  # (connect_timeout, read_timeout)
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
            
            # Special handling for known enterprise instances
            if hostname in ['github.XYXY.com']:
                print(f"🏢 Detected Wells Fargo GitHub Enterprise - using enterprise-optimized settings")
                disable_ssl = True  # Wells Fargo typically has SSL certificate issues
            
            if disable_ssl:
                request_kwargs["verify"] = False
                print("⚠️ SSL verification disabled for GitHub Enterprise")
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            elif ca_bundle and os.path.exists(ca_bundle):
                request_kwargs["verify"] = ca_bundle
                print(f"🔐 Using custom CA bundle: {ca_bundle}")
            else:
                print("🔐 Using default SSL verification")
        else:
            # For GitHub.com, also check for global SSL bypass
            disable_ssl = (
                os.getenv('CODEGATES_DISABLE_SSL', 'false').lower() == 'true' or
                os.getenv('DISABLE_SSL_VERIFICATION', 'false').lower() == 'true'
            )
            
            if disable_ssl:
                request_kwargs["verify"] = False
                print("⚠️ SSL verification disabled for GitHub.com")
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
                raise Exception(f"Connection reset by peer. This often happens with enterprise GitHub due to network/SSL issues.")
            else:
                raise Exception(f"Connection error: {str(e)}")
        
        except requests.exceptions.Timeout as e:
            raise Exception(f"Request timeout. The repository might be too large or the network is slow: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Failed to download repository via API: {str(e)}")
        
        finally:
            session.close()
    
    def _parse_github_url(self, repo_url: str) -> Tuple[str, str]:
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
    
    async def get_repository_info(self, repo_path: str) -> RepositoryInfo:
        """Extract repository information"""
        try:
            repo_path = Path(repo_path)
            
            # Get commit hash
            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                cwd=repo_path, capture_output=True, text=True
            ).stdout.strip()
            
            # Get branch
            branch = subprocess.run(
                ["git", "branch", "--show-current"], 
                cwd=repo_path, capture_output=True, text=True
            ).stdout.strip()
            
            # Get remote URL
            remote_url = subprocess.run(
                ["git", "remote", "get-url", "origin"], 
                cwd=repo_path, capture_output=True, text=True
            ).stdout.strip()
            
            # Count files and lines
            total_files = 0
            total_lines = 0
            languages = set()
            
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    total_files += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            total_lines += len(lines)
                        
                        # Detect language from extension
                        ext = file_path.suffix.lower()
                        if ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c']:
                            languages.add(ext[1:])  # Remove dot
                    except Exception:
                        continue
            
            # Find build and config files
            build_files = self._find_build_files(repo_path)
            config_files = self._find_config_files(repo_path)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(repo_path)
            
            return RepositoryInfo(
                repo_url=remote_url,
                branch=branch,
                local_path=str(repo_path),
                commit_hash=commit_hash,
                total_files=total_files,
                total_lines=total_lines,
                languages=list(languages),
                dependencies=dependencies,
                build_files=build_files,
                config_files=config_files
            )
            
        except Exception as e:
            print(f"❌ Failed to get repository info: {e}")
            raise
    
    def _get_cd_repo_url(self, repo_url: str) -> str:
        """Generate CD repository URL by adding '-cd' suffix"""
        # Handle different repository URL formats
        if repo_url.endswith('.git'):
            base_url = repo_url[:-4]  # Remove .git
            return f"{base_url}-cd.git"
        else:
            return f"{repo_url}-cd"
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
            '.pytest_cache', 'target', 'build', 'dist', 'out',
            '.idea', '.vscode', '.vs', '.DS_Store'
        ]
        
        for pattern in ignore_patterns:
            if pattern in str(file_path):
                return True
        
        # Ignore binary files
        binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                           '.mp4', '.avi', '.mov', '.mp3', '.wav',
                           '.zip', '.tar', '.gz', '.rar', '.7z',
                           '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                           '.exe', '.dll', '.so', '.dylib',
                           '.jar', '.war', '.ear', '.class'}
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        return False
    
    def _find_build_files(self, repo_path: Path) -> list:
        """Find build configuration files"""
        build_files = []
        build_patterns = [
            'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml',
            'pom.xml', 'build.gradle', 'Cargo.toml', 'go.mod',
            'Makefile', 'CMakeLists.txt', 'Dockerfile', '.dockerignore'
        ]
        
        for pattern in build_patterns:
            for file_path in repo_path.rglob(pattern):
                build_files.append(str(file_path.relative_to(repo_path)))
        
        return build_files
    
    def _find_config_files(self, repo_path: Path) -> list:
        """Find configuration files"""
        config_files = []
        config_patterns = [
            '.env', '.env.local', '.env.production', 'config.json', 'config.yaml',
            'settings.json', 'application.properties', 'application.yml',
            '.gitignore', '.eslintrc', '.prettierrc', 'tsconfig.json'
        ]
        
        for pattern in config_patterns:
            for file_path in repo_path.rglob(pattern):
                config_files.append(str(file_path.relative_to(repo_path)))
        
        return config_files
    
    def _extract_dependencies(self, repo_path: Path) -> Dict[str, list]:
        """Extract dependencies from build files"""
        dependencies = {}
        
        # Python dependencies
        requirements_file = repo_path / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    deps = [line.strip().split('==')[0] for line in f 
                           if line.strip() and not line.startswith('#')]
                dependencies['python'] = deps
            except Exception:
                pass
        
        # Node.js dependencies
        package_file = repo_path / "package.json"
        if package_file.exists():
            try:
                import json
                with open(package_file, 'r') as f:
                    data = json.load(f)
                    deps = list(data.get('dependencies', {}).keys())
                    deps.extend(data.get('devDependencies', {}).keys())
                dependencies['nodejs'] = deps
            except Exception:
                pass
        
        return dependencies
    
    def cleanup(self, repo_path: str):
        """Clean up cloned repository"""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                print(f"🧹 Cleaned up: {repo_path}")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
    
    def configure_git_timeouts(
        self,
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
        
        return self.get_git_timeout_status()
    
    def get_git_timeout_status(self) -> dict:
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
    
    def set_ocp_optimized_timeouts(self):
        """
        Set timeouts optimized for OpenShift Container Platform environments
        These are conservative values to prevent hanging in resource-constrained environments
        """
        return self.configure_git_timeouts(
            clone_timeout=180,  # 3 minutes for clone
            fetch_timeout=120,  # 2 minutes for fetch
            api_timeout=90      # 1.5 minutes for API
        )


class EnhancedGitIntegration:
    """
    Enhanced Git integration for enterprise environments
    Supports multiple Git platforms: GitHub, GitLab, Bitbucket, Azure DevOps
    """
    
    def __init__(self):
        # Define API timeouts for different platforms
        self.api_timeouts = {
            "github.com": 120,
            "github.abc.com": 180,  # Enterprise might be slower
            "github.XYXY.com": 180,  # Wells Fargo Enterprise
            "gitlab.com": 120,
            "bitbucket.org": 120,
            "dev.azure.com": 120
        }
    
    def search_repositories(self, keywords: list, git_endpoint: str = "github.com", limit: int = 20, github_token: Optional[str] = None) -> list:
        """Search repositories across different Git platforms with enhanced private repository support and prioritization"""
        if git_endpoint == "github.com":
            # Strategy: First get user's private repositories, then fill with search results
            repositories = []
            
            # Step 1: Get user's accessible repositories first (prioritizes private repos)
            if github_token:
                print(f"🔒 Step 1: Searching user's accessible private repositories...")
                private_repos = self._search_user_accessible_repositories(keywords, limit, github_token, prioritize_private=True)
                repositories.extend(private_repos)
                print(f"✅ Found {len(private_repos)} private/accessible repositories")
            
            # Step 2: Fill remaining slots with public search results
            remaining_limit = limit - len(repositories)
            if remaining_limit > 0:
                print(f"🔍 Step 2: Searching public repositories to fill remaining {remaining_limit} slots...")
                public_repos = self._search_github_repositories(keywords, remaining_limit, github_token)
                
                # Deduplicate and add public repos
                existing_full_names = {f"{repo['owner']}/{repo['name']}" for repo in repositories}
                for repo in public_repos:
                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                    if repo_full_name not in existing_full_names:
                        repositories.append(repo)
                        if len(repositories) >= limit:
                            break
            
            # Sort results: private first, then by updated date
            self._sort_repositories_by_priority(repositories)
            return repositories[:limit]
            
        elif git_endpoint in ["github.abc.com", "github.XYXY.com"]:
            # Strategy: Similar approach for enterprise GitHub
            repositories = []
            
            # Step 1: Get user's accessible enterprise repositories first
            if github_token:
                print(f"🔒 Step 1: Searching user's accessible enterprise repositories on {git_endpoint}...")
                private_repos = self._search_enterprise_user_accessible_repositories(keywords, limit, git_endpoint, github_token, prioritize_private=True)
                repositories.extend(private_repos)
                print(f"✅ Found {len(private_repos)} private/accessible repositories")
            
            # Step 2: Fill remaining slots with enterprise search results
            remaining_limit = limit - len(repositories)
            if remaining_limit > 0:
                print(f"🔍 Step 2: Searching {git_endpoint} to fill remaining {remaining_limit} slots...")
                enterprise_repos = self._search_github_enterprise_repositories(keywords, remaining_limit, git_endpoint, github_token)
                
                # Deduplicate and add enterprise repos
                existing_full_names = {f"{repo['owner']}/{repo['name']}" for repo in repositories}
                for repo in enterprise_repos:
                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                    if repo_full_name not in existing_full_names:
                        repositories.append(repo)
                        if len(repositories) >= limit:
                            break
            
            # Sort results: private first, then by updated date
            self._sort_repositories_by_priority(repositories)
            return repositories[:limit]
            
        elif git_endpoint == "gitlab.com":
            return self._search_gitlab_repositories(keywords, limit)
        elif git_endpoint == "bitbucket.org":
            return self._search_bitbucket_repositories(keywords, limit)
        elif git_endpoint == "dev.azure.com":
            return self._search_azure_repositories(keywords, limit)
        else:
            raise ValueError(f"Unsupported Git endpoint: {git_endpoint}")
    
    def list_branches(self, owner: str, name: str, git_endpoint: str = "github.com", github_token: Optional[str] = None) -> list:
        """List repository branches across different Git platforms"""
        if git_endpoint == "github.com":
            return self._list_github_branches(owner, name, github_token)
        elif git_endpoint in ["github.abc.com", "github.XYXY.com"]:
            return self._list_github_enterprise_branches(owner, name, git_endpoint, github_token)
        elif git_endpoint == "gitlab.com":
            return self._list_gitlab_branches(owner, name)
        elif git_endpoint == "bitbucket.org":
            return self._list_bitbucket_branches(owner, name)
        elif git_endpoint == "dev.azure.com":
            return self._list_azure_branches(owner, name)
        else:
            raise ValueError(f"Unsupported Git endpoint: {git_endpoint}")
    
    def _sort_repositories_by_priority(self, repositories: list) -> list:
        """Sort repositories by private status first, then by updated date"""
        def sort_key(repo):
            # Private repos come first (False < True, so we negate)
            is_private = repo.get('private', False)
            
            # Handle updated_at date - provide fallback for missing or invalid dates
            updated_at = repo.get('updated_at', '')
            if not updated_at:
                updated_at = '1970-01-01T00:00:00Z'  # Very old date as fallback
            
            # Return tuple: (private_priority, updated_date)
            # We want private repos first, so we use 'not is_private'
            # We want recent dates first, so we'll reverse the sort
            return (not is_private, updated_at)
        
        # Sort with reverse=True to get recent dates first
        repositories.sort(key=sort_key, reverse=True)
        return repositories
    
    def _search_github_repositories(self, keywords: list, limit: int, github_token: Optional[str] = None) -> list:
        """Search GitHub repositories including private ones the token has access to"""
        try:
            # Build search query - include both public and private repositories
            base_query = " ".join(keywords)
            
            # When token is provided, modify query to include private repositories user has access to
            if github_token:
                # GitHub Search API: include private repositories user has access to
                # Use 'in:name,description,readme' to search in multiple fields
                # Don't restrict by visibility to include both public and private
                query = f"{base_query} in:name,description,readme"
                print(f"🔍 Searching GitHub with token - including private repositories accessible to token")
            else:
                # Without token, only public repositories
                query = f"{base_query} is:public in:name,description,readme"
                print(f"🔍 Searching GitHub without token - public repositories only")
            
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": "updated",  # Changed from "stars" to "updated" for better private repo results
                "order": "desc",
                "per_page": min(limit, 100)
            }
            
            headers = {"Accept": "application/vnd.github.v3+json"}
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            print(f"🔍 GitHub search query: '{query}'")
            
            # Use requests timeout instead of signal-based timeout
            response = requests.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=self.api_timeouts["github.com"]
            )
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            public_count = 0
            private_count = 0
            
            for repo in data.get("items", []):
                is_private = repo.get("private", False)
                if is_private:
                    private_count += 1
                else:
                    public_count += 1
                    
                repositories.append({
                    "name": repo["name"],
                    "owner": repo["owner"]["login"],
                    "description": repo.get("description", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language", ""),
                    "html_url": repo["html_url"],
                    "clone_url": repo["clone_url"],
                    "git_endpoint": "github.com",
                    "private": is_private,
                    "updated_at": repo.get("updated_at", "")
                })
            
            print(f"✅ Found {len(repositories)} repositories: {public_count} public, {private_count} private")
            return repositories
            
        except Exception as e:
            print(f"Error searching GitHub repositories: {e}")
            return []

    def _search_user_accessible_repositories(self, keywords: list, limit: int, github_token: str, prioritize_private: bool = False) -> list:
        """Search through user's accessible repositories (public and private) for keyword matches"""
        try:
            print(f"🔍 Searching user's accessible repositories for keyword matches...")
            
            repositories = []
            
            # Search through different types of user repositories with expanded coverage
            affiliations = ['owner', 'collaborator', 'organization_member']
            repo_types = ['all']  # Include all types: public, private, forks
            
            for affiliation in affiliations:
                if len(repositories) >= limit:
                    break
                    
                for repo_type in repo_types:
                    if len(repositories) >= limit:
                        break
                        
                    # Use pagination to get more repositories
                    for page in range(1, 4):  # Check up to 3 pages (300 repos max)
                        if len(repositories) >= limit:
                            break
                            
                        url = "https://api.github.com/user/repos"
                        params = {
                            "affiliation": affiliation,
                            "type": repo_type,
                            "sort": "updated", 
                            "direction": "desc",
                            "per_page": 100,  # Maximum per page
                            "page": page
                        }
                        
                        headers = {
                            "Accept": "application/vnd.github.v3+json",
                            "Authorization": f"token {github_token}"
                        }
                        
                        response = requests.get(
                            url,
                            params=params,
                            headers=headers,
                            timeout=self.api_timeouts["github.com"]
                        )
                        
                        if response.status_code == 200:
                            repos_data = response.json()
                            
                            # If no repos returned, break pagination
                            if not repos_data:
                                break
                            
                            # Process repositories
                            matched_repos = []
                            for repo in repos_data:
                                if self._repo_matches_keywords(repo, keywords):
                                    repo_data = {
                                        "name": repo["name"],
                                        "owner": repo["owner"]["login"],
                                        "description": repo.get("description", ""),
                                        "stars": repo.get("stargazers_count", 0),
                                        "forks": repo.get("forks_count", 0),
                                        "language": repo.get("language", ""),
                                        "html_url": repo["html_url"],
                                        "clone_url": repo["clone_url"],
                                        "git_endpoint": "github.com",
                                        "private": repo.get("private", False),
                                        "updated_at": repo.get("updated_at", ""),
                                        "pushed_at": repo.get("pushed_at", "")
                                    }
                                    matched_repos.append(repo_data)
                            
                            # If prioritizing private, separate and sort
                            if prioritize_private:
                                private_repos = [r for r in matched_repos if r.get('private', False)]
                                public_repos = [r for r in matched_repos if not r.get('private', False)]
                                
                                # Add private repos first
                                for repo in private_repos:
                                    if len(repositories) >= limit:
                                        break
                                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                                    existing_full_names = {f"{r['owner']}/{r['name']}" for r in repositories}
                                    if repo_full_name not in existing_full_names:
                                        repositories.append(repo)
                                
                                # Then add public repos
                                for repo in public_repos:
                                    if len(repositories) >= limit:
                                        break
                                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                                    existing_full_names = {f"{r['owner']}/{r['name']}" for r in repositories}
                                    if repo_full_name not in existing_full_names:
                                        repositories.append(repo)
                            else:
                                # Add all matched repos
                                for repo in matched_repos:
                                    if len(repositories) >= limit:
                                        break
                                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                                    existing_full_names = {f"{r['owner']}/{r['name']}" for r in repositories}
                                    if repo_full_name not in existing_full_names:
                                        repositories.append(repo)
                        
                        else:
                            break  # Stop pagination on error
            
            # Final sort if prioritizing private
            if prioritize_private:
                self._sort_repositories_by_priority(repositories)
            
            private_count = len([r for r in repositories if r.get('private', False)])
            public_count = len([r for r in repositories if not r.get('private', False)])
            
            print(f"✅ Found {len(repositories)} total repositories ({private_count} private, {public_count} public)")
            return repositories
            
        except Exception as e:
            print(f"Error searching user accessible repositories: {e}")
            return []

    def _repo_matches_keywords(self, repo: dict, keywords: list) -> bool:
        """Check if a repository matches the given keywords"""
        try:
            # Create searchable text from repo metadata
            searchable_text = " ".join([
                repo.get("name", ""),
                repo.get("description", ""),
                repo.get("language", ""),
                " ".join(repo.get("topics", [])) if repo.get("topics") else ""
            ]).lower()
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword.lower() in searchable_text:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _search_enterprise_user_accessible_repositories(self, keywords: list, limit: int, git_endpoint: str, github_token: str, prioritize_private: bool = False) -> list:
        """Search through user's accessible enterprise repositories for keyword matches"""
        try:
            print(f"🔍 Searching user's accessible repositories on {git_endpoint} for keyword matches...")
            
            repositories = []
            
            # Search through different types of user repositories with expanded coverage
            affiliations = ['owner', 'collaborator', 'organization_member']
            repo_types = ['all']  # Include all types: public, private, forks
            
            for affiliation in affiliations:
                if len(repositories) >= limit:
                    break
                    
                for repo_type in repo_types:
                    if len(repositories) >= limit:
                        break
                        
                    # Use pagination to get more repositories
                    for page in range(1, 4):  # Check up to 3 pages (300 repos max)
                        if len(repositories) >= limit:
                            break
                            
                        api_url = f"https://{git_endpoint}/api/v3/user/repos"
                        params = {
                            "affiliation": affiliation,
                            "type": repo_type,
                            "sort": "updated", 
                            "direction": "desc",
                            "per_page": 100,  # Maximum per page
                            "page": page
                        }
                        
                        headers = {
                            "Accept": "application/vnd.github.v3+json",
                            "Authorization": f"token {github_token}"
                        }
                        
                        # Enterprise-specific SSL handling
                        verify_ssl = os.getenv('GITHUB_ENTERPRISE_DISABLE_SSL', 'true').lower() != 'true'
                        if git_endpoint == 'github.XYXY.com':
                            verify_ssl = False
                        
                        response = requests.get(
                            api_url,
                            params=params,
                            headers=headers,
                            timeout=self.api_timeouts.get(git_endpoint, 180),
                            verify=verify_ssl
                        )
                        
                        if response.status_code == 200:
                            repos_data = response.json()
                            
                            # If no repos returned, break pagination
                            if not repos_data:
                                break
                            
                            # Process repositories
                            matched_repos = []
                            for repo in repos_data:
                                if self._repo_matches_keywords(repo, keywords):
                                    repo_data = {
                                        "name": repo["name"],
                                        "owner": repo["owner"]["login"],
                                        "description": repo.get("description", ""),
                                        "stars": repo.get("stargazers_count", 0),
                                        "forks": repo.get("forks_count", 0),
                                        "language": repo.get("language", ""),
                                        "html_url": repo["html_url"],
                                        "clone_url": repo["clone_url"],
                                        "git_endpoint": git_endpoint,
                                        "private": repo.get("private", False),
                                        "updated_at": repo.get("updated_at", ""),
                                        "pushed_at": repo.get("pushed_at", "")
                                    }
                                    matched_repos.append(repo_data)
                            
                            # If prioritizing private, separate and sort
                            if prioritize_private:
                                private_repos = [r for r in matched_repos if r.get('private', False)]
                                public_repos = [r for r in matched_repos if not r.get('private', False)]
                                
                                # Add private repos first
                                for repo in private_repos:
                                    if len(repositories) >= limit:
                                        break
                                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                                    existing_full_names = {f"{r['owner']}/{r['name']}" for r in repositories}
                                    if repo_full_name not in existing_full_names:
                                        repositories.append(repo)
                                
                                # Then add public repos
                                for repo in public_repos:
                                    if len(repositories) >= limit:
                                        break
                                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                                    existing_full_names = {f"{r['owner']}/{r['name']}" for r in repositories}
                                    if repo_full_name not in existing_full_names:
                                        repositories.append(repo)
                            else:
                                # Add all matched repos
                                for repo in matched_repos:
                                    if len(repositories) >= limit:
                                        break
                                    repo_full_name = f"{repo['owner']}/{repo['name']}"
                                    existing_full_names = {f"{r['owner']}/{r['name']}" for r in repositories}
                                    if repo_full_name not in existing_full_names:
                                        repositories.append(repo)
                        
                        else:
                            break  # Stop pagination on error
            
            # Final sort if prioritizing private
            if prioritize_private:
                self._sort_repositories_by_priority(repositories)
            
            private_count = len([r for r in repositories if r.get('private', False)])
            public_count = len([r for r in repositories if not r.get('private', False)])
            
            print(f"✅ Found {len(repositories)} total repositories on {git_endpoint} ({private_count} private, {public_count} public)")
            return repositories
            
        except Exception as e:
            print(f"Error searching enterprise user accessible repositories: {e}")
            return []

    def _search_github_enterprise_repositories(self, keywords: list, limit: int, git_endpoint: str, github_token: Optional[str] = None) -> list:
        """Search GitHub Enterprise repositories including private ones the token has access to"""
        try:
            # Build search query - include both public and private repositories
            base_query = " ".join(keywords)
            
            # Try multiple token sources for GitHub Enterprise
            token = (
                github_token or 
                os.getenv("GITHUB_TOKEN") or 
                os.getenv("GITHUB_ENTERPRISE_TOKEN") or
                os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or
                os.getenv("GH_TOKEN")
            )
            
            # Build query based on token availability
            if token:
                # With token: include private repositories user has access to
                # Use 'in:name,description,readme' to search in multiple fields
                # Don't restrict by visibility to include both public and private
                query = f"{base_query} in:name,description,readme"
                print(f"🔍 Searching {git_endpoint} with token - including private repositories accessible to token")
            else:
                # Without token: only public repositories
                query = f"{base_query} is:public in:name,description,readme"
                print(f"🔍 Searching {git_endpoint} without token - public repositories only")
            
            # Use the full git_endpoint for API URL construction
            api_url = f"https://{git_endpoint}/api/v3/search/repositories"
            params = {
                "q": query,
                "sort": "updated",  # Changed from "stars" to "updated" for better private repo results
                "order": "desc",
                "per_page": min(limit, 100)
            }
            
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            if token:
                headers["Authorization"] = f"token {token}"
                print(f"🔑 Using GitHub token for {git_endpoint} authentication")
            else:
                print(f"⚠️ No GitHub token found - may have limited access to {git_endpoint}")
                print("   Set via: GITHUB_TOKEN, GITHUB_ENTERPRISE_TOKEN, or GH_TOKEN environment variable")
            
            # Enterprise-specific SSL and timeout handling
            verify_ssl = os.getenv('GITHUB_ENTERPRISE_DISABLE_SSL', 'true').lower() != 'true'
            if git_endpoint == 'github.XYXY.com':
                verify_ssl = False  # Wells Fargo specific
            
            print(f"🔍 Enterprise search query: '{query}' (SSL verify: {verify_ssl})")
            
            response = requests.get(
                api_url, 
                params=params, 
                headers=headers, 
                timeout=self.api_timeouts.get(git_endpoint, 180),
                verify=verify_ssl
            )
            
            if not verify_ssl:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            public_count = 0
            private_count = 0
            
            for repo in data.get("items", []):
                is_private = repo.get("private", False)
                if is_private:
                    private_count += 1
                else:
                    public_count += 1
                    
                repositories.append({
                    "name": repo["name"],
                    "owner": repo["owner"]["login"],
                    "description": repo.get("description", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language", ""),
                    "html_url": repo["html_url"],
                    "clone_url": repo["clone_url"],
                    "git_endpoint": git_endpoint,
                    "private": is_private,
                    "updated_at": repo.get("updated_at", "")
                })
            
            print(f"✅ Found {len(repositories)} repositories on {git_endpoint}: {public_count} public, {private_count} private")
            return repositories
            
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error for {git_endpoint}: {e}")
            print(f"💡 Try setting: export GITHUB_ENTERPRISE_DISABLE_SSL=true")
            return []
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection Error for {git_endpoint}: {e}")
            print(f"💡 Check VPN connection and enterprise network access")
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"🔑 Authentication failed for {git_endpoint}")
                print(f"💡 Check your GitHub Enterprise token permissions")
            elif e.response.status_code == 403:
                print(f"🚫 Access forbidden for {git_endpoint}")
                print(f"💡 Token may lack repository search permissions")
            else:
                print(f"🚨 HTTP Error {e.response.status_code} for {git_endpoint}: {e}")
            return []
        except Exception as e:
            print(f"❌ Error searching GitHub Enterprise repositories on {git_endpoint}: {e}")
            return []
    
    def _search_gitlab_repositories(self, keywords: list, limit: int) -> list:
        """Search GitLab repositories"""
        try:
            query = " ".join(keywords)
            url = f"https://gitlab.com/api/v4/projects"
            params = {
                "search": query,
                "order_by": "star_count",
                "sort": "desc",
                "per_page": min(limit, 100),
                "visibility": "public"
            }
            
            headers = {"Accept": "application/json"}
            token = os.getenv("GITLAB_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = requests.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=self.api_timeouts["gitlab.com"]
            )
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            for repo in data:
                repositories.append({
                    "name": repo["name"],
                    "owner": repo["namespace"]["name"],
                    "description": repo.get("description", ""),
                    "stars": repo.get("star_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": "",  # GitLab API doesn't return primary language in search
                    "html_url": repo["web_url"],
                    "clone_url": repo["http_url_to_repo"],
                    "git_endpoint": "gitlab.com",
                    "private": repo.get("visibility", "public") != "public"
                })
            
            return repositories
            
        except Exception as e:
            print(f"Error searching GitLab repositories: {e}")
            return []
    
    def _search_bitbucket_repositories(self, keywords: list, limit: int) -> list:
        """Search Bitbucket repositories"""
        try:
            query = " ".join(keywords)
            url = f"https://api.bitbucket.org/2.0/repositories"
            params = {
                "q": f'name ~ "{query}"',
                "sort": "-updated_on",
                "pagelen": min(limit, 100)
            }
            
            headers = {"Accept": "application/json"}
            
            response = requests.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=self.api_timeouts["bitbucket.org"]
            )
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            for repo in data.get("values", []):
                repositories.append({
                    "name": repo["name"],
                    "owner": repo["owner"]["display_name"],
                    "description": repo.get("description", ""),
                    "stars": 0,  # Bitbucket doesn't have stars
                    "forks": 0,  # Would need separate API call
                    "language": repo.get("language", ""),
                    "html_url": repo["links"]["html"]["href"],
                    "clone_url": repo["links"]["clone"][0]["href"],
                    "git_endpoint": "bitbucket.org",
                    "private": repo.get("is_private", False)
                })
            
            return repositories
            
        except Exception as e:
            print(f"Error searching Bitbucket repositories: {e}")
            return []
    
    def _search_azure_repositories(self, keywords: list, limit: int) -> list:
        """Search Azure DevOps repositories (placeholder - requires organization context)"""
        # Azure DevOps requires organization context, so this is a basic implementation
        print("Azure DevOps search requires organization-specific configuration")
        return []
    
    def _list_github_branches(self, owner: str, name: str, github_token: Optional[str] = None) -> list:
        """List GitHub repository branches"""
        try:
            url = f"https://api.github.com/repos/{owner}/{name}/branches"
            
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            # Use provided token or fall back to environment
            token = github_token or os.getenv("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.api_timeouts["github.com"]
            )
            response.raise_for_status()
            
            data = response.json()
            branches = []
            
            # Get default branch info
            repo_url = f"https://api.github.com/repos/{owner}/{name}"
            repo_response = requests.get(repo_url, headers=headers, timeout=30)
            default_branch = None
            if repo_response.status_code == 200:
                default_branch = repo_response.json().get("default_branch")
            
            for branch in data:
                branches.append({
                    "name": branch["name"],
                    "commit_sha": branch["commit"]["sha"],
                    "is_default": branch["name"] == default_branch,
                    "protected": branch.get("protected", False)
                })
            
            return branches
            
        except Exception as e:
            print(f"Error listing GitHub branches: {e}")
            return []
    
    def _list_github_enterprise_branches(self, owner: str, name: str, git_endpoint: str, github_token: Optional[str] = None) -> list:
        """List GitHub Enterprise repository branches"""
        try:
            # Use the full git_endpoint for API URL construction
            url = f"https://{git_endpoint}/api/v3/repos/{owner}/{name}/branches"
            
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            # Try multiple token sources for GitHub Enterprise
            token = (
                github_token or 
                os.getenv("GITHUB_TOKEN") or 
                os.getenv("GITHUB_ENTERPRISE_TOKEN") or
                os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or
                os.getenv("GH_TOKEN")
            )
            
            if token:
                headers["Authorization"] = f"token {token}"
                print(f"🔑 Using GitHub token for {git_endpoint} branch listing")
            else:
                print(f"⚠️ No GitHub token found - may have limited access to {git_endpoint}")
            
            # Enterprise-specific SSL and timeout handling
            verify_ssl = os.getenv('GITHUB_ENTERPRISE_DISABLE_SSL', 'true').lower() != 'true'
            if git_endpoint == 'github.XYXY.com':
                verify_ssl = False  # Wells Fargo specific
            
            print(f"📋 Listing branches for {owner}/{name} on {git_endpoint} (SSL verify: {verify_ssl})")
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.api_timeouts.get(git_endpoint, 180),
                verify=verify_ssl
            )
            
            if not verify_ssl:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response.raise_for_status()
            
            data = response.json()
            branches = []
            
            # Get default branch info
            repo_url = f"https://{git_endpoint}/api/v3/repos/{owner}/{name}"
            repo_response = requests.get(
                repo_url, 
                headers=headers, 
                timeout=30,
                verify=verify_ssl
            )
            default_branch = None
            if repo_response.status_code == 200:
                default_branch = repo_response.json().get("default_branch")
            
            for branch in data:
                branches.append({
                    "name": branch["name"],
                    "commit_sha": branch["commit"]["sha"],
                    "is_default": branch["name"] == default_branch,
                    "protected": branch.get("protected", False)
                })
            
            print(f"✅ Found {len(branches)} branches for {owner}/{name}")
            return branches
            
        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error listing branches for {git_endpoint}: {e}")
            print(f"💡 Try setting: export GITHUB_ENTERPRISE_DISABLE_SSL=true")
            return []
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection Error listing branches for {git_endpoint}: {e}")
            print(f"💡 Check VPN connection and enterprise network access")
            return []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"🔑 Authentication failed for {git_endpoint}")
                print(f"💡 Check your GitHub Enterprise token permissions")
            elif e.response.status_code == 403:
                print(f"🚫 Access forbidden for {git_endpoint}")
                print(f"💡 Token may lack repository access permissions")
            elif e.response.status_code == 404:
                print(f"🔍 Repository {owner}/{name} not found on {git_endpoint}")
                print(f"💡 Check repository name and permissions")
            else:
                print(f"🚨 HTTP Error {e.response.status_code} for {git_endpoint}: {e}")
            return []
        except Exception as e:
            print(f"❌ Error listing GitHub Enterprise branches on {git_endpoint}: {e}")
            return []
    
    def _list_gitlab_branches(self, owner: str, name: str) -> list:
        """List GitLab repository branches"""
        try:
            # GitLab uses project ID or URL encoding
            project_id = f"{owner}%2F{name}"
            url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/branches"
            
            headers = {"Accept": "application/json"}
            token = os.getenv("GITLAB_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.api_timeouts["gitlab.com"]
            )
            response.raise_for_status()
            
            data = response.json()
            branches = []
            
            for branch in data:
                branches.append({
                    "name": branch["name"],
                    "commit_sha": branch["commit"]["id"],
                    "is_default": branch.get("default", False),
                    "protected": branch.get("protected", False)
                })
            
            return branches
            
        except Exception as e:
            print(f"Error listing GitLab branches: {e}")
            return []
    
    def _list_bitbucket_branches(self, owner: str, name: str) -> list:
        """List Bitbucket repository branches"""
        try:
            url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{name}/refs/branches"
            
            headers = {"Accept": "application/json"}
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.api_timeouts["bitbucket.org"]
            )
            response.raise_for_status()
            
            data = response.json()
            branches = []
            
            for branch in data.get("values", []):
                branches.append({
                    "name": branch["name"],
                    "commit_sha": branch["target"]["hash"],
                    "is_default": branch["name"] == "main" or branch["name"] == "master",  # Heuristic
                    "protected": False  # Bitbucket doesn't easily expose this
                })
            
            return branches
            
        except Exception as e:
            print(f"Error listing Bitbucket branches: {e}")
            return []
    
    def _list_azure_branches(self, owner: str, name: str) -> list:
        """List Azure DevOps repository branches (placeholder)"""
        print("Azure DevOps branch listing requires organization-specific configuration")
        return []
