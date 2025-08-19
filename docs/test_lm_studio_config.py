#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔧 Testing LM Studio configuration...")

try:
    from gates.advanced_llm.embedding import EmbeddingService
    
    # Test LM Studio configuration
    config = {
        "provider": "local",
        "model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "base_url": "http://localhost:1234",
        "batch_size": 32
    }
    
    print(f"✅ Creating EmbeddingService with config: {config}")
    embedding_service = EmbeddingService(config)
    
    print(f"✅ EmbeddingService created successfully")
    print(f"🔧 Health check: {embedding_service.health_check()}")
    
    # Test embedding generation
    test_texts = ["Hello world", "This is a test"]
    print(f"🔧 Testing embedding generation for: {test_texts}")
    
    embeddings = embedding_service.embed_texts(test_texts)
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"🔧 First embedding dimension: {len(embeddings[0]) if embeddings else 'None'}")
    
    print("✅ LM Studio configuration test passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
