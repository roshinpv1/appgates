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
    
    def search(self, collection_name: str, query: str, 
               limit: int = 10, score_threshold: float = 0.7) -> List[SearchResult]:
        """Search for similar vectors using text query"""
        try:
            # Convert text query to embedding
            from services.embedding_service import EmbeddingService
            embedding_service = EmbeddingService(self.config)
            query_vector = embedding_service.embed_single(query)
            
            return self.search_similar(collection_name, query_vector, limit, score_threshold)
            
        except Exception as e:
            print(f"❌ Failed to search collection {collection_name} with query '{query}': {e}")
            return []

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
            
            # Search in single collection for both main and CD repositories
            collection = f"repo_{scan_id}"
            
            # Enhanced queries for better project analysis
            queries = [
                # Technology and framework detection
                "spring boot java application framework",
                "maven gradle build configuration dependencies",
                "database configuration mysql postgresql h2",
                "application properties configuration setup",
                "main application class controller service",
                "testing framework junit mockito test",
                "logging configuration logback log4j",
                "security authentication authorization",
                "docker kubernetes deployment configuration",
                "monitoring health check actuator",
                "api rest controller endpoint",
                "entity model data structure",
                "repository data access layer",
                "service business logic layer",
                "web security configuration",
                "database schema sql migration",
                "application startup configuration",
                "development tools configuration",
                "production deployment setup",
                "microservices architecture patterns"
            ]
            
            all_main_results = []
            all_cd_results = []
            
            for query in queries:
                try:
                    # Generate embedding for the query
                    query_embedding = embedding_service.embed_single(query)
                    
                    if not query_embedding:
                        continue
                    
                    # Search in single collection for both main and CD repositories
                    all_results = self.search_similar(
                        collection_name=collection,
                        query_vector=query_embedding,
                        limit=30,  # Increased limit to get both main and CD results
                        score_threshold=0.05  # Even lower threshold for comprehensive results
                    )
                    
                    # Separate results by repo_type
                    for result in all_results:
                        repo_type = result.payload.get("repo_type", "main")
                        if repo_type == "main":
                            all_main_results.append(result)
                        elif repo_type == "cd":
                            all_cd_results.append(result)
                        
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
            
            # Extract comprehensive project information
            technologies = set()
            frameworks = set()
            file_types = set()
            dependencies = set()
            architecture_patterns = set()
            security_features = set()
            testing_frameworks = set()
            build_tools = set()
            deployment_configs = set()
            database_technologies = set()
            monitoring_tools = set()
            
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
                
                # Enhanced technology and framework detection patterns
                tech_patterns = {
                    # Core Technologies
                    "java": ["java", "javax", "jakarta", "jdk", "jre", "jvm"],
                    "spring": ["spring", "spring boot", "spring framework", "spring mvc", "spring data", "spring security"],
                    "maven": ["maven", "pom.xml", "mvn", "maven-compiler-plugin"],
                    "gradle": ["gradle", "build.gradle", "gradle wrapper", "gradlew"],
                    
                    # Database Technologies
                    "h2": ["h2", "h2 database", "h2console"],
                    "mysql": ["mysql", "mariadb", "mysql connector"],
                    "postgresql": ["postgresql", "postgres", "psql"],
                    "jpa": ["jpa", "hibernate", "entity", "@entity", "@table"],
                    "jdbc": ["jdbc", "datasource", "connection pool"],
                    
                    # Testing Frameworks
                    "junit": ["junit", "junit5", "@test", "testng"],
                    "mockito": ["mockito", "@mock", "@injectmocks"],
                    "spring test": ["@springboottest", "@webmvctest", "@datajpatest"],
                    
                    # Security
                    "spring security": ["spring security", "security config", "@secured", "@preauthorize"],
                    "oauth": ["oauth", "oauth2", "jwt", "token"],
                    
                    # Monitoring and Health
                    "actuator": ["actuator", "health check", "metrics", "prometheus"],
                    "logging": ["logback", "log4j", "slf4j", "logging", "logger"],
                    
                    # Build and Deployment
                    "docker": ["docker", "dockerfile", "container"],
                    "kubernetes": ["kubernetes", "k8s", "helm", "deployment"],
                    "jenkins": ["jenkins", "pipeline", "ci/cd"],
                    "github actions": ["github actions", "workflow", ".github/workflows"],
                    
                    # Web Technologies
                    "thymeleaf": ["thymeleaf", "html template", "template engine"],
                    "bootstrap": ["bootstrap", "css framework"],
                    "jquery": ["jquery", "javascript library"],
                    
                    # Development Tools
                    "devcontainer": ["devcontainer", "docker compose", "development environment"],
                    "git": ["git", "gitignore", "version control"],
                    
                    # Application Patterns
                    "mvc": ["mvc", "model view controller", "@controller", "@service", "@repository"],
                    "rest": ["rest", "restful", "@restcontroller", "@requestmapping"],
                    "microservices": ["microservices", "service discovery", "api gateway"],
                    
                    # Configuration
                    "properties": ["application.properties", "application.yml", "yaml", "configuration"],
                    "profiles": ["@profile", "spring profiles", "environment specific"]
                }
                
                # Enhanced technology detection with categorization
                for tech, patterns in tech_patterns.items():
                    if any(pattern in content for pattern in patterns):
                        technologies.add(tech)
                        
                        # Categorize technologies
                        if tech in ["java", "spring", "maven", "gradle"]:
                            frameworks.add(tech)
                        elif tech in ["h2", "mysql", "postgresql", "jpa", "jdbc"]:
                            database_technologies.add(tech)
                        elif tech in ["junit", "mockito", "spring test"]:
                            testing_frameworks.add(tech)
                        elif tech in ["spring security", "oauth"]:
                            security_features.add(tech)
                        elif tech in ["actuator", "logging"]:
                            monitoring_tools.add(tech)
                        elif tech in ["docker", "kubernetes", "jenkins", "github actions"]:
                            deployment_configs.add(tech)
                        elif tech in ["maven", "gradle"]:
                            build_tools.add(tech)
                        elif tech in ["mvc", "rest", "microservices"]:
                            architecture_patterns.add(tech)
                
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
            
            # Generate comprehensive project summary
            summary = f"Project analysis for {repo_url} reveals a comprehensive "
            
            # Technology stack
            if frameworks:
                framework_list = list(frameworks)[:3]
                summary += f"technology stack built on {', '.join(framework_list)}. "
            elif technologies:
                tech_list = list(technologies)[:3]
                summary += f"technology stack using {', '.join(tech_list)}. "
            else:
                summary += "technology stack. "
            
            # Architecture patterns
            if architecture_patterns:
                arch_list = list(architecture_patterns)[:2]
                summary += f"The application follows {', '.join(arch_list)} architecture patterns. "
            
            # Database technologies
            if database_technologies:
                db_list = list(database_technologies)[:2]
                summary += f"Database layer uses {', '.join(db_list)}. "
            
            # Security features
            if security_features:
                sec_list = list(security_features)[:2]
                summary += f"Security is implemented using {', '.join(sec_list)}. "
            
            # Testing approach
            if testing_frameworks:
                test_list = list(testing_frameworks)[:2]
                summary += f"Testing is handled with {', '.join(test_list)}. "
            
            # Monitoring and logging
            if monitoring_tools:
                monitor_list = list(monitoring_tools)[:2]
                summary += f"Monitoring and logging use {', '.join(monitor_list)}. "
            
            # Build and deployment
            if build_tools:
                build_list = list(build_tools)[:2]
                summary += f"Build process uses {', '.join(build_list)}. "
            
            if deployment_configs:
                deploy_list = list(deployment_configs)[:2]
                summary += f"Deployment configuration includes {', '.join(deploy_list)}. "
            
            # File structure
            if file_types:
                file_list = list(file_types)[:5]
                summary += f"The codebase contains {', '.join(file_list)} file types. "
            
            # Dependencies
            if dependencies:
                dep_list = list(dependencies)[:5]
                summary += f"Key dependencies include {', '.join(dep_list)}. "
            
            # CD repository
            if cd_results:
                summary += "The project includes a separate CD (Continuous Deployment) repository for infrastructure and deployment configurations. "
            
            summary += "The analysis focuses on evaluating compliance with hard gates across auditability, error handling, availability, and testing categories."
            
            return {
                "summary": summary,
                "technologies": list(technologies),
                "frameworks": list(frameworks),
                "file_types": list(file_types),
                "dependencies": list(dependencies),
                "architecture_patterns": list(architecture_patterns),
                "security_features": list(security_features),
                "testing_frameworks": list(testing_frameworks),
                "build_tools": list(build_tools),
                "deployment_configs": list(deployment_configs),
                "database_technologies": list(database_technologies),
                "monitoring_tools": list(monitoring_tools),
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
