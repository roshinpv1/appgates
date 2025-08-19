"""
Enhanced Scanning Module
Leverages vector embeddings and semantic search for improved code analysis
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from .advanced_llm.core import AdvancedLLMService
    from .advanced_llm.embedding import EmbeddingService
    from .advanced_llm.vector_store import VectorStore, SearchResult
except ImportError:
    from advanced_llm.core import AdvancedLLMService
    from advanced_llm.embedding import EmbeddingService
    from advanced_llm.vector_store import VectorStore, SearchResult


@dataclass
class SemanticPattern:
    """Semantic pattern for enhanced scanning"""
    name: str
    description: str
    keywords: List[str]
    semantic_queries: List[str]
    severity: str  # HIGH, MEDIUM, LOW
    category: str  # SECURITY, PERFORMANCE, MAINTAINABILITY, etc.


@dataclass
class EnhancedScanResult:
    """Enhanced scan result with semantic insights"""
    gate_name: str
    traditional_score: float
    semantic_score: float
    context_analysis: Dict[str, Any]
    semantic_matches: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: float


class SemanticPatternMatcher:
    """Enhanced pattern matcher using semantic similarity"""
    
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
        # Pre-defined semantic patterns
        self.semantic_patterns = self._load_semantic_patterns()
    
    def _load_semantic_patterns(self) -> Dict[str, SemanticPattern]:
        """Load semantic patterns for different gates"""
        patterns = {
            "STRUCTURED_LOGS": SemanticPattern(
                name="Structured Logging",
                description="Code that implements structured logging patterns",
                keywords=["logging", "logger", "structured", "json", "log"],
                semantic_queries=[
                    "structured logging implementation",
                    "JSON log format",
                    "log with structured data",
                    "logging with context"
                ],
                severity="HIGH",
                category="OBSERVABILITY"
            ),
            "SECURITY_AUTHENTICATION": SemanticPattern(
                name="Security Authentication",
                description="Code that implements proper authentication",
                keywords=["authentication", "auth", "login", "password", "token"],
                semantic_queries=[
                    "user authentication implementation",
                    "secure login process",
                    "password validation",
                    "token-based authentication"
                ],
                severity="HIGH",
                category="SECURITY"
            ),
            "ERROR_HANDLING": SemanticPattern(
                name="Error Handling",
                description="Code that implements proper error handling",
                keywords=["try", "catch", "exception", "error", "handle"],
                semantic_queries=[
                    "error handling implementation",
                    "exception handling patterns",
                    "graceful error recovery",
                    "error logging and reporting"
                ],
                severity="MEDIUM",
                category="RELIABILITY"
            ),
            "PERFORMANCE_OPTIMIZATION": SemanticPattern(
                name="Performance Optimization",
                description="Code that implements performance optimizations",
                keywords=["cache", "optimize", "performance", "efficient", "fast"],
                semantic_queries=[
                    "performance optimization techniques",
                    "caching implementation",
                    "efficient algorithms",
                    "performance monitoring"
                ],
                severity="MEDIUM",
                category="PERFORMANCE"
            )
        }
        return patterns
    
    def find_semantic_patterns(self, repo_id: str, gate_name: str) -> List[Dict[str, Any]]:
        """Find code that semantically matches a specific gate pattern"""
        
        if gate_name not in self.semantic_patterns:
            return []
        
        pattern = self.semantic_patterns[gate_name]
        semantic_matches = []
        
        # Search using semantic queries
        for query in pattern.semantic_queries:
            query_embedding = self.embedding_service.embed_single(query)
            if query_embedding:
                matches = self.vector_store.search_similar(
                    collection_name=repo_id,
                    query_vector=query_embedding,
                    limit=20,
                    score_threshold=0.6
                )
                
                for match in matches:
                    semantic_matches.append({
                        "id": match.id,
                        "score": match.score,
                        "content": match.payload.get("content", ""),
                        "file_path": match.payload.get("file_path", ""),
                        "start_line": match.payload.get("start_line", 0),
                        "end_line": match.payload.get("end_line", 0),
                        "language": match.payload.get("language", "text"),
                        "query": query,
                        "pattern_name": pattern.name
                    })
        
        # Remove duplicates and sort by score
        unique_matches = self._deduplicate_matches(semantic_matches)
        unique_matches.sort(key=lambda x: x["score"], reverse=True)
        
        return unique_matches
    
    def _deduplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """Remove duplicate matches based on file path and line numbers"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            key = (match["file_path"], match["start_line"], match["end_line"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches


