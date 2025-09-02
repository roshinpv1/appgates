"""
Centralized file filtering utility for includes/excludes across the pipeline.
"""

from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple
import fnmatch
import json
import os


# Default file patterns (glob-like)
DEFAULT_INCLUDE_PATTERNS: Set[str] = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
    "*Makefile", "*.yaml", "*.yml", "*.properties"
}

DEFAULT_EXCLUDE_PATTERNS: Set[str] = {
    "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
    "*docs/*",
    "*venv/*",
    "*.venv/*",
    "*test*",
    "*tests/*",
    "*examples/*",
    "v1/*",
    "*dist/*",
    "*build/*",
    "*experimental/*",
    "*deprecated/*",
    "*misc/*",
    "*legacy/*",
    ".git/*", ".github/*", ".next/*", ".vscode/*",
    "*obj/*",
    "*bin/*",
    "*node_modules/*",
    "*.log"
}


class FileFilter:
    def __init__(
        self,
        include_patterns: Optional[Iterable[str]] = None,
        exclude_patterns: Optional[Iterable[str]] = None,
        extra_include: Optional[Iterable[str]] = None,
        extra_exclude: Optional[Iterable[str]] = None,
        max_file_size_mb: Optional[int] = None,
    ) -> None:
        self.include_patterns: List[str] = list(include_patterns or [])
        self.exclude_patterns: List[str] = list(exclude_patterns or [])
        if extra_include:
            self.include_patterns.extend(list(extra_include))
        if extra_exclude:
            self.exclude_patterns.extend(list(extra_exclude))
        self.max_file_size_mb = max_file_size_mb

    @staticmethod
    def _to_posix(path: Path) -> str:
        try:
            return path.as_posix()
        except Exception:
            return str(path).replace("\\", "/")

    def _match_any(self, path_str: str, patterns: List[str]) -> bool:
        for pat in patterns:
            if fnmatch.fnmatch(path_str, pat):
                return True
        return False

    def is_excluded(self, path: Path) -> bool:
        p = self._to_posix(path)
        return self._match_any(p, self.exclude_patterns)

    def is_included(self, path: Path) -> bool:
        p = self._to_posix(path)
        # If include_patterns empty, include everything by default
        if not self.include_patterns:
            return True
        return self._match_any(p, self.include_patterns)

    def should_process_file(self, path: Path) -> bool:
        if not path.is_file():
            return False
        # Size limit
        if self.max_file_size_mb is not None:
            try:
                if path.stat().st_size > self.max_file_size_mb * 1024 * 1024:
                    return False
            except Exception:
                pass
        if self.is_excluded(path):
            return False
        if not self.is_included(path):
            return False
        return True

    def iter_files(self, root: Path) -> Iterable[Path]:
        for p in root.rglob("*"):
            try:
                if self.should_process_file(p):
                    yield p
            except Exception:
                continue


# Load JSON config (file_filtering_config.json) and merge with defaults
def _load_json_config() -> Tuple[Optional[List[str]], Optional[List[str]], Optional[int]]:
    try:
        base_dir = Path(__file__).resolve().parent.parent
        cfg_path = base_dir / 'data' / 'file_filtering_config.json'
        if not cfg_path.exists():
            return None, None, None
        with open(cfg_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ff = data.get('file_filtering', {})
        inc = ff.get('include_patterns')
        exc = ff.get('ignore_patterns') or ff.get('exclude_patterns')
        max_size = ff.get('max_file_size_mb')
        return inc, exc, max_size
    except Exception:
        return None, None, None


_INC, _EXC, _MAX = _load_json_config()

DEFAULT_FILE_FILTER = FileFilter(
    include_patterns=_INC or DEFAULT_INCLUDE_PATTERNS,
    exclude_patterns=_EXC or DEFAULT_EXCLUDE_PATTERNS,
    max_file_size_mb=_MAX
)


