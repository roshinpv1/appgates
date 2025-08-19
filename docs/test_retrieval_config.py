#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gates.advanced_llm.core import RetrievalConfig

# Test configuration
config = {
    "max_chunks": 24,
    "max_tokens_per_chunk": 800,
    "vector_search_weight": 0.4,
    "keyword_search_weight": 0.3,
    "symbol_search_weight": 0.2,
    "proximity_weight": 0.1,
    "score_threshold": 0.3
}

print("🔧 Testing RetrievalConfig initialization...")
print(f"🔧 Config: {config}")

try:
    retrieval_config = RetrievalConfig(**config)
    print(f"✅ RetrievalConfig initialized successfully")
    print(f"🔧 score_threshold: {retrieval_config.score_threshold}")
    print(f"🔧 max_chunks: {retrieval_config.max_chunks}")
    print(f"🔧 vector_search_weight: {retrieval_config.vector_search_weight}")
    
    # Test accessing score_threshold
    print(f"🔧 Direct access to score_threshold: {retrieval_config.score_threshold}")
    
except Exception as e:
    print(f"❌ RetrievalConfig test failed: {e}")
    import traceback
    traceback.print_exc()
