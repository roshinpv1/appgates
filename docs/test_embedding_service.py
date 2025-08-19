#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.embedding import EmbeddingService

# Test configuration
config = {
    "provider": "local",
    "model": "nomic-embed-text",
    "batch_size": 32
}

print("🔧 Testing EmbeddingService...")
print(f"🔧 Config: {config}")

try:
    embedding_service = EmbeddingService(config)
    print(f"✅ EmbeddingService initialized successfully")
    
    # Test health check
    health = embedding_service.health_check()
    print(f"🔧 Health check: {health}")
    
    # Test single embedding
    text = "What is this repository about?"
    embedding = embedding_service.embed_single(text)
    print(f"🔧 Single embedding length: {len(embedding)}")
    print(f"🔧 First few values: {embedding[:5]}")
    
    # Test batch embedding
    texts = ["Hello world", "Test text", "Another test"]
    embeddings = embedding_service.embed_texts(texts)
    print(f"🔧 Batch embeddings count: {len(embeddings)}")
    print(f"🔧 First embedding length: {len(embeddings[0])}")
    
except Exception as e:
    print(f"❌ EmbeddingService test failed: {e}")
    import traceback
    traceback.print_exc()
