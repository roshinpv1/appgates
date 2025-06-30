"""
Language Detection System for Multi-Language Codebases
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter

from ..models import Language


class LanguageDetector:
    """Detects programming languages in a codebase"""
    
    # File extension mappings
    EXTENSION_MAP = {
        '.java': Language.JAVA,
        '.py': Language.PYTHON,
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.cs': Language.CSHARP,
        '.vb': Language.DOTNET,
        '.fs': Language.DOTNET,
    }
    
    # Content-based detection patterns
    CONTENT_PATTERNS = {
        Language.JAVA: [
            r'package\s+[\w.]+;',
            r'import\s+[\w.]+;',
            r'public\s+class\s+\w+',
            r'@\w+\s*\(.*\)',
            r'System\.out\.print'
        ],
        Language.PYTHON: [
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*\(',
            r'if\s+__name__\s*==\s*["\']__main__["\']:',
            r'print\s*\('
        ],
        Language.JAVASCRIPT: [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'require\s*\(["\'][\w./]+["\']\)',
            r'module\.exports\s*=',
            r'console\.log\s*\('
        ],
        Language.TYPESCRIPT: [
            r'interface\s+\w+\s*{',
            r'type\s+\w+\s*=',
            r'enum\s+\w+\s*{',
            r'export\s+\w+',
            r'import.*from\s+["\'][\w./]+["\']',
            r':\s*\w+\s*=',
            r'<\w+>'
        ],
        Language.CSHARP: [
            r'using\s+\w+;',
            r'namespace\s+[\w.]+',
            r'public\s+class\s+\w+',
            r'public\s+static\s+void\s+Main',
            r'Console\.WriteLine\s*\(',
            r'\[.*\]\s*public'
        ]
    }
    
    # Configuration files that indicate language presence
    CONFIG_FILES = {
        Language.JAVA: [
            'pom.xml', 'build.gradle', 'build.gradle.kts', 
            'maven.xml', 'ivy.xml'
        ],
        Language.PYTHON: [
            'requirements.txt', 'setup.py', 'pyproject.toml',
            'Pipfile', 'poetry.lock', 'conda.yml'
        ],
        Language.JAVASCRIPT: [
            'package.json', 'bower.json', 'gulpfile.js',
            'webpack.config.js', 'rollup.config.js'
        ],
        Language.TYPESCRIPT: [
            'tsconfig.json', 'tslint.json', 'webpack.config.ts'
        ],
        Language.CSHARP: [
            '*.csproj', '*.sln', 'packages.config', 
            'project.json', 'Directory.Build.props'
        ]
    }
    
    def __init__(self):
        self.file_counts = defaultdict(int)
        self.content_matches = defaultdict(int)
        self.config_matches = defaultdict(bool)
    
    def detect_languages(self, root_path: Path) -> List[Language]:
        """Detect all languages present in the codebase"""
        
        self._reset_counters()
        
        # Scan directory structure
        self._scan_directory(root_path)
        
        # Determine primary languages
        detected_languages = self._analyze_results()
        
        return detected_languages
    
    def get_language_statistics(self) -> Dict[Language, Dict[str, int]]:
        """Get detailed statistics about detected languages"""
        
        stats = {}
        for lang in Language:
            stats[lang] = {
                'file_count': self.file_counts[lang],
                'content_matches': self.content_matches[lang],
                'has_config': self.config_matches[lang],
                'confidence': self._calculate_confidence(lang)
            }
        
        return stats
    
    def detect_file_language(self, file_path: Path) -> Language:
        """Detect language of a single file"""
        
        # Check by extension first
        extension = file_path.suffix.lower()
        if extension in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[extension]
        
        # Check by content if no extension match
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Read first 1KB
                
            for lang, patterns in self.CONTENT_PATTERNS.items():
                matches = sum(1 for pattern in patterns if re.search(pattern, content))
                if matches >= 2:  # Require at least 2 pattern matches
                    return lang
                    
        except (IOError, UnicodeDecodeError):
            pass
        
        return None
    
    def _reset_counters(self):
        """Reset all counters for fresh detection"""
        self.file_counts.clear()
        self.content_matches.clear()
        self.config_matches.clear()
    
    def _scan_directory(self, root_path: Path):
        """Recursively scan directory for language indicators"""
        
        exclude_dirs = {
            '.git', '.svn', '.hg', 'node_modules', '__pycache__', 
            'target', 'bin', 'obj', '.vscode', '.idea', 'venv', 
            'env', '.env', 'dist', 'build'
        }
        
        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            root_path_obj = Path(root)
            
            # Check configuration files
            self._check_config_files(files, root_path_obj)
            
            # Analyze source files
            for file_name in files:
                file_path = root_path_obj / file_name
                
                # Skip large files (>1MB)
                try:
                    if file_path.stat().st_size > 1024 * 1024:
                        continue
                except OSError:
                    continue
                
                lang = self.detect_file_language(file_path)
                if lang:
                    self.file_counts[lang] += 1
                    self._analyze_file_content(file_path, lang)
    
    def _check_config_files(self, files: List[str], directory: Path):
        """Check for language-specific configuration files"""
        
        file_set = set(files)
        
        for lang, config_patterns in self.CONFIG_FILES.items():
            for pattern in config_patterns:
                if '*' in pattern:
                    # Handle glob patterns
                    pattern_regex = pattern.replace('*', r'.*')
                    if any(re.match(pattern_regex, f) for f in files):
                        self.config_matches[lang] = True
                else:
                    # Direct file match
                    if pattern in file_set:
                        self.config_matches[lang] = True
    
    def _analyze_file_content(self, file_path: Path, lang: Language):
        """Analyze file content to increase confidence"""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2048)  # Read first 2KB
            
            patterns = self.CONTENT_PATTERNS.get(lang, [])
            matches = sum(1 for pattern in patterns if re.search(pattern, content))
            self.content_matches[lang] += matches
            
        except (IOError, UnicodeDecodeError):
            pass
    
    def _calculate_confidence(self, lang: Language) -> float:
        """Calculate confidence score for a language (0-100)"""
        
        file_count = self.file_counts[lang]
        content_matches = self.content_matches[lang]
        has_config = self.config_matches[lang]
        
        if file_count == 0 and content_matches == 0 and not has_config:
            return 0.0
        
        # Base score from file count (up to 40 points)
        file_score = min(file_count * 2, 40)
        
        # Content analysis score (up to 40 points) 
        content_score = min(content_matches * 3, 40)
        
        # Configuration bonus (up to 20 points)
        config_score = 20 if has_config else 0
        
        total_score = file_score + content_score + config_score
        return min(total_score, 100.0)
    
    def _analyze_results(self) -> List[Language]:
        """Analyze detection results and return detected languages"""
        
        detected = []
        
        for lang in Language:
            confidence = self._calculate_confidence(lang)
            
            # Include language if confidence is above threshold
            if confidence >= 30.0:  # 30% confidence threshold
                detected.append(lang)
        
        # If no languages detected with high confidence, 
        # include top language by file count
        if not detected:
            top_lang = max(Language, key=lambda l: self.file_counts[l])
            if self.file_counts[top_lang] > 0:
                detected.append(top_lang)
        
        return detected
    
    def get_file_extensions(self, root_path: Path) -> Dict[str, int]:
        """Get count of all file extensions in the codebase"""
        
        extension_counts = Counter()
        
        for root, dirs, files in os.walk(root_path):
            for file_name in files:
                ext = Path(file_name).suffix.lower()
                if ext:
                    extension_counts[ext] += 1
        
        return dict(extension_counts) 