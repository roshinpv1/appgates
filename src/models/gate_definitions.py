#!/usr/bin/env python3
"""
Centralized Gate Definitions

This module provides a single source of truth for all gate definitions,
eliminating the need for scattered gate definitions across multiple files.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import os


class GateCategory(Enum):
    """Gate categories (expanded to align with enhanced pattern library)"""
    LOGGING = "Logging"
    SECURITY = "Security"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    DEVOPS = "DevOps"
    QUALITY = "Quality"
    # legacy categories retained for compatibility
    AUDITABILITY = "auditability"
    ERROR_HANDLING = "error_handling"
    AVAILABILITY = "availability"
    ALERTING = "alerting"


class GateSeverity(Enum):
    """Gate severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class GateDefinition:
    """Complete gate definition structure"""
    gate_id: str  # unique internal id (e.g., AUD-1.1, ERR-1.1)
    display_id: str  # user-facing number string (e.g., "1.1")
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
        """Initialize gate definitions from YAML (primary) with JSON fallback."""
        self._gates.clear()
        # First try to load YAML-based gate definitions
        try:
            import yaml  # type: ignore
            yaml_path = os.path.join(os.path.dirname(__file__), "..", "data", "gate_definitions.yml")
            yaml_path = os.path.abspath(yaml_path)
            with open(yaml_path, "r") as f:
                ydoc = yaml.safe_load(f) or {}
            gates_root: Dict[str, Any] = (ydoc or {}).get("gates", {})

            # Category string -> GateCategory mapping (supports both legacy and new names)
            cat_map: Dict[str, GateCategory] = {
                "logging": GateCategory.LOGGING,
                "security": GateCategory.SECURITY,
                "testing": GateCategory.TESTING,
                "documentation": GateCategory.DOCUMENTATION,
                "devops": GateCategory.DEVOPS,
                "quality": GateCategory.QUALITY,
                # Explicit mappings for YAML categories
                "alerting": GateCategory.ALERTING,
                "auditability": GateCategory.AUDITABILITY,
                "errorhandling": GateCategory.ERROR_HANDLING,
                "error_handling": GateCategory.ERROR_HANDLING,
                "availability": GateCategory.AVAILABILITY,
            }

            for category_key, items in gates_root.items():
                if not isinstance(items, dict):
                    continue
                cat_lookup_key = str(category_key).strip().lower().replace(" ", "").replace("_", "")
                category = cat_map.get(cat_lookup_key, GateCategory.QUALITY)
                for display_id, meta in items.items():
                    # Compose gate_id like "Category_1.1"
                    gate_id = f"{category_key}_{display_id}"
                    gate_name = str((meta or {}).get("name", gate_id))
                    summary = str((meta or {}).get("summary", "")).strip()

                    # Default severity when not provided in YAML
                    severity = GateSeverity.HIGH

                    self._gates[gate_id] = GateDefinition(
                        gate_id=gate_id,
                        display_id=str(display_id),
                        gate_name=gate_name,
                        prompt=summary,
                        category=category,
                        severity=severity,
                        is_hard_gate=True,
                        implementation_type=None,
                        description=summary,
                    )
            if self._gates:
                return
        except Exception as e:
            print(f"⚠️ Failed to initialize gates from YAML: {e}")

        # Fallback: load from enhanced pattern library JSON
        try:
            from services.pattern_library_service import PatternLibraryService
            pls = PatternLibraryService()
            gates = pls.pattern_library.get("gates", {})
            cat_map_json = {
                "logging": GateCategory.LOGGING,
                "security": GateCategory.SECURITY,
                "testing": GateCategory.TESTING,
                "documentation": GateCategory.DOCUMENTATION,
                "devops": GateCategory.DEVOPS,
                "quality": GateCategory.QUALITY,
                "alerting": GateCategory.ALERTING,
                "auditability": GateCategory.AUDITABILITY,
                "errorhandling": GateCategory.ERROR_HANDLING,
                "error_handling": GateCategory.ERROR_HANDLING,
                "availability": GateCategory.AVAILABILITY,
            }
            sev_map = {
                "critical": GateSeverity.CRITICAL,
                "high": GateSeverity.HIGH,
                "medium": GateSeverity.MEDIUM,
                "low": GateSeverity.LOW,
            }
            for key, cfg in gates.items():
                gate_id = key
                display_name = cfg.get("display_name", key)
                description = cfg.get("description", "")
                category_str = cfg.get("category", "Quality")
                priority_str = str(cfg.get("priority", "Medium")).lower()
                category = cat_map_json.get(str(category_str).lower().replace(" ", "").replace("_", ""), GateCategory.QUALITY)
                severity = sev_map.get(priority_str, GateSeverity.MEDIUM)
                self._gates[gate_id] = GateDefinition(
                    gate_id=gate_id,
                    display_id=gate_id.split("_", 1)[-1] if "_" in gate_id else gate_id,
                    gate_name=display_name,
                    prompt=description,
                    category=category,
                    severity=severity,
                    is_hard_gate=True,
                    implementation_type=None,
                    description=description,
                )
        except Exception as e:
            print(f"⚠️ Failed to initialize gates from pattern library: {e}")
    
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
        gates_lines: List[str] = []
        for gate in self._gates.values():
            # Normalize category for display (title case, underscores to spaces)
            cat_disp = gate.category.value.replace("_", " ").title()
            # Required fields: gate number (display_id), category, name, summary
            gates_lines.append(
                f"{gate.display_id} | {cat_disp} | {gate.gate_name} | {gate.prompt}"
            )
        return "\n".join(gates_lines)
    
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
