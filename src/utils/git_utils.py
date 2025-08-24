"""
Git utilities for repository operations
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from models.scan_models import RepositoryInfo


class GitUtils:
    """Git operations utility"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "codegates_scan"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def clone_repository(self, repo_url: str, branch: str = "main", 
                             git_token: Optional[str] = None) -> str:
        """Clone repository to temporary directory"""
        try:
            # Create unique directory for this clone
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            clone_dir = self.temp_dir / f"{repo_name}_{timestamp}"
            
            # Clear proxy environment for git operations
            env = os.environ.copy()
            env.pop('HTTP_PROXY', None)
            env.pop('HTTPS_PROXY', None)
            env.pop('NO_PROXY', None)
            
            # Prepare git command - try with branch first, then fallback to default
            if git_token and "github.com" in repo_url:
                # Use token for GitHub
                auth_url = repo_url.replace("https://", f"https://{git_token}@")
                cmd = ["git", "clone", "-b", branch, auth_url, str(clone_dir)]
            else:
                cmd = ["git", "clone", "-b", branch, repo_url, str(clone_dir)]
            
            # Execute clone with branch
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
            
            # If branch fails, try without branch (use default)
            if result.returncode != 0 and "Remote branch" in result.stderr:
                print(f"⚠️ Branch '{branch}' not found, trying default branch")
                if git_token and "github.com" in repo_url:
                    auth_url = repo_url.replace("https://", f"https://{git_token}@")
                    cmd = ["git", "clone", auth_url, str(clone_dir)]
                else:
                    cmd = ["git", "clone", repo_url, str(clone_dir)]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            print(f"✅ Repository cloned to: {clone_dir}")
            return str(clone_dir)
            
        except Exception as e:
            print(f"❌ Repository clone failed: {e}")
            raise
    
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
