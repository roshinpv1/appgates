"""
Advanced LLM Service Core
Orchestrates the enhanced LLM assistance system with vector search, AST parsing, and streaming
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Import existing utilities
try:
    from ..utils.llm_client import LLMClient, LLMConfig, LLMProvider
    from ..utils.file_processor import OptimizedFileProcessor
    from ..utils.git_operations import clone_repository, cleanup_repository
    from ..utils.pattern_cache import get_pattern_cache
except ImportError:
    from utils.llm_client import LLMClient, LLMConfig, LLMProvider
    from utils.file_processor import OptimizedFileProcessor
    from utils.git_operations import clone_repository, cleanup_repository
    from utils.pattern_cache import get_pattern_cache

# Import new components
from .indexing import CodeIndexer
from .retrieval import ContextRetriever
from .embedding import EmbeddingService
from .ast_parser import ASTParser
from .vector_store import VectorStore
from .cache import CacheManager
from .pattern_library import PatternLibraryService


@dataclass
class RetrievalConfig:
    """Configuration for context retrieval"""
    max_chunks: int = 24
    max_tokens_per_chunk: int = 800
    overlap_percentage: float = 0.15
    vector_search_weight: float = 0.4
    keyword_search_weight: float = 0.3
    symbol_search_weight: float = 0.2
    proximity_weight: float = 0.1
    enable_reranking: bool = True
    rerank_top_k: int = 50
    rerank_final_k: int = 16
    score_threshold: float = 0.7


@dataclass
class IndexingConfig:
    """Configuration for code indexing"""
    chunk_size: int = 800
    overlap_size: int = 120
    max_file_size_mb: int = 10
    supported_languages: List[str] = None
    enable_ast_parsing: bool = True
    enable_symbol_extraction: bool = True
    enable_dependency_graph: bool = True
    batch_size: int = 64


class AdvancedLLMService:
    """
    Advanced LLM Service with vector search, AST parsing, and streaming capabilities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the advanced LLM service"""
        self.config = config or {}
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Load configurations
        self.retrieval_config = RetrievalConfig(**self.config.get("retrieval", {}))
        self.indexing_config = IndexingConfig(**self.config.get("indexing", {}))
        
        # Initialize components
        self._initialize_components()
        
        # Performance tracking
        self.stats = {
            "requests_processed": 0,
            "total_latency_ms": 0,
            "retrieval_latency_ms": 0,
            "llm_latency_ms": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        
        print("🚀 Advanced LLM Service initialized")
        print(f"   📊 Retrieval: {self.retrieval_config.max_chunks} chunks, {self.retrieval_config.max_tokens_per_chunk} tokens")
        print(f"   🔍 Indexing: {self.indexing_config.chunk_size} chunk size, {self.indexing_config.batch_size} batch")
        print(f"   🤖 LLM: {self.llm_client.config.provider.value}, {self.llm_client.config.model}")
    
    def _initialize_components(self):
        """Initialize all service components"""
        try:
            # Initialize pattern library service
            self.pattern_library = PatternLibraryService()
            
            # Initialize vector store
            vector_store_config = self.config.get("vector_store", {})
            # Set correct embedding dimensions for nomic-embed-text (768)
            vector_store_config["vector_size"] = 768
            self.vector_store = VectorStore(vector_store_config)
            
            # Initialize embedding service with separate configuration
            embedding_config = self.config.get("embedding", {})
            self.embedding_service = EmbeddingService(embedding_config)
            
            # Initialize AST parser
            self.ast_parser = ASTParser(self.config.get("ast_parser", {}))
            
            # Initialize cache manager
            self.cache_manager = CacheManager(self.config.get("cache", {}))
            
            # Initialize LLM client using existing implementation
            llm_config = self.config.get("llm", {})
            self.llm_client = LLMClient(LLMConfig(
                provider=LLMProvider(llm_config.get("provider", "openai")),
                model=llm_config.get("model", "gpt-4"),
                api_key=llm_config.get("api_key"),
                base_url=llm_config.get("base_url"),
                temperature=llm_config.get("temperature", 0.3),
                max_tokens=llm_config.get("max_tokens", 2000),
                timeout=llm_config.get("timeout", 30)
            ))
            
            # Initialize file processor (reuse existing)
            self.file_processor = OptimizedFileProcessor()
            
            # Initialize other components lazily when needed
            self.code_indexer = None
            self.context_retriever = None
            
            # Index pattern library texts
            self._index_pattern_library()
            
            print("✅ Core components initialized successfully")
            print(f"   🧠 Embeddings: {embedding_config.get('provider', 'openai')} at {embedding_config.get('base_url', 'default')}")
            print(f"   🤖 LLM: {llm_config.get('provider', 'openai')} at {llm_config.get('base_url', 'default')}")
            print(f"   📚 Pattern Library: {len(self.pattern_library.patterns)} gates loaded")
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            raise
    
    def _ensure_code_indexer(self):
        """Ensure code indexer is initialized"""
        if self.code_indexer is None:
            self.code_indexer = CodeIndexer(
                vector_store=self.vector_store,
                embedding_service=self.embedding_service,
                ast_parser=self.ast_parser,
                config=self.indexing_config
            )
    
    def _ensure_context_retriever(self):
        """Ensure context retriever is initialized"""
        if self.context_retriever is None:
            self.context_retriever = ContextRetriever(
                vector_store=self.vector_store,
                cache_manager=self.cache_manager,
                embedding_service=self.embedding_service,
                config=self.retrieval_config
            )
    
    def _index_pattern_library(self):
        """Index pattern library texts in the vector store"""
        try:
            pattern_texts = self.pattern_library.get_pattern_texts()
            if not pattern_texts:
                print("⚠️ No pattern texts to index")
                return
            
            print(f"📚 Indexing {len(pattern_texts)} pattern texts...")
            
            # Generate embeddings for pattern texts
            embeddings = self.embedding_service.embed_texts(pattern_texts)
            
            # Create collection for pattern library if it doesn't exist
            pattern_collection = "pattern_library"
            if not self.vector_store.collection_exists(pattern_collection):
                self.vector_store.create_collection(pattern_collection)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (text, embedding) in enumerate(zip(pattern_texts, embeddings)):
                vector_data = {
                    "id": f"pattern_{i}",
                    "vector": embedding,
                    "payload": {
                        "text": text,
                        "type": "pattern_library",
                        "source": "enhanced_pattern_library.json",
                        "index": i,
                        "text_length": len(text)
                    }
                }
                vectors.append(vector_data)
            
            # Store in vector store
            success = self.vector_store.upsert_vectors(pattern_collection, vectors)
            
            if success:
                print(f"✅ Indexed {len(pattern_texts)} pattern texts in vector store")
            else:
                print(f"❌ Failed to index pattern texts in vector store")
            
        except Exception as e:
            print(f"❌ Failed to index pattern library: {e}")
    
    def _get_relevant_patterns_for_query(self, query: str, max_patterns: int = 3) -> List[str]:
        """Get relevant patterns for a query to include as context"""
        try:
            # First try vector search if pattern library is indexed
            pattern_collection = "pattern_library"
            if self.vector_store.collection_exists(pattern_collection):
                # Generate embedding for the query
                query_embedding = self.embedding_service.embed_single(query)
                
                if query_embedding:
                    # Search for similar patterns
                    search_results = self.vector_store.search_similar(
                        collection_name=pattern_collection,
                        query_vector=query_embedding,
                        limit=max_patterns,
                        score_threshold=0.5
                    )
                    
                    if search_results:
                        relevant_patterns = []
                        for result in search_results:
                            if "text" in result.payload:
                                relevant_patterns.append(result.payload["text"])
                        
                        if relevant_patterns:
                            print(f"🔍 Found {len(relevant_patterns)} relevant patterns via vector search")
                            return relevant_patterns
            
            # Fallback to keyword-based search
            relevant_patterns = self.pattern_library.get_relevant_patterns_for_query(
                query, max_patterns=max_patterns
            )
            
            if relevant_patterns:
                print(f"🔍 Found {len(relevant_patterns)} relevant patterns via keyword search")
                return relevant_patterns
            
            return []
            
        except Exception as e:
            print(f"⚠️ Failed to get relevant patterns: {e}")
            return []
    
    def index_repository(self, repo_url: str, branch: str = "main", 
                              github_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Index a repository for advanced LLM assistance
        """
        start_time = time.time()
        repo_id = self._generate_repo_id(repo_url, branch)
        
        try:
            print(f"📚 Indexing repository: {repo_url} (branch: {branch})")
            
            # Ensure code indexer is initialized
            self._ensure_code_indexer()
            
            # Check if already indexed
            if self._is_repository_indexed(repo_id):
                print(f"✅ Repository {repo_id} already indexed")
                return {"repo_id": repo_id, "status": "already_indexed"}
            
            # Clone repository to get commit hash
            repo_path = self._clone_repository(repo_url, branch, github_token)
            
            # Get repository info including commit hash
            from gates.utils.git_operations import get_repository_info
            repo_info = get_repository_info(str(repo_path))
            
            if repo_info.get("is_git_repo") and repo_info.get("commit_hash"):
                commit_hash = repo_info["commit_hash"]
                print(f"🔍 Repository commit hash: {commit_hash}")
                
                # Check if this specific commit is already indexed
                commit_repo_id = self._generate_repo_id_with_commit(repo_url, branch, commit_hash)
                
                if self._is_repository_indexed(commit_repo_id):
                    print(f"✅ Repository with commit {commit_hash} already indexed")
                    # Clean up the cloned repository
                    self._cleanup_repository(repo_path)
                    return {"repo_id": commit_repo_id, "status": "already_indexed", "commit_hash": commit_hash}
                
                # If not indexed, use the commit-specific repo_id for indexing
                repo_id = commit_repo_id
                print(f"🔄 Indexing repository with commit hash: {commit_hash}")
            else:
                print(f"⚠️ Could not determine commit hash, using fallback repo_id")
            
            # Index repository
            result = self.code_indexer.index_repository(
                repo_id=repo_id,
                repo_path=repo_path,
                repo_url=repo_url,
                branch=branch
            )
            
            # Cleanup
            self._cleanup_repository(repo_path)
            
            indexing_time = (time.time() - start_time) * 1000
            
            return {
                **result,
                "repo_id": repo_id,
                "indexing_time_ms": indexing_time,
                "status": "success",
                "commit_hash": repo_info.get("commit_hash") if repo_info.get("is_git_repo") else None
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Failed to index repository {repo_url}: {e}")
            raise
    
    def get_context(self, repo_id: str, query: str, 
                         cursor_context: Optional[Dict[str, Any]] = None,
                         max_chunks: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query
        """
        start_time = time.time()
        
        try:
            # Ensure context retriever is initialized
            self._ensure_context_retriever()
            
            # Use cache if available
            cache_key = self._generate_cache_key(repo_id, query, cursor_context)
            cached_result = self.cache_manager.get(cache_key)
            
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result
            
            self.stats["cache_misses"] += 1
            
            # Retrieve context
            context_result = self.context_retriever.retrieve_context(
                repo_id=repo_id,
                query=query,
                cursor_context=cursor_context,
                max_chunks=max_chunks or self.retrieval_config.max_chunks
            )
            
            # Cache the result
            self.cache_manager.set(cache_key, context_result, ttl=300)  # 5 minutes
            
            retrieval_time = (time.time() - start_time) * 1000
            self.stats["retrieval_latency_ms"] += retrieval_time
            
            return {
                **context_result,
                "retrieval_time_ms": retrieval_time,
                "cache_hit": False
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Failed to retrieve context for {repo_id}: {e}")
            raise
    
    async def complete_with_context(self, repo_id: str, instruction: str,
                                   context_result: Dict[str, Any],
                                   mode: str = "chat") -> Dict[str, Any]:
        """
        Generate completion using retrieved context
        """
        start_time = time.time()
        
        try:
            # Assemble prompt with context
            prompt = self._assemble_prompt(
                repo_id=repo_id,
                instruction=instruction,
                context_result=context_result,
                mode=mode
            )
            
            # Generate completion using existing LLM client
            content = self.llm_client.call_llm(prompt)
            
            llm_time = (time.time() - start_time) * 1000
            self.stats["llm_latency_ms"] += llm_time
            self.stats["requests_processed"] += 1
            
            return {
                "content": content,
                "mode": mode,
                "llm_time_ms": llm_time,
                "context_chunks_used": len(context_result.get("chunks", [])),
                "total_tokens": len(content.split()),  # Approximate token count
                "provider": self.llm_client.config.provider.value
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Failed to generate completion: {e}")
            raise
    
    async def generate_patch(self, repo_id: str, instruction: str,
                           context_result: Dict[str, Any],
                           target_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a patch/diff for code changes
        """
        try:
            # Add patch-specific context
            patch_context = {
                **context_result,
                "target_file": target_file,
                "mode": "patch"
            }
            
            # Generate patch
            patch_result = await self.complete_with_context(
                repo_id=repo_id,
                instruction=instruction,
                context_result=patch_context,
                mode="patch"
            )
            
            # Parse unified diff from response
            patch_content = self._extract_patch_content(patch_result.get("content", ""))
            
            return {
                **patch_result,
                "patch_content": patch_content,
                "patch_type": "unified_diff"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate patch: {e}")
            raise
    
    def _assemble_prompt(self, repo_id: str, instruction: str,
                              context_result: Dict[str, Any], mode: str) -> str:
        """
        Assemble hierarchical prompt with context and relevant patterns
        """
        chunks = context_result.get("chunks", [])
        
        # Get relevant patterns for the instruction
        relevant_patterns = self._get_relevant_patterns_for_query(instruction, max_patterns=3)
        
        # Build context blocks
        context_blocks = []
        for chunk in chunks:
            context_block = f"```{chunk.get('language', 'text')}\n"
            context_block += f"// File: {chunk.get('file_path', 'unknown')}\n"
            context_block += f"// Lines: {chunk.get('start_line', 0)}-{chunk.get('end_line', 0)}\n"
            context_block += chunk.get('content', '') + "\n```\n"
            context_blocks.append(context_block)
        
        # Build pattern context
        pattern_context = ""
        if relevant_patterns:
            pattern_context = "\n\nRelevant Code Quality Patterns:\n"
            for i, pattern in enumerate(relevant_patterns, 1):
                pattern_context += f"\n--- Pattern {i} ---\n{pattern}\n"
        
        # Assemble prompt based on mode
        if mode == "patch":
            prompt = f"""You are an expert code assistant. Generate a unified diff patch for the following changes.

Context:
{chr(10).join(context_blocks)}{pattern_context}

Instruction: {instruction}

Generate a unified diff patch that implements the requested changes. Consider the relevant code quality patterns when making changes. Include only the necessary modifications."""

        else:  # chat mode
            prompt = f"""You are an expert code assistant. Use the following context to answer the question.

Context:
{chr(10).join(context_blocks)}{pattern_context}

Question: {instruction}

Provide a clear, actionable answer based on the code context and relevant patterns. Consider the code quality gates and patterns when providing recommendations."""
        
        return prompt
    
    def _generate_repo_id(self, repo_url: str, branch: str) -> str:
        """Generate unique repository ID"""
        import hashlib
        repo_key = f"{repo_url}:{branch}"
        return hashlib.sha256(repo_key.encode()).hexdigest()[:16]
    
    def _generate_repo_id_with_commit(self, repo_url: str, branch: str, commit_hash: str) -> str:
        """Generate unique repository ID including commit hash"""
        import hashlib
        repo_key = f"{repo_url}:{branch}:{commit_hash}"
        return hashlib.sha256(repo_key.encode()).hexdigest()[:16]
    
    def _generate_cache_key(self, repo_id: str, query: str, 
                           cursor_context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for context retrieval"""
        import hashlib
        context_str = json.dumps(cursor_context or {}, sort_keys=True)
        key_data = f"{repo_id}:{query}:{context_str}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _is_repository_indexed(self, repo_id: str) -> bool:
        """Check if repository is already indexed"""
        try:
            return self.vector_store.collection_exists(repo_id)
        except Exception:
            return False
    
    def _clone_repository(self, repo_url: str, branch: str, 
                               github_token: Optional[str]) -> Path:
        """Clone repository to temporary location"""
        # Reuse existing git operations utility
        temp_dir = Path("/tmp") / f"codegates_advanced_{int(time.time())}"
        temp_dir.mkdir(exist_ok=True)
        
        repo_path = clone_repository(
            repo_url=repo_url,
            branch=branch,
            github_token=github_token,
            target_dir=str(temp_dir)
        )
        
        return Path(repo_path)
    
    def _cleanup_repository(self, repo_path: Path):
        """Clean up temporary repository"""
        try:
            cleanup_repository(str(repo_path))
        except Exception as e:
            self.logger.warning(f"Failed to cleanup repository {repo_path}: {e}")
    
    def _extract_patch_content(self, content: str) -> str:
        """Extract unified diff content from LLM response"""
        # Look for diff markers
        diff_start = content.find("---")
        if diff_start == -1:
            return content
        
        return content[diff_start:]
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the advanced LLM service"""
        try:
            # Check all components
            vector_health = self.vector_store.health_check()
            embedding_health = self.embedding_service.health_check()
            cache_health = self.cache_manager.health_check()
            ast_health = self.ast_parser.health_check()
            
            # Check if all components are healthy
            all_healthy = (
                vector_health.get("status") == "healthy" and
                embedding_health.get("status") == "healthy" and
                cache_health.get("status") == "healthy" and
                ast_health.get("status") == "healthy"
            )
            
            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "components": {
                    "vector_store": vector_health,
                    "embedding_service": embedding_health,
                    "cache_manager": cache_health,
                    "ast_parser": ast_health
                },
                "stats": self.get_stats()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            **self.stats,
            "cache_hit_ratio": self.stats["cache_hits"] / max(self.stats["requests_processed"], 1),
            "avg_retrieval_latency": self.stats["retrieval_latency_ms"] / max(self.stats["requests_processed"], 1),
            "avg_llm_latency": self.stats["llm_latency_ms"] / max(self.stats["requests_processed"], 1)
        }
