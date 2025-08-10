"""
Gate Configuration Loader
Loads and manages gate configurations from YAML files with support for multiple validation types
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationType(Enum):
    """Supported validation types"""
    PATTERN = "pattern"
    DATABASE = "database"
    EVIDENCE = "evidence"
    LLM = "llm"
    STATIC = "static"
    API = "api"


@dataclass
class ValidationConfig:
    """Configuration for a validation type"""
    enabled: bool
    mandatory: bool = False  # NEW: Whether this validation type is mandatory
    config: Dict[str, Any] = None
    validation_type: ValidationType


@dataclass
class GateConfig:
    """Configuration for a gate"""
    name: str
    display_name: str
    description: str
    category: str
    priority: str
    weight: float
    enabled: bool
    validation_types: Dict[ValidationType, ValidationConfig]
    scoring: Dict[str, Any]
    expected_coverage: Dict[str, Any]
    mandatory_evidence_collectors: List[str] = None  # NEW: List of mandatory evidence collectors


class GateConfigLoader:
    """Loads and manages gate configurations from YAML files"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the gate configuration loader"""
        if config_path is None:
            # Default config path
            config_path = Path(__file__).parent.parent / "config" / "gate_config.yml"
        
        self.config_path = Path(config_path)
        self.config_data = {}
        self.gates = {}
        self.global_config = {}
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                print(f"⚠️ Configuration file not found: {self.config_path}")
                print("   Using default hardcoded gates...")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            
            # Load global configuration
            self.global_config = self.config_data.get('global', {})
            
            # Load gates
            self._load_gates()
            
            print(f"✅ Loaded {len(self.gates)} gates from configuration")
            
        except Exception as e:
            print(f"❌ Error loading gate configuration: {e}")
            print("   Using default hardcoded gates...")
    
    def _load_gates(self):
        """Load all gates from configuration"""
        gates_data = self.config_data.get('gates', {})
        custom_gates_data = self.config_data.get('custom_gates', {})
        
        # Load standard gates
        for gate_name, gate_data in gates_data.items():
            self.gates[gate_name] = self._create_gate_config(gate_name, gate_data)
        
        # Load custom gates
        for gate_name, gate_data in custom_gates_data.items():
            self.gates[gate_name] = self._create_gate_config(gate_name, gate_data)
    
    def _create_gate_config(self, gate_name: str, gate_data: Dict[str, Any]) -> GateConfig:
        """Create a GateConfig object from gate data"""
        validation_types = {}
        
        # Process validation types
        validation_types_data = gate_data.get('validation_types', {})
        
        for val_type_str, val_config in validation_types_data.items():
            try:
                val_type = ValidationType(val_type_str)
                validation_types[val_type] = ValidationConfig(
                    enabled=val_config.get('enabled', True),
                    mandatory=val_config.get('mandatory', False),  # NEW: Parse mandatory field
                    config=val_config,
                    validation_type=val_type
                )
            except ValueError:
                print(f"⚠️ Unknown validation type: {val_type_str} for gate {gate_name}")
        
        return GateConfig(
            name=gate_name,
            display_name=gate_data.get('display_name', gate_name),
            description=gate_data.get('description', ''),
            category=gate_data.get('category', 'Unknown'),
            priority=gate_data.get('priority', 'medium'),
            weight=gate_data.get('weight', 1.0),
            enabled=gate_data.get('enabled', True),
            validation_types=validation_types,
            scoring=gate_data.get('scoring', {}),
            expected_coverage=gate_data.get('expected_coverage', {}),
            mandatory_evidence_collectors=gate_data.get('mandatory_evidence_collectors', [])
        )
    
    def get_gate(self, gate_name: str) -> Optional[GateConfig]:
        """Get a specific gate configuration"""
        return self.gates.get(gate_name)
    
    def get_all_gates(self) -> List[GateConfig]:
        """Get all enabled gates"""
        return [gate for gate in self.gates.values() if gate.enabled]
    
    def get_gates_by_category(self, category: str) -> List[GateConfig]:
        """Get all gates in a specific category"""
        return [gate for gate in self.gates.values() 
                if gate.enabled and gate.category == category]
    
    def get_gates_by_priority(self, priority: str) -> List[GateConfig]:
        """Get all gates with a specific priority"""
        return [gate for gate in self.gates.values() 
                if gate.enabled and gate.priority == priority]
    
    def get_gates_by_validation_type(self, validation_type: ValidationType) -> List[GateConfig]:
        """Get all gates that use a specific validation type"""
        return [gate for gate in self.gates.values() 
                if gate.enabled and validation_type in gate.validation_types 
                and gate.validation_types[validation_type].enabled]
    
    def add_custom_gate(self, gate_name: str, gate_data: Dict[str, Any]):
        """Add a custom gate dynamically"""
        self.gates[gate_name] = self._create_gate_config(gate_name, gate_data)
        print(f"✅ Added custom gate: {gate_name}")
    
    def remove_gate(self, gate_name: str):
        """Remove a gate (disable it)"""
        if gate_name in self.gates:
            self.gates[gate_name].enabled = False
            print(f"✅ Disabled gate: {gate_name}")
        else:
            print(f"⚠️ Gate not found: {gate_name}")
    
    def enable_gate(self, gate_name: str):
        """Enable a gate"""
        if gate_name in self.gates:
            self.gates[gate_name].enabled = True
            print(f"✅ Enabled gate: {gate_name}")
        else:
            print(f"⚠️ Gate not found: {gate_name}")
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        return self.global_config
    
    def reload_config(self):
        """Reload configuration from file"""
        print("🔄 Reloading gate configuration...")
        self._load_config()
    
    def export_config(self, output_path: str):
        """Export current configuration to YAML file"""
        try:
            export_data = {
                'version': self.config_data.get('version', '2.0'),
                'metadata': self.config_data.get('metadata', {}),
                'global': self.global_config,
                'gates': {},
                'custom_gates': {}
            }
            
            # Export gates
            for gate_name, gate_config in self.gates.items():
                gate_data = {
                    'display_name': gate_config.display_name,
                    'description': gate_config.description,
                    'category': gate_config.category,
                    'priority': gate_config.priority,
                    'weight': gate_config.weight,
                    'enabled': gate_config.enabled,
                    'validation_types': {},
                    'scoring': gate_config.scoring,
                    'expected_coverage': gate_config.expected_coverage,
                    'mandatory_evidence_collectors': gate_config.mandatory_evidence_collectors
                }
                
                # Export validation types
                for val_type, val_config in gate_config.validation_types.items():
                    gate_data['validation_types'][val_type.value] = val_config.config
                
                # Determine if it's a custom gate
                if gate_name.startswith('CUSTOM_'):
                    export_data['custom_gates'][gate_name] = gate_data
                else:
                    export_data['gates'][gate_name] = gate_data
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False, indent=2)
            
            print(f"✅ Configuration exported to: {output_path}")
            
        except Exception as e:
            print(f"❌ Error exporting configuration: {e}")


# Global instance for easy access
gate_config_loader = GateConfigLoader()


def get_gate_config(gate_name: str) -> Optional[GateConfig]:
    """Get gate configuration by name"""
    return gate_config_loader.get_gate(gate_name)


def get_all_gates() -> List[GateConfig]:
    """Get all enabled gates"""
    return gate_config_loader.get_all_gates()


def get_gates_by_validation_type(validation_type: ValidationType) -> List[GateConfig]:
    """Get gates that use a specific validation type"""
    return gate_config_loader.get_gates_by_validation_type(validation_type) 