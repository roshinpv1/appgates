"""
Data models for the Hard Gate Validation System
"""

from typing import List, Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime
import os


class Language(str, Enum):
    """Supported programming languages"""
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CSHARP = "csharp"
    DOTNET = "dotnet"


class GateType(str, Enum):
    """15 Hard Gates for validation"""
    STRUCTURED_LOGS = "structured_logs"
    AVOID_LOGGING_SECRETS = "avoid_logging_secrets"
    AUDIT_TRAIL = "audit_trail"
    CORRELATION_ID = "correlation_id"
    LOG_API_CALLS = "log_api_calls"
    LOG_BACKGROUND_JOBS = "log_background_jobs"
    LOG_APPLICATION_MESSAGES = "log_application_messages"  # Added new enum value
    UI_ERRORS = "ui_errors"
    RETRY_LOGIC = "retry_logic"
    TIMEOUTS = "timeouts"
    THROTTLING = "throttling"
    CIRCUIT_BREAKERS = "circuit_breakers"
    ERROR_LOGS = "error_logs"
    HTTP_CODES = "http_codes"
    UI_ERROR_TOOLS = "ui_error_tools"
    AUTOMATED_TESTS = "automated_tests"


class GateScore(BaseModel):
    """Score for a single gate"""
    gate: GateType
    expected: int = Field(ge=0, description="Expected number of implementations")
    found: int = Field(ge=0, description="Actual number found")
    coverage: float = Field(default=0.0, ge=0, le=100, description="Coverage percentage")
    quality_score: float = Field(default=0.0, ge=0, le=100, description="Quality score")
    final_score: float = Field(default=0.0, ge=0, le=100, description="Final weighted score")
    status: str = Field(default="UNKNOWN", description="Pass/Fail/Warning status")
    details: List[str] = Field(default_factory=list, description="Implementation details")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    matches: List[Dict[str, Any]] = Field(default_factory=list, description="Enhanced metadata for pattern matches")
    
    @field_validator('quality_score', mode='before')
    @classmethod
    def validate_quality_score(cls, v):
        """Ensure quality_score is never None"""
        if v is None:
            return 0.0
        return max(0.0, min(float(v), 100.0))
    
    @field_validator('coverage', mode='before')
    @classmethod
    def calculate_coverage(cls, v, info):
        if v is not None:
            return min(max(float(v), 0.0), 100.0)  # Clamp between 0 and 100
        
        data = info.data if hasattr(info, 'data') else {}
        expected = data.get('expected', 0)
        found = data.get('found', 0)
        
        if expected == 0:
            return 100.0 if found == 0 else 0.0  # Perfect score if both are 0, else 0
        
        coverage = (found / expected) * 100
        return min(max(coverage, 0.0), 100.0)  # Clamp between 0 and 100
    
    @field_validator('final_score', mode='before')
    @classmethod
    def calculate_final_score(cls, v, info):
        if v is not None:
            return min(max(float(v), 0.0), 100.0)  # Clamp between 0 and 100
            
        data = info.data if hasattr(info, 'data') else {}
        coverage = data.get('coverage', 0)
        quality = data.get('quality_score', 0)
        final_score = (coverage * 0.7) + (quality * 0.3)
        return min(max(final_score, 0.0), 100.0)  # Clamp between 0 and 100
    
    @field_validator('recommendations', mode='before')
    @classmethod
    def validate_recommendations(cls, v):
        """Ensure recommendations is always a list and handle unhashable types"""
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            # Convert any non-string items to strings and ensure uniqueness
            result = []
            seen = set()
            for item in v:
                if isinstance(item, dict):
                    # Convert dict to string representation
                    item_str = str(item)
                else:
                    item_str = str(item)
                
                if item_str not in seen:
                    result.append(item_str)
                    seen.add(item_str)
            return result
        return [str(v)]


class FileAnalysis(BaseModel):
    """Analysis result for a single file"""
    file_path: str
    language: Language
    lines_of_code: int = 0
    gates_found: List[GateType] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Complete validation result for a codebase"""
    project_name: str
    project_path: str
    language: Language
    total_files: int = 0
    total_lines: int = 0
    scan_duration: float = Field(ge=0, description="Scan duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
    repository_url: Optional[str] = None  # Add repository URL field
    
    # Gate scores
    gate_scores: List[GateScore] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0, le=100, description="Overall project score")
    
    # File analysis
    file_analyses: List[FileAnalysis] = Field(default_factory=list)
    
    # Summary metrics
    passed_gates: int = 0
    warning_gates: int = 0
    failed_gates: int = 0
    
    # Recommendations
    critical_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    @computed_field
    @property
    def computed_overall_score(self) -> float:
        """Calculate overall score from gate scores"""
        if not self.gate_scores:
            return 0.0
        
        total_score = sum(gate.final_score for gate in self.gate_scores)
        return total_score / len(self.gate_scores)


class ReportConfig(BaseModel):
    """Configuration for report generation"""
    format: str = Field(default="json", description="Output format: json, html, pdf, excel")
    output_path: str = Field(default_factory=lambda: os.getenv('CODEGATES_REPORTS_DIR', './details'), description="Output directory")
    include_details: bool = Field(default=True, description="Include detailed analysis")
    include_recommendations: bool = Field(default=True, description="Include recommendations")
    template: Optional[str] = Field(default=None, description="Custom template path")


class ScanConfig(BaseModel):
    """Configuration for codebase scanning"""
    target_path: str = Field(description="Path to scan")
    languages: List[Language] = Field(default_factory=list, description="Languages to scan")
    exclude_patterns: List[str] = Field(default_factory=list, description="Patterns to exclude")
    include_patterns: List[str] = Field(default_factory=list, description="Patterns to include")
    max_file_size: int = Field(default=1024*1024, description="Max file size in bytes")
    follow_symlinks: bool = Field(default=False, description="Follow symbolic links")
    
    # Gate-specific configurations
    gate_configs: Dict[GateType, Dict[str, Any]] = Field(default_factory=dict)
    
    # Thresholds
    min_coverage_threshold: float = Field(default=70.0, ge=0, le=100)
    min_quality_threshold: float = Field(default=80.0, ge=0, le=100) 