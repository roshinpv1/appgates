"""
Contextual Recommendations Module
Leverages vector embeddings and semantic search for intelligent code recommendations
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .advanced_llm.vector_store import VectorStore, SearchResult
    from .advanced_llm.pattern_library import PatternLibraryService
    from .advanced_llm.core import AdvancedLLMService
except ImportError:
    from advanced_llm.vector_store import VectorStore, SearchResult
    from advanced_llm.pattern_library import PatternLibraryService
    from advanced_llm.core import AdvancedLLMService


class RecommendationType(Enum):
    """Types of recommendations"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    BEST_PRACTICES = "best_practices"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    OBSERVABILITY = "observability"


@dataclass
class ContextualRecommendation:
    """A contextual recommendation with metadata"""
    title: str
    description: str
    recommendation_type: RecommendationType
    confidence_score: float
    code_examples: List[str]
    pattern_references: List[str]
    similar_implementations: List[Dict[str, Any]]
    reasoning: str
    priority: str  # "high", "medium", "low"
    impact: str    # "critical", "important", "nice_to_have"


class ContextualRecommendationEngine:
    """Engine for generating contextual recommendations using vector search"""
    
    def __init__(self, vector_store: VectorStore, pattern_library: PatternLibraryService, advanced_llm: AdvancedLLMService):
        self.vector_store = vector_store
        self.pattern_library = pattern_library
        self.advanced_llm = advanced_llm
        
    async def generate_contextual_recommendations(
        self,
        code_context: str,
        language: str,
        domain: str = "general",
        recommendation_types: List[RecommendationType] = None
    ) -> List[ContextualRecommendation]:
        """Generate contextual recommendations based on code analysis"""
        
        if recommendation_types is None:
            recommendation_types = list(RecommendationType)
        
        recommendations = []
        
        for rec_type in recommendation_types:
            type_recommendations = await self._generate_type_recommendations(
                code_context, language, domain, rec_type
            )
            recommendations.extend(type_recommendations)
        
        # Sort by confidence and priority
        recommendations.sort(key=lambda x: (x.confidence_score, self._priority_score(x.priority)), reverse=True)
        
        return recommendations
    
    async def _generate_type_recommendations(
        self,
        code_context: str,
        language: str,
        domain: str,
        rec_type: RecommendationType
    ) -> List[ContextualRecommendation]:
        """Generate recommendations for a specific type"""
        
        # Create contextual query
        contextual_query = self._build_contextual_query(
            code_context, language, domain, rec_type
        )
        
        # Search for relevant patterns and code
        pattern_results = await self._search_patterns(contextual_query, rec_type)
        code_results = await self._search_similar_code(contextual_query, language)
        
        # Generate recommendations from search results
        recommendations = await self._create_recommendations(
            pattern_results, code_results, code_context, rec_type
        )
        
        return recommendations
    
    def _build_contextual_query(
        self,
        code_context: str,
        language: str,
        domain: str,
        rec_type: RecommendationType
    ) -> str:
        """Build a contextual search query"""
        
        query_templates = {
            RecommendationType.SECURITY: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find security vulnerabilities, authentication patterns, input validation, 
            authorization mechanisms, and security best practices
            """,
            
            RecommendationType.PERFORMANCE: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find performance optimization techniques, caching strategies, 
            database optimization, and scalability patterns
            """,
            
            RecommendationType.BEST_PRACTICES: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find coding best practices, design patterns, clean code principles, 
            and industry standards
            """,
            
            RecommendationType.CODE_QUALITY: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find code quality improvements, refactoring opportunities, 
            maintainability patterns, and readability enhancements
            """,
            
            RecommendationType.ARCHITECTURE: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find architectural patterns, design principles, 
            separation of concerns, and modularity approaches
            """,
            
            RecommendationType.TESTING: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find testing strategies, unit test patterns, 
            integration testing approaches, and test coverage improvements
            """,
            
            RecommendationType.OBSERVABILITY: f"""
            Language: {language}
            Domain: {domain}
            Code context: {code_context}
            Find logging patterns, monitoring strategies, 
            tracing implementations, and observability best practices
            """
        }
        
        return query_templates.get(rec_type, f"Find {rec_type.value} recommendations for {language} code")
    
    async def _search_patterns(self, query: str, rec_type: RecommendationType) -> List[SearchResult]:
        """Search for relevant patterns"""
        try:
            results = await self.vector_store.search(
                query=query,
                collection="pattern_library",
                limit=10
            )
            return results
        except Exception as e:
            print(f"⚠️ Pattern search failed: {e}")
            return []
    
    async def _search_similar_code(self, query: str, language: str) -> List[SearchResult]:
        """Search for similar code implementations"""
        try:
            # Add language filter to query
            language_query = f"{query} Language: {language}"
            
            results = await self.vector_store.search(
                query=language_query,
                collection="code_chunks",
                limit=15
            )
            return results
        except Exception as e:
            print(f"⚠️ Code search failed: {e}")
            return []
    
    async def _create_recommendations(
        self,
        pattern_results: List[SearchResult],
        code_results: List[SearchResult],
        code_context: str,
        rec_type: RecommendationType
    ) -> List[ContextualRecommendation]:
        """Create recommendations from search results"""
        
        recommendations = []
        
        # Process pattern-based recommendations
        for result in pattern_results[:5]:  # Top 5 patterns
            if hasattr(result, 'payload') and result.payload:
                recommendation = await self._create_pattern_recommendation(
                    result, code_context, rec_type
                )
                if recommendation:
                    recommendations.append(recommendation)
        
        # Process code-based recommendations
        for result in code_results[:3]:  # Top 3 code examples
            if hasattr(result, 'payload') and result.payload:
                recommendation = await self._create_code_recommendation(
                    result, code_context, rec_type
                )
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    async def _create_pattern_recommendation(
        self,
        pattern_result: SearchResult,
        code_context: str,
        rec_type: RecommendationType
    ) -> Optional[ContextualRecommendation]:
        """Create recommendation from pattern search result"""
        
        try:
            payload = pattern_result.payload
            
            # Extract pattern information
            title = payload.get('name', f"{rec_type.value.title()} Pattern")
            description = payload.get('description', '')
            confidence = getattr(pattern_result, 'score', 0.7)
            
            # Generate reasoning using LLM
            reasoning = await self._generate_reasoning(
                code_context, title, description, rec_type
            )
            
            return ContextualRecommendation(
                title=title,
                description=description,
                recommendation_type=rec_type,
                confidence_score=confidence,
                code_examples=payload.get('examples', []),
                pattern_references=[title],
                similar_implementations=[],
                reasoning=reasoning,
                priority=self._determine_priority(confidence, rec_type),
                impact=self._determine_impact(rec_type)
            )
            
        except Exception as e:
            print(f"⚠️ Failed to create pattern recommendation: {e}")
            return None
    
    async def _create_code_recommendation(
        self,
        code_result: SearchResult,
        code_context: str,
        rec_type: RecommendationType
    ) -> Optional[ContextualRecommendation]:
        """Create recommendation from code search result"""
        
        try:
            payload = code_result.payload
            
            # Extract code information
            content = payload.get('content', '')
            filename = payload.get('filename', 'Unknown file')
            confidence = getattr(code_result, 'score', 0.6)
            
            # Generate recommendation from similar code
            title = f"Similar {rec_type.value.title()} Implementation"
            description = f"Based on similar code in {filename}"
            
            reasoning = await self._generate_code_reasoning(
                code_context, content, rec_type
            )
            
            return ContextualRecommendation(
                title=title,
                description=description,
                recommendation_type=rec_type,
                confidence_score=confidence,
                code_examples=[content],
                pattern_references=[],
                similar_implementations=[{
                    'filename': filename,
                    'content': content,
                    'similarity': confidence
                }],
                reasoning=reasoning,
                priority=self._determine_priority(confidence, rec_type),
                impact=self._determine_impact(rec_type)
            )
            
        except Exception as e:
            print(f"⚠️ Failed to create code recommendation: {e}")
            return None
    
    async def _generate_reasoning(
        self,
        code_context: str,
        title: str,
        description: str,
        rec_type: RecommendationType
    ) -> str:
        """Generate reasoning for recommendation using LLM"""
        
        try:
            prompt = f"""
            Code Context: {code_context}
            
            Recommendation: {title}
            Description: {description}
            Type: {rec_type.value}
            
            Explain why this recommendation is relevant to the given code context.
            Provide specific reasoning and potential benefits.
            Keep it concise and actionable.
            """
            
            response = await self.advanced_llm.complete(prompt)
            return response.get('content', f"Relevant {rec_type.value} pattern for the codebase.")
            
        except Exception as e:
            print(f"⚠️ LLM reasoning generation failed: {e}")
            return f"Relevant {rec_type.value} pattern for the codebase."
    
    async def _generate_code_reasoning(
        self,
        code_context: str,
        similar_code: str,
        rec_type: RecommendationType
    ) -> str:
        """Generate reasoning for code-based recommendation"""
        
        try:
            prompt = f"""
            Current Code Context: {code_context}
            
            Similar Implementation:
            {similar_code}
            
            Type: {rec_type.value}
            
            Explain how this similar implementation can be applied to improve the current code.
            Highlight the key benefits and implementation approach.
            """
            
            response = await self.advanced_llm.complete(prompt)
            return response.get('content', f"Similar {rec_type.value} implementation found.")
            
        except Exception as e:
            print(f"⚠️ LLM code reasoning generation failed: {e}")
            return f"Similar {rec_type.value} implementation found."
    
    def _determine_priority(self, confidence: float, rec_type: RecommendationType) -> str:
        """Determine recommendation priority"""
        
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _determine_impact(self, rec_type: RecommendationType) -> str:
        """Determine recommendation impact"""
        
        critical_types = [RecommendationType.SECURITY, RecommendationType.PERFORMANCE]
        important_types = [RecommendationType.BEST_PRACTICES, RecommendationType.CODE_QUALITY]
        
        if rec_type in critical_types:
            return "critical"
        elif rec_type in important_types:
            return "important"
        else:
            return "nice_to_have"
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score for sorting"""
        priority_scores = {"high": 3, "medium": 2, "low": 1}
        return priority_scores.get(priority, 1)


class ContextualSearchAPI:
    """API for contextual search and recommendations"""
    
    def __init__(self, recommendation_engine: ContextualRecommendationEngine):
        self.engine = recommendation_engine
    
    async def search_contextual_patterns(
        self,
        query: str,
        language: str,
        pattern_type: str = None
    ) -> List[Dict[str, Any]]:
        """Search for contextual patterns"""
        
        try:
            # Build contextual query
            contextual_query = f"""
            Query: {query}
            Language: {language}
            Find relevant patterns, best practices, and implementation examples
            """
            
            # Search patterns
            pattern_results = await self.engine.vector_store.search(
                query=contextual_query,
                collection="pattern_library",
                limit=10
            )
            
            # Search similar code
            code_results = await self.engine.vector_store.search(
                query=contextual_query,
                collection="code_chunks",
                limit=10
            )
            
            # Format results
            results = []
            
            for result in pattern_results:
                if hasattr(result, 'payload') and result.payload:
                    results.append({
                        'type': 'pattern',
                        'title': result.payload.get('name', 'Pattern'),
                        'description': result.payload.get('description', ''),
                        'confidence': getattr(result, 'score', 0.0),
                        'examples': result.payload.get('examples', [])
                    })
            
            for result in code_results:
                if hasattr(result, 'payload') and result.payload:
                    results.append({
                        'type': 'code',
                        'title': result.payload.get('filename', 'Code Example'),
                        'description': result.payload.get('content', '')[:200] + '...',
                        'confidence': getattr(result, 'score', 0.0),
                        'content': result.payload.get('content', '')
                    })
            
            # Sort by confidence
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"⚠️ Contextual pattern search failed: {e}")
            return []
    
    async def get_similar_implementations(
        self,
        target_code: str,
        language: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar code implementations"""
        
        try:
            query = f"""
            Target code: {target_code}
            Language: {language}
            Find similar implementations, alternative approaches, and best practices
            """
            
            results = await self.engine.vector_store.search(
                query=query,
                collection="code_chunks",
                limit=limit
            )
            
            similar_implementations = []
            
            for result in results:
                if hasattr(result, 'payload') and result.payload:
                    similar_implementations.append({
                        'filename': result.payload.get('filename', 'Unknown'),
                        'content': result.payload.get('content', ''),
                        'similarity': getattr(result, 'score', 0.0),
                        'metadata': {
                            'language': result.payload.get('language', language),
                            'file_type': result.payload.get('file_type', ''),
                            'complexity': result.payload.get('complexity_score', 0)
                        }
                    })
            
            return similar_implementations
            
        except Exception as e:
            print(f"⚠️ Similar implementation search failed: {e}")
            return []
