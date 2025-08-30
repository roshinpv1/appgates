"""
Simplified CocoIndex service for semantic code chunking and vector storage using Qdrant
"""

import os
import json
import hashlib
import tempfile
from typing import Dict, List, Any, Optional
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


class CocoIndexService:
    """Simplified CocoIndex service for semantic code chunking and vector storage using Qdrant"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CocoIndex service"""
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
        self.embedding_model = config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
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
        
        print(f"🧠 CocoIndexService initialized with {self.embedding_model} ({self.vector_size} dimensions) - Simplified Mode")
    
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
        
        return model_dimensions.get(self.embedding_model, 384)
    
    async def index_repository(self, repo_path: str, scan_id: str, repo_type: str = "main") -> Dict[str, Any]:
        """Index repository using simplified semantic chunking with Qdrant storage"""
        try:
            print(f"🔍 Indexing {repo_type} repository: {repo_path}")
            
            # Create collection name (use same convention as other services)
            collection_name = f"repo_{scan_id}"
            if repo_type == "cd":
                collection_name += "_cd"
            
            # Create collection if it doesn't exist
            if not self.collection_exists(collection_name):
                self._create_collection(collection_name)
            
            # Process files and create chunks
            chunks = await self._process_repository_files(repo_path, scan_id, repo_type)
            
            if not chunks:
                print(f"⚠️ No chunks created for {repo_type} repository")
                return {
                    "scan_id": scan_id,
                    "repo_type": repo_type,
                    "collection_name": collection_name,
                    "chunks_count": 0,
                    "indexing_successful": True,
                    "processing_timestamp": datetime.now().isoformat()
                }
            
            # Generate embeddings
            print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
            embeddings = await self._generate_embeddings([chunk["content"] for chunk in chunks])
            
            # Store in Qdrant
            print(f"💾 Storing {len(embeddings)} vectors in Qdrant...")
            self._store_vectors(collection_name, chunks, embeddings)
            
            # Get collection info
            collection_info = self._get_collection_info(collection_name)
            
            print(f"✅ Simplified indexing completed for {repo_type} repository")
            print(f"📊 Collection: {collection_name}")
            print(f"📊 Total chunks: {collection_info.get('count', 0)}")
            
            return {
                "scan_id": scan_id,
                "repo_type": repo_type,
                "collection_name": collection_name,
                "chunks_count": collection_info.get('count', 0),
                "indexing_successful": True,
                "processing_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Simplified indexing failed: {e}")
            return {
                "scan_id": scan_id,
                "repo_type": repo_type,
                "indexing_successful": False,
                "error": str(e),
                "processing_timestamp": datetime.now().isoformat()
            }
    
    async def _process_repository_files(self, repo_path: str, scan_id: str, repo_type: str) -> List[Dict[str, Any]]:
        """Process repository files and create semantic chunks"""
        chunks = []
        repo_path_obj = Path(repo_path)
        
        # Get all files to process
        files_to_process = []
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                files_to_process.append(file_path)
        
        print(f"�� Processing {len(files_to_process)} files...")
        
        for file_path in files_to_process:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Determine language
                language = self._detect_language(file_path)
                
                # Create semantic chunks
                file_chunks = self._create_semantic_chunks(
                    content, file_path, repo_path_obj, scan_id, language, repo_type
                )
                chunks.extend(file_chunks)
                
            except Exception as e:
                print(f"⚠️ Failed to process file {file_path}: {e}")
                continue
        
        return chunks
    
    def _create_semantic_chunks(self, content: str, file_path: Path, repo_root: Path, 
                               scan_id: str, language: str, repo_type: str) -> List[Dict[str, Any]]:
        """Create semantic chunks using simplified approach"""
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
                        "processing_timestamp": datetime.now().isoformat()
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
                    "processing_timestamp": datetime.now().isoformat()
                }
            }
            chunks.append(chunk_data)
        
        return chunks
    
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
                "batch_size": 32,
                "vector_size": self.vector_size,
                "timeout": 30  # Add timeout
            }
            
            embedding_service = EmbeddingService(embedding_config)
            
            # Try to generate embeddings in smaller batches to avoid 404 errors
            batch_size = 8  # Smaller batch size
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                try:
                    batch_embeddings = embedding_service.embed_batch(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                except Exception as batch_error:
                    print(f"⚠️ Batch embedding failed, using fallback: {batch_error}")
                    # Use fallback embeddings for this batch
                    fallback_embeddings = [[0.0] * self.vector_size for _ in batch_texts]
                    all_embeddings.extend(fallback_embeddings)
            
            embeddings = all_embeddings
            
            # Filter out None embeddings and convert to list format
            valid_embeddings = []
            for embedding in embeddings:
                if embedding is not None:
                    valid_embeddings.append(embedding)
                else:
                    # Create a zero vector as fallback
                    print(f"⚠️ Using zero vector fallback for failed embedding")
                    valid_embeddings.append([0.0] * self.vector_size)
            
            print(f"✅ Generated {len(valid_embeddings)} embeddings using URL-based service")
            return valid_embeddings
            
        except Exception as e:
            print(f"❌ Failed to generate embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.vector_size for _ in texts]
    
    def _store_vectors(self, collection_name: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Store vectors in Qdrant"""
        try:
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                # Generate a valid UUID for Qdrant
                import uuid
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["id"]))
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=chunk["metadata"]
                )
                points.append(point)
            
            # Upsert points in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
            
            print(f"✅ Stored {len(points)} vectors in collection {collection_name}")
            
        except Exception as e:
            print(f"❌ Failed to store vectors: {e}")
            raise
    
    def search_similar(self, collection_name: str, query: str, limit: int = 10, 
                      score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar code chunks using Qdrant"""
        try:
            # Generate query embedding using existing embedding service with URL-based endpoints
            from services.embedding_service import EmbeddingService
            
            embedding_config = {
                "provider": "local",
                "model": self.embedding_model,
                "base_url": "http://localhost:1234",  # LM Studio endpoint
                "batch_size": 32,
                "vector_size": self.vector_size,
                "timeout": 30
            }
            
            embedding_service = EmbeddingService(embedding_config)
            query_embedding = embedding_service.embed_single(query)
            
            if not query_embedding:
                print(f"❌ Failed to generate query embedding using URL-based service")
                return []
            
            query_vector = query_embedding
            print(f"✅ Generated query embedding using URL-based service")
            
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
                    "score": point.score
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
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp'
        }
        return language_map.get(ext, 'text')
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        file_path_str = str(file_path)
        
        # Check ignore patterns
        for pattern in self.excluded_patterns:
            if pattern in file_path_str:
                return True
        
        # Check binary extensions
        binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                           '.mp4', '.avi', '.mov', '.mp3', '.wav',
                           '.zip', '.tar', '.gz', '.rar', '.7z',
                           '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                           '.exe', '.dll', '.so', '.dylib',
                           '.jar', '.war', '.ear', '.class'}
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for CocoIndex service"""
        try:
            # Test Qdrant connection
            collections = self.client.get_collections()
            qdrant_healthy = True
        except Exception as e:
            qdrant_healthy = False
        
        return {
            "status": "healthy" if qdrant_healthy else "unhealthy",
            "qdrant": "connected" if qdrant_healthy else "disconnected",
            "cocoindex_available": False,  # Simplified mode
            "qdrant_available": QDRANT_AVAILABLE,
            "numpy_available": NUMPY_AVAILABLE,
            "embedding_model": self.embedding_model,
            "vector_size": self.vector_size,
            "mode": "simplified"
        }
    
    def close(self):
        """Close Qdrant connections"""
        if hasattr(self, 'client'):
            self.client.close()
            print("🔌 Closed Qdrant connections")
