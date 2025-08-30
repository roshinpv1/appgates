#!/usr/bin/env python3
"""
Centralized Gate Definitions

This module provides a single source of truth for all gate definitions,
eliminating the need for scattered gate definitions across multiple files.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


class GateCategory(Enum):
    """Gate categories"""
    AUDITABILITY = "auditability"
    ERROR_HANDLING = "error_handling"
    AVAILABILITY = "availability"
    TESTING = "testing"
    SECURITY = "security"


class GateSeverity(Enum):
    """Gate severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class GateDefinition:
    """Complete gate definition structure"""
    gate_id: str
    gate_name: str
    prompt: str
    category: GateCategory
    severity: GateSeverity
    is_hard_gate: bool = False
    expected_patterns: Optional[List[str]] = None
    implementation_type: Optional[str] = None
    description: Optional[str] = None


class GateRegistry:
    """
    Centralized registry for all gate definitions
    Provides a single source of truth for gate information
    """
    
    def __init__(self):
        self._gates: Dict[str, GateDefinition] = {}
        self._initialize_gates()
    
    def _initialize_gates(self):
        """Initialize all gate definitions"""
        
        # Alerting Gates
        self._gates.update({
            "0.1": GateDefinition(
                gate_id="0.1",
                gate_name="All alerting is actionable",
                prompt="Implement actionable alerting that provides clear guidance on what actions to take when alerts are triggered. Alerts should include Splunk, AppDynamics, ThousandEyes or similar monitoring tools.",
                category=GateCategory.SECURITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="alerting",
                description="Implement actionable alerting with monitoring tools"
            )
        })
        
        # Auditability Gates
        self._gates.update({
            "1.2": GateDefinition(
                gate_id="1.2",
                gate_name="Log Application Messages",
                prompt="Log application messages with standard log libraries to make it easier to capture the right information in the right format. The Enterprise NFR needs to be completed by the app team and validated prior to release deployment.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="application_logging",
                description="Use standard logging libraries for application messages"
            ),
            "1.3": GateDefinition(
                gate_id="1.3",
                gate_name="Audit Trail",
                prompt="Maintain logs of user and system activity to support system failure, system response, issues, and incident response.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="audit_trail",
                description="Maintain comprehensive audit trails"
            ),
            "1.5": GateDefinition(
                gate_id="1.5",
                gate_name="Correlation ID",
                prompt="Implement correlation IDs to track requests across different services and components for better debugging and monitoring.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.MEDIUM,
                is_hard_gate=True,
                implementation_type="correlation_id",
                description="Implement correlation IDs for request tracking"
            ),
            "1.6": GateDefinition(
                gate_id="1.6",
                gate_name="Log API Calls",
                prompt="Log REST API calls to capture external component interaction for troubleshooting. The Enterprise NFR needs to be completed by the app team.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="api_logging",
                description="Log all API calls for troubleshooting"
            ),
            "1.8": GateDefinition(
                gate_id="1.8",
                gate_name="Logs Searchable/Available",
                prompt="Logs are searchable and available for both the platform and development team. Application logs written to standard output and log files must be sent to a central application for troubleshooting. The Enterprise Architecture NFR needs to be completed by the app team prior to release deployment.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="logging",
                description="Make logs searchable and available"
            ),
            "1.10": GateDefinition(
                gate_id="1.10",
                gate_name="Avoid Logging Sensitive Data",
                prompt="Avoid logging sensitive data such as passwords, tokens, and personal information. Implement proper data masking and filtering in logging configurations.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="security_logging",
                description="Prevent logging of sensitive information"
            ),
            "2.7": GateDefinition(
                gate_id="2.7",
                gate_name="Client UI Errors Logged",
                prompt="Log client-side UI errors and send them to the central logging system for monitoring and debugging.",
                category=GateCategory.AUDITABILITY,
                severity=GateSeverity.MEDIUM,
                is_hard_gate=True,
                implementation_type="ui_error_logging",
                description="Log client-side UI errors"
            )
        })
        
        # Error Handling Gates
        self._gates.update({
            "2.1": GateDefinition(
                gate_id="2.1",
                gate_name="Error Logs",
                prompt="Implement comprehensive error logging and exception handling throughout the application to capture and track all errors.",
                category=GateCategory.ERROR_HANDLING,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="error_logging",
                description="Implement comprehensive error logging"
            ),
            "2.3": GateDefinition(
                gate_id="2.3",
                gate_name="HTTP Status Codes",
                prompt="Use appropriate HTTP status codes for all API responses to provide clear error information to clients.",
                category=GateCategory.ERROR_HANDLING,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="http_status_codes",
                description="Use proper HTTP status codes"
            ),
            "2.4": GateDefinition(
                gate_id="2.4",
                gate_name="Client Error Tracking",
                prompt="Implement client-side error tracking and reporting to capture user experience issues and application errors.",
                category=GateCategory.ERROR_HANDLING,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="client_error_tracking",
                description="Track and report client-side errors"
            )
        })
        
        # Availability Gates
        self._gates.update({
            "1.5": GateDefinition(
                gate_id="1.5",
                gate_name="Timeouts",
                prompt="Implement proper timeout configurations for all external calls and operations to prevent hanging requests and improve system responsiveness.",
                category=GateCategory.AVAILABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="timeouts",
                description="Implement proper timeout configurations"
            ),
            "1.12": GateDefinition(
                gate_id="1.12",
                gate_name="Retry Logic",
                prompt="Implement retry logic for transient failures to improve system reliability and user experience.",
                category=GateCategory.AVAILABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="retry_logic",
                description="Implement retry mechanisms for transient failures"
            ),
            "3.6": GateDefinition(
                gate_id="3.6",
                gate_name="Throttling",
                prompt="Implement request throttling to prevent system overload and ensure fair resource distribution.",
                category=GateCategory.AVAILABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="throttling",
                description="Implement request throttling mechanisms"
            ),
            "3.9": GateDefinition(
                gate_id="3.9",
                gate_name="Circuit Breakers",
                prompt="Implement circuit breakers to detect failures and prevent cascading failures in distributed systems.",
                category=GateCategory.AVAILABILITY,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="circuit_breaker",
                description="Implement circuit breakers for external dependencies"
            ),
            "3.18": GateDefinition(
                gate_id="3.18",
                gate_name="Auto Scale",
                prompt="System can automatically scale based on usage telemetry. The Enterprise Architecture NFR needs to be completed by the app team.",
                category=GateCategory.AVAILABILITY,
                severity=GateSeverity.MEDIUM,
                is_hard_gate=True,
                implementation_type="auto_scaling",
                description="Implement automatic scaling capabilities"
            )
        })
        
        # Testing Gates
        self._gates.update({
            "2": GateDefinition(
                gate_id="2",
                gate_name="Automated Tests",
                prompt="Implement comprehensive automated tests including unit tests, integration tests, and end-to-end tests to ensure code quality and reliability.",
                category=GateCategory.TESTING,
                severity=GateSeverity.HIGH,
                is_hard_gate=True,
                implementation_type="automated_testing",
                description="Implement comprehensive automated testing"
            )
        })
    
    def get_gate(self, gate_id: str) -> Optional[GateDefinition]:
        """Get a specific gate by ID"""
        return self._gates.get(gate_id)
    
    def get_all_gates(self) -> List[GateDefinition]:
        """Get all gate definitions"""
        return list(self._gates.values())
    
    def get_gates_by_category(self, category: GateCategory) -> List[GateDefinition]:
        """Get all gates in a specific category"""
        return [gate for gate in self._gates.values() if gate.category == category]
    
    def get_hard_gates(self) -> List[GateDefinition]:
        """Get all hard gates"""
        return [gate for gate in self._gates.values() if gate.is_hard_gate]
    
    def get_hard_gate_ids(self) -> List[str]:
        """Get IDs of all hard gates"""
        return [gate.gate_id for gate in self._gates.values() if gate.is_hard_gate]
    
    def get_gate_ids(self) -> List[str]:
        """Get all gate IDs"""
        return list(self._gates.keys())
    
    def get_gates_by_implementation_type(self, implementation_type: str) -> List[GateDefinition]:
        """Get gates by implementation type"""
        return [gate for gate in self._gates.values() if gate.implementation_type == implementation_type]
    
    def get_categories(self) -> List[GateCategory]:
        """Get all available categories"""
        return list(set(gate.category for gate in self._gates.values()))
    
    def get_gates_summary_text(self) -> str:
        """Get formatted text summary of all gates"""
        if not self._gates:
            return "No gates defined"
        
        gates_text = []
        
        # Group by category
        categories = {}
        for gate in self._gates.values():
            if gate.category.value not in categories:
                categories[gate.category.value] = []
            categories[gate.category.value].append(gate)
        
        for category_name, category_gates in categories.items():
            gates_text.append(f"\n{category_name.upper()} GATES:")
            for gate in category_gates:
                hard_gate_indicator = " (HARD GATE)" if gate.is_hard_gate else ""
                gates_text.append(f"  {gate.gate_id}: {gate.gate_name} ({gate.severity.value.upper()}){hard_gate_indicator}")
                gates_text.append(f"    {gate.prompt}")
        
        return "\n".join(gates_text)
    
    def get_gates_for_llm_analysis(self) -> str:
        """Get gates formatted for LLM analysis"""
        gates_text = []
        
        for gate in self._gates.values():
            hard_gate_indicator = " (HARD GATE)" if gate.is_hard_gate else ""
            gates_text.append(f"Gate {gate.gate_id}: {gate.gate_name}{hard_gate_indicator}")
            gates_text.append(f"  Category: {gate.category.value}")
            gates_text.append(f"  Severity: {gate.severity.value}")
            gates_text.append(f"  Description: {gate.prompt}")
            gates_text.append("")
        
        return "\n".join(gates_text)
    
    def get_predefined_categories(self) -> Dict[str, List[str]]:
        """Get predefined category groupings for reporting"""
        categories = {}
        for gate in self._gates.values():
            category_name = gate.category.value.title()
            if category_name not in categories:
                categories[category_name] = []
            categories[category_name].append(gate.gate_id)
        return categories
    
    def to_dict_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to dictionary format for backward compatibility"""
        result = {}
        for gate in self._gates.values():
            category = gate.category.value
            if category not in result:
                result[category] = []
            
            result[category].append({
                "gate_id": gate.gate_id,
                "gate_name": gate.gate_name,
                "prompt": gate.prompt,
                "category": gate.category.value,
                "severity": gate.severity.value,
                "is_hard_gate": gate.is_hard_gate,
                "implementation_type": gate.implementation_type,
                "description": gate.description
            })
        return result


# Global instance for easy access
gate_registry = GateRegistry()


# Convenience functions for backward compatibility
def get_gate(gate_id: str) -> Optional[GateDefinition]:
    """Get a specific gate by ID"""
    return gate_registry.get_gate(gate_id)


def get_all_gates() -> List[GateDefinition]:
    """Get all gate definitions"""
    return gate_registry.get_all_gates()


def get_hard_gates() -> List[GateDefinition]:
    """Get all hard gates"""
    return gate_registry.get_hard_gates()


def get_hard_gate_ids() -> List[str]:
    """Get IDs of all hard gates"""
    return gate_registry.get_hard_gate_ids()


def get_gates_by_category(category: GateCategory) -> List[GateDefinition]:
    """Get all gates in a specific category"""
    return gate_registry.get_gates_by_category(category)


def get_gates_summary_text() -> str:
    """Get formatted text summary of all gates"""
    return gate_registry.get_gates_summary_text()


def get_gates_for_llm_analysis() -> str:
    """Get gates formatted for LLM analysis"""
    return gate_registry.get_gates_for_llm_analysis()


def get_predefined_categories() -> Dict[str, List[str]]:
    """Get predefined category groupings for reporting"""
    return gate_registry.get_predefined_categories()
