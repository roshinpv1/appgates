"""Analysis result models for code quality gates"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CodeAnalysisResult:
    """Result of LLM code analysis"""
    quality_score: float
    patterns_found: List[str]
    security_issues: List[str]
    recommendations: List[str]
    technology_insights: Dict[str, Any]
    code_smells: List[str]
    best_practices: List[str] 