from fastapi import FastAPI, HTTPException, Body, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Set
import uvicorn
import json
import os
import re
import tempfile
import shutil
import subprocess
import asyncio
from urllib.parse import urlparse
import requests
from pathlib import Path
from datetime import datetime
import uuid
import zipfile
import io
import contextlib
import atexit
import signal
import weakref
import time
import ssl
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import hashlib

# Load environment variables first
import sys
import os
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from codegates.utils.env_loader import EnvironmentLoader
    # Force reload environment to ensure .env files are loaded
    EnvironmentLoader.load_environment(force_reload=True)
    print("✅ Environment loaded via EnvironmentLoader")
except ImportError:
    print("⚠️ EnvironmentLoader not available, using basic environment loading")
    # Fallback to basic dotenv loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
        load_dotenv('.env')
        load_dotenv('config.env')
        print("✅ Environment loaded via dotenv")
    except ImportError:
        print("⚠️ python-dotenv not available, using system environment only")

# Try to import JIRA integration
try:
    from codegates.integrations.jira_integration import JiraIntegration
    JIRA_AVAILABLE = True
    print("✅ JIRA integration available")
except ImportError:
    JIRA_AVAILABLE = False
    print("⚠️ JIRA integration not available")

# Load configuration using ConfigLoader
try:
    from codegates.utils.config_loader import get_config
    config = get_config()
    
    # Get all configuration sections
    api_config = config.get_api_config()
    cors_config = config.get_cors_config()
    reports_config = config.get_reports_config()
    timeout_config = config.get_timeout_config()
    
    # Extract values
    API_HOST = api_config['host']
    API_PORT = api_config['port']
    API_BASE_URL = api_config['base_url'] or f"http://localhost:{API_PORT}"
    
    # DEBUG: Ensure API_BASE_URL has correct format
    if API_BASE_URL and not ':' in API_BASE_URL.replace('://', '').split('/')[0]:
        # If API_BASE_URL doesn't have a port, add the default port
        if API_BASE_URL.endswith('/'):
            API_BASE_URL = API_BASE_URL.rstrip('/')
        API_BASE_URL = f"{API_BASE_URL}:{API_PORT}"
        print(f"🔧 Fixed API_BASE_URL to include port: {API_BASE_URL}")
    
    API_VERSION_PREFIX = api_config['version_prefix']
    API_TITLE = api_config['title']
    API_DESCRIPTION = api_config['description']
    DOCS_ENABLED = api_config['docs_enabled']
    DOCS_URL = api_config['docs_url'] if DOCS_ENABLED else None
    REDOC_URL = api_config['redoc_url'] if DOCS_ENABLED else None
    
    # CORS settings
    CORS_ORIGINS = cors_config['origins']
    CORS_METHODS = cors_config['methods']
    CORS_HEADERS = cors_config['headers']
    CORS_EXPOSE_HEADERS = cors_config['expose_headers']
    
    # Reports settings
    REPORTS_DIR = reports_config['reports_dir']
    REPORTS_URL_BASE = reports_config['report_url_base']
    HTML_REPORTS_ENABLED = reports_config['html_reports_enabled']
    
    # Timeout settings
    TIMEOUT_CONFIG = timeout_config
    
    print(f"✅ Configuration loaded successfully")
    print(f"   API: {API_BASE_URL}")
    print(f"   Host: {API_HOST}:{API_PORT}")
    print(f"   Reports Dir: {REPORTS_DIR}")
    print(f"   Timeouts: Git={timeout_config['git_clone_timeout']}s, Analysis={timeout_config['analysis_timeout']}s")
    
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        print("⚠️ Configuration issues found:")
        for issue in config_issues:
            print(f"   - {issue}")
    
except ImportError:
    print("⚠️ ConfigLoader not available, using fallback configuration")
    # Fallback to original hardcoded configuration
    API_HOST = os.getenv('CODEGATES_API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('CODEGATES_API_PORT', '8000'))
    API_BASE_URL = os.getenv('CODEGATES_API_BASE_URL', f'http://localhost:{API_PORT}')
    
    # DEBUG: Ensure API_BASE_URL has correct format (fallback section)
    if API_BASE_URL and not ':' in API_BASE_URL.replace('://', ''):
        # If API_BASE_URL doesn't have a port, add the default port
        if API_BASE_URL.endswith('/'):
            API_BASE_URL = API_BASE_URL.rstrip('/')
        API_BASE_URL = f"{API_BASE_URL}:{API_PORT}"
        print(f"🔧 Fixed fallback API_BASE_URL to include port: {API_BASE_URL}")
    
    API_VERSION_PREFIX = os.getenv('CODEGATES_API_VERSION_PREFIX', '/api/v1')
    API_TITLE = os.getenv('CODEGATES_API_TITLE', 'MyGates API')
    API_DESCRIPTION = os.getenv('CODEGATES_API_DESCRIPTION', 'API for validating code quality gates across different programming languages')
    DOCS_ENABLED = os.getenv('CODEGATES_API_DOCS_ENABLED', 'true').lower() == 'true'
    DOCS_URL = os.getenv('CODEGATES_API_DOCS_URL', '/docs') if DOCS_ENABLED else None
    REDOC_URL = os.getenv('CODEGATES_API_REDOC_URL', '/redoc') if DOCS_ENABLED else None
    
    # CORS Configuration from environment
    CORS_ORIGINS_STR = os.getenv('CODEGATES_CORS_ORIGINS', 'vscode-webview://*,http://localhost:*,http://127.0.0.1:*,https://localhost:*,https://127.0.0.1:*')
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(',')]
    CORS_METHODS_STR = os.getenv('CODEGATES_CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS,PATCH')
    CORS_METHODS = [method.strip() for method in CORS_METHODS_STR.split(',')]
    CORS_HEADERS_STR = os.getenv('CODEGATES_CORS_HEADERS', 'Accept,Accept-Language,Content-Language,Content-Type,Authorization,X-Requested-With,User-Agent,Origin,Access-Control-Request-Method,Access-Control-Request-Headers')
    CORS_HEADERS = [header.strip() for header in CORS_HEADERS_STR.split(',')]
    CORS_EXPOSE_HEADERS_STR = os.getenv('CODEGATES_CORS_EXPOSE_HEADERS', 'Content-Type,Content-Length,Date,Server')
    CORS_EXPOSE_HEADERS = [header.strip() for header in CORS_EXPOSE_HEADERS_STR.split(',')]
    
    # Reports Configuration from environment (fallback)
    REPORTS_DIR = os.getenv('CODEGATES_REPORTS_DIR', 'reports')
    REPORTS_URL_BASE = os.getenv('CODEGATES_REPORT_URL_BASE', f'{API_BASE_URL}{API_VERSION_PREFIX}/reports')
    HTML_REPORTS_ENABLED = os.getenv('CODEGATES_HTML_REPORTS_ENABLED', 'true').lower() == 'true'
    
    # Timeout Configuration from environment (fallback)
    TIMEOUT_CONFIG = {
        'git_clone_timeout': int(os.getenv('CODEGATES_GIT_CLONE_TIMEOUT', '3000')),
        'git_ls_remote_timeout': int(os.getenv('CODEGATES_GIT_LS_REMOTE_TIMEOUT', '300')),
        'api_download_timeout': int(os.getenv('CODEGATES_API_DOWNLOAD_TIMEOUT', '1200')),
        'analysis_timeout': int(os.getenv('CODEGATES_ANALYSIS_TIMEOUT', '1800')),
        'llm_request_timeout': int(os.getenv('CODEGATES_LLM_REQUEST_TIMEOUT', '300')),
        'http_request_timeout': int(os.getenv('CODEGATES_HTTP_REQUEST_TIMEOUT', '100')),
        'health_check_timeout': int(os.getenv('CODEGATES_HEALTH_CHECK_TIMEOUT', '5')),
        'jira_request_timeout': int(os.getenv('CODEGATES_JIRA_REQUEST_TIMEOUT', '300')),
        'jira_health_timeout': int(os.getenv('CODEGATES_JIRA_HEALTH_TIMEOUT', '100')),
        'github_connect_timeout': int(os.getenv('CODEGATES_GITHUB_CONNECT_TIMEOUT', '300')),
        'github_read_timeout': int(os.getenv('CODEGATES_GITHUB_READ_TIMEOUT', '1200')),
        'vscode_api_timeout': int(os.getenv('CODEGATES_VSCODE_API_TIMEOUT', '3000')),
        'llm_batch_timeout': int(os.getenv('CODEGATES_LLM_BATCH_TIMEOUT', '300')),
    }

# Add intake imports after existing imports, before the main app configuration
try:
    # Import intake assessment functionality
    import sys
    import os
    from pathlib import Path
    
    # Add intake module to path
    intake_path = Path(__file__).parent.parent.parent / "intake"
    if intake_path.exists():
        sys.path.insert(0, str(intake_path))
        
        # Import intake components with error handling
        try:
            from flow import create_analysis_flow, create_excel_analysis_flow
            from nodes import OcpAssessmentNode, AnalyzeCode, FetchRepo, ProcessExcel, FetchJiraStories, GenerateReport
            
            INTAKE_AVAILABLE = True
            print("✅ Intake assessment module available")
        except ImportError as import_error:
            INTAKE_AVAILABLE = False
            print(f"⚠️ Intake components not available: {import_error}")
    else:
        INTAKE_AVAILABLE = False
        print("⚠️ Intake module directory not found")
        
except Exception as e:
    INTAKE_AVAILABLE = False
    print(f"⚠️ Intake assessment initialization failed: {e}")

# Create the main FastAPI app with lifecycle management
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Handle application startup"""
    print("🚀 MyGates API starting up...")
    
    # Clean up any orphaned directories from previous runs
    print("🧹 Cleaning up orphaned directories from previous runs...")
    cleanup_orphaned_temp_directories()
    
    print("✅ MyGates API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown"""
    print("🛑 MyGates API shutting down...")
    
    # Clean up all registered temporary directories
    print("🧹 Cleaning up all temporary directories...")
    try:
        await cleanup_all_temp_directories()
        print("✅ Temporary directory cleanup completed")
    except Exception as e:
        print(f"⚠️ Error during shutdown cleanup: {e}")
    
    print("✅ MyGates API shutdown complete")

# Configure CORS for the main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
    expose_headers=CORS_EXPOSE_HEADERS
)

# Create a sub-application for /api/v1 routes
api_v1 = FastAPI(
    title="MyGates API v1",
    description="API v1 routes for MyGates",
)

# Configure CORS for the v1 sub-application
api_v1.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
    expose_headers=CORS_EXPOSE_HEADERS
)

# In-memory storage for scan results (in production, use a database)
scan_results = {}

# Global registry for tracking temporary directories
_TEMP_DIRECTORIES: Set[str] = set()
_TEMP_DIR_LOCK = asyncio.Lock()

def register_temp_directory(path: str):
    """Register a temporary directory for cleanup"""
    if path and os.path.exists(path):
        _TEMP_DIRECTORIES.add(path)
        print(f"📝 Registered temp directory for cleanup: {path}")

def unregister_temp_directory(path: str):
    """Unregister a temporary directory from cleanup"""
    _TEMP_DIRECTORIES.discard(path)

