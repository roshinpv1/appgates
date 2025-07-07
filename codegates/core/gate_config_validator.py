#!/usr/bin/env python3
"""
Gate Configuration Validator - Validates gate configuration completeness and pattern coverage
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import logging

from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


@dataclass
class PatternCoverage:
    """Pattern coverage information for a language"""
    total_patterns: int
    missing_patterns: List[str]
    coverage_percentage: float


@dataclass
class GateValidationResult:
    """Result of gate configuration validation"""
    gate_name: str
    pattern_coverage: Dict[str, PatternCoverage]
    overall_coverage: float
    issues: List[str]


class GateConfigValidator:
    """Validates gate configuration completeness and pattern coverage"""
    
    def __init__(self):
        """Initialize validator"""
        self._config_manager = get_config_manager()
        
        # Essential patterns that should be present for each gate/language
        self.essential_patterns = self._define_essential_patterns()
        
        # Language-specific file extensions
        self.language_extensions = {
            'java': ['.java', '.xml', '.properties', '.gradle', '.xml'],
            'python': ['.py', '.yaml', '.yml', '.json', '.cfg', '.ini'],
            'javascript': ['.js', '.json', '.yaml', '.yml'],
            'typescript': ['.ts', '.js', '.json', '.yaml', '.yml'],
            'dotnet': ['.cs', '.json', '.xml', '.config'],
            'csharp': ['.cs', '.json', '.xml', '.config'],
            'php': ['.php', '.json', '.yaml', '.yml'],
            'all_languages': ['*']
        }
    
    def validate_config(self) -> Dict[str, GateValidationResult]:
        """Validate gate configuration and pattern coverage"""
        config = self._config_manager.config
        if not config or 'hard_gates' not in config:
            raise ValueError("Invalid configuration: missing 'hard_gates' section")
        
        results = {}
        for gate in config['hard_gates']:
            gate_key = self._get_gate_key_from_name(gate['name'])
            results[gate_key] = self._validate_gate(gate)
        
        return results
    
    def _validate_gate(self, gate: Dict[str, Any]) -> GateValidationResult:
        """Validate a single gate configuration"""
        gate_name = gate['name']
        patterns = gate.get('patterns', {})
        issues = []
        pattern_coverage = {}
        
        # Check required fields
        if 'id' not in gate:
            issues.append(f"Gate '{gate_name}' missing required field 'id'")
        if 'description' not in gate:
            issues.append(f"Gate '{gate_name}' missing required field 'description'")
        
        # Validate patterns for each language
        for language, essential_patterns in self.essential_patterns.items():
            language_patterns = patterns.get(language, [])
            missing = []
            
            # Check for essential patterns
            for pattern_type in essential_patterns:
                if not any(pattern_type.lower() in p.lower() for p in language_patterns):
                    missing.append(pattern_type)
            
            # Calculate coverage
            total = len(essential_patterns)
            found = total - len(missing)
            coverage = (found / total * 100) if total > 0 else 0
            
            pattern_coverage[language] = PatternCoverage(
                total_patterns=len(language_patterns),
                missing_patterns=missing,
                coverage_percentage=coverage
            )
        
        # Calculate overall coverage
        total_coverage = sum(pc.coverage_percentage for pc in pattern_coverage.values())
        avg_coverage = total_coverage / len(pattern_coverage) if pattern_coverage else 0
        
        return GateValidationResult(
            gate_name=gate_name,
            pattern_coverage=pattern_coverage,
            overall_coverage=avg_coverage,
            issues=issues
        )
    
    def _define_essential_patterns(self) -> Dict[str, List[str]]:
        """Define essential patterns that should be present for each gate/language"""
        return {
            'java': [
                'logger',
                'exception',
                'error',
                'config',
                'annotation'
            ],
            'python': [
                'logging',
                'exception',
                'error',
                'config',
                'decorator'
            ],
            'javascript': [
                'console',
                'error',
                'config',
                'try/catch'
            ],
            'typescript': [
                'logger',
                'error',
                'config',
                'interface'
            ],
            'dotnet': [
                'ILogger',
                'Exception',
                'config',
                'attribute'
            ],
            'php': [
                'log',
                'exception',
                'error',
                'config'
            ]
        }
    
    def _get_gate_key_from_name(self, gate_name: str) -> str:
        """Convert gate name to key for pattern lookup"""
        # Map gate names to keys
        name_to_key = {
            'Logs Searchable/Available': 'structured_logs',
            'Avoid Logging Confidential Data': 'avoid_logging_secrets',
            'Audit Trail': 'audit_trail',
            'Error Logs': 'error_logs',
            'Retry Logic': 'retry_logic',
            'Timeouts': 'timeouts',
            'Circuit Breakers': 'circuit_breakers',
            'Throttling': 'throttling',
            'Correlation ID': 'correlation_id',
            'Automated Tests': 'automated_tests',
            'API Logs': 'api_logs',
            'Background Jobs': 'background_jobs',
            'UI Errors': 'ui_errors',
            'UI Error Tools': 'ui_error_tools',
            'HTTP Codes': 'http_codes'
        }
        
        return name_to_key.get(gate_name, gate_name.lower().replace(' ', '_'))
    
    def generate_missing_patterns_file(self) -> str:
        """Generate a file with missing patterns that can be added to gate_config.yml"""
        validation_results = self.validate_config()
        
        missing_patterns = {}
        
        for gate_key, result in validation_results.items():
            gate_name = result.gate_name
            for lang, coverage in result.pattern_coverage.items():
                if coverage.missing_patterns:
                    if gate_name not in missing_patterns:
                        missing_patterns[gate_name] = {}
                    missing_patterns[gate_name][lang] = coverage.missing_patterns
        
        # Generate YAML content
        yaml_content = []
        yaml_content.append("# Missing patterns to add to gate_config.yml")
        yaml_content.append("# Generated by GateConfigValidator")
        yaml_content.append("")
        
        for gate_name, languages in missing_patterns.items():
            yaml_content.append(f"# {gate_name}")
            for lang, patterns in languages.items():
                yaml_content.append(f"# Missing {lang} patterns:")
                for pattern in patterns:
                    yaml_content.append(f"# - {pattern}")
                yaml_content.append("")
        
        return "\n".join(yaml_content)
    
    def validate_pattern_syntax(self) -> List[str]:
        """Validate regex pattern syntax"""
        issues = []
        
        config = self._config_manager.config
        if not config or 'hard_gates' not in config:
            logger.warning("No configuration loaded to validate pattern syntax.")
            return issues
        
        for gate in config['hard_gates']:
            gate_name = gate['name']
            patterns = gate.get('patterns', {})
            
            for language, lang_patterns in patterns.items():
                for pattern in lang_patterns:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        issues.append(f"Invalid regex pattern in gate '{gate_name}' for language '{language}': {pattern} (Error: {e})")
        
        return issues
    
    def suggest_new_patterns(self, codebase_path: Path) -> Dict[str, List[str]]:
        """Analyze codebase and suggest new patterns to add"""
        # This would analyze the actual codebase to suggest patterns
        # For now, return empty suggestions
        return {}


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate gate configuration')
    parser.add_argument('--config', type=Path, help='Path to gate_config.yml')
    parser.add_argument('--report', action='store_true', help='Generate coverage report')
    parser.add_argument('--missing', action='store_true', help='Generate missing patterns file')
    parser.add_argument('--syntax', action='store_true', help='Validate regex syntax')
    
    args = parser.parse_args()
    
    validator = GateConfigValidator()
    
    if args.report:
        # The original generate_coverage_report method is removed, so this will fail.
        # Keeping the call as per instructions, but it will not function as intended.
        # If a report is needed, it would require a new implementation or a different validator.
        print("Coverage report generation is not available with the new GateConfigValidator.")
    elif args.missing:
        print(validator.generate_missing_patterns_file())
    elif args.syntax:
        issues = validator.validate_pattern_syntax()
        if issues:
            print(f"Found {len(issues)} syntax issues:")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("No syntax issues found")
    else:
        results = validator.validate_config()
        print(f"Validated {len(results)} gates")
        for gate_key, result in results.items():
            print(f"Gate: {result.gate_name}")
            print(f"Overall Coverage: {result.overall_coverage:.1f}%")
            if result.issues:
                print("Issues:")
                for issue in result.issues:
                    print(f"- {issue}")
            if result.pattern_coverage:
                print("Pattern Coverage:")
                for lang, coverage in result.pattern_coverage.items():
                    print(f"  - {lang}: {coverage.coverage_percentage:.1f}% (Missing: {len(coverage.missing_patterns)})")
            print("---")


if __name__ == "__main__":
    main() 