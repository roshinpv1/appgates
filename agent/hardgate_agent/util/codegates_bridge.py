"""
CodeGates Bridge Utilities
Standardizes cloning and cleanup to match gates/utils behavior for agent tools.
"""

import os
import tempfile
import shutil
import subprocess
from typing import Optional, Tuple

try:
    from gates.utils.git_operations import clone_repository as cg_clone_repository  # type: ignore
    from gates.utils.git_operations import cleanup_repository as cg_cleanup_repository  # type: ignore
    HAS_CG_GIT = True
except Exception:
    cg_clone_repository = None
    cg_cleanup_repository = None
    HAS_CG_GIT = False


def ensure_local_repo(repository_path: Optional[str] = None,
                      repository_url: Optional[str] = None,
                      branch: str = "main",
                      github_token: Optional[str] = None) -> Tuple[str, Optional[str], bool]:
    """Ensure a local repository path is available.
    Returns: (local_path, temp_dir, created_temp)
    - If repository_path is a real local path, returns it with (None, False)
    - If repository_path looks like a URL, treat it as repository_url and clone
    - If repository_url is provided, clones into a temp dir with prefix 'hardgate_analysis_'
    """
    # If repository_path is actually a URL, normalize to repository_url
    if repository_path and (repository_path.startswith("http://") or repository_path.startswith("https://") or repository_path.startswith("git@")):
        repository_url = repository_path
        repository_path = None

    if repository_path:
        return repository_path, None, False

    if not repository_url:
        raise ValueError("repository_path or repository_url must be provided")

    temp_dir = tempfile.mkdtemp(prefix="hardgate_analysis_")
    try:
        if HAS_CG_GIT and cg_clone_repository is not None:
            local_path = cg_clone_repository(repository_url, branch=branch, dest_dir=temp_dir)
            return local_path, temp_dir, True

        # Fallback: subprocess clone directly into temp_dir (consistent with app)
        clone_url = repository_url
        if github_token and "github.com" in repository_url and repository_url.startswith("https://"):
            clone_url = repository_url.replace("https://", f"https://{github_token}@")
        cmd = ["git", "clone", "-b", branch, clone_url, temp_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        return temp_dir, temp_dir, True
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def cleanup_temp_dir(temp_dir: Optional[str]) -> None:
    """Cleanup a temporary repository clone directory."""
    if not temp_dir:
        return
    try:
        if HAS_CG_GIT and cg_cleanup_repository is not None:
            cg_cleanup_repository(temp_dir)
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True) 