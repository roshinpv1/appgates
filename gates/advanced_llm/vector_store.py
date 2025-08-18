"""
Vector Store Component
Manages vector embeddings and similarity search
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ Qdrant not available, using in-memory storage")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available")


@dataclass
class SearchResult:
    """Search result from vector store"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


class VectorStore:
    """
    Vector store for managing embeddings and similarity search
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize vector store"""
        self.config = config
        self.vector_size = config.get("vector_size", 1536)  # OpenAI embedding size
        self.distance_metric = config.get("distance_metric", "cosine")
        
        # Initialize storage
        if QDRANT_AVAILABLE and config.get("use_qdrant", True):
            self._init_qdrant()
        else:
            self._init_memory_store()
        
        print(f"💾 VectorStore initialized with {self.vector_size} dimensions")
    
    def _init_qdrant(self):
        """Initialize embedded Qdrant client"""
        try:
            # Use embedded Qdrant (in-memory or local file)
            qdrant_path = self.config.get("qdrant_path", ":memory:")
            print(f"🔧 Attempting to initialize Qdrant at {qdrant_path}")
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
                # Create collection in Qdrant
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
            else:
                # Create collection in memory
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
        """Upsert vectors into collection"""
        try:
            if self.use_qdrant:
                # Prepare points for Qdrant
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
                
                # Upsert to Qdrant
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
            else:
                # Upsert to memory store
                if collection_name not in self.vectors:
                    self.vectors[collection_name] = []
                
                # Update or add vectors
                for vector_data in vectors:
                    vector_id = vector_data["id"]
                    
                    # Remove existing vector with same ID
                    self.vectors[collection_name] = [
                        v for v in self.vectors[collection_name] 
                        if v["id"] != vector_id
                    ]
                    
                    # Add new vector
                    self.vectors[collection_name].append(vector_data)
                
                # Update collection count
                if collection_name in self.collections:
                    self.collections[collection_name]["count"] = len(self.vectors[collection_name])
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to upsert vectors to collection {collection_name}: {e}")
            return False
    
    def search_similar(self, collection_name: str, query_vector: List[float], 
                           limit: int = 10, score_threshold: float = 0.7) -> List[SearchResult]:
        """Search for similar vectors"""
        try:
            if self.use_qdrant:
                # Search in Qdrant
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
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            if self.use_qdrant:
                # Delete collection from Qdrant
                self.client.delete_collection(collection_name=collection_name)
                return True
            else:
                if collection_name in self.collections:
                    del self.collections[collection_name]
                if collection_name in self.vectors:
                    del self.vectors[collection_name]
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete collection {collection_name}: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            if self.use_qdrant:
                # Get actual stats from Qdrant
                try:
                    collection_info = self.client.get_collection(collection_name=collection_name)
                    return {
                        "name": collection_name,
                        "vector_size": collection_info.config.params.vectors.size,
                        "count": collection_info.points_count,
                        "status": "ok"
                    }
                except Exception as e:
                    print(f"⚠️ Failed to get collection stats for {collection_name}: {e}")
                    return {
                        "name": collection_name,
                        "vector_size": 768,  # Default for nomic-embed-text
                        "count": 0,
                        "status": "error"
                    }
            else:
                if collection_name in self.collections:
                    return {
                        "name": collection_name,
                        "vector_size": self.collections[collection_name]["vector_size"],
                        "count": self.collections[collection_name]["count"],
                        "status": "ok"
                    }
                else:
                    return {"error": "Collection not found"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not NUMPY_AVAILABLE:
            # Fallback to manual calculation
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            magnitude1 = sum(a * a for a in vector1) ** 0.5
            magnitude2 = sum(b * b for b in vector2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        else:
            # Use NumPy for faster calculation
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            dot_product = np.dot(v1, v2)
            magnitude1 = np.linalg.norm(v1)
            magnitude2 = np.linalg.norm(v2)
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for vector store"""
        try:
            if self.use_qdrant:
                # Get actual collections from Qdrant
                try:
                    collections = self.client.get_collections()
                    collection_count = len(collections.collections)
                    return {
                        "status": "healthy",
                        "backend": "qdrant",
                        "collections": collection_count
                    }
                except Exception as e:
                    print(f"⚠️ Failed to get Qdrant collections: {e}")
                    return {
                        "status": "healthy",
                        "backend": "qdrant",
                        "collections": 0
                    }
            else:
                # Check memory store
                return {
                    "status": "healthy",
                    "backend": "memory",
                    "collections": len(self.collections)
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
