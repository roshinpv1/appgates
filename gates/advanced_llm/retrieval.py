"""
Context Retriever Component
Retrieves relevant context using hybrid search (vector + keyword + symbol + proximity)
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .vector_store import VectorStore, SearchResult


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
class ChunkResult:
    """Result from context retrieval"""
    id: str
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    score: float
    source: str  # vector, keyword, symbol, proximity
    metadata: Dict[str, Any]


class ContextRetriever:
    """
    Context retriever with hybrid search capabilities
    """
    
    def __init__(self, vector_store: VectorStore, cache_manager, embedding_service, config: RetrievalConfig):
        """Initialize context retriever"""
        self.vector_store = vector_store
        self.cache_manager = cache_manager
        self.embedding_service = embedding_service
        self.config = config
        
        # Statistics
        self.stats = {
            "retrievals": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "vector_searches": 0,
            "keyword_searches": 0,
            "symbol_searches": 0,
            "total_time_ms": 0
        }
        
        print(f"🔍 ContextRetriever initialized with {self.config.max_chunks} max chunks")
    
    def retrieve_context(self, repo_id: str, query: str, 
                              cursor_context: Optional[Dict[str, Any]] = None,
                              max_chunks: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(repo_id, query, cursor_context)
            cached_result = self.cache_manager.get(cache_key)
            
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result
            
            self.stats["cache_misses"] += 1
            
            # Perform hybrid search
            search_results = self._hybrid_search(repo_id, query, cursor_context)
            
            # Rank and merge results
            ranked_results = self._rank_fusion(search_results)
            
            # Apply proximity boosting if cursor context provided
            if cursor_context:
                ranked_results = self._apply_proximity_boost(ranked_results, cursor_context)
            
            # Optional reranking
            if self.config.enable_reranking and len(ranked_results) > self.config.rerank_top_k:
                ranked_results = self._rerank_results(ranked_results, query)
            
            # Limit results
            max_chunks = max_chunks or self.config.max_chunks
            final_results = ranked_results[:max_chunks]
            
            # Format results
            chunks = []
            for result in final_results:
                payload = result.payload
                chunk = {
                    "id": result.id,
                    "content": payload.get("content", ""),
                    "file_path": payload.get("file_path", ""),
                    "language": payload.get("language", "text"),
                    "start_line": payload.get("start_line", 0),
                    "end_line": payload.get("end_line", 0),
                    "score": result.score,
                    "source": payload.get("source", "vector"),
                    "metadata": payload.get("metadata", {})
                }
                chunks.append(chunk)
            
            # Cache results
            result_data = {
                "chunks": chunks,
                "total_chunks": len(chunks),
                "query": query,
                "repo_id": repo_id,
                "retrieval_time_ms": (time.time() - start_time) * 1000
            }
            
            self.cache_manager.set(cache_key, result_data, ttl=300)  # 5 minutes
            
            # Update statistics
            self.stats["retrievals"] += 1
            self.stats["total_time_ms"] += (time.time() - start_time) * 1000
            
            return result_data
            
        except Exception as e:
            print(f"❌ Failed to retrieve context for {repo_id}: {e}")
            return {
                "chunks": [],
                "total_chunks": 0,
                "query": query,
                "repo_id": repo_id,
                "error": str(e)
            }
    
    def _hybrid_search(self, repo_id: str, query: str, 
                           cursor_context: Optional[Dict[str, Any]]) -> List[SearchResult]:
        """
        Perform hybrid search combining multiple search strategies
        """
        all_results = []
        
        # 1. Vector search
        try:
            vector_results = self._vector_search(repo_id, query)
            all_results.extend(vector_results)
            self.stats["vector_searches"] += 1
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}")
        
        # 2. Keyword search
        try:
            keyword_results = self._keyword_search(repo_id, query)
            all_results.extend(keyword_results)
            self.stats["keyword_searches"] += 1
        except Exception as e:
            print(f"⚠️ Keyword search failed: {e}")
        
        # 3. Symbol search
        try:
            symbol_results = self._symbol_search(repo_id, query)
            all_results.extend(symbol_results)
            self.stats["symbol_searches"] += 1
        except Exception as e:
            print(f"⚠️ Symbol search failed: {e}")
        
        # 4. Proximity search (if cursor context provided)
        if cursor_context:
            try:
                proximity_results = self._proximity_search(repo_id, cursor_context)
                all_results.extend(proximity_results)
            except Exception as e:
                print(f"⚠️ Proximity search failed: {e}")
        
        return all_results
    
    def _vector_search(self, repo_id: str, query: str) -> List[SearchResult]:
        """Perform vector similarity search"""
        try:
            # Generate embedding for query using embedding service
            query_embedding = self.embedding_service.embed_single(query)
            
            if not query_embedding:
                print(f"⚠️ Failed to generate embedding for query: {query}")
                return []
            
            # Search vector store
            results = self.vector_store.search_similar(
                collection_name=repo_id,
                query_vector=query_embedding,
                limit=50,
                score_threshold=self.config.score_threshold
            )
            
            print(f"🔍 Vector search found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            print(f"⚠️ Vector search error: {e}")
            return []
    
    def _keyword_search(self, repo_id: str, query: str) -> List[SearchResult]:
        """Perform keyword-based search"""
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            
            # For now, we'll return empty results
            # In a real implementation, you'd search a keyword index
            return []
            
        except Exception as e:
            print(f"⚠️ Keyword search error: {e}")
            return []
    
    def _symbol_search(self, repo_id: str, query: str) -> List[SearchResult]:
        """Perform symbol-based search"""
        try:
            # Extract potential symbols from query
            symbols = self._extract_symbols(query)
            
            # For now, we'll return empty results
            # In a real implementation, you'd search a symbol index
            return []
            
        except Exception as e:
            print(f"⚠️ Symbol search error: {e}")
            return []
    
    def _proximity_search(self, repo_id: str, cursor_context: Dict[str, Any]) -> List[SearchResult]:
        """Perform proximity-based search around cursor"""
        try:
            file_path = cursor_context.get("file_path")
            line = cursor_context.get("line", 0)
            
            if not file_path:
                return []
            
            # For now, we'll return empty results
            # In a real implementation, you'd search for nearby chunks
            return []
            
        except Exception as e:
            print(f"⚠️ Proximity search error: {e}")
            return []
    
    def _rank_fusion(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Apply rank fusion to combine results from different search strategies
        """
        try:
            # Group results by ID
            grouped_results = {}
            for result in results:
                result_id = result.id
                if result_id not in grouped_results:
                    grouped_results[result_id] = []
                grouped_results[result_id].append(result)
            
            # Apply weighted scoring
            fused_results = []
            for result_id, result_list in grouped_results.items():
                # Calculate weighted score
                weighted_score = 0.0
                total_weight = 0.0
                
                for result in result_list:
                    # Determine source and weight
                    source = self._determine_source(result)
                    weight = self._get_source_weight(source)
                    
                    weighted_score += result.score * weight
                    total_weight += weight
                
                if total_weight > 0:
                    final_score = weighted_score / total_weight
                    
                    # Create fused result
                    fused_result = SearchResult(
                        id=result_id,
                        score=final_score,
                        payload=result_list[0].payload,  # Use first result's payload
                        vector=result_list[0].vector
                    )
                    fused_results.append(fused_result)
            
            # Sort by score
            fused_results.sort(key=lambda x: x.score, reverse=True)
            
            return fused_results
            
        except Exception as e:
            print(f"⚠️ Rank fusion error: {e}")
            return results
    
    def _apply_proximity_boost(self, results: List[SearchResult], 
                                   cursor_context: Dict[str, Any]) -> List[SearchResult]:
        """
        Apply proximity boosting to results near cursor
        """
        try:
            cursor_file = cursor_context.get("file_path")
            cursor_line = cursor_context.get("line", 0)
            
            if not cursor_file:
                return results
            
            boosted_results = []
            for result in results:
                payload = result.payload
                result_file = payload.get("file_path")
                result_line = payload.get("start_line", 0)
                
                # Calculate proximity boost
                proximity_boost = 0.0
                if result_file == cursor_file:
                    # Same file boost
                    line_distance = abs(result_line - cursor_line)
                    if line_distance <= 10:
                        proximity_boost = 0.3
                    elif line_distance <= 50:
                        proximity_boost = 0.1
                
                # Apply boost
                boosted_score = result.score + (proximity_boost * self.config.proximity_weight)
                boosted_result = SearchResult(
                    id=result.id,
                    score=boosted_score,
                    payload=result.payload,
                    vector=result.vector
                )
                boosted_results.append(boosted_result)
            
            # Re-sort by boosted score
            boosted_results.sort(key=lambda x: x.score, reverse=True)
            
            return boosted_results
            
        except Exception as e:
            print(f"⚠️ Proximity boost error: {e}")
            return results
    
    def _rerank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Apply cross-encoder reranking (placeholder implementation)
        """
        try:
            # For now, we'll just return the results as-is
            # In a real implementation, you'd use a cross-encoder model
            return results
            
        except Exception as e:
            print(f"⚠️ Reranking error: {e}")
            return results
    
    def _convert_to_chunks(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """
        Convert search results to chunk format
        """
        chunks = []
        
        for result in results:
            payload = result.payload
            
            chunk = {
                "id": result.id,
                "file_path": payload.get("file_path", "unknown"),
                "language": payload.get("language", "text"),
                "start_line": payload.get("start_line", 0),
                "end_line": payload.get("end_line", 0),
                "score": result.score,
                "source": self._determine_source(result),
                "metadata": {
                    "symbol_name": payload.get("symbol_name"),
                    "symbol_kind": payload.get("symbol_kind"),
                    "imports": payload.get("imports", []),
                    "references": payload.get("references", []),
                    "chunk_type": payload.get("chunk_type", "unknown")
                }
            }
            
            # Get content from payload
            chunk["content"] = payload.get("content", f"// Content from {payload.get('file_path', 'unknown')} lines {payload.get('start_line', 0)}-{payload.get('end_line', 0)}")
            
            chunks.append(chunk)
        
        return chunks
    
    def _merge_adjacent_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge adjacent chunks from the same file
        """
        try:
            if not chunks:
                return chunks
            
            # Group chunks by file
            file_groups = {}
            for chunk in chunks:
                file_path = chunk["file_path"]
                if file_path not in file_groups:
                    file_groups[file_path] = []
                file_groups[file_path].append(chunk)
            
            merged_chunks = []
            
            for file_path, file_chunks in file_groups.items():
                # Sort by start line
                file_chunks.sort(key=lambda x: x["start_line"])
                
                # Merge adjacent chunks
                current_chunk = file_chunks[0]
                
                for next_chunk in file_chunks[1:]:
                    # Check if chunks are adjacent
                    if next_chunk["start_line"] <= current_chunk["end_line"] + 5:  # Allow small gap
                        # Merge chunks
                        current_chunk["end_line"] = max(current_chunk["end_line"], next_chunk["end_line"])
                        current_chunk["score"] = max(current_chunk["score"], next_chunk["score"])
                        current_chunk["content"] += f"\n{next_chunk['content']}"
                    else:
                        # Add current chunk and start new one
                        merged_chunks.append(current_chunk)
                        current_chunk = next_chunk
                
                # Add last chunk
                merged_chunks.append(current_chunk)
            
            return merged_chunks
            
        except Exception as e:
            print(f"⚠️ Chunk merging error: {e}")
            return chunks
    
    def _generate_cache_key(self, repo_id: str, query: str, 
                           cursor_context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for retrieval"""
        import hashlib
        context_str = json.dumps(cursor_context or {}, sort_keys=True)
        key_data = f"retrieval:{repo_id}:{query}:{context_str}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Simple keyword extraction
        import re
        words = re.findall(r'\b\w+\b', query.lower())
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def _extract_symbols(self, query: str) -> List[str]:
        """Extract potential symbols from query"""
        import re
        # Look for camelCase, snake_case, or PascalCase identifiers
        symbols = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', query)
        return symbols
    
    def _determine_source(self, result: SearchResult) -> str:
        """Determine the source of a search result"""
        # This would be determined by the search method that found it
        # For now, we'll use a simple heuristic
        payload = result.payload
        if payload.get("symbol_name"):
            return "symbol"
        elif payload.get("chunk_type") == "ast_symbol":
            return "symbol"
        else:
            return "vector"
    
    def _get_source_weight(self, source: str) -> float:
        """Get weight for a search source"""
        weights = {
            "vector": self.config.vector_search_weight,
            "keyword": self.config.keyword_search_weight,
            "symbol": self.config.symbol_search_weight,
            "proximity": self.config.proximity_weight
        }
        return weights.get(source, 0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            **self.stats,
            "avg_retrieval_time": self.stats["total_time_ms"] / max(self.stats["retrievals"], 1),
            "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["cache_hits"] + self.stats["cache_misses"], 1)
        }
