#!/usr/bin/env python3
"""
Example: Server with separate endpoints for embeddings and LLM
"""

import os
import sys
from pathlib import Path

# Add gates directory to path
gates_dir = Path(__file__).parent / "gates"
sys.path.insert(0, str(gates_dir))

def create_server_with_separate_endpoints():
    """Create server configuration with separate endpoints"""
    
    # Configuration with separate endpoints
    config = {
        "retrieval": {
            "max_chunks": 24,
            "max_tokens_per_chunk": 800,
            "vector_search_weight": 0.4,
            "keyword_search_weight": 0.3,
            "symbol_search_weight": 0.2,
            "proximity_weight": 0.1
        },
        "indexing": {
            "chunk_size": 800,
            "overlap_size": 120,
            "supported_languages": ["python", "javascript", "typescript", "java"]
        },
        # Embeddings on port 1234 (LM Studio)
        "embedding": {
            "provider": "local",
            "local_provider": "lm_studio",
            "local_base_url": "http://localhost:1234",
            "local_model": "nomic-embed-text",
            "batch_size": 64,
            "timeout": 30
        },
        # LLM on port 8000 (your main service)
        "llm": {
            "provider": "local",
            "base_url": "http://localhost:8000",
            "model": "llama3.2",
            "temperature": 0.3,
            "max_tokens": 2000,
            "timeout": 30
        },
        "vector_store": {
            "backend": "memory"
        }
    }
    
    print("🚀 Creating server with separate endpoints...")
    print(f"   🧠 Embeddings: {config['embedding']['local_provider']} at {config['embedding']['local_base_url']}")
    print(f"   🤖 LLM: {config['llm']['provider']} at {config['llm']['base_url']}")
    
    return config

def create_server_with_ollama_embeddings():
    """Create server configuration with Ollama embeddings"""
    
    config = {
        "retrieval": {
            "max_chunks": 24,
            "max_tokens_per_chunk": 800
        },
        "indexing": {
            "chunk_size": 800,
            "overlap_size": 120,
            "supported_languages": ["python", "javascript", "typescript", "java"]
        },
        # Ollama embeddings on port 1234
        "embedding": {
            "provider": "local",
            "local_provider": "ollama",
            "local_base_url": "http://localhost:1234",
            "local_model": "nomic-embed-text",
            "batch_size": 64,
            "timeout": 30
        },
        # LLM on different port
        "llm": {
            "provider": "local",
            "base_url": "http://localhost:8000",
            "model": "llama3.2",
            "temperature": 0.3,
            "max_tokens": 2000,
            "timeout": 30
        },
        "vector_store": {
            "backend": "memory"
        }
    }
    
    print("🚀 Creating server with Ollama embeddings...")
    print(f"   🧠 Embeddings: {config['embedding']['local_provider']} at {config['embedding']['local_base_url']}")
    print(f"   🤖 LLM: {config['llm']['provider']} at {config['llm']['base_url']}")
    
    return config

def create_server_with_openai_embeddings():
    """Create server configuration with OpenAI embeddings"""
    
    config = {
        "retrieval": {
            "max_chunks": 24,
            "max_tokens_per_chunk": 800
        },
        "indexing": {
            "chunk_size": 800,
            "overlap_size": 120,
            "supported_languages": ["python", "javascript", "typescript", "java"]
        },
        # OpenAI embeddings (cloud)
        "embedding": {
            "provider": "openai",
            "model": "text-embedding-3-small",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "batch_size": 64,
            "timeout": 30
        },
        # Local LLM
        "llm": {
            "provider": "local",
            "base_url": "http://localhost:8000",
            "model": "llama3.2",
            "temperature": 0.3,
            "max_tokens": 2000,
            "timeout": 30
        },
        "vector_store": {
            "backend": "memory"
        }
    }
    
    print("🚀 Creating server with OpenAI embeddings...")
    print(f"   🧠 Embeddings: {config['embedding']['provider']} (cloud)")
    print(f"   🤖 LLM: {config['llm']['provider']} at {config['llm']['base_url']}")
    
    return config

if __name__ == "__main__":
    print("🔧 Example configurations for separate endpoints...\n")
    
    # Example 1: LM Studio embeddings + Local LLM
    config1 = create_server_with_separate_endpoints()
    print(f"   📝 Use this config for LM Studio embeddings on port 1234\n")
    
    # Example 2: Ollama embeddings + Local LLM
    config2 = create_server_with_ollama_embeddings()
    print(f"   📝 Use this config for Ollama embeddings on port 1234\n")
    
    # Example 3: OpenAI embeddings + Local LLM
    config3 = create_server_with_openai_embeddings()
    print(f"   📝 Use this config for OpenAI embeddings (cloud)\n")
    
    print("💡 To use these configurations:")
    print("   1. Choose the configuration that matches your setup")
    print("   2. Pass it to AdvancedLLMService(config)")
    print("   3. Or set it in your server startup code")
    print("\n🔗 For more details, see SEPARATE_ENDPOINTS_GUIDE.md")
