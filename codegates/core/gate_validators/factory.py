"""
Gate Validator Factory - Creates appropriate validators for each gate/language combination
"""

from typing import Optional, Dict, Type
from ...models import GateType, Language
from .base import BaseGateValidator


class GateValidatorFactory:
    """Factory for creating gate validators"""
    
    def __init__(self):
        self._validators = self._initialize_validator_map()
    
    def get_validator(self, gate_type: GateType, 
                     language: Language) -> Optional[BaseGateValidator]:
        """Get appropriate validator for gate type and language"""
        
        validator_class = self._validators.get((gate_type, language))
        if validator_class:
            return validator_class(language)
        
        # Try to get a generic validator for the gate type
        generic_validator = self._get_generic_validator(gate_type, language)
        if generic_validator:
            return generic_validator
        
        return None
    
    def _initialize_validator_map(self) -> Dict[tuple, Type[BaseGateValidator]]:
        """Initialize the validator mapping"""
        
        # Import validators dynamically to avoid circular imports
        from .logging_validators import (
            StructuredLogsValidator, SecretLogsValidator,
            AuditTrailValidator, CorrelationIdValidator,
            ApiLogsValidator, BackgroundJobLogsValidator
        )
        from .error_validators import (
            ErrorLogsValidator, UiErrorsValidator,
            HttpCodesValidator, UiErrorToolsValidator
        )
        from .reliability_validators import (
            RetryLogicValidator, TimeoutsValidator,
            ThrottlingValidator, CircuitBreakerValidator
        )
        from .testing_validators import AutomatedTestsValidator
        
        validators = {}
        
        # Map each gate type to supported languages
        gate_language_map = {
            # Logging gates - supported by all languages
            GateType.STRUCTURED_LOGS: {
                Language.JAVA: StructuredLogsValidator,
                Language.PYTHON: StructuredLogsValidator,
                Language.JAVASCRIPT: StructuredLogsValidator,
                Language.TYPESCRIPT: StructuredLogsValidator,
                Language.CSHARP: StructuredLogsValidator,
            },
            GateType.AVOID_LOGGING_SECRETS: {
                Language.JAVA: SecretLogsValidator,
                Language.PYTHON: SecretLogsValidator,
                Language.JAVASCRIPT: SecretLogsValidator,
                Language.TYPESCRIPT: SecretLogsValidator,
                Language.CSHARP: SecretLogsValidator,
            },
            GateType.AUDIT_TRAIL: {
                Language.JAVA: AuditTrailValidator,
                Language.PYTHON: AuditTrailValidator,
                Language.JAVASCRIPT: AuditTrailValidator,
                Language.TYPESCRIPT: AuditTrailValidator,
                Language.CSHARP: AuditTrailValidator,
            },
            GateType.CORRELATION_ID: {
                Language.JAVA: CorrelationIdValidator,
                Language.PYTHON: CorrelationIdValidator,
                Language.JAVASCRIPT: CorrelationIdValidator,
                Language.TYPESCRIPT: CorrelationIdValidator,
                Language.CSHARP: CorrelationIdValidator,
            },
            GateType.LOG_API_CALLS: {
                Language.JAVA: ApiLogsValidator,
                Language.PYTHON: ApiLogsValidator,
                Language.JAVASCRIPT: ApiLogsValidator,
                Language.TYPESCRIPT: ApiLogsValidator,
                Language.CSHARP: ApiLogsValidator,
            },
            GateType.LOG_BACKGROUND_JOBS: {
                Language.JAVA: BackgroundJobLogsValidator,
                Language.PYTHON: BackgroundJobLogsValidator,
                Language.JAVASCRIPT: BackgroundJobLogsValidator,
                Language.TYPESCRIPT: BackgroundJobLogsValidator,
                Language.CSHARP: BackgroundJobLogsValidator,
            },
            
            # Error handling gates
            GateType.ERROR_LOGS: {
                Language.JAVA: ErrorLogsValidator,
                Language.PYTHON: ErrorLogsValidator,
                Language.JAVASCRIPT: ErrorLogsValidator,
                Language.TYPESCRIPT: ErrorLogsValidator,
                Language.CSHARP: ErrorLogsValidator,
            },
            GateType.UI_ERRORS: {
                Language.JAVASCRIPT: UiErrorsValidator,
                Language.TYPESCRIPT: UiErrorsValidator,
            },
            GateType.HTTP_CODES: {
                Language.JAVA: HttpCodesValidator,
                Language.PYTHON: HttpCodesValidator,
                Language.JAVASCRIPT: HttpCodesValidator,
                Language.TYPESCRIPT: HttpCodesValidator,
                Language.CSHARP: HttpCodesValidator,
            },
            GateType.UI_ERROR_TOOLS: {
                Language.JAVASCRIPT: UiErrorToolsValidator,
                Language.TYPESCRIPT: UiErrorToolsValidator,
            },
            
            # Reliability gates
            GateType.RETRY_LOGIC: {
                Language.JAVA: RetryLogicValidator,
                Language.PYTHON: RetryLogicValidator,
                Language.JAVASCRIPT: RetryLogicValidator,
                Language.TYPESCRIPT: RetryLogicValidator,
                Language.CSHARP: RetryLogicValidator,
            },
            GateType.TIMEOUTS: {
                Language.JAVA: TimeoutsValidator,
                Language.PYTHON: TimeoutsValidator,
                Language.JAVASCRIPT: TimeoutsValidator,
                Language.TYPESCRIPT: TimeoutsValidator,
                Language.CSHARP: TimeoutsValidator,
            },
            GateType.THROTTLING: {
                Language.JAVA: ThrottlingValidator,
                Language.PYTHON: ThrottlingValidator,
                Language.JAVASCRIPT: ThrottlingValidator,
                Language.TYPESCRIPT: ThrottlingValidator,
                Language.CSHARP: ThrottlingValidator,
            },
            GateType.CIRCUIT_BREAKERS: {
                Language.JAVA: CircuitBreakerValidator,
                Language.PYTHON: CircuitBreakerValidator,
                Language.JAVASCRIPT: CircuitBreakerValidator,
                Language.TYPESCRIPT: CircuitBreakerValidator,
                Language.CSHARP: CircuitBreakerValidator,
            },
            
            # Testing gates
            GateType.AUTOMATED_TESTS: {
                Language.JAVA: AutomatedTestsValidator,
                Language.PYTHON: AutomatedTestsValidator,
                Language.JAVASCRIPT: AutomatedTestsValidator,
                Language.TYPESCRIPT: AutomatedTestsValidator,
                Language.CSHARP: AutomatedTestsValidator,
            }
        }
        
        # Flatten the nested dictionary
        for gate_type, lang_validators in gate_language_map.items():
            for lang, validator_class in lang_validators.items():
                validators[(gate_type, lang)] = validator_class
        
        return validators
    
    def _get_generic_validator(self, gate_type: GateType, 
                             language: Language) -> Optional[BaseGateValidator]:
        """Get a generic validator that might work across languages"""
        
        # For now, try to find any validator for this gate type
        for (gt, lang), validator_class in self._validators.items():
            if gt == gate_type:
                try:
                    return validator_class(language)
                except Exception:
                    continue
        
        return None
    
    def get_supported_gates(self, language: Language) -> list[GateType]:
        """Get list of supported gates for a language"""
        
        supported_gates = []
        for (gate_type, lang), _ in self._validators.items():
            if lang == language and gate_type not in supported_gates:
                supported_gates.append(gate_type)
        
        return supported_gates
    
    def get_supported_languages(self, gate_type: GateType) -> list[Language]:
        """Get list of supported languages for a gate"""
        
        supported_languages = []
        for (gt, lang), _ in self._validators.items():
            if gt == gate_type and lang not in supported_languages:
                supported_languages.append(lang)
        
        return supported_languages 