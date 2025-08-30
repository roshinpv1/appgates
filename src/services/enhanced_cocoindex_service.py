"""
Enhanced CocoIndex service with true Tree-sitter AST-based parsing
"""

import os
import json
import hashlib
import tempfile
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

try:
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ Qdrant not available")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available")

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️ Tree-sitter not available")

# Import language-specific Tree-sitter grammars
try:
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_java
    import tree_sitter_go
    import tree_sitter_rust
    import tree_sitter_cpp
    TREE_SITTER_LANGUAGES_AVAILABLE = True
except ImportError:
    TREE_SITTER_LANGUAGES_AVAILABLE = False
    print("⚠️ Tree-sitter language grammars not available")

# Use the existing AST parser service for Tree-sitter functionality
try:
    from services.ast_parser_service import ASTParserService
    AST_PARSER_AVAILABLE = True
except ImportError:
    AST_PARSER_AVAILABLE = False
    print("⚠️ AST parser service not available")


class EnhancedCocoIndexService:
    """Enhanced CocoIndex service with true Tree-sitter AST-based parsing"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Enhanced CocoIndex service"""
        self.config = config
        
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant is required but not available")
        
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required but not available")
        
        # Initialize Qdrant client
        self._init_qdrant()
        
        # Configuration
        self.chunk_size = config.get("chunk_size", 1000)
        self.chunk_overlap = config.get("chunk_overlap", 300)
        self.embedding_model = config.get("embedding_model", "text-embedding-nomic-embed-text-v1.5-embedding")
        self.vector_size = self._get_vector_size()
        
        # File patterns
        self.included_patterns = config.get("included_patterns", [
            "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cs", 
            "*.go", "*.rs", "*.cpp", "*.c", "*.h", "*.hpp", "*.md", "*.mdx"
        ])
        self.excluded_patterns = config.get("excluded_patterns", [
            ".*", "node_modules", "__pycache__", "target", "build", "dist", 
            "*.pyc", "*.class", "*.o", "*.so", "*.dylib", "*.dll"
        ])
        
        # Initialize Tree-sitter parsers using existing AST parser service
        self.parsers = {}
        self.languages = {}
        self.ast_parser_service = None
        
        if TREE_SITTER_AVAILABLE and AST_PARSER_AVAILABLE:
            try:
                # Use existing AST parser service
                ast_config = {"supported_languages": ["python", "javascript", "typescript", "java", "go", "rust", "cpp"]}
                self.ast_parser_service = ASTParserService(ast_config)
                print("✅ Initialized AST parser service for Tree-sitter parsing")
            except Exception as e:
                print(f"⚠️ Failed to initialize AST parser service: {e}")
        else:
            print("⚠️ Tree-sitter not fully available, falling back to regex-based parsing")
        
        print(f"🧠 EnhancedCocoIndexService initialized with {self.embedding_model} ({self.vector_size} dimensions)")
        print(f"🔧 Tree-sitter AST parsing: {'✅ Enabled' if self.ast_parser_service else '❌ Disabled'}")
    
    def _init_qdrant(self):
        """Initialize Qdrant client"""
        try:
            qdrant_path = self.config.get("qdrant_path", "./qdrant_data")
            print(f"🔧 Initializing Qdrant at {qdrant_path}")
            
            # Ensure the directory exists
            os.makedirs(qdrant_path, exist_ok=True)
            
            # Check if there's a lock file and remove it if it's stale
            lock_file = os.path.join(qdrant_path, ".lock")
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    print(f"🔓 Removed stale lock file")
                except Exception as e:
                    print(f"⚠️ Could not remove lock file: {e}")
            
            self.client = QdrantClient(path=qdrant_path)
            print(f"🔗 Successfully initialized Qdrant at {qdrant_path}")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Qdrant: {e}")
    

    
    def _get_vector_size(self) -> int:
        """Get vector size for the embedding model"""
        model_dimensions = {
            "text-embedding-nomic-embed-text-v1.5-embedding": 768,
            "text-embedding-nomic-embed-text-v1.5": 768,
            "text-embedding-all-minilm-l6-v2-embedding": 384,
            "nomic-embed-text": 768,
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "multi-qa-MiniLM-L6-cos-v1": 384
        }
        return model_dimensions.get(self.embedding_model, 768)
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp'
        }
        return language_map.get(ext, 'text')
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        file_path_str = str(file_path)
        
        # Check ignore patterns
        for pattern in self.excluded_patterns:
            if pattern in file_path_str:
                return True
        
        # Check include patterns
        for pattern in self.included_patterns:
            if file_path.match(pattern):
                return False
        
        return True
    
    def _create_ast_based_chunks(self, content: str, file_path: Path, repo_root: Path, 
                                scan_id: str, language: str, repo_type: str) -> List[Dict[str, Any]]:
        """Create semantic chunks using Tree-sitter AST parsing"""
        if not self.ast_parser_service:
            # Fallback to regex-based chunking
            return self._create_regex_based_chunks(content, file_path, repo_root, scan_id, language, repo_type)
        
        try:
            # Use existing AST parser service
            ast_result = self.ast_parser_service.parse_file(content, language)
            
            chunks = []
            
            # Extract chunks from AST symbols
            if ast_result and "symbols" in ast_result:
                for symbol in ast_result["symbols"]:
                    # Get the actual code for this symbol
                    symbol_content = self._extract_symbol_content(content, symbol, language)
                    
                    if symbol_content and len(symbol_content.strip()) > 10:
                        chunk_id = f"{scan_id}_{repo_type}_{file_path.name}_{symbol.get('start_line', 1)}_{symbol.get('end_line', 1)}"
                        
                        chunk_data = {
                            "id": chunk_id,
                            "content": symbol_content,
                            "metadata": {
                                "scan_id": scan_id,
                                "repo_type": repo_type,
                                "file_path": str(file_path.relative_to(repo_root)),
                                "filename": file_path.name,
                                "language": language,
                                "start_line": symbol.get('start_line', 1),
                                "end_line": symbol.get('end_line', 1),
                                "chunk_size": len(symbol_content),
                                "node_type": symbol.get('type', 'unknown'),
                                "symbol_name": symbol.get('name', ''),
                                "processing_timestamp": datetime.now().isoformat(),
                                "chunking_method": "ast_based"
                            }
                        }
                        chunks.append(chunk_data)
            
            # If no semantic chunks found, create fallback chunks
            if not chunks:
                print(f"⚠️ No semantic chunks found for {file_path}, using fallback chunking")
                return self._create_regex_based_chunks(content, file_path, repo_root, scan_id, language, repo_type)
            
            # Add overlapping chunks for better context
            chunks = self._add_overlapping_chunks(chunks, content, file_path, repo_root, scan_id, language, repo_type)
            
            return chunks
            
        except Exception as e:
            print(f"⚠️ AST parsing failed for {file_path}: {e}")
            return self._create_regex_based_chunks(content, file_path, repo_root, scan_id, language, repo_type)
    
    def _extract_symbol_content(self, content: str, symbol: Dict[str, Any], language: str) -> str:
        """Extract the actual code content for a symbol"""
        try:
            lines = content.split('\n')
            start_line = symbol.get('start_line', 1) - 1  # Convert to 0-based
            end_line = symbol.get('end_line', len(lines)) - 1
            
            # Extract the lines for this symbol
            symbol_lines = lines[start_line:end_line + 1]
            return '\n'.join(symbol_lines)
        except Exception as e:
            print(f"⚠️ Failed to extract symbol content: {e}")
            return ""
    
    def _create_regex_based_chunks(self, content: str, file_path: Path, repo_root: Path, 
                                  scan_id: str, language: str, repo_type: str) -> List[Dict[str, Any]]:
        """Create semantic chunks using regex-based approach (fallback)"""
        chunks = []
        
        # Simple semantic chunking based on functions, classes, and logical blocks
        lines = content.split('\n')
        current_chunk = []
        chunk_start_line = 1
        
        for i, line in enumerate(lines, 1):
            current_chunk.append(line)
            
            # Check for semantic boundaries
            is_semantic_boundary = (
                # Function definitions
                line.strip().startswith('def ') or
                line.strip().startswith('function ') or
                line.strip().startswith('public ') or
                line.strip().startswith('private ') or
                line.strip().startswith('protected ') or
                # Class definitions
                line.strip().startswith('class ') or
                # Import statements
                line.strip().startswith('import ') or
                line.strip().startswith('from ') or
                line.strip().startswith('using ') or
                # Documentation blocks
                line.strip().startswith('"""') or
                line.strip().startswith("'''") or
                line.strip().startswith('/*') or
                line.strip().startswith(' *') or
                # Large chunks (force split)
                len(current_chunk) >= self.chunk_size
            )
            
            if is_semantic_boundary and len(current_chunk) > 10:
                # Create chunk
                chunk_content = '\n'.join(current_chunk)
                chunk_id = f"{scan_id}_{repo_type}_{file_path.name}_{chunk_start_line}_{i}"
                
                chunk_data = {
                    "id": chunk_id,
                    "content": chunk_content,
                    "metadata": {
                        "scan_id": scan_id,
                        "repo_type": repo_type,
                        "file_path": str(file_path.relative_to(repo_root)),
                        "filename": file_path.name,
                        "language": language,
                        "start_line": chunk_start_line,
                        "end_line": i,
                        "chunk_size": len(chunk_content),
                        "processing_timestamp": datetime.now().isoformat(),
                        "chunking_method": "regex_based"
                    }
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_lines = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else []
                current_chunk = overlap_lines
                chunk_start_line = i - len(overlap_lines) + 1
        
        # Add remaining content as final chunk
        if current_chunk and len(current_chunk) > 10:
            chunk_content = '\n'.join(current_chunk)
            chunk_id = f"{scan_id}_{repo_type}_{file_path.name}_{chunk_start_line}_{len(lines)}"
            
            chunk_data = {
                "id": chunk_id,
                "content": chunk_content,
                "metadata": {
                    "scan_id": scan_id,
                    "repo_type": repo_type,
                    "file_path": str(file_path.relative_to(repo_root)),
                    "filename": file_path.name,
                    "language": language,
                    "start_line": chunk_start_line,
                    "end_line": len(lines),
                    "chunk_size": len(chunk_content),
                    "processing_timestamp": datetime.now().isoformat(),
                    "chunking_method": "regex_based"
                }
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def _add_overlapping_chunks(self, chunks: List[Dict[str, Any]], content: str, file_path: Path, 
                               repo_root: Path, scan_id: str, language: str, repo_type: str) -> List[Dict[str, Any]]:
        """Add overlapping chunks for better context"""
        if not chunks or self.chunk_overlap <= 0:
            return chunks
        
        lines = content.split('\n')
        enhanced_chunks = chunks.copy()
        
        for i, chunk in enumerate(chunks):
            start_line = chunk["metadata"]["start_line"] - 1  # Convert to 0-based
            end_line = chunk["metadata"]["end_line"] - 1
            
            # Add context before the chunk
            context_start = max(0, start_line - self.chunk_overlap)
            if context_start < start_line:
                context_lines = lines[context_start:start_line]
                if context_lines:
                    context_content = '\n'.join(context_lines)
                    context_id = f"{scan_id}_{repo_type}_{file_path.name}_context_before_{start_line}"
                    
                    context_chunk = {
                        "id": context_id,
                        "content": context_content,
                        "metadata": {
                            "scan_id": scan_id,
                            "repo_type": repo_type,
                            "file_path": str(file_path.relative_to(repo_root)),
                            "filename": file_path.name,
                            "language": language,
                            "start_line": context_start + 1,
                            "end_line": start_line,
                            "chunk_size": len(context_content),
                            "processing_timestamp": datetime.now().isoformat(),
                            "chunking_method": "context_overlap"
                        }
                    }
                    enhanced_chunks.append(context_chunk)
            
            # Add context after the chunk
            context_end = min(len(lines), end_line + 1 + self.chunk_overlap)
            if context_end > end_line + 1:
                context_lines = lines[end_line + 1:context_end]
                if context_lines:
                    context_content = '\n'.join(context_lines)
                    context_id = f"{scan_id}_{repo_type}_{file_path.name}_context_after_{end_line}"
                    
                    context_chunk = {
                        "id": context_id,
                        "content": context_content,
                        "metadata": {
                            "scan_id": scan_id,
                            "repo_type": repo_type,
                            "file_path": str(file_path.relative_to(repo_root)),
                            "filename": file_path.name,
                            "language": language,
                            "start_line": end_line + 2,
                            "end_line": context_end,
                            "chunk_size": len(context_content),
                            "processing_timestamp": datetime.now().isoformat(),
                            "chunking_method": "context_overlap"
                        }
                    }
                    enhanced_chunks.append(context_chunk)
        
        return enhanced_chunks
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks using existing embedding service"""
        try:
            # Use existing embedding service with URL-based endpoints
            from services.embedding_service import EmbeddingService
            
            # Create embedding service with same config as main service
            embedding_config = {
                "provider": "local",
                "model": self.embedding_model,
                "base_url": "http://localhost:1234",  # LM Studio endpoint
                "batch_size": 8,  # Smaller batch size for better reliability
                "vector_size": self.vector_size,
                "timeout": 30
            }
            
            embedding_service = EmbeddingService(embedding_config)
            
            # Generate embeddings in batches
            all_embeddings = []
            batch_size = embedding_config["batch_size"]
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                try:
                    batch_embeddings = await embedding_service.generate_embeddings(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                except Exception as e:
                    print(f"⚠️ Failed to generate embeddings for batch {i//batch_size + 1}: {e}")
                    # Add zero vectors as fallback
                    all_embeddings.extend([[0.0] * self.vector_size] * len(batch_texts))
            
            return all_embeddings
            
        except Exception as e:
            print(f"❌ Failed to generate embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.vector_size] * len(texts)
    
    async def _store_vectors(self, collection_name: str, chunks: List[Dict[str, Any]], 
                           embeddings: List[List[float]]) -> bool:
        """Store vectors in Qdrant"""
        try:
            # Prepare points for Qdrant
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point = PointStruct(
                    id=hash(chunk["id"]) % (2**63),  # Generate numeric ID
                    vector=embedding,
                    payload={
                        "scan_id": chunk["metadata"]["scan_id"],
                        "repo_type": chunk["metadata"]["repo_type"],
                        "file_path": chunk["metadata"]["file_path"],
                        "filename": chunk["metadata"]["filename"],
                        "language": chunk["metadata"]["language"],
                        "start_line": chunk["metadata"]["start_line"],
                        "end_line": chunk["metadata"]["end_line"],
                        "content": chunk["content"],
                        "chunk_size": chunk["metadata"]["chunk_size"],
                        "chunking_method": chunk["metadata"].get("chunking_method", "unknown"),
                        "node_type": chunk["metadata"].get("node_type", ""),
                        "processing_timestamp": chunk["metadata"]["processing_timestamp"]
                    }
                )
                points.append(point)
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            print(f"💾 Stored {len(points)} vectors in collection {collection_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store vectors: {e}")
            return False
    
    async def index_repository(self, repo_path: str, scan_id: str, repo_type: str = "main") -> Dict[str, Any]:
        """Index repository using enhanced AST-based chunking"""
        try:
            repo_path = Path(repo_path)
            if not repo_path.exists():
                return {
                    "indexing_successful": False,
                    "error": f"Repository path does not exist: {repo_path}"
                }
            
            print(f"🔍 Indexing {repo_type} repository: {repo_path}")
            
            # Create collection name
            collection_name = f"repo_{scan_id}_{repo_type}" if repo_type != "main" else f"repo_{scan_id}"
            
            # Create collection if it doesn't exist
            if not self.collection_exists(collection_name):
                self._create_collection(collection_name)
            
            # Process files
            all_chunks = []
            processed_files = 0
            
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    try:
                        # Detect language
                        language = self._detect_language(file_path)
                        
                        # Skip unsupported languages
                        if language not in self.parsers and language != 'text':
                            continue
                        
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if not content.strip():
                            continue
                        
                        # Create chunks using AST-based parsing
                        chunks = self._create_ast_based_chunks(
                            content, file_path, repo_path, scan_id, language, repo_type
                        )
                        
                        all_chunks.extend(chunks)
                        processed_files += 1
                        
                        if processed_files % 10 == 0:
                            print(f"📁 Processed {processed_files} files, {len(all_chunks)} chunks so far...")
                    
                    except Exception as e:
                        print(f"⚠️ Failed to process {file_path}: {e}")
                        continue
            
            if not all_chunks:
                return {
                    "indexing_successful": False,
                    "error": "No chunks generated from repository"
                }
            
            # Generate embeddings
            print(f"🧠 Generating embeddings for {len(all_chunks)} chunks...")
            chunk_texts = [chunk["content"] for chunk in all_chunks]
            embeddings = await self._generate_embeddings(chunk_texts)
            
            # Store vectors
            print(f"💾 Storing {len(all_chunks)} vectors in Qdrant...")
            success = await self._store_vectors(collection_name, all_chunks, embeddings)
            
            if not success:
                return {
                    "indexing_successful": False,
                    "error": "Failed to store vectors in Qdrant"
                }
            
            # Get collection info
            collection_info = self._get_collection_info(collection_name)
            
            # Calculate chunking statistics
            ast_chunks = sum(1 for chunk in all_chunks if chunk["metadata"].get("chunking_method") == "ast_based")
            regex_chunks = sum(1 for chunk in all_chunks if chunk["metadata"].get("chunking_method") == "regex_based")
            context_chunks = sum(1 for chunk in all_chunks if chunk["metadata"].get("chunking_method") == "context_overlap")
            
            print(f"✅ Enhanced indexing completed for {repo_type} repository")
            print(f"📊 Collection: {collection_name}")
            print(f"📁 Total files: {processed_files}")
            print(f"📄 Total chunks: {len(all_chunks)}")
            print(f"🔧 AST-based chunks: {ast_chunks}")
            print(f"🔍 Regex-based chunks: {regex_chunks}")
            print(f"🔗 Context chunks: {context_chunks}")
            
            return {
                "indexing_successful": True,
                "collection_name": collection_name,
                "total_files": processed_files,
                "total_chunks": len(all_chunks),
                "ast_chunks": ast_chunks,
                "regex_chunks": regex_chunks,
                "context_chunks": context_chunks,
                "collection_info": collection_info
            }
            
        except Exception as e:
            print(f"❌ Enhanced indexing failed: {e}")
            return {
                "indexing_successful": False,
                "error": str(e)
            }
    
    def search_similar(self, collection_name: str, query: str, limit: int = 10, 
                      score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar code chunks"""
        try:
            # Generate query embedding
            from services.embedding_service import EmbeddingService
            
            embedding_config = {
                "provider": "local",
                "model": self.embedding_model,
                "base_url": "http://localhost:1234",
                "vector_size": self.vector_size
            }
            
            embedding_service = EmbeddingService(embedding_config)
            query_vector = asyncio.run(embedding_service.generate_embeddings([query]))[0]
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for point in search_result:
                results.append({
                    "scan_id": point.payload.get("scan_id"),
                    "filename": point.payload.get("filename"),
                    "file_path": point.payload.get("file_path"),
                    "location": f"{point.payload.get('start_line')}-{point.payload.get('end_line')}",
                    "code": point.payload.get("content", ""),
                    "score": point.score,
                    "chunking_method": point.payload.get("chunking_method", "unknown"),
                    "node_type": point.payload.get("node_type", ""),
                    "language": point.payload.get("language", "")
                })
            
            return results
                    
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def _create_collection(self, collection_name: str):
        """Create Qdrant collection"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"📊 Created collection: {collection_name}")
        except Exception as e:
            print(f"⚠️ Collection {collection_name} might already exist: {e}")
    
    def _get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information from Qdrant"""
        try:
            collection_info = self.client.get_collection(collection_name)
            if collection_info:
                return {
                    "count": collection_info.points_count,
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance
                }
            else:
                return {"count": 0, "vector_size": 0, "distance": None}
        except Exception as e:
            print(f"⚠️ Could not get collection info: {e}")
            return {"count": 0, "vector_size": 0, "distance": None}
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in Qdrant"""
        try:
            collections = self.client.get_collections()
            return any(col.name == collection_name for col in collections.collections)
        except Exception as e:
            print(f"⚠️ Could not check collection existence: {e}")
            return False
    
    def cleanup_collection(self, collection_name: str) -> bool:
        """Clean up collection from Qdrant"""
        try:
            self.client.delete_collection(collection_name)
            print(f"🧹 Cleaned up collection: {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to cleanup collection: {e}")
            return False