class ContextAwareAnalyzer:
    """Analyze code with surrounding context"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def analyze_context_completeness(self, repo_id: str, match: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the completeness of a pattern match with surrounding context"""
        
        file_path = match["file_path"]
        start_line = match["start_line"]
        end_line = match["end_line"]
        
        # Get surrounding context (before and after the matched code)
        context_before = self._get_context_before(repo_id, file_path, start_line)
        context_after = self._get_context_after(repo_id, file_path, end_line)
        
        # Analyze completeness based on pattern type
        completeness_score = self._calculate_completeness_score(
            match, context_before, context_after
        )
        
        # Identify missing elements
        missing_elements = self._identify_missing_elements(
            match, context_before, context_after
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            match, missing_elements, completeness_score
        )
        
        return {
            "completeness_score": completeness_score,
            "context_before": context_before,
            "context_after": context_after,
            "missing_elements": missing_elements,
            "recommendations": recommendations
        }
    
    def _get_context_before(self, repo_id: str, file_path: str, start_line: int) -> List[Dict]:
        """Get code context before the matched lines"""
        # Implementation would search for chunks in the same file before start_line
        return []
    
    def _get_context_after(self, repo_id: str, file_path: str, end_line: int) -> List[Dict]:
        """Get code context after the matched lines"""
        # Implementation would search for chunks in the same file after end_line
        return []
    
    def _calculate_completeness_score(self, match: Dict, context_before: List, context_after: List) -> float:
        """Calculate how complete the pattern implementation is"""
        # Base score from semantic match
        base_score = match["score"]
        
        # Adjust based on context analysis
        context_score = 0.0
        
        # Example: Check if error handling has proper logging
        if "error" in match["content"].lower():
            if any("log" in ctx.get("content", "").lower() for ctx in context_before + context_after):
                context_score += 0.2
        
        return min(1.0, base_score + context_score)
    
    def _identify_missing_elements(self, match: Dict, context_before: List, context_after: List) -> List[str]:
        """Identify missing elements in the pattern implementation"""
        missing = []
        
        # Example: Check for missing elements in error handling
        if "try" in match["content"] and "catch" not in match["content"]:
            missing.append("Exception handling (catch block)")
        
        if "log" in match["content"].lower() and "error" in match["content"].lower():
            if not any("level" in ctx.get("content", "").lower() for ctx in context_before + context_after):
                missing.append("Log level specification")
        
        return missing
    
    def _generate_recommendations(self, match: Dict, missing_elements: List[str], score: float) -> List[str]:
        """Generate recommendations for improving the pattern implementation"""
        recommendations = []
        
        if score < 0.7:
            recommendations.append("Consider improving the implementation completeness")
        
        for element in missing_elements:
            recommendations.append(f"Add missing: {element}")
        
        return recommendations


