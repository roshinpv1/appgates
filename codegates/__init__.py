"""
CodeGates - A code quality gate validation framework
"""

__version__ = "0.1.0"

# Core components
from .models import Language, GateType, ScanConfig, ValidationResult, GateScore
from .core.gate_validator import GateValidator
from .core.language_detector import LanguageDetector

# CLI is imported separately to avoid circular dependencies

__all__ = [
    "Language",
    "GateType", 
    "ScanConfig",
    "ValidationResult",
    "GateScore",
    "GateValidator",
    "LanguageDetector",
    "__version__"
] 