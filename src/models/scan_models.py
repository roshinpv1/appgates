"""
Data models for the scan process
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class GateStatus(Enum):
    """Gate evaluation status"""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RecommendationType(Enum):
    """Recommendation types"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    BEST_PRACTICES = "best_practices"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    OBSERVABILITY = "observability"


@dataclass
class Symbol:
    """Code symbol information"""
    name: str
    kind: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    signature: Optional[str] = None
    references: Optional[List[str]] = None
    imports: Optional[List[str]] = None


@dataclass
class ImportInfo:
    """Import information"""
    module: str
    line: int
    name: Optional[str] = None
    alias: Optional[str] = None
    type: str = "import"


@dataclass
class FileMetadata:
    """File metadata"""
    filename: str
    relative_path: str
    file_size: int
    total_lines: int
    language: str
    file_type: str
    is_binary: bool
    encoding: str
    permissions: str
    git_status: str
    git_tracked: bool
    mtime: datetime
    complexity_score: Optional[float] = None
    cyclomatic_complexity: Optional[int] = None


@dataclass
class CodeChunk:
    """Code chunk with metadata"""
    content: str
    start_line: int
    end_line: int
    chunk_size: int
    overlap_size: int
    content_hash: str
    symbol_name: Optional[str] = None
    symbol_kind: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class PatternMatch:
    """Detailed pattern match information"""
    file_path: str
    line_number: int
    match_text: str
    repo_type: str  # "main" or "cd"
    start_pos: int
    end_pos: int
    pattern: str  # The regex pattern that matched


@dataclass
class Pattern:
    """Pattern definition"""
    gate_id: str
    name: str
    description: str
    pattern: str
    severity: str
    category: str
    source: str = "static"  # static, dynamic
    examples: List[str] = field(default_factory=list)


@dataclass
class GateResult:
    """Gate evaluation result"""
    gate_id: str
    gate_name: str
    status: GateStatus
    expected_count: int
    actual_count: int
    threshold: int
    patterns_found: List[str]  # Keep for backward compatibility
    recommendations: List[str]
    confidence_score: float
    reasoning: str
    detailed_matches: List[PatternMatch] = field(default_factory=list)  # New detailed matches


@dataclass
class ContextualRecommendation:
    """Contextual recommendation"""
    title: str
    description: str
    recommendation_type: RecommendationType
    confidence_score: float
    code_examples: List[str]
    pattern_references: List[str]
    similar_implementations: List[Dict[str, Any]]
    reasoning: str
    priority: str
    impact: str


@dataclass
class ScanResult:
    """Final scan result"""
    scan_id: str
    repo_url: str
    branch: str
    scan_timestamp: datetime
    total_gates: int
    passed_gates: int
    failed_gates: int
    partial_gates: int
    skipped_gates: int
    gate_results: List[GateResult]
    recommendations: List[str]
    risk_score: float
    scan_duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepositoryInfo:
    """Repository information"""
    repo_url: str
    branch: str
    local_path: str
    commit_hash: str
    total_files: int
    total_lines: int
    languages: List[str]
    dependencies: Dict[str, List[str]]
    build_files: List[str]
    config_files: List[str]