async def cleanup_temp_directory(path: str, description: str = "temporary directory") -> bool:
    """
    Robustly cleanup a temporary directory with comprehensive error handling
    
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    if not path or not os.path.exists(path):
        return True
    
    print(f"🧹 Cleaning up {description}: {path}")
    
    try:
        # Unregister from global tracking
        unregister_temp_directory(path)
        
        # Try multiple cleanup strategies
        cleanup_strategies = [
            _cleanup_with_shutil,
            _cleanup_with_pathlib,
            _cleanup_with_os_commands
        ]
        
        for strategy in cleanup_strategies:
            try:
                if await strategy(path):
                    print(f"✅ Successfully cleaned up {description}")
                    return True
            except Exception as e:
                print(f"⚠️ Cleanup strategy failed for {path}: {e}")
                continue
        
        print(f"❌ All cleanup strategies failed for {path}")
        return False
        
    except Exception as e:
        print(f"❌ Critical cleanup error for {path}: {e}")
        return False

async def _cleanup_with_shutil(path: str) -> bool:
    """Cleanup using shutil.rmtree"""
    def _remove():
        # Make all files writable before deletion (handles permission issues)
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.chmod(file_path, 0o777)
                except (OSError, PermissionError):
                    pass
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.chmod(dir_path, 0o777)
                except (OSError, PermissionError):
                    pass
        
        shutil.rmtree(path, ignore_errors=True)
        return not os.path.exists(path)
    
    # Run in thread to avoid blocking
    return await asyncio.to_thread(_remove)

async def _cleanup_with_pathlib(path: str) -> bool:
    """Cleanup using pathlib for better error handling"""
    def _remove():
        from pathlib import Path
        target = Path(path)
        
        # Remove files first, then directories
        for item in target.rglob('*'):
            if item.is_file():
                try:
                    item.chmod(0o777)
                    item.unlink()
                except (OSError, PermissionError):
                    pass
        
        # Remove directories in reverse order (deepest first)
        for item in sorted(target.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if item.is_dir():
                try:
                    item.rmdir()
                except (OSError, PermissionError):
                    pass
        
        # Finally remove the root directory
        try:
            target.rmdir()
        except (OSError, PermissionError):
            pass
        
        return not target.exists()
    
    return await asyncio.to_thread(_remove)

async def _cleanup_with_os_commands(path: str) -> bool:
    """Cleanup using OS commands as last resort"""
    try:
        import platform
        system = platform.system().lower()
        
        if system in ['linux', 'darwin']:  # Unix-like systems
            result = await asyncio.create_subprocess_exec(
                'rm', '-rf', path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            return not os.path.exists(path)
        elif system == 'windows':
            result = await asyncio.create_subprocess_exec(
                'rmdir', '/s', '/q', path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            await result.wait()
            return not os.path.exists(path)
        
    except Exception:
        pass
    
    return False

async def cleanup_all_temp_directories():
    """Cleanup all registered temporary directories"""
    if not _TEMP_DIRECTORIES:
        return
    
    print(f"🧹 Cleaning up {len(_TEMP_DIRECTORIES)} registered temporary directories...")
    
    async with _TEMP_DIR_LOCK:
        temp_dirs = list(_TEMP_DIRECTORIES)  # Create a copy to avoid modification during iteration
        
        cleanup_tasks = []
        for temp_dir in temp_dirs:
            task = cleanup_temp_directory(temp_dir, f"registered temp directory")
            cleanup_tasks.append(task)
        
        # Run all cleanups concurrently
        if cleanup_tasks:
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            successful_cleanups = sum(1 for result in results if result is True)
            print(f"✅ Successfully cleaned up {successful_cleanups}/{len(cleanup_tasks)} directories")

def cleanup_orphaned_temp_directories():
    """Cleanup orphaned temporary directories from previous runs"""
    try:
        temp_base_options = [
            os.environ.get('TEMP_REPO_DIR'),
            os.environ.get('TMPDIR'),
            '/tmp',
            './temp'
        ]
        
        cleaned_count = 0
        for temp_base in temp_base_options:
            if not temp_base or not os.path.exists(temp_base):
                continue
            
            try:
                for item in os.listdir(temp_base):
                    if item.startswith('mygates_'):
                        orphaned_path = os.path.join(temp_base, item)
                        if os.path.isdir(orphaned_path):
                            try:
                                # Check if directory is old (more than 1 hour)
                                stat = os.stat(orphaned_path)
                                age = time.time() - stat.st_mtime
                                if age > 3600:  # 1 hour
                                    shutil.rmtree(orphaned_path, ignore_errors=True)
                                    if not os.path.exists(orphaned_path):
                                        cleaned_count += 1
                                        print(f"🧹 Cleaned orphaned directory: {orphaned_path}")
                            except Exception as e:
                                print(f"⚠️ Failed to clean orphaned directory {orphaned_path}: {e}")
                
            except (OSError, PermissionError) as e:
                print(f"⚠️ Cannot access temp base {temp_base}: {e}")
        
        if cleaned_count > 0:
            print(f"✅ Cleaned up {cleaned_count} orphaned temporary directories")
            
    except Exception as e:
        print(f"⚠️ Error during orphaned directory cleanup: {e}")

@contextlib.asynccontextmanager
async def managed_temp_directory(prefix: str = "mygates_", description: str = "temporary directory"):
    """
    Context manager for temporary directories with guaranteed cleanup
    """
    temp_dir = None
    try:
        # Use the improved unique directory creation
        temp_dir = create_unique_temp_directory(prefix, description)
        yield temp_dir
        
    finally:
        if temp_dir:
            await cleanup_temp_directory(temp_dir, description)

# Setup cleanup handlers
def _cleanup_handler(signum=None, frame=None):
    """Handle cleanup on application shutdown"""
    print("🧹 Application shutdown - cleaning up temporary directories...")
    
    # Run cleanup in the current event loop if available
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(cleanup_all_temp_directories())
    except RuntimeError:
        # No event loop running, create a new one
        asyncio.run(cleanup_all_temp_directories())

# Register cleanup handlers
atexit.register(_cleanup_handler)
signal.signal(signal.SIGTERM, _cleanup_handler)
signal.signal(signal.SIGINT, _cleanup_handler)

# Cleanup orphaned directories on startup
cleanup_orphaned_temp_directories()

def get_default_scan_options() -> Dict[str, Any]:
    """Get default scan options from environment configuration"""
    try:
        from codegates.utils.config_loader import get_config
        config = get_config()
        git_config = config.get_git_config()
        
        return {
            'threshold': 70,  # Keep hardcoded default for threshold
            'prefer_api_checkout': git_config['prefer_api_checkout'],
            'enable_api_fallback': git_config['enable_api_fallback']
        }
    except Exception as e:
        print(f"⚠️ Failed to load git configuration, using hardcoded defaults: {e}")
        return {
            'threshold': 70,
            'prefer_api_checkout': False,
            'enable_api_fallback': True
        }

# Get environment-based defaults at startup
_DEFAULT_SCAN_OPTIONS = get_default_scan_options()

class ScanOptions(BaseModel):
    threshold: Optional[int] = Field(
        default=_DEFAULT_SCAN_OPTIONS['threshold'],
        ge=0,
        le=100,
        description="Quality threshold percentage (0-100)"
    )
    prefer_api_checkout: Optional[bool] = Field(
        default=_DEFAULT_SCAN_OPTIONS['prefer_api_checkout'],
        description="Prefer GitHub API for repository checkout over git clone. Useful when git is not available or unreliable."
    )
    enable_api_fallback: Optional[bool] = Field(
        default=_DEFAULT_SCAN_OPTIONS['enable_api_fallback'],
        description="Enable automatic fallback to GitHub API if git clone fails. Recommended for robust operation."
    )
    verify_ssl: Optional[bool] = Field(
        default=None,
        description="Override SSL certificate verification for this scan. None=use global config, True=force enable, False=force disable. Useful for GitHub Enterprise with self-signed certificates."
    )
    
    # Timeout configurations
    git_clone_timeout: Optional[int] = Field(
        default=None,
        ge=10,
        le=3600,
        description="Git clone timeout in seconds (10-3600). None=use global config."
    )
    api_download_timeout: Optional[int] = Field(
        default=None,
        ge=10,
        le=1800,
        description="API download timeout in seconds (10-1800). None=use global config."
    )
    analysis_timeout: Optional[int] = Field(
        default=None,
        ge=30,
        le=1800,
        description="Analysis timeout in seconds (30-1800). None=use global config."
    )
    llm_request_timeout: Optional[int] = Field(
        default=None,
        ge=5,
        le=300,
        description="LLM request timeout in seconds (5-300). None=use global config."
    )

class JiraOptions(BaseModel):
    enabled: bool = Field(
        default=True,  # Changed to True to enable by default
        description="Enable JIRA integration for this scan"
    )
    issue_key: Optional[str] = Field(
        None,
        description="JIRA issue key to post the report to (e.g., PROJECT-123)"
    )
    comment_format: Optional[str] = Field(
        default="markdown",
        description="Comment format: 'markdown' or 'text'"
    )
    include_details: Optional[bool] = Field(
        default=True,
        description="Include detailed gate results in the comment"
    )
    include_recommendations: Optional[bool] = Field(
        default=True,
        description="Include recommendations in the comment"
    )
    attach_html_report: Optional[bool] = Field(
        default=True,  # Changed to True to enable by default
        description="Attach HTML report to JIRA issue"
    )

class ScanRequest(BaseModel):
    repository_url: str = Field(
        ...,  # This makes it required
        description="Git repository URL (GitHub or GitHub Enterprise)"
    )
    branch: str = Field(
        default="main",
        description="Git branch to analyze"
    )
    github_token: Optional[str] = Field(
        None,
        description="GitHub token for private repositories (optional)"
    )
    scan_options: Optional[ScanOptions] = Field(
        default=None,
        description="Scan configuration options"
    )
    jira_options: Optional[JiraOptions] = Field(
        default=None,
        description="JIRA integration options (optional)"
    )

    @property
    def is_github_enterprise(self) -> bool:
        """Check if the repository URL is from GitHub Enterprise."""
        parsed_url = urlparse(self.repository_url)
        hostname = parsed_url.netloc.lower()
        # Check if it contains 'github' but is not github.com
        return 'github' in hostname and hostname != 'github.com'

    @property
    def is_github_com(self) -> bool:
        """Check if the repository URL is from github.com."""
        parsed_url = urlparse(self.repository_url)
        return parsed_url.netloc.lower() == 'github.com'

    def validate_github_url(self) -> bool:
        """Validate that this is a proper GitHub URL format."""
        try:
            parsed_url = urlparse(self.repository_url)
            
            # Check if it's a valid GitHub URL
            hostname = parsed_url.netloc.lower()
            if not ('github' in hostname):
                raise HTTPException(
                    status_code=400,
                    detail="Repository URL must be a GitHub.com or GitHub Enterprise URL (hostname must contain 'github')"
                )
            
            # Check path format (should be /owner/repo or /owner/repo.git)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid repository URL format. Expected: https://github.example.com/owner/repo"
                )
            
            # Clean up repo name if it ends with .git
            repo_name = path_parts[1]
            if repo_name.endswith('.git'):
                path_parts[1] = repo_name[:-4]
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid repository URL format: {str(e)}"
            )

    def check_repository_access(self):
        """Check if repository is accessible using git commands instead of GitHub API."""
        try:
            # First validate the URL format
            self.validate_github_url()
            
            # Parse repository URL
            parsed_url = urlparse(self.repository_url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid repository URL format"
                )
            
            owner = path_parts[0]
            repo = path_parts[1]
            
            # Clean up repo name if it ends with .git
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            # Build the Git URL for testing
            if self.github_token:
                # Use token for authentication
                test_url = f"https://{self.github_token}@{parsed_url.netloc}{parsed_url.path}"
            else:
                # Try without token first
                test_url = f"https://{parsed_url.netloc}{parsed_url.path}"
            
            # Ensure URL ends with .git
            if not test_url.endswith('.git'):
                test_url += '.git'
            
            print(f"🔍 Testing repository access with git ls-remote: {parsed_url.netloc}{parsed_url.path}")
            
            # Use git ls-remote to test repository access
            # This works with both public/private repos and handles SSL certificates properly
            cmd = ["git", "ls-remote", "--heads", test_url]
            
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=TIMEOUT_CONFIG['git_ls_remote_timeout'],
                    env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}  # Disable interactive prompts
                )
                
                if result.returncode == 0:
                    print(f"✅ Repository accessible")
                    return True
                else:
                    # Parse git error for better user messages
                    error_output = result.stderr.lower()
                    
                    if 'authentication failed' in error_output or 'could not read username' in error_output:
                        if self.github_token:
                            raise HTTPException(
                                status_code=401,
                                detail="Invalid GitHub token or insufficient permissions. Please check if the token has 'repo' scope access."
                            )
                        else:
                            raise HTTPException(
                                status_code=401,
                                detail="Repository is private or authentication required. Please provide a GitHub token with 'repo' scope."
                            )
                    elif 'repository not found' in error_output or 'not found' in error_output:
                        raise HTTPException(
                            status_code=404,
                            detail="Repository not found. Please check the repository URL."
                        )
                    elif 'permission denied' in error_output:
                        raise HTTPException(
                            status_code=403,
                            detail="Permission denied. Please check if the token has access to this repository."
                        )
                    elif 'ssl certificate' in error_output or 'certificate verify failed' in error_output:
                        # For SSL certificate issues, suggest using token or configuring git
                        raise HTTPException(
                            status_code=400,
                            detail="SSL certificate verification failed. This is common with GitHub Enterprise. Please provide a GitHub token for authentication."
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot access repository: {result.stderr.strip()}"
                        )
            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=408,
                    detail="Repository access test timed out. Please check the repository URL and network connectivity."
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to validate repository access: {str(e)}"
            )

class GateResult(BaseModel):
    name: str = Field(..., description="Name of the quality gate")
    status: str = Field(..., description="Gate status: 'PASS' | 'FAIL' | 'WARNING' | 'NOT_APPLICABLE'")
    score: float = Field(..., ge=0, le=100, description="Gate score (0-100)")
    details: List[str] = Field(default_factory=list, description="Detailed findings")
    expected: Optional[int] = Field(None, description="Expected number of implementations")
    found: Optional[int] = Field(None, description="Actual number found")
    coverage: Optional[float] = Field(None, ge=0, le=100, description="Coverage percentage")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Quality score")
    matches: List[Dict[str, Any]] = Field(default_factory=list, description="Enhanced metadata for pattern matches")

class ScanResult(BaseModel):
    scan_id: str = Field(..., description="Unique scan identifier")
    status: str = Field(..., description="Scan status: 'completed' | 'failed' | 'running'")
    score: float = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    gates: List[GateResult] = Field(default_factory=list, description="Individual gate results")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    report_url: Optional[str] = Field(None, description="URL to detailed report")
    jira_result: Optional[Dict[str, Any]] = Field(None, description="JIRA integration result")

def ensure_writable_directory(path: str, description: str = "directory") -> str:
    """Ensure directory exists and is writable, with container-friendly fallbacks"""
    
    # List of fallback options
    fallback_options = [
        path,
        f"./app/{Path(path).name}",  # App-relative path
        f"./{Path(path).name}",      # Current dir relative
        f"./temp/{Path(path).name}"  # Temp subdirectory
    ]
    
    for option in fallback_options:
        if not option:
            continue
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(option, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(option, f'.write_test_{os.getpid()}')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            print(f"✅ Using {description}: {option}")
            return option
            
        except (OSError, PermissionError) as e:
            print(f"⚠️ Cannot use {option} for {description}: {e}")
            continue
    
    # If all options failed, raise an error
    raise Exception(f"No writable {description} found. Please set appropriate environment variables or ensure container has write permissions.")

def download_repository_via_api(repo_url: str, branch: str, token: Optional[str] = None, verify_ssl: Optional[bool] = None, scan_options: Optional[ScanOptions] = None) -> str:
    """Download repository using GitHub API as fallback when git clone fails"""
    
    try:
        # Parse repository URL to extract owner and repo
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise Exception("Invalid repository URL format for API download")
        
        owner = path_parts[0]
        repo = path_parts[1]
        
        # Clean up repo name if it ends with .git
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        # Determine API base URL (GitHub.com vs GitHub Enterprise)
        if parsed_url.netloc.lower() == 'github.com':
            api_base_url = 'https://api.github.com'
        else:
            # GitHub Enterprise
            api_base_url = f"https://{parsed_url.netloc}/api/v3"
        
        print(f"🌐 Attempting API download from {api_base_url}")
        print(f"📦 Repository: {owner}/{repo}, Branch: {branch}")
        
        # Create unique temporary directory for extraction
        temp_dir = create_unique_temp_directory("mygates_api_", "API download directory")
        
        # Create SSL-configured session
        session = get_requests_session(verify_ssl)
        
        # Download repository archive via API
        archive_url = f"{api_base_url}/repos/{owner}/{repo}/zipball/{branch}"
        
        # Configure headers
        if token:
            session.headers.update({'Authorization': f'token {token}'})
        
        # Get configurable timeout
        api_timeout = get_api_download_timeout(scan_options)
        print(f"🔄 Downloading repository archive... (timeout: {api_timeout}s)")
        print(f"🔒 SSL verification: {'enabled' if session.verify else 'disabled'}")
        
        try:
            response = session.get(archive_url, timeout=api_timeout)
        except requests.exceptions.SSLError as ssl_error:
            error_msg = str(ssl_error).lower()
            
            if 'certificate verify failed' in error_msg or 'ssl certificate' in error_msg:
                # Provide helpful error message for SSL issues
                if verify_ssl is None:  # Only suggest if not explicitly set
                    raise Exception(
                        f"SSL certificate verification failed for GitHub Enterprise server '{parsed_url.netloc}'. "
                        f"To resolve this issue:\n"
                        f"1. Set CODEGATES_SSL_VERIFY=false in your .env file to disable SSL verification\n"
                        f"2. Or set CODEGATES_SSL_CA_BUNDLE=/path/to/your/ca-bundle.pem to use custom certificates\n"
                        f"3. Or provide a GitHub token for authentication which may bypass some SSL issues\n"
                        f"Original error: {ssl_error}"
                    )
                else:
                    raise Exception(f"SSL certificate verification failed: {ssl_error}")
            else:
                raise Exception(f"SSL connection error: {ssl_error}")
        except requests.exceptions.ConnectionError as conn_error:
            raise Exception(f"Connection error to GitHub Enterprise server '{parsed_url.netloc}': {conn_error}")
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout connecting to GitHub Enterprise server '{parsed_url.netloc}'. Check network connectivity.")
        
        if response.status_code == 200:
            print(f"✅ Repository archive downloaded successfully ({len(response.content)} bytes)")
            
            # Extract ZIP archive using the safe extraction function
            try:
                return safe_extract_archive(response.content, temp_dir)
                        
            except Exception as e:
                raise Exception(f"Failed to extract repository archive: {e}")
                
        elif response.status_code == 401:
            raise Exception("Authentication failed. Please check your GitHub token and ensure it has 'repo' scope access.")
        elif response.status_code == 403:
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            if rate_limit_remaining == '0':
                reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
                raise Exception(f"GitHub API rate limit exceeded. Rate limit resets at {reset_time}. Consider using a GitHub token.")
            else:
                raise Exception("Access forbidden. Token may lack required permissions or repository may be private.")
        elif response.status_code == 404:
            raise Exception(f"Repository or branch not found: {owner}/{repo}@{branch}. Check the repository URL and branch name.")
        elif response.status_code == 422:
            raise Exception(f"Invalid branch name '{branch}' for repository {owner}/{repo}. Check if the branch exists.")
        else:
            try:
                error_detail = response.json().get('message', response.text)
            except:
                error_detail = response.text
            raise Exception(f"GitHub API request failed with status {response.status_code}: {error_detail}")
            
    except requests.RequestException as e:
        if 'ssl' in str(e).lower() or 'certificate' in str(e).lower():
            raise Exception(
                f"SSL/Certificate error during API download from GitHub Enterprise. "
                f"Consider setting CODEGATES_SSL_VERIFY=false or CODEGATES_SSL_CA_BUNDLE=/path/to/ca-bundle.pem. "
                f"Error: {e}"
            )
        else:
            raise Exception(f"Network error during API download: {e}")
    except Exception as e:
        # Cleanup on failure (temp_dir will be cleaned by our global cleanup system)
        print(f"❌ API download failed: {e}")
        raise e

def clone_repository(repo_url: str, branch: str, token: Optional[str] = None, prefer_api: bool = False, verify_ssl: Optional[bool] = None, scan_options: Optional[ScanOptions] = None) -> str:
    """
    Clone repository with Git fallback to GitHub API
    
    Args:
        repo_url: Repository URL
        branch: Branch to checkout
        token: GitHub token (optional)
        prefer_api: If True, try API first; if False, try git first
        verify_ssl: SSL verification setting (None=use config, True=force enable, False=force disable)
        scan_options: Scan options with timeout overrides
    """
    
    git_error = None
    api_error = None
    
    # Determine order of methods to try
    if prefer_api:
        methods = [
            ("GitHub API", lambda url, br, tok: download_repository_via_api(url, br, tok, verify_ssl, scan_options)),
            ("Git Clone", lambda url, br, tok: _clone_repository_via_git(url, br, tok, scan_options))
        ]
    else:
        methods = [
            ("Git Clone", lambda url, br, tok: _clone_repository_via_git(url, br, tok, scan_options)),
            ("GitHub API", lambda url, br, tok: download_repository_via_api(url, br, tok, verify_ssl, scan_options))
        ]
    
    for method_name, method_func in methods:
        try:
            print(f"🔄 Trying {method_name} for repository checkout...")
            result = method_func(repo_url, branch, token)
            print(f"✅ Successfully checked out repository using {method_name}")
            return result
            
        except Exception as e:
            print(f"❌ {method_name} failed: {str(e)}")
            if method_name == "Git Clone":
                git_error = str(e)
            else:
                api_error = str(e)
            
            # Continue to next method
            continue
    
    # Both methods failed, raise comprehensive error
    error_details = []
    if git_error:
        error_details.append(f"Git Clone: {git_error}")
    if api_error:
        error_details.append(f"API Download: {api_error}")
    
    # Check if both failed due to SSL issues and provide helpful guidance
    ssl_related_errors = ['ssl', 'certificate', 'tls']
    if any(ssl_term in str(error_details).lower() for ssl_term in ssl_related_errors):
        ssl_help = (
            f"\n\n🔒 SSL Certificate Issues Detected:\n"
            f"Both git clone and API download failed with SSL-related errors. "
            f"For GitHub Enterprise servers with self-signed certificates:\n\n"
            f"1. Disable SSL verification (quick fix):\n"
            f"   Add to your .env file: CODEGATES_SSL_VERIFY=false\n\n"
            f"2. Use custom CA bundle (secure fix):\n"
            f"   Add to your .env file: CODEGATES_SSL_CA_BUNDLE=/path/to/ca-bundle.pem\n\n"
            f"3. Configure git globally:\n"
            f"   git config --global http.sslVerify false\n\n"
            f"4. Use authentication token (may help):\n"
            f"   Provide a GitHub Enterprise token with 'repo' scope"
        )
        
        raise Exception(f"All repository checkout methods failed due to SSL issues. {'; '.join(error_details)}{ssl_help}")
    else:
        raise Exception(f"All repository checkout methods failed. Errors: {'; '.join(error_details)}")

def _clone_repository_via_git(repo_url: str, branch: str, token: Optional[str] = None, scan_options: Optional[ScanOptions] = None) -> str:
    """Original git clone implementation (extracted from clone_repository)"""
    
    # Create unique temporary directory for git clone
    temp_dir = create_unique_temp_directory("mygates_git_", "git clone directory")
    
    try:
        # Build clone URL
        parsed_url = urlparse(repo_url)
        if token:
            clone_url = f"https://{token}@{parsed_url.netloc}{parsed_url.path}.git"
        else:
            clone_url = f"https://{parsed_url.netloc}{parsed_url.path}.git"
        
        # Get configurable timeout
        git_timeout = get_git_clone_timeout(scan_options)
        
        # Clone repository with enhanced error handling
        cmd = ["git", "clone", "-b", branch, "--depth", "1", clone_url, temp_dir]
        print(f"🔄 Running: git clone -b {branch} --depth 1 [URL] {temp_dir} (timeout: {git_timeout}s)")
        
        # Ensure target directory is empty before cloning
        if os.path.exists(temp_dir) and os.listdir(temp_dir):
            print(f"⚠️ Target directory not empty, cleaning: {temp_dir}")
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    try:
                        os.remove(item_path)
                    except OSError:
                        pass
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=git_timeout,
            env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            
            # Enhanced error messages for containers and directory issues
            if 'permission denied' in error_msg.lower():
                raise Exception(f"Permission denied during git clone. This might be due to container security constraints. Error: {error_msg}")
            elif 'command not found' in error_msg.lower() or 'git' in error_msg.lower():
                raise Exception(f"Git command not available. Consider using API fallback. Error: {error_msg}")
            elif 'directory not empty' in error_msg.lower() or 'already exists' in error_msg.lower():
                raise Exception(f"Target directory issue during git clone. This might be a race condition. Error: {error_msg}")
            else:
                raise Exception(f"Git clone failed: {error_msg}")
        
        print(f"✅ Repository cloned successfully via git to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        raise Exception("Git clone operation timed out after 5 minutes")
        
    except Exception as e:
        # The temp_dir will be cleaned up by our global cleanup system on failure
        print(f"❌ Git clone failed: {e}")
        raise e

def analyze_repository(repo_path: str, threshold: int, repository_url: Optional[str] = None) -> Dict:
    """Analyze repository using CodeGates"""
    try:
        # Try to import and use the actual CodeGates analysis
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            
            from codegates.core.gate_validator import GateValidator
            from codegates.core.language_detector import LanguageDetector
            from codegates.models import ScanConfig, Language
            
            # Try to import LLM components
            llm_manager = None
            try:
                from codegates.core.llm_analyzer import LLMIntegrationManager, LLMConfig, LLMProvider
                from codegates.utils.env_loader import EnvironmentLoader
                
                # Get LLM configuration from EnvironmentLoader
                env_loader = EnvironmentLoader()
                preferred_provider = env_loader.get_preferred_llm_provider()
                
                if preferred_provider:
                    provider_config = env_loader.get_llm_config(preferred_provider)
                    print(f"🔧 Using {preferred_provider} LLM provider")
                    print(f"   Configuration: {provider_config}")
                    
                    if preferred_provider == 'openai':
                        llm_config = LLMConfig(
                            provider=LLMProvider.OPENAI,
                            model=provider_config['model'],
                            api_key=provider_config['api_key'],
                            base_url=provider_config.get('base_url'),
                            temperature=provider_config['temperature'],
                            max_tokens=provider_config['max_tokens']
                        )
                    elif preferred_provider == 'anthropic':
                        llm_config = LLMConfig(
                            provider=LLMProvider.ANTHROPIC,
                            model=provider_config['model'],
                            api_key=provider_config['api_key'],
                            base_url=provider_config.get('base_url'),
                            temperature=provider_config['temperature'],
                            max_tokens=provider_config['max_tokens']
                        )
                    elif preferred_provider == 'local':
                        llm_config = LLMConfig(
                            provider=LLMProvider.LOCAL,
                            model=provider_config['model'],
                            api_key=provider_config['api_key'],
                            base_url=provider_config['base_url'],
                            temperature=provider_config['temperature'],
                            max_tokens=provider_config['max_tokens']
                        )
                    else:
                        print(f"⚠️ Unsupported provider: {preferred_provider}")
                        llm_config = None
                    
                    if llm_config:
                        llm_manager = LLMIntegrationManager(llm_config)
                        
                        # Test if LLM is available
                        if llm_manager.is_enabled():
                            print(f"✅ LLM integration enabled with {preferred_provider}")
                        else:
                            print(f"⚠️ LLM integration failed for {preferred_provider}, continuing with pattern-based analysis")
                            llm_manager = None
                else:
                    print("⚠️ No LLM provider configured")
                    print("📝 To enable LLM analysis:")
                    print("   Option 1: Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
                    print("   Option 2: Configure local LLM service in .env file")
                    print("   Continuing with pattern-based analysis only...")
                    llm_manager = None
                        
            except ImportError:
                print("⚠️ LLM components not available, continuing with pattern-based analysis only")
                llm_manager = None
            
            # Detect languages
            detector = LanguageDetector()
            languages = detector.detect_languages(Path(repo_path))
            
            if not languages:
                languages = [Language.PYTHON]  # Default fallback
            
            print(f"🔍 Detected languages: {[lang.value for lang in languages]}")
            
            # Create scan configuration
            config = ScanConfig(
                target_path=repo_path,
                languages=languages,
                min_coverage_threshold=threshold,
                exclude_patterns=[
                    "node_modules/**", ".git/**", "**/__pycache__/**",
                    "**/target/**", "**/bin/**", "**/obj/**", "**/.vscode/**"
                ],
                max_file_size=1024*1024  # 1MB max file size
            )
            
            # Run validation
            validator = GateValidator(config)
            result = validator.validate(Path(repo_path), llm_manager, repository_url)
            
            print(f"📊 Analysis completed. Overall score: {result.overall_score:.1f}%")
            print(f"📈 Gates analyzed: {len(result.gate_scores)}")
            
            # Convert to API format
            gates = []
            for gate_score in result.gate_scores:
                # Handle different status types including NOT_APPLICABLE
                if gate_score.status == "NOT_APPLICABLE":
                    status = "NOT_APPLICABLE"
                elif gate_score.final_score >= 80:
                    status = "PASS"
                elif gate_score.final_score >= 60:
                    status = "WARNING"
                else:
                    status = "FAIL"
                
                # Limit details to avoid overwhelming the response
                details = gate_score.details[:5] if gate_score.details else [
                    f"Expected: {gate_score.expected}, Found: {gate_score.found}",
                    f"Coverage: {gate_score.coverage:.1f}%"
                ]
                
                gates.append({
                    "name": gate_score.gate.value,
                    "status": status,
                    "score": gate_score.final_score,
                    "details": details,
                    "expected": gate_score.expected,
                    "found": gate_score.found,
                    "coverage": gate_score.coverage,
                    "quality_score": gate_score.quality_score,
                    "matches": gate_score.matches  # Include enhanced metadata directly from GateScore
                })
            
            return {
                "score": result.overall_score,
                "gates": gates,
                "recommendations": result.recommendations[:5] if result.recommendations else [
                    "Implement structured logging across your codebase",
                    "Add comprehensive error handling",
                    "Include automated tests for critical functionality"
                ],
                "llm_enhanced": llm_manager is not None,
                "languages_detected": [lang.value for lang in languages],
                "total_files": result.total_files,
                "total_lines": result.total_lines,
                "result_object": result  # Include full result for HTML generation
            }
            
        except ImportError as e:
            print(f"CodeGates import failed: {e}")
            # Fallback analysis
            return perform_basic_analysis(repo_path, threshold)
            
    except Exception as e:
        print(f"Analysis failed: {e}")
        # Return basic analysis as fallback
        return perform_basic_analysis(repo_path, threshold)

def perform_basic_analysis(repo_path: str, threshold: int) -> Dict:
    """Perform basic analysis when CodeGates is not available"""
    
    # Count files by type
    file_counts = {}
    total_files = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'target', 'bin', 'obj']]
        
        for file in files:
            total_files += 1
            ext = os.path.splitext(file)[1].lower()
            file_counts[ext] = file_counts.get(ext, 0) + 1
    
    # Basic scoring based on file types and structure
    score = 50  # Base score
    
    # Language detection and scoring
    gates = []
    
    # Check for common quality indicators
    has_tests = any(ext in ['.test.js', '.spec.js', '.test.py', '.spec.py'] or 'test' in ext for ext in file_counts.keys())
    has_config = any(file in ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle'] for file in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, file)))
    has_readme = any(file.lower().startswith('readme') for file in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, file)))
    
    # Test coverage gate
    test_score = 80 if has_tests else 30
    gates.append({
        "name": "automated_tests",
        "status": "PASS" if test_score >= 70 else "FAIL",
        "score": test_score,
        "details": ["Test files found" if has_tests else "No test files detected"]
    })
    
    # Configuration gate
    config_score = 90 if has_config else 40
    gates.append({
        "name": "project_structure",
        "status": "PASS" if config_score >= 70 else "FAIL", 
        "score": config_score,
        "details": ["Configuration files found" if has_config else "No configuration files detected"]
    })
    
    # Documentation gate
    doc_score = 85 if has_readme else 35
    gates.append({
        "name": "documentation",
        "status": "PASS" if doc_score >= 70 else "FAIL",
        "score": doc_score,
        "details": ["README file found" if has_readme else "No README file detected"]
    })
    
    # Calculate overall score
    overall_score = sum(gate["score"] for gate in gates) / len(gates) if gates else 50
    
    recommendations = []
    if not has_tests:
        recommendations.append("Add automated tests to improve code quality")
    if not has_config:
        recommendations.append("Add configuration files (package.json, requirements.txt, etc.)")
    if not has_readme:
        recommendations.append("Add README documentation")
    
    return {
        "score": overall_score,
        "gates": gates,
        "recommendations": recommendations,
        "llm_enhanced": False
    }

async def perform_scan(scan_id: str, request: ScanRequest):
    """Perform the actual repository scan with timeout handling"""
    repo_path = None
    try:
        # Update status to running
        scan_results[scan_id]["status"] = "running"
        scan_results[scan_id]["message"] = "Cloning repository..."
        
        # Get scan options with environment defaults
        scan_options = request.scan_options or ScanOptions()
        
        # Debug: Show which options are being used
        print(f"🔧 Scan Options Configuration:")
        print(f"   threshold: {scan_options.threshold}")
        print(f"   prefer_api_checkout: {scan_options.prefer_api_checkout} {'(from env)' if _DEFAULT_SCAN_OPTIONS['prefer_api_checkout'] else '(default)'}")
        print(f"   enable_api_fallback: {scan_options.enable_api_fallback} {'(from env)' if _DEFAULT_SCAN_OPTIONS['enable_api_fallback'] else '(default)'}")
        
        # Determine checkout method preferences
        prefer_api = scan_options.prefer_api_checkout
        enable_fallback = scan_options.enable_api_fallback
        
        print(f"🔄 Repository checkout method: {'API preferred' if prefer_api else 'Git preferred'} (fallback {'enabled' if enable_fallback else 'disabled'})")
        
        # Clone repository with API fallback support
        if enable_fallback:
            # Use the enhanced clone_repository with fallback
            repo_path = clone_repository(
                request.repository_url, 
                request.branch, 
                request.github_token,
                prefer_api=prefer_api,
                verify_ssl=scan_options.verify_ssl,
                scan_options=scan_options
            )
        else:
            # Use only git clone (legacy behavior)
            try:
                repo_path = _clone_repository_via_git(
                    request.repository_url, 
                    request.branch, 
                    request.github_token,
                    scan_options=scan_options
                )
            except Exception as git_error:
                if prefer_api:
                    # Fallback to API even if fallback is disabled but API is preferred
                    print("🔄 Git failed, trying API as requested preference...")
                    repo_path = download_repository_via_api(
                        request.repository_url, 
                        request.branch, 
                        request.github_token,
                        verify_ssl=scan_options.verify_ssl,
                        scan_options=scan_options
                    )
                else:
                    raise git_error
        
        try:
            scan_results[scan_id]["message"] = "Analyzing repository with optimized LLM processing..."
            
            # Analyze repository with timeout
            threshold = scan_options.threshold
            
            # Use asyncio timeout for better control
            try:
                # Get configurable timeout
                analysis_timeout = get_analysis_timeout(scan_options)
                print(f"🔍 Starting analysis with timeout: {analysis_timeout}s")
                
                analysis_result = await asyncio.wait_for(
                    asyncio.to_thread(analyze_repository, repo_path, threshold, request.repository_url),
                    timeout=float(analysis_timeout)
                )
                
                # Update scan results
                scan_results[scan_id].update({
                    "status": "completed",
                    "score": analysis_result["score"],
                    "gates": analysis_result["gates"],
                    "recommendations": analysis_result["recommendations"],
                    "report_url": f"{API_BASE_URL}{API_VERSION_PREFIX}/reports/{scan_id}",
                    "message": f"Scan completed {'with LLM enhancement' if analysis_result.get('llm_enhanced') else 'with pattern-based analysis'}",
                    "completed_at": datetime.now().isoformat(),
                    "llm_enhanced": analysis_result.get('llm_enhanced', False),
                    "total_files": analysis_result.get('total_files', 0),
                    "total_lines": analysis_result.get('total_lines', 0),
                    "result_object": analysis_result.get('result_object'),  # Store full result for HTML generation
                    "repository_url": request.repository_url,  # Store repository URL
                    "branch": request.branch,  # Store branch
                    "checkout_method": analysis_result.get('checkout_method', 'unknown')  # Track which method was used
                })
                
                # Generate and save HTML report immediately
                try:
                    validation_result = analysis_result.get('result_object')
                    if validation_result:
                        from codegates.reports import ReportGenerator
                        from codegates.models import ReportConfig
                        
                        # Create reports directory using configuration
                        reports_dir_path = get_reports_directory()
                        reports_dir = Path(reports_dir_path)
                        
                        # Generate and save report to file
                        report_filename = f"hard_gate_report_{scan_id}.html"
                        report_path = reports_dir / report_filename
                        
                        # Create report config for HTML generation
                        report_config = ReportConfig(
                            format='html',
                            output_path=str(reports_dir),
                            include_details=True,
                            include_recommendations=True
                        )
                        
                        # Generate HTML report
                        generator = ReportGenerator(report_config)
                        html_content = generator._generate_html_content(validation_result)
                        
                        # Save the HTML file
                        with open(report_path, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        print(f"📄 HTML report saved to: {report_path}")
                        scan_results[scan_id]["report_file"] = str(report_path)
                        
                except Exception as report_error:
                    print(f"⚠️ Failed to generate HTML report: {report_error}")
                    # Continue without failing the scan
                
                # Log API_BASE_URL for debugging
                print(f"🔍 DEBUG: API_BASE_URL = '{API_BASE_URL}'")
                print(f"🔍 DEBUG: API_VERSION_PREFIX = '{API_VERSION_PREFIX}'")
                print(f"🔍 DEBUG: Full report URL = '{API_BASE_URL}{API_VERSION_PREFIX}/reports/{scan_id}'")
                
                # JIRA Integration (if enabled and available)
                jira_result = None
                if (JIRA_AVAILABLE and 
                    request.jira_options and 
                    request.jira_options.enabled and 
                    analysis_result.get('result_object')):
                    
                    try:
                        scan_results[scan_id]["message"] = "Posting report to JIRA..."
                        
                        # Create JIRA integration instance
                        jira_config = {}
                        if request.jira_options.comment_format:
                            jira_config['comment_format'] = request.jira_options.comment_format
                        if request.jira_options.include_details is not None:
                            jira_config['include_details'] = request.jira_options.include_details
                        if request.jira_options.include_recommendations is not None:
                            jira_config['include_recommendations'] = request.jira_options.include_recommendations
                        if request.jira_options.attach_html_report is not None:
                            jira_config['attach_html_report'] = request.jira_options.attach_html_report
                        
                        jira_integration = JiraIntegration(jira_config if jira_config else None)
                        
                        if jira_integration.is_available():
                            # Prepare additional context
                            additional_context = {
                                'repository_url': request.repository_url,
                                'branch': request.branch,
                                'scan_id': scan_id,
                                'report_url': f"{API_BASE_URL}{API_VERSION_PREFIX}/reports/{scan_id}"
                            }
                            
                            # Get HTML report path if available
                            html_report_path = scan_results[scan_id].get("report_file")
                            
                            # Post to JIRA
                            jira_result = jira_integration.post_report_comment(
                                analysis_result['result_object'],
                                request.jira_options.issue_key,
                                additional_context,
                                html_report_path
                            )
                            
                            if jira_result.get('success'):
                                print(f"✅ Report posted to JIRA issue {jira_result.get('jira_issue')}")
                                scan_results[scan_id]["message"] += f" | Posted to JIRA: {jira_result.get('jira_issue')}"
                            else:
                                print(f"⚠️ JIRA posting failed: {jira_result.get('message')}")
                        else:
                            jira_result = {
                                'success': False,
                                'message': 'JIRA integration not properly configured',
                                'posted': False
                            }
                            
                    except Exception as jira_error:
                        print(f"⚠️ JIRA integration error: {str(jira_error)}")
                        jira_result = {
                            'success': False,
                            'message': f'JIRA integration failed: {str(jira_error)}',
                            'posted': False,
                            'error': str(jira_error)
                        }
                
                # Store JIRA result
                if jira_result:
                    scan_results[scan_id]["jira_result"] = jira_result
                
            except asyncio.TimeoutError:
                analysis_timeout = get_analysis_timeout(scan_options)
                print(f"⏰ Repository scan timed out after {analysis_timeout} seconds")
                scan_results[scan_id].update({
                    "status": "completed",
                    "score": 0.0,
                    "gates": [],
                    "recommendations": [
                        f"Scan timed out after {analysis_timeout} seconds",
                        "Try scanning a smaller repository or specific directory",
                        "Consider disabling LLM analysis for faster results",
                        "You can increase the timeout using the analysis_timeout parameter"
                    ],
                    "report_url": f"{API_BASE_URL}{API_VERSION_PREFIX}/reports/{scan_id}",
                    "message": f"Scan timed out - completed with basic analysis only (timeout: {analysis_timeout}s)",
                    "error": "timeout",
                    "completed_at": datetime.now().isoformat()
                })
                
        finally:
            # Enhanced cleanup - use the robust cleanup system
            if repo_path and os.path.exists(repo_path):
                print(f"🧹 Starting cleanup of repository directory: {repo_path}")
                cleanup_success = await cleanup_temp_directory(repo_path, "repository scan directory")
                if cleanup_success:
                    print(f"✅ Repository directory cleaned up successfully")
                else:
                    print(f"⚠️ Repository directory cleanup had issues, but scan completed")
                
    except Exception as e:
        print(f"❌ Scan failed for {scan_id}: {str(e)}")
        
        # Enhanced error handling with cleanup
        scan_results[scan_id].update({
            "status": "failed",
            "message": f"Scan failed: {str(e)}",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })
        
        # Cleanup on failure as well
        if repo_path and os.path.exists(repo_path):
            print(f"🧹 Cleaning up after scan failure: {repo_path}")
            try:
                cleanup_success = await cleanup_temp_directory(repo_path, "failed scan directory")
                if cleanup_success:
                    print(f"✅ Failed scan directory cleaned up successfully")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup after scan failure: {cleanup_error}")
    
    finally:
        # Additional safety cleanup - ensure no temp directories are left behind
        print(f"🧹 Final cleanup check for scan {scan_id}")
        try:
            # Clean up any remaining registered temp directories
            await cleanup_all_temp_directories()
        except Exception as final_cleanup_error:
            print(f"⚠️ Final cleanup check failed: {final_cleanup_error}")

@api_v1.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests for all routes"""
    return {"message": "OK"}

