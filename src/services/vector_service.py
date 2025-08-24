"""
Vector service for embeddings and similarity search
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available")

try:
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ Qdrant not available, using in-memory storage")


@dataclass
class SearchResult:
    """Search result from vector store"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


class VectorService:
    """Vector service for embeddings and similarity search"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize vector service"""
        self.config = config
        self.vector_size = config.get("vector_size", 768)
        self.distance_metric = config.get("distance_metric", "cosine")
        
        # Initialize storage
        if QDRANT_AVAILABLE and config.get("use_qdrant", True):
            self._init_qdrant()
        else:
            self._init_memory_store()
        
        print(f"💾 VectorService initialized with {self.vector_size} dimensions")
    
    def _init_qdrant(self):
        """Initialize Qdrant client"""
        try:
            qdrant_path = self.config.get("qdrant_path", ":memory:")
            print(f"🔧 Attempting to initialize Qdrant at {qdrant_path}")
            
            # For embedded Qdrant, ensure the directory exists
            if qdrant_path != ":memory:":
                import os
                os.makedirs(qdrant_path, exist_ok=True)
                
                # Check if there's a lock file and remove it if it's stale
                lock_file = os.path.join(qdrant_path, ".lock")
                if os.path.exists(lock_file):
                    try:
                        # Try to remove stale lock file
                        os.remove(lock_file)
                        print(f"🔓 Removed stale lock file")
                    except Exception as e:
                        print(f"⚠️ Could not remove lock file: {e}")
            
            self.client = QdrantClient(path=qdrant_path)
            self.use_qdrant = True
            print(f"🔗 Successfully initialized embedded Qdrant at {qdrant_path}")
            print(f"🔧 use_qdrant flag set to: {self.use_qdrant}")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize embedded Qdrant: {e}, falling back to memory store")
            self._init_memory_store()
    
    def _init_memory_store(self):
        """Initialize in-memory vector store"""
        self.use_qdrant = False
        self.collections = {}
        self.vectors = {}
        print("💾 Using in-memory vector store")
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a new collection"""
        try:
            if self.use_qdrant:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
            else:
                self.collections[collection_name] = {
                    "name": collection_name,
                    "vector_size": self.vector_size,
                    "count": 0
                }
                self.vectors[collection_name] = []
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create collection {collection_name}: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            if self.use_qdrant:
                collections = self.client.get_collections()
                return any(col.name == collection_name for col in collections.collections)
            else:
                return collection_name in self.collections
        except Exception:
            return False
    
    def upsert_vectors(self, collection_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """Upsert vectors to collection"""
        try:
            if not self.collection_exists(collection_name):
                self.create_collection(collection_name)
            
            if self.use_qdrant:
                points = []
                for vector_data in vectors:
                    # Convert string ID to UUID if needed
                    point_id = vector_data["id"]
                    if isinstance(point_id, str):
                        import uuid
                        # Generate UUID from string ID for consistency
                        point_id = uuid.uuid5(uuid.NAMESPACE_DNS, point_id)
                    
                    # Convert UUID to string for Qdrant
                    if hasattr(point_id, 'hex'):
                        point_id = str(point_id)
                    
                    point = PointStruct(
                        id=point_id,
                        vector=vector_data["vector"],
                        payload=vector_data["payload"]
                    )
                    points.append(point)
                
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
            else:
                # Update in-memory store
                for vector_data in vectors:
                    # Remove existing if present
                    self.vectors[collection_name] = [
                        v for v in self.vectors[collection_name] 
                        if v["id"] != vector_data["id"]
                    ]
                    # Add new vector
                    self.vectors[collection_name].append(vector_data)
                
                self.collections[collection_name]["count"] = len(self.vectors[collection_name])
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to upsert vectors to {collection_name}: {e}")
            return False
    
    def search_similar(self, collection_name: str, query_vector: List[float], 
                      limit: int = 10, score_threshold: float = 0.7) -> List[SearchResult]:
        """Search for similar vectors"""
        try:
            if self.use_qdrant:
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold
                )
                
                results = []
                for result in search_result:
                    results.append(SearchResult(
                        id=result.id,
                        score=result.score,
                        payload=result.payload
                    ))
                
                return results
                
            else:
                # Search in memory store
                if collection_name not in self.vectors:
                    return []
                
                results = []
                vectors = self.vectors[collection_name]
                
                for vector_data in vectors:
                    score = self._calculate_similarity(query_vector, vector_data["vector"])
                    if score >= score_threshold:
                        results.append(SearchResult(
                            id=vector_data["id"],
                            score=score,
                            payload=vector_data["payload"]
                        ))
                
                # Sort by score and limit
                results.sort(key=lambda x: x.score, reverse=True)
                return results[:limit]
                
        except Exception as e:
            print(f"❌ Failed to search collection {collection_name}: {e}")
            return []
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not NUMPY_AVAILABLE:
            # Simple cosine similarity without numpy
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        else:
            # Use numpy for better performance
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)
            
            dot_product = np.dot(vec1_array, vec2_array)
            norm1 = np.linalg.norm(vec1_array)
            norm2 = np.linalg.norm(vec2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            if self.use_qdrant:
                self.client.delete_collection(collection_name=collection_name)
            else:
                if collection_name in self.collections:
                    del self.collections[collection_name]
                if collection_name in self.vectors:
                    del self.vectors[collection_name]
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete collection {collection_name}: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        try:
            if self.use_qdrant:
                collection_info = self.client.get_collection(collection_name=collection_name)
                return {
                    "name": collection_name,  # Use the input collection_name instead of collection_info.name
                    "vector_size": collection_info.config.params.vectors.size,
                    "count": collection_info.points_count
                }
            else:
                if collection_name in self.collections:
                    return {
                        "name": collection_name,
                        "vector_size": self.collections[collection_name]["vector_size"],
                        "count": self.collections[collection_name]["count"]
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get collection info for {collection_name}: {e}")
            return None
    
    def generate_project_summary(self, repo_url: str, scan_id: str) -> Dict[str, Any]:
        """Generate project summary from vector database"""
        try:
            from services.embedding_service import EmbeddingService
            
            # Initialize embedding service
            embedding_service = EmbeddingService(self.config)
            
            # Search in main repository collection
            main_collection = f"repo_{scan_id}"
            cd_collection = f"repo_{scan_id}_cd"
            
            # Try multiple queries to get better results
            queries = [
                "project technologies frameworks dependencies",
                "main application setup configuration",
                "spring boot java application",
                "project structure and dependencies",
                "application configuration files",
                "main technologies used in project",
                "framework and library dependencies",
                "project setup and requirements"
            ]
            
            all_main_results = []
            all_cd_results = []
            
            for query in queries:
                try:
                    # Generate embedding for the query
                    query_embedding = embedding_service.embed_single(query)
                    
                    if not query_embedding:
                        continue
                    
                    # Search in main collection with lower threshold
                    main_results = self.search_similar(
                        collection_name=main_collection,
                        query_vector=query_embedding,
                        limit=10,
                        score_threshold=0.1  # Lower threshold for better results
                    )
                    all_main_results.extend(main_results)
                    
                    # Search in CD collection if it exists
                    try:
                        if self.collection_exists(cd_collection):
                            cd_results = self.search_similar(
                                collection_name=cd_collection,
                                query_vector=query_embedding,
                                limit=5,
                                score_threshold=0.1
                            )
                            all_cd_results.extend(cd_results)
                    except Exception as e:
                        # Silently ignore CD collection errors - it's expected for repos without CD
                        pass
                        
                except Exception as e:
                    print(f"⚠️ Query '{query}' failed: {e}")
                    continue
            
            # Remove duplicates based on content hash
            seen_hashes = set()
            unique_main_results = []
            for result in all_main_results:
                content_hash = result.payload.get("content_hash", "")
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    unique_main_results.append(result)
            
            seen_hashes = set()
            unique_cd_results = []
            for result in all_cd_results:
                content_hash = result.payload.get("content_hash", "")
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    unique_cd_results.append(result)
            
            # Extract relevant information from search results
            project_info = self._extract_project_info(unique_main_results, unique_cd_results, repo_url)
            
            return project_info
            
        except Exception as e:
            print(f"❌ Failed to generate project summary: {e}")
            return self._get_fallback_project_summary(repo_url)
    
    def _extract_project_info(self, main_results: List[SearchResult], 
                             cd_results: List[SearchResult], repo_url: str) -> Dict[str, Any]:
        """Extract project information from search results"""
        try:
            # Combine all results
            all_results = main_results + cd_results
            
            # Extract technologies and frameworks
            technologies = set()
            frameworks = set()
            file_types = set()
            dependencies = set()
            
            for result in all_results:
                payload = result.payload
                
                # Extract file information
                if "file_path" in payload:
                    file_path = payload["file_path"]
                    file_ext = file_path.split(".")[-1].lower() if "." in file_path else ""
                    if file_ext:
                        file_types.add(file_ext)
                
                # Extract content for technology detection
                content = payload.get("content", "").lower()
                
                # Detect technologies and frameworks
                tech_patterns = {
                    "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "pip", "requirements.txt", "py", "python3"],
                    "javascript": ["javascript", "node.js", "react", "vue", "angular", "express", "npm", "package.json", "js", "ts", "typescript"],
                    "java": ["java", "spring", "maven", "gradle", "junit", "javax", "jakarta", "spring boot", "spring framework", "pom.xml", "build.gradle"],
                    "go": ["go", "golang", "go.mod", "go.sum"],
                    "rust": ["rust", "cargo", "cargo.toml", "cargo.lock"],
                    "php": ["php", "laravel", "symfony", "composer.json"],
                    "ruby": ["ruby", "rails", "gemfile", "gemfile.lock"],
                    "csharp": ["c#", "dotnet", "asp.net", ".csproj", ".sln"],
                    "docker": ["docker", "dockerfile", "docker-compose", "container"],
                    "kubernetes": ["kubernetes", "k8s", "helm", "deployment.yaml", "service.yaml"],
                    "aws": ["aws", "amazon", "lambda", "ec2", "s3", "cloudformation"],
                    "azure": ["azure", "microsoft", "azure devops"],
                    "gcp": ["gcp", "google cloud", "firebase", "cloud run"],
                    "database": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch", "h2", "hibernate", "jpa"],
                    "monitoring": ["prometheus", "grafana", "jaeger", "zipkin", "actuator"],
                    "testing": ["jest", "pytest", "junit", "cypress", "selenium", "test", "spec"],
                    "build_tools": ["maven", "gradle", "ant", "make", "cmake"],
                    "web_frameworks": ["spring boot", "spring mvc", "express", "fastapi", "django", "flask"],
                    "orm": ["hibernate", "jpa", "sqlalchemy", "sequelize", "prisma"],
                    "logging": ["logback", "log4j", "slf4j", "winston", "logging"]
                }
                
                for tech, patterns in tech_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        technologies.add(tech)
                
                # Extract dependencies from specific files
                file_path = payload.get("file_path", "").lower()
                
                if "requirements.txt" in file_path:
                    deps = content.split("\n")
                    for dep in deps:
                        dep = dep.strip().split("==")[0].split(">=")[0].split("<=")[0]
                        if dep and not dep.startswith("#") and len(dep) > 0:
                            dependencies.add(dep)
                
                elif "package.json" in file_path:
                    # Extract npm dependencies
                    if "dependencies" in content:
                        try:
                            # Simple regex-like extraction
                            deps_section = content.split('"dependencies"')[1].split('}')[0]
                            for line in deps_section.split('\n'):
                                if '"' in line and ':' in line:
                                    parts = line.split('"')
                                    if len(parts) >= 2:
                                        dep = parts[1]
                                        if dep and not dep.startswith('@') and not dep.startswith('_'):
                                            dependencies.add(dep)
                        except:
                            pass
                
                elif "pom.xml" in file_path:
                    # Extract Maven dependencies
                    if "<dependency>" in content:
                        try:
                            deps = content.split("<dependency>")
                            for dep in deps[1:]:  # Skip first split
                                if "<artifactId>" in dep and "</artifactId>" in dep:
                                    artifact = dep.split("<artifactId>")[1].split("</artifactId>")[0]
                                    if artifact:
                                        dependencies.add(artifact)
                        except:
                            pass
                
                elif "build.gradle" in file_path:
                    # Extract Gradle dependencies
                    if "implementation" in content or "compile" in content:
                        lines = content.split('\n')
                        for line in lines:
                            if 'implementation' in line or 'compile' in line:
                                if "'" in line or '"' in line:
                                    try:
                                        dep = line.split("'")[1] if "'" in line else line.split('"')[1]
                                        if dep and not dep.startswith(':'):
                                            dependencies.add(dep)
                                    except:
                                        pass
            
            # Generate summary
            summary = f"Project analysis for {repo_url} reveals a "
            
            if technologies:
                tech_list = list(technologies)[:5]  # Top 5 technologies
                summary += f"technology stack primarily using {', '.join(tech_list)}. "
            
            if file_types:
                file_list = list(file_types)[:5]  # Top 5 file types
                summary += f"The codebase contains {', '.join(file_list)} files. "
            
            if dependencies:
                dep_list = list(dependencies)[:5]  # Top 5 dependencies
                summary += f"Key dependencies include {', '.join(dep_list)}. "
            
            if cd_results:
                summary += "The project includes a separate CD (Continuous Deployment) repository for infrastructure and deployment configurations. "
            
            summary += "The analysis focuses on evaluating compliance with hard gates across auditability, error handling, availability, and testing categories."
            
            return {
                "summary": summary,
                "technologies": list(technologies),
                "frameworks": list(frameworks),
                "file_types": list(file_types),
                "dependencies": list(dependencies),
                "has_cd_repo": len(cd_results) > 0,
                "total_files_analyzed": len(all_results)
            }
            
        except Exception as e:
            print(f"❌ Failed to extract project info: {e}")
            return self._get_fallback_project_summary(repo_url)
    
    def _get_fallback_project_summary(self, repo_url: str) -> Dict[str, Any]:
        """Get fallback project summary when vector search fails"""
        return {
            "summary": f"Project analysis for {repo_url}. The codebase has been analyzed for compliance with hard gates across auditability, error handling, availability, and testing categories. Detailed analysis results are provided in the gate evaluation sections below.",
            "technologies": [],
            "frameworks": [],
            "file_types": [],
            "dependencies": [],
            "has_cd_repo": False,
            "total_files_analyzed": 0
        }
