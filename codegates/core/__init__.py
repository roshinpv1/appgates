"""Core components for the CodeGates framework"""

from .language_detector import LanguageDetector
from .gate_validator import GateValidator
from .gate_scorer import GateScorer

# Import the factory from the gate_validators package
try:
    from .gate_validators.factory import GateValidatorFactory
except ImportError:
    # Fallback if imports fail
    class GateValidatorFactory:
        def get_validator(self, gate_type, language):
            return None

__all__ = [
    "LanguageDetector",
    "GateValidator", 
    "GateScorer",
    "GateValidatorFactory"
] 