@api_v1.get("/health")
async def health_check():
    """Check API health status."""
    return {"status": "healthy", "cors_enabled": True}

@api_v1.post("/scan", response_model=ScanResult)
async def scan_repository(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Scan a Git repository for code quality.
    
    - Supports both GitHub.com and GitHub Enterprise repositories
    - GitHub token is optional for public repositories
    - GitHub token is required for private repositories
    - Validates repository URL and branch
    - Returns detailed quality analysis results
    """
    try:
        # Check repository access (handles public/private repos)
        #request.check_repository_access()

        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Initialize scan result
        scan_results[scan_id] = {
            "scan_id": scan_id,
            "status": "running",
            "score": 0.0,
            "gates": [],
            "recommendations": [],
            "report_url": None,
            "message": "Scan initiated",
            "created_at": datetime.now().isoformat()
        }
        
        # Start background scan
        background_tasks.add_task(perform_scan, scan_id, request)
        
        return ScanResult(
            scan_id=scan_id,
            status="running",
            score=0.0,
            gates=[],
            recommendations=[],
            report_url=None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/scan/{scan_id}/status", response_model=ScanResult)
async def get_scan_status(scan_id: str):
    """Get the status and results of a specific scan."""
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        result = scan_results[scan_id]
        
        return ScanResult(
            scan_id=result["scan_id"],
            status=result["status"],
            score=result["score"],
            gates=[GateResult(**gate) for gate in result["gates"]],
            recommendations=result["recommendations"],
            report_url=result.get("report_url"),
            jira_result=result.get("jira_result")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/reports/{scan_id}")
async def get_html_report(scan_id: str, comments: Optional[str] = Query(None, description="JSON string of comments")):
    """Generate and return HTML report for a scan with optional comments."""
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        result = scan_results[scan_id]
        
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Scan not completed yet")
        
        # Parse comments if provided
        parsed_comments = {}
        if comments:
            try:
                parsed_comments = json.loads(comments)
            except json.JSONDecodeError:
                print(f"⚠️ Invalid comments JSON format, ignoring comments")
                parsed_comments = {}
        
        # Check for stored comments in scan result
        stored_comments = result.get("comments", {})
        if stored_comments:
            parsed_comments.update(stored_comments)
        
        # First, try to serve from saved file if no comments or comments match
        if not parsed_comments and "report_file" in result:
            report_path = Path(result["report_file"])
            if report_path.exists():
                try:
                    with open(report_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    return HTMLResponse(content=html_content, status_code=200)
                except Exception as file_error:
                    print(f"⚠️ Failed to read saved report file: {file_error}")
                    # Fall through to regeneration
        
        # Try to find report file by scan_id if not stored in result
        reports_dir = Path(get_reports_directory())
        report_filename = f"hard_gate_report_{scan_id}.html"
        report_path = reports_dir / report_filename
        
        # If no comments and file exists, serve it
        if not parsed_comments and report_path.exists():
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                return HTMLResponse(content=html_content, status_code=200)
            except Exception as file_error:
                print(f"⚠️ Failed to read report file: {file_error}")
                # Fall through to regeneration
        
        # Generate HTML report with comments (on-demand or with comments)
        print(f"📄 Generating HTML report for {scan_id}" + (f" with {len(parsed_comments)} comments" if parsed_comments else ""))
        
        # Get the full validation result object
        validation_result = result.get("result_object")
        
        if not validation_result:
            raise HTTPException(status_code=500, detail="Report data not available")
        
        # Generate HTML report with comments
        try:
            from codegates.reports import ReportGenerator
            from codegates.models import ReportConfig
            
            # Create reports directory using configuration
            reports_dir_path = get_reports_directory()
            reports_dir = Path(reports_dir_path)
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Create report config for HTML generation
            report_config = ReportConfig(
                format='html',
                output_path=str(reports_dir),
                include_details=True,
                include_recommendations=True
            )
            
            # Generate HTML report with comments
            generator = ReportGenerator(report_config)
            html_content = generator._generate_html_content(validation_result, parsed_comments)
            
            # Save the HTML file (with comments if provided)
            if parsed_comments:
                # Save with comments suffix for caching
                comments_hash = hashlib.md5(json.dumps(parsed_comments, sort_keys=True).encode()).hexdigest()[:8]
                report_filename = f"hard_gate_report_{scan_id}_{comments_hash}.html"
            else:
                report_filename = f"hard_gate_report_{scan_id}.html"
            
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 HTML report saved to: {report_path}")
            
            # Update scan result with report file path if no comments (main report)
            if not parsed_comments:
                scan_results[scan_id]["report_file"] = str(report_path)
            
            return HTMLResponse(content=html_content, status_code=200)
            
        except ImportError:
            # Fallback to basic HTML if report generator not available
            
            # Extract project name from repository URL 
            project_name = "Unknown Project"
            repository_url = result.get("repository_url")
            if repository_url:
                try:
                    url_parts = repository_url.rstrip('/').split('/')
                    if len(url_parts) >= 2:
                        project_name = url_parts[-1]
                        if project_name.endswith('.git'):
                            project_name = project_name[:-4]
                except Exception:
                    project_name = "Unknown Project"
            
            # Generate basic HTML with comments
            comments_html = ""
            if parsed_comments:
                comments_html = "<h2>Comments</h2><ul>"
                for gate_name, comment in parsed_comments.items():
                    comments_html += f"<li><strong>{gate_name}:</strong> {comment}</li>"
                comments_html += "</ul>"
            
            basic_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Hard Gate Assessment - {project_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .score {{ font-size: 24px; color: #2563eb; font-weight: bold; }}
                    .gate {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
                    .pass {{ background-color: #ecfdf5; }}
                    .fail {{ background-color: #fef2f2; }}
                    .warning {{ background-color: #fffbeb; }}
                </style>
            </head>
            <body>
                <h1>{project_name}</h1>
                <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report{' (with comments)' if parsed_comments else ''}</p>
                <div class="score">Overall Score: {result['score']:.1f}%</div>
                <h2>Gate Results</h2>
                {''.join([f'<div class="gate {gate["status"].lower()}"><strong>{gate["name"]}</strong>: {gate["status"]} ({gate["score"]:.1f}%)</div>' for gate in result["gates"]])}
                <h2>Recommendations</h2>
                <ul>
                    {''.join([f'<li>{rec}</li>' for rec in result.get("recommendations", [])])}
                </ul>
                {comments_html}
            </body>
            </html>
            """
            
            # Save basic report to file as well
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(basic_html)
            
            # Update scan result with report file path
            if not parsed_comments:
                scan_results[scan_id]["report_file"] = str(report_path)
            
            return HTMLResponse(content=basic_html, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.post("/reports/{scan_id}/comments")
async def update_report_comments(scan_id: str, comments: Dict[str, str]):
    """Update report comments and regenerate HTML"""
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        result = scan_results[scan_id]
        
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Scan not completed yet")
        
        # Store comments with scan result
        scan_results[scan_id]["comments"] = comments
        
        # Get the validation result for regeneration
        validation_result = result.get("result_object")
        if not validation_result:
            raise HTTPException(status_code=500, detail="Report data not available for regeneration")
        
        try:
            from codegates.reports import ReportGenerator
            from codegates.models import ReportConfig
            
            # Create reports directory
            reports_dir_path = get_reports_directory()
            reports_dir = Path(reports_dir_path)
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate HTML with comments
            report_config = ReportConfig(
                format='html',
                output_path=str(reports_dir),
                include_details=True,
                include_recommendations=True
            )
            
            generator = ReportGenerator(report_config)
            html_content = generator._generate_html_content(validation_result, comments)
            
            # Save updated HTML file with comments
            comments_hash = hashlib.md5(json.dumps(comments, sort_keys=True).encode()).hexdigest()[:8]
            report_filename = f"hard_gate_report_{scan_id}_{comments_hash}.html"
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 HTML report with comments saved to: {report_path}")
            
            return {
                "status": "success", 
                "message": f"Comments updated and report regenerated with {len(comments)} comments",
                "report_url": f"{get_reports_url_base()}/{scan_id}",
                "comments_count": len(comments)
            }
            
        except ImportError:
            # Fallback if report generator not available
            return {
                "status": "success", 
                "message": f"Comments stored (fallback mode) - {len(comments)} comments",
                "comments_count": len(comments)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/reports")
async def list_reports():
    """List all available saved reports."""
    try:
        reports_dir = Path(get_reports_directory())
        
        if not reports_dir.exists():
            return {"reports": []}
        
        reports = []
        for report_file in reports_dir.glob("hard_gate_report_*.html"):
            try:
                # Extract scan_id from filename
                scan_id = report_file.stem.replace("hard_gate_report_", "")
                
                # Get file stats
                stat = report_file.stat()
                
                # Check if we have scan result data
                scan_data = scan_results.get(scan_id, {})
                
                reports.append({
                    "scan_id": scan_id,
                    "filename": report_file.name,
                    "file_size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "score": scan_data.get("score"),
                    "status": scan_data.get("status", "unknown"),
                    "report_url": f"{get_reports_url_base()}/{scan_id}"
                })
                
            except Exception as e:
                print(f"⚠️ Error processing report file {report_file}: {e}")
                continue
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "reports": reports,
            "total_count": len(reports)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/jira/status")
async def get_jira_status():
    """Get JIRA integration status and configuration."""
    try:
        if not JIRA_AVAILABLE:
            return {
                "available": False,
                "message": "JIRA integration module not available"
            }
        
        jira_integration = JiraIntegration()
        connection_test = jira_integration.test_connection()
        
        return {
            "available": JIRA_AVAILABLE,
            "enabled": jira_integration.is_available(),
            "configuration": {
                "jira_url": jira_integration.jira_url if jira_integration.enabled else None,
                "username": jira_integration.username if jira_integration.enabled else None,
                "comment_format": jira_integration.comment_format if jira_integration.enabled else None,
            },
            "connection_test": connection_test
        }
        
    except Exception as e:
        return {
            "available": JIRA_AVAILABLE,
            "enabled": False,
            "error": str(e)
        }

class JiraPostRequest(BaseModel):
    scan_id: str = Field(..., description="Scan ID to post to JIRA")
    issue_key: str = Field(..., description="JIRA issue key (e.g., PROJECT-123)")
    comment_format: Optional[str] = Field(default="markdown", description="Comment format: 'markdown' or 'text'")
    include_details: Optional[bool] = Field(default=True, description="Include detailed gate results")
    include_recommendations: Optional[bool] = Field(default=True, description="Include recommendations")
    attach_html_report: Optional[bool] = Field(
        default=True,  # Changed to True to enable by default
        description="Attach HTML report to JIRA issue"
    )

@api_v1.post("/jira/post")
async def post_to_jira(request: JiraPostRequest):
    """Manually post a scan report to JIRA."""
    try:
        if not JIRA_AVAILABLE:
            raise HTTPException(status_code=500, detail="JIRA integration not available")
        
        # Check if scan exists
        if request.scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        result = scan_results[request.scan_id]
        
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Scan not completed yet")
        
        validation_result = result.get("result_object")
        if not validation_result:
            raise HTTPException(status_code=500, detail="Scan result data not available")
        
        # Create JIRA integration with custom config
        jira_config = {
            'comment_format': request.comment_format,
            'include_details': request.include_details,
            'include_recommendations': request.include_recommendations,
            'attach_html_report': request.attach_html_report
        }
        
        jira_integration = JiraIntegration(jira_config)
        
        if not jira_integration.is_available():
            raise HTTPException(status_code=500, detail="JIRA integration not properly configured")
        
        # Prepare additional context
        additional_context = {
            'scan_id': request.scan_id,
            'report_url': f"{API_BASE_URL}{API_VERSION_PREFIX}/reports/{request.scan_id}"
        }
        
        # Get HTML report path if available
        html_report_path = result.get("report_file")
        
        # Post to JIRA
        jira_result = jira_integration.post_report_comment(
            validation_result,
            request.issue_key,
            additional_context,
            html_report_path
        )
        
        return jira_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/system/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of all temporary directories."""
    try:
        # Clean up all registered temp directories
        await cleanup_all_temp_directories()
        
        # Clean up orphaned directories
        cleanup_orphaned_temp_directories()
        
        return {
            "status": "success",
            "message": "Cleanup completed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cleanup failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@api_v1.get("/system/temp-status")
async def get_temp_directory_status():
    """Get status of temporary directories."""
    try:
        temp_status = {
            "registered_directories": len(_TEMP_DIRECTORIES),
            "directories": list(_TEMP_DIRECTORIES),
            "orphaned_check": {}
        }
        
        # Check for orphaned directories
        temp_base_options = [
            os.environ.get('TEMP_REPO_DIR'),
            os.environ.get('TMPDIR'),
            '/tmp',
            './temp'
        ]
        
        for temp_base in temp_base_options:
            if not temp_base or not os.path.exists(temp_base):
                continue
            
            try:
                orphaned_dirs = []
                for item in os.listdir(temp_base):
                    if item.startswith('mygates_'):
                        orphaned_path = os.path.join(temp_base, item)
                        if os.path.isdir(orphaned_path):
                            stat = os.stat(orphaned_path)
                            age_hours = (time.time() - stat.st_mtime) / 3600
                            orphaned_dirs.append({
                                "path": orphaned_path,
                                "age_hours": round(age_hours, 2),
                                "size_mb": round(sum(os.path.getsize(os.path.join(dirpath, filename)) 
                                                   for dirpath, dirnames, filenames in os.walk(orphaned_path) 
                                                   for filename in filenames) / (1024*1024), 2)
                            })
                
                temp_status["orphaned_check"][temp_base] = orphaned_dirs
                
            except (OSError, PermissionError) as e:
                temp_status["orphaned_check"][temp_base] = f"Access denied: {e}"
        
        return temp_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SSL Configuration
def get_ssl_config():
    """Get SSL configuration from environment"""
    try:
        from codegates.utils.config_loader import get_config
        config = get_config()
        return config.get_ssl_config()
    except Exception:
        # Fallback to environment variables
        return {
            'verify_ssl': os.getenv('CODEGATES_SSL_VERIFY', 'true').lower() == 'true',
            'ca_bundle': os.getenv('CODEGATES_SSL_CA_BUNDLE'),
            'client_cert': os.getenv('CODEGATES_SSL_CLIENT_CERT'),
            'client_key': os.getenv('CODEGATES_SSL_CLIENT_KEY'),
            'disable_warnings': os.getenv('CODEGATES_SSL_DISABLE_WARNINGS', 'false').lower() == 'true'
        }

# Get SSL configuration at startup
_SSL_CONFIG = get_ssl_config()

# Configure SSL warnings
if _SSL_CONFIG.get('disable_warnings', False):
    urllib3.disable_warnings(InsecureRequestWarning)
    print("⚠️ SSL certificate warnings disabled")

def get_requests_session(verify_ssl: Optional[bool] = None) -> requests.Session:
    """
    Create a requests session with proper SSL configuration for GitHub Enterprise
    
    Args:
        verify_ssl: Override SSL verification setting
    """
    session = requests.Session()
    
    # Determine SSL verification setting
    if verify_ssl is not None:
        ssl_verify = verify_ssl
    else:
        ssl_verify = _SSL_CONFIG.get('verify_ssl', True)
    
    # Configure SSL verification
    if not ssl_verify:
        session.verify = False
        print("⚠️ SSL certificate verification disabled")
    elif _SSL_CONFIG.get('ca_bundle'):
        session.verify = _SSL_CONFIG['ca_bundle']
        print(f"🔒 Using custom CA bundle: {_SSL_CONFIG['ca_bundle']}")
    else:
        session.verify = True
    
    # Configure client certificates (for mutual TLS)
    if _SSL_CONFIG.get('client_cert') and _SSL_CONFIG.get('client_key'):
        session.cert = (_SSL_CONFIG['client_cert'], _SSL_CONFIG['client_key'])
        print(f"🔒 Using client certificate: {_SSL_CONFIG['client_cert']}")
    elif _SSL_CONFIG.get('client_cert'):
        session.cert = _SSL_CONFIG['client_cert']
        print(f"🔒 Using client certificate: {_SSL_CONFIG['client_cert']}")
    
    # Set appropriate headers
    session.headers.update({
        'User-Agent': 'MyGates/1.0.0 (GitHub Enterprise Client)',
        'Accept': 'application/vnd.github.v3+json'
    })
    
    return session

def configure_git_ssl_settings():
    """Configure git SSL settings for GitHub Enterprise"""
    try:
        ssl_config = _SSL_CONFIG
        
        if not ssl_config.get('verify_ssl', True):
            # Disable SSL verification for git
            print("🔧 Configuring git to skip SSL verification...")
            os.environ['GIT_SSL_NO_VERIFY'] = '1'
            
            # Also set git config for the current session
            subprocess.run(['git', 'config', '--global', 'http.sslVerify', 'false'], 
                         capture_output=True, text=True)
        else:
            # Ensure SSL verification is enabled
            os.environ.pop('GIT_SSL_NO_VERIFY', None)
            
            # Configure custom CA bundle if provided
            if ssl_config.get('ca_bundle'):
                os.environ['GIT_SSL_CAINFO'] = ssl_config['ca_bundle']
                subprocess.run(['git', 'config', '--global', 'http.sslCAInfo', ssl_config['ca_bundle']], 
                             capture_output=True, text=True)
                print(f"🔒 Configured git to use CA bundle: {ssl_config['ca_bundle']}")
        
        print("✅ Git SSL configuration applied")
        
    except Exception as e:
        print(f"⚠️ Failed to configure git SSL settings: {e}")

# Configure git SSL settings at startup
configure_git_ssl_settings()

# Mount the v1 API router
app.mount("/api/v1", api_v1)

def start_server():
    uvicorn.run(app, host=API_HOST, port=API_PORT)

def create_unique_temp_directory(prefix: str, description: str = "temporary directory") -> str:
    """
    Create a unique temporary directory with better uniqueness guarantees
    
    Args:
        prefix: Prefix for the directory name
        description: Description for logging
        
    Returns:
        Path to the created temporary directory
        
    Raises:
        Exception: If no writable temporary directory can be created
    """
    # Add more uniqueness to prevent collisions
    timestamp = int(time.time() * 1000000)  # microsecond precision
    pid = os.getpid()
    unique_id = f"{timestamp}_{pid}"
    
    temp_base_options = [
        os.environ.get('TEMP_REPO_DIR'),
        os.environ.get('TMPDIR'),
        '/tmp',
        './temp',
        '.'
    ]
    
    for temp_base in temp_base_options:
        if not temp_base:
            continue
            
        try:
            os.makedirs(temp_base, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(temp_base, f'.write_test_{pid}')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            # Try multiple attempts to create unique directory
            for attempt in range(5):
                try:
                    full_prefix = f"{prefix}{unique_id}_{attempt}_"
                    temp_dir = tempfile.mkdtemp(prefix=full_prefix, dir=temp_base)
                    
                    # Double-check the directory is actually empty and writable
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        register_temp_directory(temp_dir)
                        print(f"📁 Created unique {description}: {temp_dir}")
                        return temp_dir
                    else:
                        # Directory exists but not empty, try cleanup and retry
                        try:
                            if os.path.exists(temp_dir):
                                shutil.rmtree(temp_dir, ignore_errors=True)
                        except Exception:
                            pass
                        continue
                        
                except (OSError, FileExistsError) as e:
                    print(f"⚠️ Attempt {attempt + 1} failed for {temp_base}: {e}")
                    if attempt == 4:  # Last attempt
                        break
                    time.sleep(0.1)  # Brief pause before retry
                    continue
            
        except (OSError, PermissionError) as e:
            print(f"⚠️ Cannot use {temp_base} for {description}: {e}")
            continue
    
    raise Exception(f"No writable location found for {description}. All temporary directory creation attempts failed.")

def safe_extract_archive(archive_content: bytes, temp_dir: str) -> str:
    """
    Safely extract a ZIP archive with robust error handling
    
    Args:
        archive_content: ZIP file content as bytes
        temp_dir: Target directory for extraction
        
    Returns:
        Path to the extracted repository content
        
    Raises:
        Exception: If extraction fails
    """
    try:
        with zipfile.ZipFile(io.BytesIO(archive_content)) as zip_ref:
            # List all files first to check structure
            file_list = zip_ref.namelist()
            if not file_list:
                raise Exception("Archive is empty")
            
            print(f"📦 Archive contains {len(file_list)} files")
            
            # Extract all files
            zip_ref.extractall(temp_dir)
            
            # GitHub creates a folder with format: owner-repo-commit_hash
            extracted_items = [item for item in os.listdir(temp_dir) if not item.startswith('.')]
            
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_items[0])):
                extracted_folder = os.path.join(temp_dir, extracted_items[0])
                
                print(f"📁 Moving contents from wrapper folder: {extracted_folder}")
                
                # Move contents to temp_dir root with better error handling
                try:
                    # Use os.walk to handle all files including hidden ones
                    for root, dirs, files in os.walk(extracted_folder):
                        # Calculate relative path from extracted_folder
                        rel_path = os.path.relpath(root, extracted_folder)
                        if rel_path == '.':
                            target_root = temp_dir
                        else:
                            target_root = os.path.join(temp_dir, rel_path)
                            os.makedirs(target_root, exist_ok=True)
                        
                        # Move all files in this directory
                        for file in files:
                            source_file = os.path.join(root, file)
                            target_file = os.path.join(target_root, file)
                            
                            # Handle existing files
                            if os.path.exists(target_file):
                                print(f"⚠️ Destination already exists, removing: {target_file}")
                                try:
                                    os.remove(target_file)
                                except OSError:
                                    pass
                            
                            # Move the file
                            try:
                                shutil.move(source_file, target_file)
                                print(f"✅ Moved: {os.path.relpath(target_file, temp_dir)}")
                            except Exception as move_error:
                                print(f"⚠️ Failed to move {file}: {move_error}")
                                # Try copy as fallback
                                try:
                                    shutil.copy2(source_file, target_file)
                                    os.remove(source_file)
                                    print(f"✅ Copied: {os.path.relpath(target_file, temp_dir)}")
                                except Exception as copy_error:
                                    print(f"❌ Failed to copy {file}: {copy_error}")
                    
                    # Remove the wrapper folder more robustly
                    try:
                        # First try simple rmdir
                        os.rmdir(extracted_folder)
                        print(f"✅ Removed wrapper folder: {extracted_folder}")
                    except OSError as e:
                        print(f"⚠️ Simple rmdir failed: {e}")
                        # Try more aggressive cleanup
                        try:
                            # Remove any remaining files/folders recursively
                            for root, dirs, files in os.walk(extracted_folder, topdown=False):
                                # Remove files first
                                for file in files:
                                    try:
                                        file_path = os.path.join(root, file)
                                        os.chmod(file_path, 0o777)
                                        os.remove(file_path)
                                    except Exception:
                                        pass
                                # Then remove directories
                                for dir in dirs:
                                    try:
                                        dir_path = os.path.join(root, dir)
                                        os.chmod(dir_path, 0o777)
                                        os.rmdir(dir_path)
                                    except Exception:
                                        pass
                            # Finally remove the root
                            os.rmdir(extracted_folder)
                            print(f"✅ Force-removed wrapper folder: {extracted_folder}")
                        except Exception as cleanup_error:
                            print(f"⚠️ Could not remove wrapper folder {extracted_folder}: {cleanup_error}")
                            # This is not critical - the content is extracted
                
                except Exception as extract_error:
                    print(f"⚠️ Error during content extraction: {extract_error}")
                    # Continue anyway - the files might still be usable
                
                print(f"✅ Repository extracted successfully to {temp_dir}")
                return temp_dir
            else:
                # Archive doesn't have the expected structure, but that's okay
                print(f"✅ Repository extracted directly to {temp_dir}")
                return temp_dir
                
    except zipfile.BadZipFile as e:
        raise Exception(f"Invalid ZIP archive: {e}")
    except Exception as e:
        raise Exception(f"Failed to extract repository archive: {e}")

def get_reports_directory() -> str:
    """
    Get the configured reports directory path with container-friendly fallbacks
    
    Returns:
        str: Path to the reports directory
    """
    try:
        # Use the globally configured reports directory
        return ensure_writable_directory(REPORTS_DIR, "reports directory")
    except Exception as e:
        print(f"⚠️ Cannot use configured reports directory '{REPORTS_DIR}': {e}")
        # Fallback to hardcoded default
        return get_reports_directory()

def get_reports_url_base() -> str:
    """
    Get the configured reports URL base
    
    Returns:
        str: Base URL for reports
    """
    try:
        return REPORTS_URL_BASE
    except NameError:
        # Fallback if not configured
        return f"{API_BASE_URL}{API_VERSION_PREFIX}/reports"

def get_timeout_value(timeout_name: str, scan_options: Optional[ScanOptions] = None) -> int:
    """
    Get timeout value with optional per-request override
    
    Args:
        timeout_name: Name of the timeout from TIMEOUT_CONFIG
        scan_options: Optional scan options with timeout overrides
        
    Returns:
        int: Timeout value in seconds
    """
    # Check for per-request override first
    if scan_options:
        override_value = getattr(scan_options, timeout_name, None)
        if override_value is not None:
            print(f"🕒 Using custom {timeout_name}: {override_value}s (overridden via API)")
            return override_value
    
    # Fall back to global configuration
    global_value = TIMEOUT_CONFIG.get(timeout_name, 30)  # 30s default fallback
    return global_value

def get_git_clone_timeout(scan_options: Optional[ScanOptions] = None) -> int:
    """Get git clone timeout with optional override"""
    return get_timeout_value('git_clone_timeout', scan_options)

def get_api_download_timeout(scan_options: Optional[ScanOptions] = None) -> int:
    """Get API download timeout with optional override"""
    return get_timeout_value('api_download_timeout', scan_options)

def get_analysis_timeout(scan_options: Optional[ScanOptions] = None) -> int:
    """Get analysis timeout with optional override"""
    return get_timeout_value('analysis_timeout', scan_options)

def get_llm_request_timeout(scan_options: Optional[ScanOptions] = None) -> int:
    """Get LLM request timeout with optional override"""
    return get_timeout_value('llm_request_timeout', scan_options)

@api_v1.get("/system/timeout-config")
async def get_timeout_configuration():
    """Get current timeout configuration."""
    try:
        return {
            "status": "success",
            "timeout_config": TIMEOUT_CONFIG,
            "description": {
                "git_clone_timeout": "Git clone operation timeout (seconds)",
                "git_ls_remote_timeout": "Git repository access test timeout (seconds)",
                "api_download_timeout": "GitHub API download timeout (seconds)",
                "analysis_timeout": "Code analysis timeout (seconds)",
                "llm_request_timeout": "LLM request timeout (seconds)",
                "http_request_timeout": "General HTTP request timeout (seconds)",
                "health_check_timeout": "Health check timeout (seconds)",
                "jira_request_timeout": "JIRA API request timeout (seconds)",
                "jira_health_timeout": "JIRA health check timeout (seconds)",
                "github_connect_timeout": "GitHub connection timeout (seconds)",
                "github_read_timeout": "GitHub read timeout (seconds)",
                "vscode_api_timeout": "VS Code extension API timeout (seconds)",
                "llm_batch_timeout": "LLM batch processing timeout (seconds)"
            },
            "override_info": {
                "message": "These values can be overridden per scan request using scan_options",
                "available_overrides": [
                    "git_clone_timeout",
                    "api_download_timeout", 
                    "analysis_timeout",
                    "llm_request_timeout"
                ]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get timeout configuration: {str(e)}"
        }

# Intake Assessment Models
class ComponentData(BaseModel):
    """Structured component data extracted from Excel or other sources"""
    component_name: str = Field(..., description="Name of the component being assessed")
    business_criticality: Optional[str] = Field(None, description="Business criticality (High/Medium/Low)")
    current_environment: Optional[str] = Field(None, description="Current hosting environment")
    application_type: Optional[str] = Field(None, description="Type of application")
    technology_stack: Optional[Dict[str, Any]] = Field(None, description="Technology stack details")
    dependencies: Optional[List[str]] = Field(None, description="List of dependencies")
    component_declarations: Optional[Dict[str, bool]] = Field(None, description="Component declarations (Yes/No for each component)")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Additional custom fields from Excel")

class IntakeAssessmentOptions(BaseModel):
    include_patterns: Optional[List[str]] = Field(
        default=[
            "*.py", "*.js", "*.ts", "*.java", "*.go", "*.rb", "*.php",
            "*.cpp", "*.h", "*.hpp", "*.c", "*.cs", "*.swift",
            "*.yaml", "*.yml", "*.json", "*.xml", "*.html", "*.css",
            "Dockerfile", "docker-compose*.yml", "*.sh", "*.bash",
            "*.md", "*.rst", "*.txt"
        ],
        description="File patterns to include in analysis"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=[
            "tests/*", "test/*", "docs/*", "node_modules/*", "__pycache__/*",
            "*.test.*", "*.spec.*", "*.min.*", "dist/*", "build/*",
            ".git/*", ".github/*", ".vscode/*", "*.log"
        ],
        description="File patterns to exclude from analysis"
    )
    max_file_size: Optional[int] = Field(
        default=100000,
        description="Maximum file size in bytes to analyze"
    )
    use_cache: Optional[bool] = Field(
        default=True,
        description="Enable LLM response caching"
    )
    include_jira: Optional[bool] = Field(
        default=False,
        description="Include JIRA stories in assessment"
    )

class IntakeAssessmentRequest(BaseModel):
    # Code analysis sources (at least one required)
    repository_url: Optional[str] = Field(
        None,
        description="Git repository URL for code analysis"
    )
    local_directory: Optional[str] = Field(
        None,
        description="Local directory path for code analysis"
    )
    
    # Component data (structured information)
    component_data: Optional[ComponentData] = Field(
        None,
        description="Structured component information (extracted from Excel or other sources)"
    )
    
    # Authentication and configuration
    github_token: Optional[str] = Field(
        None,
        description="GitHub token for private repositories"
    )
    options: Optional[IntakeAssessmentOptions] = Field(
        default=None,
        description="Assessment configuration options"
    )
    
    def validate_input(self):
        """Validate that at least a repository or local directory is provided"""
        if not self.repository_url and not self.local_directory:
            raise HTTPException(
                status_code=400,
                detail="Either repository_url or local_directory must be provided for code analysis"
            )

class IntakeAssessmentResult(BaseModel):
    assessment_id: str = Field(..., description="Unique assessment identifier")
    status: str = Field(..., description="Assessment status: 'completed' | 'failed' | 'running'")
    component_name: Optional[str] = Field(None, description="Assessed component name")
    migration_score: Optional[float] = Field(None, ge=0, le=100, description="Migration readiness score (0-100)")
    migration_feasibility: Optional[str] = Field(None, description="Migration feasibility rating")
    reports: Optional[Dict[str, str]] = Field(None, description="Generated report file paths")
    recommendations: Optional[List[str]] = Field(None, description="Migration recommendations")
    component_analysis: Optional[Dict[str, Any]] = Field(None, description="Component analysis results")
    error_message: Optional[str] = Field(None, description="Error message if assessment failed")

# In-memory storage for intake assessment results (in production, use a database)
intake_results = {}

async def perform_intake_assessment(assessment_id: str, request: IntakeAssessmentRequest):
    """Perform the actual intake assessment with comprehensive error handling"""
    temp_dir = None
    try:
        # Update status to running
        intake_results[assessment_id]["status"] = "running"
        intake_results[assessment_id]["message"] = "Starting intake assessment..."
        
        # Validate input
        request.validate_input()
        
        # Get options with defaults
        options = request.options or IntakeAssessmentOptions()
        
        # Create unique temporary directory for assessment outputs
        temp_dir = create_unique_temp_directory("intake_assessment_", "intake assessment directory")
        register_temp_directory(temp_dir)
        
        # Initialize shared state for intake assessment
        shared = {
            "repo_url": request.repository_url,
            "local_dir": request.local_directory,
            "include_patterns": options.include_patterns,
            "exclude_patterns": options.exclude_patterns,
            "max_file_size": options.max_file_size,
            "use_cache": options.use_cache,
            "output_dir": temp_dir,
            "github_token": request.github_token
        }
        
        # Add component data if provided (structured approach)
        if request.component_data:
            # Convert ComponentData to the format expected by intake module
            excel_validation = {
                "component_name": request.component_data.component_name,
                "business_criticality": request.component_data.business_criticality or "Medium",
                "current_environment": request.component_data.current_environment or "Unknown",
                "application_type": request.component_data.application_type or "Unknown"
            }
            
            # Add any custom fields
            if request.component_data.custom_fields:
                excel_validation.update(request.component_data.custom_fields)
            
            # Set excel validation data in shared state
            shared["excel_validation"] = excel_validation
            shared["project_name"] = request.component_data.component_name
            
            # Add component declarations if provided
            if request.component_data.component_declarations:
                excel_components = {}
                for component, declared in request.component_data.component_declarations.items():
                    excel_components[component] = {"is_yes": declared}
                shared["excel_components"] = excel_components
            
            # Add technology stack and dependencies
            if request.component_data.technology_stack:
                shared["technology_stack"] = request.component_data.technology_stack
            
            if request.component_data.dependencies:
                shared["dependencies"] = request.component_data.dependencies
        
        print(f"🔄 Starting intake assessment for: {request.repository_url or request.local_directory or (request.component_data.component_name if request.component_data else 'Unknown')}")
        
        # Choose appropriate flow based on input type
        if request.component_data and not request.repository_url and not request.local_directory:
            # Pure component data assessment (no code analysis)
            intake_results[assessment_id]["message"] = "Processing component data..."
            analysis_flow = create_analysis_flow()  # Use analysis flow with only OCP assessment
        elif request.component_data:
            # Combined code + component data assessment  
            intake_results[assessment_id]["message"] = "Analyzing repository with component data..."
            analysis_flow = create_analysis_flow()  # Use analysis flow with code + OCP assessment
        else:
            # Code-only assessment
            intake_results[assessment_id]["message"] = "Analyzing repository..."
            analysis_flow = create_analysis_flow()
        
        # Run the intake assessment flow
        intake_results[assessment_id]["message"] = "Running OCP migration assessment..."
        
        # Execute the flow in a thread to avoid blocking
        await asyncio.to_thread(analysis_flow.run, shared)
        
        # Extract results from shared state
        ocp_assessment = shared.get("ocp_assessment", {})
        component_name = shared.get("project_name") or (request.component_data.component_name if request.component_data else "Unknown Component")
        
        # Parse migration score from assessment
        migration_score = 0.0
        migration_feasibility = "Unknown"
        recommendations = []
        
        if ocp_assessment:
            # Try to extract score from HTML content
            html_content = ocp_assessment.get("html", "")
            if "migration_score" in html_content.lower():
                # Simple regex to extract score (this could be enhanced)
                import re
                score_match = re.search(r'score[:\s]*(\d+(?:\.\d+)?)', html_content, re.IGNORECASE)
                if score_match:
                    migration_score = float(score_match.group(1))
            
            # Determine feasibility based on score
            if migration_score >= 90:
                migration_feasibility = "Excellent"
            elif migration_score >= 80:
                migration_feasibility = "Good"
            elif migration_score >= 70:
                migration_feasibility = "Fair"
            elif migration_score >= 60:
                migration_feasibility = "Marginal"
            else:
                migration_feasibility = "Poor"
        
        # Collect generated reports
        reports = {}
        if "hard_gate_assessment" in shared:
            reports["hard_gate_assessment"] = shared["hard_gate_assessment"]
        if "intake_assessment_html" in shared:
            reports["intake_assessment"] = shared["intake_assessment_html"]
        if ocp_assessment:
            reports["ocp_assessment"] = ocp_assessment
        
        # Get component analysis if available
        component_analysis = shared.get("code_analysis", {}).get("component_analysis", {})
        
        # Update final results
        intake_results[assessment_id].update({
            "status": "completed",
            "component_name": component_name,
            "migration_score": migration_score,
            "migration_feasibility": migration_feasibility,
            "reports": reports,
            "recommendations": recommendations,
            "component_analysis": component_analysis,
            "message": f"Intake assessment completed successfully for {component_name}",
            "completed_at": datetime.now().isoformat()
        })
        
        print(f"✅ Intake assessment completed for {component_name} with score: {migration_score}")
        
    except Exception as e:
        print(f"❌ Intake assessment failed for {assessment_id}: {str(e)}")
        
        # Update status with error
        intake_results[assessment_id].update({
            "status": "failed",
            "error_message": str(e),
            "message": f"Intake assessment failed: {str(e)}",
            "completed_at": datetime.now().isoformat()
        })
        
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            print(f"🧹 Cleaning up intake assessment directory: {temp_dir}")
            try:
                cleanup_success = await cleanup_temp_directory(temp_dir, "intake assessment directory")
                if cleanup_success:
                    print(f"✅ Intake assessment directory cleaned up successfully")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup intake assessment directory: {cleanup_error}")

## Intake Assessment API Endpoints

@api_v1.get("/intake/status")
async def get_intake_status():
    """Get intake assessment module status and configuration."""
    try:
        if not INTAKE_AVAILABLE:
            return {
                "available": False,
                "message": "Intake assessment module not available"
            }
        
        return {
            "available": INTAKE_AVAILABLE,
            "module": "OCP Migration Assessment",
            "description": "OpenShift Container Platform migration readiness assessment",
            "supported_inputs": [
                "GitHub repositories",
                "Local directories", 
                "Excel files with component data"
            ],
            "assessment_types": [
                "Hard Gate Assessment",
                "Intake Assessment", 
                "Migration Insights",
                "Component Analysis"
            ]
        }
        
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

@api_v1.post("/intake/assess", response_model=IntakeAssessmentResult)
async def start_intake_assessment(request: IntakeAssessmentRequest, background_tasks: BackgroundTasks):
    """
    Start an intake assessment for OCP migration readiness.
    
    - Supports GitHub repositories, local directories, and Excel files
    - Generates comprehensive migration assessment reports
    - Returns assessment ID for status tracking
    """
    try:
        if not INTAKE_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Intake assessment module not available"
            )
        
        # Validate input
        request.validate_input()
        
        # Generate assessment ID
        assessment_id = str(uuid.uuid4())
        
        # Initialize assessment result
        intake_results[assessment_id] = {
            "assessment_id": assessment_id,
            "status": "running",
            "component_name": None,
            "migration_score": None,
            "migration_feasibility": None,
            "reports": None,
            "recommendations": None,
            "component_analysis": None,
            "error_message": None,
            "message": "Assessment initiated",
            "created_at": datetime.now().isoformat()
        }
        
        # Start background assessment
        background_tasks.add_task(perform_intake_assessment, assessment_id, request)
        
        return IntakeAssessmentResult(
            assessment_id=assessment_id,
            status="running",
            component_name=None,
            migration_score=None,
            migration_feasibility=None,
            reports=None,
            recommendations=None,
            component_analysis=None,
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/intake/assess/{assessment_id}/status", response_model=IntakeAssessmentResult)
async def get_intake_assessment_status(assessment_id: str):
    """Get the status and results of a specific intake assessment."""
    try:
        if assessment_id not in intake_results:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        result = intake_results[assessment_id]
        
        return IntakeAssessmentResult(
            assessment_id=result["assessment_id"],
            status=result["status"],
            component_name=result.get("component_name"),
            migration_score=result.get("migration_score"),
            migration_feasibility=result.get("migration_feasibility"),
            reports=result.get("reports"),
            recommendations=result.get("recommendations"),
            component_analysis=result.get("component_analysis"),
            error_message=result.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/intake/assess/{assessment_id}/reports/{report_type}")
async def get_intake_assessment_report(assessment_id: str, report_type: str):
    """Get a specific report from an intake assessment."""
    try:
        if assessment_id not in intake_results:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        result = intake_results[assessment_id]
        
        if result["status"] != "completed":
            raise HTTPException(status_code=400, detail="Assessment not completed yet")
        
        reports = result.get("reports", {})
        if report_type not in reports:
            available_reports = list(reports.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Report type '{report_type}' not found. Available reports: {available_reports}"
            )
        
        report_data = reports[report_type]
        
        # If it's HTML content, return as HTMLResponse
        if "html" in report_data and report_type in ["ocp_assessment", "intake_assessment"]:
            html_content = report_data.get("html", "")
            if html_content:
                return HTMLResponse(content=html_content, status_code=200)
        
        # For other report types, return JSON
        return report_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/intake/assessments")
async def list_intake_assessments():
    """List all intake assessments with their current status."""
    try:
        assessments = []
        for assessment_id, result in intake_results.items():
            assessments.append({
                "assessment_id": assessment_id,
                "status": result["status"],
                "component_name": result.get("component_name"),
                "migration_score": result.get("migration_score"),
                "migration_feasibility": result.get("migration_feasibility"),
                "created_at": result.get("created_at"),
                "completed_at": result.get("completed_at"),
                "reports_available": list(result.get("reports", {}).keys()) if result.get("reports") else []
            })
        
        # Sort by creation time (newest first)
        assessments.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "assessments": assessments,
            "total_count": len(assessments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ExcelExtractionRequest(BaseModel):
    excel_file_path: str = Field(..., description="Path to Excel file to extract data from")
    sheet_name: Optional[str] = Field(None, description="Specific sheet name to process (optional)")

@api_v1.post("/intake/extract-excel")
async def extract_excel_data(request: ExcelExtractionRequest):
    """
    Extract structured component data from Excel files.
    
    This utility endpoint separates data extraction from assessment logic,
    allowing the extracted data to be used with the intake assessment endpoint.
    """
    try:
        if not INTAKE_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Intake assessment module not available"
            )
        
        # Check if file exists
        if not os.path.exists(request.excel_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Excel file not found: {request.excel_file_path}"
            )
        
        # Extract data using intake module's Excel processor
        try:
            # Use the intake module's Excel processing logic
            shared = {
                "excel_file": request.excel_file_path,
                "output_dir": "./temp",  # Temporary directory for processing
            }
            
            if request.sheet_name:
                shared["sheet_name"] = request.sheet_name
            
            # Create and run the Excel processor node
            from nodes import ProcessExcel
            excel_processor = ProcessExcel()
            
            # Process the Excel file
            prep_result = excel_processor.prep(shared)
            exec_result = excel_processor.exec(prep_result)
            excel_processor.post(shared, prep_result, exec_result)
            
            # Extract the processed data
            excel_validation = shared.get("excel_validation", {})
            excel_components = shared.get("excel_components", {})
            
            # Convert to ComponentData format
            component_declarations = {}
            if excel_components:
                for component, data in excel_components.items():
                    component_declarations[component] = data.get("is_yes", False)
            
            # Build structured component data
            component_data = ComponentData(
                component_name=excel_validation.get("component_name", "Unknown Component"),
                business_criticality=excel_validation.get("business_criticality"),
                current_environment=excel_validation.get("current_environment"),
                application_type=excel_validation.get("application_type"),
                component_declarations=component_declarations if component_declarations else None,
                custom_fields=excel_validation  # Include all Excel data as custom fields
            )
            
            return {
                "status": "success",
                "component_data": component_data,
                "extracted_fields": list(excel_validation.keys()),
                "component_declarations_count": len(component_declarations),
                "message": f"Successfully extracted data for component: {component_data.component_name}"
            }
            
        except Exception as processing_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process Excel file: {str(processing_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    start_server() 