class EnhancedScanningService:
    """Enhanced scanning service using vector embeddings"""
    
    def __init__(self, advanced_llm_service: AdvancedLLMService):
        self.advanced_llm_service = advanced_llm_service
        self.embedding_service = advanced_llm_service.embedding_service
        self.vector_store = advanced_llm_service.vector_store
        
        # Initialize components
        self.pattern_matcher = SemanticPatternMatcher(self.embedding_service, self.vector_store)
        self.context_analyzer = ContextAwareAnalyzer(self.vector_store)
    
    def enhanced_scan_repository(self, repo_id: str, gates: List[str]) -> Dict[str, Any]:
        """Perform enhanced scanning using semantic patterns"""
        
        print(f"🔍 Starting enhanced scan for repository: {repo_id}")
        
        scan_results = {}
        overall_scores = {}
        
        for gate in gates:
            print(f"  📊 Analyzing gate: {gate}")
            
            # Find semantic patterns
            semantic_matches = self.pattern_matcher.find_semantic_patterns(repo_id, gate)
            
            # Analyze context for each match
            enhanced_matches = []
            for match in semantic_matches:
                context_analysis = self.context_analyzer.analyze_context_completeness(
                    repo_id, match
                )
                
                enhanced_match = {
                    **match,
                    "context_analysis": context_analysis
                }
                enhanced_matches.append(enhanced_match)
            
            # Calculate enhanced score
            if enhanced_matches:
                avg_score = sum(match["context_analysis"]["completeness_score"] 
                              for match in enhanced_matches) / len(enhanced_matches)
            else:
                avg_score = 0.0
            
            # Generate recommendations
            all_recommendations = []
            for match in enhanced_matches:
                all_recommendations.extend(match["context_analysis"]["recommendations"])
            
            scan_results[gate] = {
                "semantic_matches": enhanced_matches,
                "total_matches": len(enhanced_matches),
                "enhanced_score": avg_score,
                "recommendations": list(set(all_recommendations)),  # Remove duplicates
                "missing_elements": self._aggregate_missing_elements(enhanced_matches)
            }
            
            overall_scores[gate] = avg_score
        
        # Calculate overall enhanced score
        overall_enhanced_score = sum(overall_scores.values()) / len(overall_scores) if overall_scores else 0.0
        
        return {
            "repo_id": repo_id,
            "scan_timestamp": time.time(),
            "gates_analyzed": gates,
            "overall_enhanced_score": overall_enhanced_score,
            "gate_results": scan_results,
            "summary": self._generate_enhanced_summary(scan_results)
        }
    
    def _aggregate_missing_elements(self, enhanced_matches: List[Dict]) -> List[str]:
        """Aggregate missing elements across all matches"""
        all_missing = []
        for match in enhanced_matches:
            all_missing.extend(match["context_analysis"]["missing_elements"])
        
        # Count occurrences and return unique elements
        from collections import Counter
        missing_counts = Counter(all_missing)
        return [f"{element} (found in {count} instances)" for element, count in missing_counts.items()]
    
    def _generate_enhanced_summary(self, scan_results: Dict) -> Dict[str, Any]:
        """Generate enhanced summary of scan results"""
        
        total_matches = sum(result["total_matches"] for result in scan_results.values())
        total_recommendations = sum(len(result["recommendations"]) for result in scan_results.values())
        
        # Identify top patterns
        top_patterns = []
        for gate, result in scan_results.items():
            if result["total_matches"] > 0:
                top_patterns.append({
                    "gate": gate,
                    "matches": result["total_matches"],
                    "score": result["enhanced_score"]
                })
        
        top_patterns.sort(key=lambda x: x["matches"], reverse=True)
        
        return {
            "total_pattern_matches": total_matches,
            "total_recommendations": total_recommendations,
            "top_patterns": top_patterns[:5],
            "improvement_areas": self._identify_improvement_areas(scan_results)
        }
    
    def _identify_improvement_areas(self, scan_results: Dict) -> List[str]:
        """Identify areas that need improvement"""
        improvement_areas = []
        
        for gate, result in scan_results.items():
            if result["enhanced_score"] < 0.5:
                improvement_areas.append(f"{gate}: Low implementation quality (score: {result['enhanced_score']:.2f})")
            
            if result["total_matches"] == 0:
                improvement_areas.append(f"{gate}: No patterns found - consider implementing")
        
        return improvement_areas
