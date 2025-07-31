"""
File Scanner Utility
Scans repository files and extracts metadata
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Set
import re


# Language detection mappings
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.java': 'Java',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.cs': 'C#',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell'
}

# Files to ignore
IGNORE_PATTERNS = [
    '.git', '.svn', '.hg',
    'node_modules', '__pycache__', '.pytest_cache',
    'target', 'build', 'dist', 'out',
    '.idea', '.vscode', '.vs',
    '*.pyc', '*.class', '*.jar', '*.war',
    '*.log', '*.tmp', '*.swp',
    '.DS_Store', 'Thumbs.db',
    # Documentation files
    '*.md', '*.txt', '*.rst', '*.adoc', '*.asciidoc',
    '*.doc', '*.docx', '*.pdf', '*.rtf',
    '*.odt', '*.ods', '*.odp',
    'LICENSE', 'README', 'CHANGELOG', 'CONTRIBUTING',
    '*.license', '*.readme', '*.changelog',
    # Documentation directories
    'docs', 'documentation', 'doc',
    # Other unnecessary files
    '*.bak', '*.backup', '*.orig',
    '*.sample', '*.example', '*.template',
    '*.min.js', '*.min.css',  # Minified files
    '*.map'  # Source maps
]

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
    '.mp4', '.avi', '.mov', '.mp3', '.wav',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.exe', '.dll', '.so', '.dylib',
    '.jar', '.war', '.ear'
}


def scan_directory(repo_path: str, max_files: int = 10000) -> Dict[str, Any]:
    """
    Scan directory and extract file metadata
    
    Args:
        repo_path: Path to repository directory
        max_files: Maximum number of files to process
        
    Returns:
        Dictionary with file metadata and statistics
    """
    
    print(f"📁 Scanning directory: {repo_path}")
    
    repo_path = Path(repo_path)
    if not repo_path.exists():
        raise ValueError(f"Directory does not exist: {repo_path}")
    
    metadata = {
        "total_files": 0,
        "total_lines": 0,
        "total_size": 0,
        "languages": {},
        "file_types": {},
        "file_list": [],
        "language_stats": {},
        "directory_structure": {},
        "build_files": [],
        "config_files": []
    }
    
    files_processed = 0
    
    for file_path in _walk_directory(repo_path):
        if files_processed >= max_files:
            print(f"⚠️ Reached maximum file limit ({max_files})")
            break
            
        try:
            file_info = _analyze_file(file_path, repo_path)
            if file_info:
                metadata["file_list"].append(file_info)
                
                # Update statistics
                metadata["total_files"] += 1
                metadata["total_lines"] += file_info["lines"]
                metadata["total_size"] += file_info["size"]
                
                # Update language stats
                language = file_info["language"]
                if language != "Unknown":
                    if language not in metadata["languages"]:
                        metadata["languages"][language] = 0
                    metadata["languages"][language] += 1
                
                # Update file type stats
                file_type = file_info["type"]
                if file_type not in metadata["file_types"]:
                    metadata["file_types"][file_type] = 0
                metadata["file_types"][file_type] += 1
                
                # Identify special files
                if _is_build_file(file_path.name):
                    metadata["build_files"].append(file_info["relative_path"])
                
                if _is_config_file(file_path.name):
                    metadata["config_files"].append(file_info["relative_path"])
                
                files_processed += 1
                
        except Exception as e:
            print(f"⚠️ Error processing file {file_path}: {e}")
            continue
    
    # Calculate language statistics
    total_language_files = sum(metadata["languages"].values())
    metadata["language_stats"] = {
        lang: {
            "files": count,
            "percentage": round((count / total_language_files) * 100, 1) if total_language_files > 0 else 0
        }
        for lang, count in metadata["languages"].items()
    }
    
    # Build directory structure
    metadata["directory_structure"] = _build_directory_structure(metadata["file_list"])
    
    print(f"✅ Scanned {metadata['total_files']} files, {metadata['total_lines']} lines")
    print(f"   Languages detected: {', '.join(metadata['languages'].keys())}")
    
    return metadata


def _walk_directory(repo_path: Path) -> List[Path]:
    """Walk directory and return list of files to process"""
    
    files = []
    
    for root, dirs, filenames in os.walk(repo_path):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not _should_ignore_directory(d)]
        
        for filename in filenames:
            file_path = Path(root) / filename
            
            if not _should_ignore_file(file_path):
                files.append(file_path)
    
    return sorted(files)


def _analyze_file(file_path: Path, repo_root: Path) -> Dict[str, Any]:
    """Analyze individual file and extract metadata"""
    
    try:
        stat = file_path.stat()
        relative_path = file_path.relative_to(repo_root)
        
        # Get basic info
        file_info = {
            "path": str(file_path),
            "relative_path": str(relative_path),
            "name": file_path.name,
            "size": stat.st_size,
            "extension": file_path.suffix.lower(),
            "language": _detect_language(file_path),
            "type": _get_file_type(file_path),
            "lines": 0,
            "is_binary": _is_binary_file(file_path)
        }
        
        # Count lines for text files
        if not file_info["is_binary"] and stat.st_size < 1024 * 1024:  # Skip files > 1MB
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_info["lines"] = sum(1 for line in f if line.strip())
            except Exception:
                file_info["lines"] = 0
        
        return file_info
        
    except Exception as e:
        print(f"⚠️ Error analyzing file {file_path}: {e}")
        return None


def _detect_language(file_path: Path) -> str:
    """Detect programming language from file extension"""
    
    extension = file_path.suffix.lower()
    
    # Check extension mapping
    if extension in LANGUAGE_EXTENSIONS:
        return LANGUAGE_EXTENSIONS[extension]
    
    # Special cases
    filename = file_path.name.lower()
    if filename == 'dockerfile':
        return 'Docker'
    elif filename == 'makefile':
        return 'Make'
    elif filename.endswith('.gradle'):
        return 'Gradle'
    elif filename == 'pom.xml':
        return 'Maven'
    
    return "Unknown"


def _get_file_type(file_path: Path) -> str:
    """Get general file type category"""
    
    extension = file_path.suffix.lower()
    
    if extension in ['.py', '.java', '.js', '.ts', '.cs', '.go', '.rb', '.php', '.cpp', '.c']:
        # Check if this is a test file
        if _is_test_file(file_path):
            return "Test Code"
        else:
            return "Source Code"
    elif extension in ['.html', '.css', '.scss', '.less']:
        return "Web"
    elif extension in ['.json', '.yaml', '.yml', '.xml', '.toml', '.ini']:
        return "Configuration"
    elif extension in ['.md', '.txt', '.rst']:
        return "Documentation"
    elif extension in ['.sql']:
        return "Database"
    elif extension in ['.sh', '.bat', '.ps1']:
        return "Script"
    elif _is_binary_file(file_path):
        return "Binary"
    else:
        return "Other"


def _is_binary_file(file_path: Path) -> bool:
    """Check if file is binary"""
    
    extension = file_path.suffix.lower()
    if extension in BINARY_EXTENSIONS:
        return True
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and not mime_type.startswith('text/'):
        return True
    
    return False


def _should_ignore_file(file_path: Path) -> bool:
    """Check if file should be ignored"""
    
    filename = file_path.name
    
    # Check ignore patterns
    for pattern in IGNORE_PATTERNS:
        if '*' in pattern:
            # Simple glob matching
            pattern_regex = pattern.replace('*', '.*')
            if re.match(pattern_regex, filename):
                return True
        else:
            if pattern in str(file_path):
                return True
    
    # Skip very large files
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            return True
    except OSError:
        return True
    
    return False


def _should_ignore_directory(dirname: str) -> bool:
    """Check if directory should be ignored"""
    
    return dirname in ['.git', '.svn', '.hg', 'node_modules', '__pycache__', 
                      '.pytest_cache', 'target', 'build', 'dist', 'out',
                      '.idea', '.vscode', '.vs']


def _is_build_file(filename: str) -> bool:
    """Check if file is a build file"""
    
    build_files = [
        'pom.xml', 'build.gradle', 'build.gradle.kts',
        'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml',
        'Cargo.toml', 'go.mod', 'Gemfile',
        'Makefile', 'CMakeLists.txt',
        'Dockerfile', 'docker-compose.yml'
    ]
    
    return filename in build_files


def _is_config_file(filename: str) -> bool:
    """Check if file is a configuration file"""
    
    config_files = [
        'application.properties', 'application.yml', 'application.yaml',
        'config.json', 'config.yaml', 'config.yml',
        'settings.json', 'settings.yaml',
        '.env', '.env.example',
        'logback.xml', 'log4j.properties', 'log4j2.xml'
    ]
    
    return filename in config_files or filename.startswith('application.')


def _is_test_file(file_path: Path) -> bool:
    """Check if file is a test file based on common patterns"""
    
    file_name = file_path.name.lower()
    path_parts = [part.lower() for part in file_path.parts]
    
    # Common test file patterns
    test_patterns = [
        # File name patterns
        'test_', '_test.', 'test.', '.test.',
        'spec_', '_spec.', 'spec.', '.spec.',
        'tests_', '_tests.', 'tests.', '.tests.',
        'specs_', '_specs.', 'specs.', '.specs.',
        
        # File name contains
        'test', 'spec', 'mock', 'stub',
        
        # Java/Kotlin specific
        'Test.java', 'Test.kt', 'Tests.java', 'Tests.kt',
        'IT.java', 'IT.kt',  # Integration tests
        
        # Python specific
        'test_', '_test.py', 'conftest.py',
        
        # JavaScript/TypeScript specific
        '.test.js', '.test.ts', '.spec.js', '.spec.ts',
        '.test.jsx', '.test.tsx', '.spec.jsx', '.spec.tsx',
        
        # C# specific
        'Test.cs', 'Tests.cs', 'Spec.cs', 'Specs.cs',
        
        # Go specific
        '_test.go',
        
        # Ruby specific
        '_test.rb', '_spec.rb',
        
        # PHP specific
        'Test.php', 'Tests.php', 'Spec.php', 'Specs.php'
    ]
    
    # Check file name patterns
    for pattern in test_patterns:
        if pattern in file_name:
            return True
    
    # Common test directory patterns
    test_directories = [
        'test', 'tests', 'spec', 'specs', 'testing',
        '__tests__', '__test__', '__spec__', '__specs__',
        'test-', 'tests-', 'spec-', 'specs-',
        'src/test', 'src/tests', 'src/spec', 'src/specs',
        'app/test', 'app/tests', 'app/spec', 'app/specs',
        'lib/test', 'lib/tests', 'lib/spec', 'lib/specs',
        'unit', 'integration', 'e2e', 'end-to-end',
        'functional', 'acceptance', 'performance',
        'cypress', 'jest', 'mocha', 'jasmine', 'karma',
        'junit', 'testng', 'nunit', 'xunit', 'mstest',
        'pytest', 'unittest', 'nose', 'tox',
        'rspec', 'minitest', 'cucumber',
        'phpunit', 'codeception', 'behat'
    ]
    
    # Check if any part of the path contains test directory patterns
    for part in path_parts:
        for test_dir in test_directories:
            if test_dir == part or test_dir in part:
                return True
    
    return False


def _build_directory_structure(file_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build directory structure from file list"""
    
    structure = {}
    
    for file_info in file_list:
        path_parts = Path(file_info["relative_path"]).parts
        current = structure
        
        for part in path_parts[:-1]:  # All except filename
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Add file info
        filename = path_parts[-1]
        current[filename] = {
            "type": "file",
            "language": file_info["language"],
            "size": file_info["size"],
            "lines": file_info["lines"]
        }
    
    return structure


if __name__ == "__main__":
    # Test the file scanner
    import tempfile
    import os
    
    # Create a test directory structure
    test_dir = tempfile.mkdtemp(prefix="test_scan_")
    
    try:
        # Create some test files
        (Path(test_dir) / "main.py").write_text("print('hello')\n# comment\n")
        (Path(test_dir) / "app.js").write_text("console.log('hello');\n")
        (Path(test_dir) / "package.json").write_text('{"name": "test"}')
        
        # Create subdirectory
        sub_dir = Path(test_dir) / "src"
        sub_dir.mkdir()
        (sub_dir / "util.py").write_text("def helper():\n    pass\n")
        
        # Scan directory
        metadata = scan_directory(test_dir)
        
        print("Test results:")
        print(f"Total files: {metadata['total_files']}")
        print(f"Languages: {metadata['languages']}")
        print(f"Build files: {metadata['build_files']}")
        
        print("✅ File scanner test completed successfully")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir) 