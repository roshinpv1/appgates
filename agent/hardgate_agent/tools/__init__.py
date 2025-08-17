"""
HardGate Agent Tools
Comprehensive security analysis tools for enterprise hard gate validation
"""

# Import wrapper functions for Google ADK compatibility
from .repository_analysis import analyze_repository
from .gate_validation import validate_gates
from .gate_validation import gate_validation  # alias for compatibility
from .evidence_collection import evidence_collection_tool
from .llm_analysis import llm_analysis_tool
from .security_analysis import analyze_security
from .code_scanning import scan_code
from .compliance_check import check_compliance
from .report_generation import generate_report
from .llm_integration import llm_integration
from .splunk_integration import splunk_integration
from .jira_integration import jira_integration
from .gate_applicability import gate_applicability
from .html_report_generator import html_report_generator

# Available tools list
__all__ = [
    # Wrapper functions
    "analyze_repository",
    "validate_gates",
    "gate_validation",
    "evidence_collection_tool",
    "llm_analysis_tool",
    "analyze_security",
    "scan_code",
    "check_compliance",
    "generate_report",
    "llm_integration",
    "splunk_integration",
    "jira_integration",
    "gate_applicability",
    "html_report_generator"
] 