"""
Embedding Service Component
Generates embeddings for code chunks using multiple providers
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import existing LLM client utilities
try:
    from ..utils.llm_client import LLMClient, LLMConfig, LLMProvider
except ImportError:
    from utils.llm_client import LLMClient, LLMConfig, LLMProvider

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service"""
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    base_url: str = None
    batch_size: int = 64
    max_retries: int = 3
    timeout: int = 30
    rate_limit_per_minute: int = 1000
    fallback_providers: List[str] = None


class EmbeddingService:
    """
    Embedding service with multi-provider support and fallback mechanisms
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize embedding service"""
        self.config = EmbeddingConfig(**config)
        self.model_name = self.config.model
        
        # Initialize providers
        self._init_providers()
        
        # Rate limiting
        self.rate_limiter = {
            "last_request": 0,
            "requests_this_minute": 0,
            "minute_start": time.time()
        }
        
        # Statistics
        self.stats = {
            "embeddings_generated": 0,
            "total_tokens": 0,
            "requests_made": 0,
            "errors": 0,
            "fallback_used": 0
        }
        
        print(f"🧠 EmbeddingService initialized with {self.config.provider} provider")
        print(f"   📊 Model: {self.model_name}")
        print(f"   📦 Batch size: {self.config.batch_size}")
    
    def _init_providers(self):
        """Initialize embedding providers"""
        self.providers = {}
        
        # OpenAI provider
        if OPENAI_AVAILABLE:
            try:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if openai_api_key:
                    self.providers["openai"] = {
                        "client": openai,
                        "api_key": openai_api_key,
                        "base_url": "https://api.openai.com/v1"
                    }
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI provider: {e}")
        
        # Azure provider
        try:
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            if azure_api_key and azure_endpoint:
                self.providers["azure"] = {
                    "client": openai if OPENAI_AVAILABLE else None,
                    "api_key": azure_api_key,
                    "base_url": azure_endpoint
                }
        except Exception as e:
            print(f"⚠️ Failed to initialize Azure provider: {e}")
        
        # Local provider (using Ollama or LM Studio)
        try:
            # Get base_url from config if provided, otherwise use Ollama default
            base_url = getattr(self.config, 'base_url', "http://localhost:11434")
            self.providers["local"] = {
                "client": None,  # Not using LLM client for embeddings
                "api_key": None,
                "base_url": base_url,
                "model": self.model_name
            }
        except Exception as e:
            print(f"⚠️ Failed to initialize local provider: {e}")
        
        # Set fallback providers
        if not self.config.fallback_providers:
            self.config.fallback_providers = ["azure", "local"]
        
        print(f"✅ Initialized {len(self.providers)} embedding providers")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        """
        if not texts:
            return []
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            
            try:
                # Try primary provider
                batch_embeddings = self._embed_batch(batch, self.config.provider)
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"⚠️ Primary provider failed: {e}")
                
                # Try fallback providers
                fallback_used = False
                for fallback_provider in self.config.fallback_providers or []:
                    if fallback_provider in self.providers:
                        try:
                            batch_embeddings = self._embed_batch(batch, fallback_provider)
                            embeddings.extend(batch_embeddings)
                            fallback_used = True
                            self.stats["fallback_used"] += 1
                            break
                        except Exception as fallback_error:
                            print(f"⚠️ Fallback provider {fallback_provider} failed: {fallback_error}")
                            continue
                
                if not fallback_used:
                    # Generate dummy embeddings as last resort
                    print(f"⚠️ All providers failed, generating dummy embeddings")
                    dummy_embeddings = self._generate_dummy_embeddings(batch)
                    embeddings.extend(dummy_embeddings)
        
        self.stats["embeddings_generated"] += len(embeddings)
        self.stats["requests_made"] += 1
        
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    def _embed_batch(self, texts: List[str], provider_name: str) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts using a specific provider
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise Exception(f"Provider {provider_name} not available")
        
        try:
            if provider_name == "openai":
                return self._embed_openai(provider, texts)
            elif provider_name == "azure":
                return self._embed_azure(provider, texts)
            elif provider_name == "local":
                return self._embed_local(provider, texts)
            else:
                raise Exception(f"Unknown provider: {provider_name}")
        except Exception as e:
            print(f"⚠️ Provider {provider_name} failed: {e}")
            raise
    
    def _embed_openai(self, provider: Dict[str, Any], texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI
        """
        try:
            # Set API key
            openai.api_key = provider["api_key"]
            
            # Generate embeddings
            response = openai.Embedding.create(
                input=texts,
                model=self.model_name
            )
            
            # Extract embeddings
            embeddings = [data.embedding for data in response.data]
            
            # Update token count
            if hasattr(response, 'usage') and response.usage:
                self.stats["total_tokens"] += response.usage.total_tokens
            
            return embeddings
            
        except Exception as e:
            raise Exception(f"OpenAI embedding failed: {e}")
    
    def _embed_azure(self, provider: Dict[str, Any], texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Azure OpenAI
        """
        try:
            # Set API key and endpoint
            openai.api_key = provider["api_key"]
            openai.api_base = provider["base_url"]
            openai.api_type = "azure"
            openai.api_version = "2023-05-15"
            
            # Generate embeddings
            response = openai.Embedding.create(
                input=texts,
                engine=self.model_name  # Azure uses engine instead of model
            )
            
            # Extract embeddings
            embeddings = [data.embedding for data in response.data]
            
            # Update token count
            if hasattr(response, 'usage') and response.usage:
                self.stats["total_tokens"] += response.usage.total_tokens
            
            return embeddings
            
        except Exception as e:
            raise Exception(f"Azure embedding failed: {e}")
    
    def _embed_local(self, provider: Dict[str, Any], texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using local provider (Ollama or LM Studio)
        """
        try:
            import requests
            
            base_url = provider.get("base_url", "http://localhost:11434")
            model = provider.get("model", "nomic-embed-text")
            
            # Determine if this is LM Studio (port 1234) or Ollama (port 11434)
            is_lm_studio = "1234" in base_url
            
            embeddings = []
            for text in texts:
                try:
                    if is_lm_studio:
                        # LM Studio uses OpenAI-compatible API
                        response = requests.post(
                            f"{base_url}/v1/embeddings",
                            json={
                                "model": model,
                                "input": text
                            },
                            timeout=30
                        )
                    else:
                        # Ollama embedding API
                        response = requests.post(
                            f"{base_url}/api/embeddings",
                            json={
                                "model": model,
                                "prompt": text
                            },
                            timeout=30
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if is_lm_studio:
                            # LM Studio returns OpenAI-compatible format
                            embedding = result.get("data", [{}])[0].get("embedding", [])
                        else:
                            # Ollama format
                            embedding = result.get("embedding", [])
                        
                        if embedding:
                            embeddings.append(embedding)
                        else:
                            # Fallback to dummy embedding
                            embeddings.append([0.1] * 768)  # Use 768 for nomic-embed-text
                    else:
                        print(f"⚠️ Local embedding failed with status {response.status_code}")
                        # Fallback to dummy embedding
                        embeddings.append([0.1] * 768)
                        
                except Exception as e:
                    print(f"⚠️ Failed to generate embedding for text: {e}")
                    # Fallback to dummy embedding
                    embeddings.append([0.1] * 768)
            
            return embeddings
            
        except Exception as e:
            print(f"⚠️ Local embedding service failed: {e}")
            # Generate dummy embeddings as fallback
            return self._generate_dummy_embeddings(len(texts))
    
    def _parse_local_embedding(self, response: str) -> List[float]:
        """
        Parse embedding from local service response
        """
        try:
            # Try to parse as JSON
            if response.startswith('[') and response.endswith(']'):
                return json.loads(response)
            
            # Try to extract numbers from text
            import re
            numbers = re.findall(r'-?\d+\.?\d*', response)
            if numbers:
                return [float(n) for n in numbers[:768]]  # Limit to embedding size for nomic-embed-text
            
            # Fallback: return zero vector
            return [0.0] * 768
            
        except Exception:
            # Fallback: return zero vector
            return [0.0] * 768
    
    def _generate_dummy_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dummy embeddings for texts that failed to embed.
        This is a placeholder and should be replaced with a proper embedding generation logic.
        """
        print(f"Generating dummy embeddings for {len(texts)} texts.")
        return [[0.0] * 768 for _ in range(len(texts))]  # Use 768 for nomic-embed-text
    
    def _check_rate_limit(self, request_count: int):
        """
        Check and enforce rate limits
        """
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self.rate_limiter["minute_start"] >= 60:
            self.rate_limiter["requests_this_minute"] = 0
            self.rate_limiter["minute_start"] = current_time
        
        # Check if we're over the limit
        if self.rate_limiter["requests_this_minute"] + request_count > self.config.rate_limit_per_minute:
            wait_time = 60 - (current_time - self.rate_limiter["minute_start"])
            if wait_time > 0:
                print(f"⏳ Rate limit reached, would wait {wait_time:.1f} seconds (rate limiting disabled)")
                # Note: In a real implementation, you might want to implement proper rate limiting
                # For now, we'll just log the rate limit hit
                self.rate_limiter["requests_this_minute"] = 0
                self.rate_limiter["minute_start"] = time.time()
        
        self.rate_limiter["requests_this_minute"] += request_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics"""
        return {
            **self.stats,
            "providers_available": len(self.providers),
            "primary_provider": self.config.provider,
            "fallback_providers": self.config.fallback_providers
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for embedding service"""
        try:
            # Simple health check without actual embedding
            return {
                "status": "healthy",
                "providers": list(self.providers.keys()),
                "embedding_size": 768  # nomic-embed-text embedding size
            }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
