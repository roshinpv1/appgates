"""
Embedding service for generating vector embeddings
"""

import os
import json
import hashlib
import requests
from typing import Dict, List, Any, Optional
import time

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available")


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize embedding service"""
        self.config = config
        self.provider = config.get("provider", "local")
        self.model = config.get("model", "text-embedding-nomic-embed-text-v1.5-embedding")
        self.base_url = config.get("base_url", "http://localhost:1234")
        self.api_key = config.get("api_key")
        self.batch_size = config.get("batch_size", 32)
        self.vector_size = config.get("vector_size", 768)
        
        # Cache for embeddings
        self.embedding_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        print(f"🧠 EmbeddingService initialized with {self.provider} provider")
    
    def embed_single(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        try:
            # Check cache first
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.embedding_cache:
                self.cache_hits += 1
                return self.embedding_cache[text_hash]
            
            self.cache_misses += 1
            
            # Generate embedding
            if self.provider == "local":
                embedding = self._embed_local(text)
            elif self.provider == "openai":
                embedding = self._embed_openai(text)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Cache the result
            if embedding:
                self.embedding_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            print(f"❌ Failed to generate embedding: {e}")
            return None
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts"""
        try:
            embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                if self.provider == "local":
                    batch_embeddings = self._embed_batch_local(batch)
                elif self.provider == "openai":
                    batch_embeddings = self._embed_batch_openai(batch)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
                
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    def _embed_local(self, text: str) -> Optional[List[float]]:
        """Generate embedding using local model (LM Studio)"""
        try:
            # Prepare request for LM Studio
            payload = {
                "model": self.model,
                "input": text,
                "encoding_format": "float"
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                headers=headers,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result["data"][0]["embedding"]
                
                # Validate embedding size
                if len(embedding) != self.vector_size:
                    print(f"⚠️ Unexpected embedding size: {len(embedding)}, expected {self.vector_size}")
                
                return embedding
            else:
                print(f"❌ Local embedding request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Local embedding failed: {e}")
            return None
    
    def _embed_batch_local(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate batch embeddings using local model"""
        try:
            # Prepare batch request
            payload = {
                "model": self.model,
                "input": texts,
                "encoding_format": "float"
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = []
                
                for item in result["data"]:
                    embedding = item["embedding"]
                    if len(embedding) == self.vector_size:
                        embeddings.append(embedding)
                    else:
                        print(f"⚠️ Invalid embedding size: {len(embedding)}")
                        embeddings.append(None)
                
                return embeddings
            else:
                print(f"❌ Local batch embedding request failed: {response.status_code}")
                return [None] * len(texts)
                
        except Exception as e:
            print(f"❌ Local batch embedding failed: {e}")
            return [None] * len(texts)
    
    def _embed_openai(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API"""
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            payload = {
                "model": self.model,
                "input": text,
                "encoding_format": "float"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result["data"][0]["embedding"]
                return embedding
            else:
                print(f"❌ OpenAI embedding request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI embedding failed: {e}")
            return None
    
    def _embed_batch_openai(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate batch embeddings using OpenAI API"""
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            payload = {
                "model": self.model,
                "input": texts,
                "encoding_format": "float"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = []
                
                for item in result["data"]:
                    embedding = item["embedding"]
                    embeddings.append(embedding)
                
                return embeddings
            else:
                print(f"❌ OpenAI batch embedding request failed: {response.status_code}")
                return [None] * len(texts)
                
        except Exception as e:
            print(f"❌ OpenAI batch embedding failed: {e}")
            return [None] * len(texts)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self.embedding_cache)
        }
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        print("🧹 Embedding cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Check embedding service health"""
        try:
            # Test with a simple text
            test_text = "Hello, world!"
            embedding = self.embed_single(test_text)
            
            return {
                "status": "healthy" if embedding else "unhealthy",
                "provider": self.provider,
                "model": self.model,
                "vector_size": len(embedding) if embedding else 0,
                "cache_stats": self.get_cache_stats()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "provider": self.provider,
                "model": self.model
            }
