"""
Code Indexer Component
Handles repository indexing with AST-aware chunking and vector storage
"""

import os
import json
import time
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re # Added for regex-based fallback

# Import existing utilities
try:
    from ..utils.file_scanner import scan_directory
    from ..utils.file_processor import OptimizedFileProcessor
    from ..utils.pattern_cache import get_pattern_cache
except ImportError:
    from utils.file_scanner import scan_directory
    from utils.file_processor import OptimizedFileProcessor
    from utils.pattern_cache import get_pattern_cache


@dataclass
class ChunkMetadata:
    """Metadata for a code chunk"""
    repo_id: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    imports: List[str]
    references: List[str]
    content_hash: str
    mtime: int
    chunk_size: int
    overlap_size: int
    symbol_name: Optional[str] = None
    symbol_kind: Optional[str] = None


class CodeIndexer:
    """
    Advanced code indexer with AST-aware chunking and vector storage
    """
    
    def __init__(self, vector_store, embedding_service, ast_parser, config):
        """Initialize the code indexer"""
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.ast_parser = ast_parser
        self.config = config
        
        # Initialize file processor (reuse existing)
        self.file_processor = OptimizedFileProcessor()
        
        # Supported languages for AST parsing
        self.supported_languages = config.supported_languages or [
            "python", "javascript", "typescript", "java", "csharp", "go", "rust"
        ]
        
        # File extensions mapping
        self.language_extensions = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp"
        }
        
        print(f"🔍 CodeIndexer initialized with {len(self.supported_languages)} supported languages")
    
    def index_repository(self, repo_id: str, repo_path: Path, 
                              repo_url: str, branch: str) -> Dict[str, Any]:
        """
        Index a repository for advanced LLM assistance
        """
        start_time = time.time()
        
        try:
            print(f"📚 Starting repository indexing for {repo_id}")
            
            # Scan repository for files
            files_info = self._scan_repository(repo_path)
            print(f"   📁 Found {len(files_info)} files to process")
            
            # Process files and create chunks
            chunks = self._process_files(repo_id, files_info)
            print(f"   📦 Created {len(chunks)} chunks")
            
            # Generate embeddings for chunks
            embeddings = self._generate_embeddings(chunks)
            print(f"   🧠 Generated {len(embeddings)} embeddings")
            
            # Store in vector database
            self._store_chunks(repo_id, chunks, embeddings)
            print(f"   💾 Stored chunks in vector database")
            
            # Create symbol index
            if self.config.enable_symbol_extraction:
                symbols = self._extract_symbols(repo_id, files_info)
                self._store_symbols(repo_id, symbols)
                print(f"   🔍 Extracted and stored {len(symbols)} symbols")
            
            # Create dependency graph
            if self.config.enable_dependency_graph:
                dependencies = self._extract_dependencies(repo_id, files_info)
                self._store_dependencies(repo_id, dependencies)
                print(f"   🔗 Extracted and stored {len(dependencies)} dependencies")
            
            indexing_time = time.time() - start_time
            
            return {
                "repo_id": repo_id,
                "chunks_created": len(chunks),
                "files_processed": len(files_info),
                "symbols_extracted": len(symbols) if self.config.enable_symbol_extraction else 0,
                "dependencies_extracted": len(dependencies) if self.config.enable_dependency_graph else 0,
                "indexing_time_seconds": indexing_time
            }
            
        except Exception as e:
            print(f"❌ Failed to index repository {repo_id}: {e}")
            raise
    
    def _scan_repository(self, repo_path: Path) -> List[Dict[str, Any]]:
        """
        Scan repository for files to index
        """
        # Use a less restrictive file scanning approach for advanced LLM indexing
        files_info = []
        
        for file_path in self._walk_directory(repo_path):
            try:
                file_info = self._analyze_file_for_indexing(file_path, repo_path)
                if file_info:
                    files_info.append(file_info)
            except Exception as e:
                print(f"⚠️ Failed to process file {file_path}: {e}")
                continue
        
        return files_info
    
    def _walk_directory(self, repo_path: Path) -> List[Path]:
        """Walk directory and return list of files to process for indexing"""
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore_directory(d)]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                if not self._should_ignore_file_for_indexing(file_path):
                    files.append(file_path)
        
        return sorted(files)
    
    def _should_ignore_directory(self, dirname: str) -> bool:
        """Check if directory should be ignored for indexing"""
        return dirname in ['.git', '.svn', '.hg', 'node_modules', '__pycache__', 
                          '.pytest_cache', 'target', 'build', 'dist', 'out',
                          '.idea', '.vscode', '.vs']
    
    def _should_ignore_file_for_indexing(self, file_path: Path) -> bool:
        """Check if file should be ignored for indexing (less restrictive)"""
        filename = file_path.name.lower()
        
        # Skip binary files and very large files
        try:
            if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB limit for indexing
                return True
        except OSError:
            return True
        
        # Skip common binary extensions
        binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                           '.mp4', '.avi', '.mov', '.mp3', '.wav',
                           '.zip', '.tar', '.gz', '.rar', '.7z',
                           '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                           '.exe', '.dll', '.so', '.dylib',
                           '.jar', '.war', '.ear', '.class'}
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        # Skip minified files and source maps
        if any(pattern in filename for pattern in ['.min.js', '.min.css', '.map']):
            return True
        
        return False
    
    def _analyze_file_for_indexing(self, file_path: Path, repo_root: Path) -> Dict[str, Any]:
        """Analyze individual file for indexing"""
        try:
            stat = file_path.stat()
            relative_path = file_path.relative_to(repo_root)
            
            # Get file extension and determine language
            file_ext = file_path.suffix.lower()
            language = self.language_extensions.get(file_ext, "text")
            
            # For files without extension, try to determine language from content
            if not file_ext:
                language = self._detect_language_from_content(file_path)
            
            # Read file content for line counting
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = len(content.splitlines())
            except Exception:
                lines = 0
            
            return {
                "path": str(file_path),
                "relative_path": str(relative_path),
                "name": file_path.name,
                "size": stat.st_size,
                "extension": file_ext,
                "language": language,
                "lines": lines,
                "mtime": int(stat.st_mtime)
            }
            
        except Exception as e:
            print(f"⚠️ Error analyzing file {file_path}: {e}")
            return None
    
    def _detect_language_from_content(self, file_path: Path) -> str:
        """Detect language from file content for files without extension"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # Read first 1KB
                
            filename = file_path.name.lower()
            
            # Common patterns for different file types
            if filename in ['readme', 'license', 'changelog', 'contributing']:
                return "markdown"
            elif 'makefile' in filename:
                return "makefile"
            elif 'dockerfile' in filename:
                return "dockerfile"
            elif filename.startswith('.env'):
                return "env"
            elif filename in ['docker-compose.yml', 'docker-compose.yaml']:
                return "yaml"
            elif content.startswith('#!/'):
                return "shell"
            elif content.startswith('<?xml'):
                return "xml"
            elif content.startswith('{') or content.startswith('['):
                return "json"
            else:
                return "text"
                
        except Exception:
            return "text"
    
    def _process_files(self, repo_id: str, files_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process files and create AST-aware chunks
        """
        chunks = []
        
        for file_info in files_info:
            file_path = file_info["path"]
            language = file_info["language"]
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Create chunks based on language support
                if language in self.supported_languages and self.config.enable_ast_parsing:
                    file_chunks = self._create_ast_chunks(
                        repo_id, file_path, content, language, file_info
                    )
                else:
                    file_chunks = self._create_sliding_chunks(
                        repo_id, file_path, content, language, file_info
                    )
                
                chunks.extend(file_chunks)
                
            except Exception as e:
                print(f"⚠️ Failed to process file {file_path}: {e}")
                continue
        
        return chunks
    
    def _create_ast_chunks(self, repo_id: str, file_path: str, content: str,
                                language: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create AST-aware chunks for supported languages
        """
        try:
            # Parse AST (synchronous fallback)
            ast_result = self._parse_ast_fallback(content, language)
            
            chunks = []
            
            # Create chunks for each function/class/method
            for symbol in ast_result.get("symbols", []):
                symbol_name = symbol.get("name", "unknown")
                symbol_kind = symbol.get("kind", "unknown")
                start_line = symbol.get("start_line", 0)
                end_line = symbol.get("end_line", 0)
                
                # Extract symbol content
                lines = content.split('\n')
                symbol_lines = lines[start_line-1:end_line] if start_line > 0 else []
                symbol_content = '\n'.join(symbol_lines)
                
                if len(symbol_content.strip()) < 10:  # Skip very small symbols (reduced from 50)
                    continue
                
                # Create chunk metadata
                chunk_metadata = ChunkMetadata(
                    repo_id=repo_id,
                    file_path=file_path,
                    language=language,
                    symbol_name=symbol_name,
                    symbol_kind=symbol_kind,
                    start_line=start_line,
                    end_line=end_line,
                    imports=ast_result.get("imports", []),
                    references=symbol.get("references", []),
                    content_hash=self._hash_content(symbol_content),
                    mtime=file_info["mtime"],
                    chunk_size=len(symbol_content),
                    overlap_size=0
                )
                
                chunks.append({
                    "metadata": chunk_metadata,
                    "content": symbol_content,
                    "type": "ast_symbol"
                })
            
            # If no symbols found, fall back to sliding chunks
            if not chunks:
                return self._create_sliding_chunks(repo_id, file_path, content, language, file_info)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ AST parsing failed for {file_path}, falling back to sliding chunks: {e}")
            return self._create_sliding_chunks(repo_id, file_path, content, language, file_info)
    
    def _create_sliding_chunks(self, repo_id: str, file_path: str, content: str,
                                    language: str, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create sliding window chunks for unsupported languages or fallback
        """
        chunks = []
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Calculate chunk parameters
        chunk_size = self.config.chunk_size
        overlap_size = self.config.overlap_size
        
        start_line = 1
        while start_line <= total_lines:
            end_line = min(start_line + chunk_size - 1, total_lines)
            
            # Extract chunk content
            chunk_lines = lines[start_line-1:end_line]
            chunk_content = '\n'.join(chunk_lines)
            
            if len(chunk_content.strip()) < 10:  # Skip very small chunks (reduced from 50)
                start_line += chunk_size - overlap_size
                continue
            
            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                repo_id=repo_id,
                file_path=file_path,
                language=language,
                symbol_name=None,
                symbol_kind=None,
                start_line=start_line,
                end_line=end_line,
                imports=[],
                references=[],
                content_hash=self._hash_content(chunk_content),
                mtime=file_info["mtime"],
                chunk_size=len(chunk_content),
                overlap_size=overlap_size
            )
            
            chunks.append({
                "metadata": chunk_metadata,
                "content": chunk_content,
                "type": "sliding_window"
            })
            
            start_line += chunk_size - overlap_size
        
        return chunks
    
    def _parse_ast_fallback(self, content: str, language: str) -> Dict[str, Any]:
        """
        Simple regex-based AST parsing fallback
        """
        symbols = []
        imports = []
        
        lines = content.split('\n')
        
        # Simple regex patterns for common symbols
        patterns = {
            "python": [
                (r"^def\s+(\w+)\s*\(", "function"),
                (r"^class\s+(\w+)", "class"),
                (r"^async\s+def\s+(\w+)\s*\(", "async_function"),
            ],
            "javascript": [
                (r"^function\s+(\w+)\s*\(", "function"),
                (r"^const\s+(\w+)\s*=\s*function", "function"),
                (r"^let\s+(\w+)\s*=\s*function", "function"),
                (r"^var\s+(\w+)\s*=\s*function", "function"),
                (r"^class\s+(\w+)", "class"),
            ],
            "java": [
                (r"^public\s+class\s+(\w+)", "class"),
                (r"^private\s+class\s+(\w+)", "class"),
                (r"^protected\s+class\s+(\w+)", "class"),
                (r"^public\s+\w+\s+(\w+)\s*\(", "method"),
                (r"^private\s+\w+\s+(\w+)\s*\(", "method"),
            ]
        }
        
        lang_patterns = patterns.get(language, [])
        
        for line_num, line in enumerate(lines, 1):
            for pattern, kind in lang_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    name = match.group(1)
                    symbols.append({
                        "name": name,
                        "kind": kind,
                        "start_line": line_num,
                        "end_line": line_num,  # Simplified
                        "references": []
                    })
        
        return {
            "symbols": symbols,
            "imports": imports
        }
    
    def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks
        """
        embeddings = []
        
        # Batch process embeddings
        batch_size = self.config.batch_size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare batch content
            batch_contents = [chunk["content"] for chunk in batch]
            
            try:
                # Generate embeddings
                batch_embeddings = self.embedding_service.embed_texts(batch_contents)
                
                # Combine with metadata
                for j, chunk in enumerate(batch):
                    if j < len(batch_embeddings):
                        embeddings.append({
                            "chunk": chunk,
                            "embedding": batch_embeddings[j],
                            "embedding_model": self.embedding_service.model_name
                        })
                
            except Exception as e:
                print(f"⚠️ Failed to generate embeddings for batch {i//batch_size}: {e}")
                continue
        
        return embeddings
    
    def _store_chunks(self, repo_id: str, chunks: List[Dict[str, Any]], 
                           embeddings: List[Dict[str, Any]]):
        """
        Store chunks and embeddings in vector database
        """
        try:
            # Create collection for repository
            self.vector_store.create_collection(repo_id)
            
            # Prepare vectors for storage
            vectors = []
            for embedding_data in embeddings:
                chunk = embedding_data["chunk"]
                metadata = chunk["metadata"]
                
                vector_data = {
                    "id": self._generate_chunk_id(repo_id, metadata.file_path, metadata.start_line),
                    "vector": embedding_data["embedding"],
                    "payload": {
                        "repo_id": metadata.repo_id,
                        "file_path": metadata.file_path,
                        "language": metadata.language,
                        "symbol_name": metadata.symbol_name,
                        "symbol_kind": metadata.symbol_kind,
                        "start_line": metadata.start_line,
                        "end_line": metadata.end_line,
                        "imports": metadata.imports,
                        "references": metadata.references,
                        "hash": metadata.content_hash,
                        "mtime": metadata.mtime,
                        "chunk_type": chunk["type"],
                        "content": chunk["content"]  # Add the actual content
                    }
                }
                vectors.append(vector_data)
            
            # Store in vector database
            self.vector_store.upsert_vectors(repo_id, vectors)
            
        except Exception as e:
            print(f"❌ Failed to store chunks in vector database: {e}")
            raise
    
    def _extract_symbols(self, repo_id: str, files_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract symbols from files for symbol search
        """
        symbols = []
        
        for file_info in files_info:
            file_path = file_info["path"]
            language = file_info["language"]
            
            if language not in self.supported_languages:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse symbols
                ast_result = self._parse_ast_fallback(content, language)
                
                for symbol in ast_result.get("symbols", []):
                    symbols.append({
                        "repo_id": repo_id,
                        "file_path": file_path,
                        "language": language,
                        "name": symbol.get("name"),
                        "kind": symbol.get("kind"),
                        "start_line": symbol.get("start_line"),
                        "end_line": symbol.get("end_line"),
                        "signature": symbol.get("signature"),
                        "references": symbol.get("references", [])
                    })
                
            except Exception as e:
                print(f"⚠️ Failed to extract symbols from {file_path}: {e}")
                continue
        
        return symbols
    
    def _extract_dependencies(self, repo_id: str, files_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract dependencies between files
        """
        dependencies = []
        
        for file_info in files_info:
            file_path = file_info["path"]
            language = file_info["language"]
            
            if language not in self.supported_languages:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse dependencies
                ast_result = self._parse_ast_fallback(content, language)
                
                for import_info in ast_result.get("imports", []):
                    dependencies.append({
                        "repo_id": repo_id,
                        "source_file": file_path,
                        "target_module": import_info.get("module"),
                        "import_type": import_info.get("type"),
                        "line_number": import_info.get("line")
                    })
                
            except Exception as e:
                print(f"⚠️ Failed to extract dependencies from {file_path}: {e}")
                continue
        
        return dependencies
    
    def _store_symbols(self, repo_id: str, symbols: List[Dict[str, Any]]):
        """
        Store symbols in search index
        """
        # This would integrate with a search service like OpenSearch
        # For now, we'll store in a simple format
        pass
    
    def _store_dependencies(self, repo_id: str, dependencies: List[Dict[str, Any]]):
        """
        Store dependencies in graph database
        """
        # This would integrate with a graph database like Neo4j
        # For now, we'll store in a simple format
        pass
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_chunk_id(self, repo_id: str, file_path: str, start_line: int) -> str:
        """Generate unique chunk ID"""
        chunk_key = f"{repo_id}:{file_path}:{start_line}"
        return hashlib.sha256(chunk_key.encode()).hexdigest()[:16]
