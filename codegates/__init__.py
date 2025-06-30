"""
CodeGates Hard Gate Validation System

A comprehensive tool for validating hard gates in software development projects.
"""

__version__ = "1.0.0"

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