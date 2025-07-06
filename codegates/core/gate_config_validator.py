#!/usr/bin/env python3
"""
Gate Configuration Validator - Validates gate_config.yml completeness and pattern coverage
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models import Language, GateType


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    gate_id: int
    gate_name: str
    language: str
    severity: ValidationSeverity
    issue_type: str
    description: str
    recommendation: str
    missing_patterns: List[str] = None


@dataclass
class PatternCoverage:
    """Pattern coverage statistics"""
    total_patterns: int
    covered_patterns: int
    missing_patterns: List[str]
    coverage_percentage: float
    quality_score: float


@dataclass
class GateValidationResult:
    """Result of gate configuration validation"""
    gate_id: int
    gate_name: str
    is_valid: bool
    issues: List[ValidationIssue]
    pattern_coverage: Dict[str, PatternCoverage]
    recommendations: List[str]


class GateConfigValidator:
    """Validates gate configuration completeness and pattern coverage"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize validator with configuration path"""
        self.config_path = config_path or Path("codegates/core/gate_config.yml")
        self.config = self._load_config()
        
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
    
    def _load_config(self) -> Dict[str, Any]:
        """Load gate configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load gate configuration: {e}")
    
    def _define_essential_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Define essential patterns that should be present for each gate"""
        return {
            'structured_logs': {
                'java': [
                    r'logger\.(info|debug|error|warn|trace)\s*\(',
                    r'JsonEncoder|JSONLayout|JsonLayout',
                    r'logback\.xml|log4j2\.xml'
                ],
                'python': [
                    r'logging\.(info|debug|error|warning|critical)\s*\(',
                    r'structlog|jsonlogger',
                    r'logging\.basicConfig'
                ],
                'javascript': [
                    r'console\.(log|error|debug|info|warn)\s*\(',
                    r'winston|bunyan|pino',
                    r'logger\.'
                ],
                'typescript': [
                    r'console\.(log|error|debug|info|warn)\s*\(',
                    r'winston|bunyan|pino',
                    r'logger\.'
                ],
                'dotnet': [
                    r'Log\.(Information|Debug|Error|Warning|Critical)\s*\(',
                    r'ILogger<\w+>',
                    r'appsettings\.json'
                ]
            },
            'avoid_logging_secrets': {
                'all_languages': [
                    r'(?i)\b(password|passwd|pwd|pass|secret|token|auth|apikey|api[_-]?key)\b',
                    r'(?i)\b(credential|credentials|client[_-]?secret|bearer)\b',
                    r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b',  # Credit card patterns
                    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN patterns
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email patterns
                ]
            },
            'audit_trail': {
                'java': [
                    r'audit|Audit',
                    r'logger\.(info|warn|error).*audit',
                    r'@Audited|@AuditTable'
                ],
                'python': [
                    r'audit|Audit',
                    r'logging\.(info|warning|error).*audit',
                    r'audit_log|audit_trail'
                ],
                'javascript': [
                    r'audit|Audit',
                    r'logger\.(info|warn|error).*audit',
                    r'audit[_-]?log'
                ],
                'typescript': [
                    r'audit|Audit',
                    r'logger\.(info|warn|error).*audit',
                    r'audit[_-]?log'
                ],
                'dotnet': [
                    r'audit|Audit',
                    r'Log\.(Information|Warning|Error).*audit',
                    r'IAuditService|AuditAttribute'
                ]
            },
            'error_logs': {
                'java': [
                    r'catch\s*\([^)]*Exception[^)]*\).*logger\.',
                    r'logger\.error\s*\(',
                    r'@ExceptionHandler'
                ],
                'python': [
                    r'except\s*[^:]*:.*logging\.',
                    r'logging\.error\s*\(',
                    r'logger\.exception\s*\('
                ],
                'javascript': [
                    r'catch\s*\([^)]*\).*console\.error',
                    r'catch\s*\([^)]*\).*logger\.',
                    r'\.catch\s*\('
                ],
                'typescript': [
                    r'catch\s*\([^)]*\).*console\.error',
                    r'catch\s*\([^)]*\).*logger\.',
                    r'\.catch\s*\('
                ],
                'dotnet': [
                    r'catch\s*\([^)]*Exception[^)]*\).*Log\.',
                    r'Log\.Error\s*\(',
                    r'IExceptionHandler'
                ]
            },
            'retry_logic': {
                'java': [
                    r'@Retryable|@Retry',
                    r'RetryTemplate',
                    r'for\s*\(\s*int\s+retries\s*='
                ],
                'python': [
                    r'@retry|@backoff',
                    r'tenacity|retrying',
                    r'for\s+attempt\s+in\s+range'
                ],
                'javascript': [
                    r'retry\s*\(',
                    r'p-retry|async-retry',
                    r'for\s*\(\s*let\s+attempt\s*='
                ],
                'typescript': [
                    r'retry\s*\(',
                    r'p-retry|async-retry',
                    r'for\s*\(\s*let\s+attempt\s*='
                ],
                'dotnet': [
                    r'\[Retry\]',
                    r'Polly\.',
                    r'for\s*\(\s*int\s+retries\s*='
                ]
            },
            'timeouts': {
                'java': [
                    r'timeout|Timeout',
                    r'@Timeout',
                    r'setTimeout|setReadTimeout'
                ],
                'python': [
                    r'timeout=',
                    r'socket\.settimeout',
                    r'requests\.get\(.*timeout'
                ],
                'javascript': [
                    r'setTimeout\s*\(',
                    r'timeout\s*:',
                    r'AbortController'
                ],
                'typescript': [
                    r'setTimeout\s*\(',
                    r'timeout\s*:',
                    r'AbortController'
                ],
                'dotnet': [
                    r'Timeout\s*=',
                    r'CancellationToken',
                    r'Task\.Delay'
                ]
            },
            'circuit_breakers': {
                'java': [
                    r'@CircuitBreaker',
                    r'CircuitBreaker\.',
                    r'Hystrix'
                ],
                'python': [
                    r'CircuitBreaker|circuit_breaker',
                    r'pybreaker',
                    r'@circuit_breaker'
                ],
                'javascript': [
                    r'CircuitBreaker|circuit-breaker',
                    r'opossum',
                    r'breaker\.'
                ],
                'typescript': [
                    r'CircuitBreaker|circuit-breaker',
                    r'opossum',
                    r'breaker\.'
                ],
                'dotnet': [
                    r'\[CircuitBreaker\]',
                    r'Polly\.CircuitBreaker',
                    r'CircuitBreakerPolicy'
                ]
            },
            'throttling': {
                'java': [
                    r'@RateLimiter|@Throttle',
                    r'RateLimiter\.',
                    r'Bucket4j'
                ],
                'python': [
                    r'@throttle|@rate_limit',
                    r'ratelimit|slowapi',
                    r'throttle_scope'
                ],
                'javascript': [
                    r'rateLimit|throttle',
                    r'express-rate-limit',
                    r'bottleneck'
                ],
                'typescript': [
                    r'rateLimit|throttle',
                    r'express-rate-limit',
                    r'bottleneck'
                ],
                'dotnet': [
                    r'\[RateLimit\]',
                    r'AspNetCoreRateLimit',
                    r'IRateLimitConfiguration'
                ]
            },
            'correlation_id': {
                'java': [
                    r'correlationId|correlation-id',
                    r'MDC\.put.*correlation',
                    r'UUID\.randomUUID'
                ],
                'python': [
                    r'correlation_id|correlation-id',
                    r'uuid\.uuid4\(\)',
                    r'threading\.local'
                ],
                'javascript': [
                    r'correlationId|correlation-id',
                    r'uuid\.v4\(\)',
                    r'x-correlation-id'
                ],
                'typescript': [
                    r'correlationId|correlation-id',
                    r'uuid\.v4\(\)',
                    r'x-correlation-id'
                ],
                'dotnet': [
                    r'CorrelationId|correlation-id',
                    r'Guid\.NewGuid\(\)',
                    r'HttpContext\.TraceIdentifier'
                ]
            },
            'automated_tests': {
                'java': [
                    r'@Test|@TestMethod',
                    r'JUnit|TestNG',
                    r'Assert\.|assertEquals'
                ],
                'python': [
                    r'def test_|class Test',
                    r'pytest|unittest',
                    r'assert |assertEqual'
                ],
                'javascript': [
                    r'describe\s*\(|it\s*\(',
                    r'jest|mocha|jasmine',
                    r'expect\s*\('
                ],
                'typescript': [
                    r'describe\s*\(|it\s*\(',
                    r'jest|mocha|jasmine',
                    r'expect\s*\('
                ],
                'dotnet': [
                    r'\[Test\]|\[TestMethod\]|\[Fact\]',
                    r'NUnit|MSTest|xUnit',
                    r'Assert\.|Should\.'
                ]
            },
            'api_logs': {
                'java': [
                    r'@RequestMapping.*logger\.',
                    r'@GetMapping.*logger\.',
                    r'@PostMapping.*logger\.'
                ],
                'python': [
                    r'@app\.route.*logging\.',
                    r'def.*request.*logging\.',
                    r'FastAPI.*logger\.'
                ],
                'javascript': [
                    r'app\.(get|post|put|delete).*logger\.',
                    r'router\.(get|post|put|delete).*logger\.',
                    r'express.*logger\.'
                ],
                'typescript': [
                    r'app\.(get|post|put|delete).*logger\.',
                    r'router\.(get|post|put|delete).*logger\.',
                    r'express.*logger\.'
                ],
                'dotnet': [
                    r'\[HttpGet\].*Log\.',
                    r'\[HttpPost\].*Log\.',
                    r'\[Route.*\].*Log\.'
                ]
            },
            'background_jobs': {
                'java': [
                    r'@Scheduled|@Async',
                    r'ExecutorService|ThreadPoolExecutor',
                    r'@BackgroundJob'
                ],
                'python': [
                    r'@celery\.task|@shared_task',
                    r'threading\.Thread|multiprocessing',
                    r'asyncio\.create_task'
                ],
                'javascript': [
                    r'setInterval\s*\(|setTimeout\s*\(',
                    r'worker_threads|cluster',
                    r'cron\.|schedule\.'
                ],
                'typescript': [
                    r'setInterval\s*\(|setTimeout\s*\(',
                    r'worker_threads|cluster',
                    r'cron\.|schedule\.'
                ],
                'dotnet': [
                    r'BackgroundService|IHostedService',
                    r'Task\.Run|Task\.Factory',
                    r'Hangfire|Quartz'
                ]
            },
            'ui_errors': {
                'javascript': [
                    r'ErrorBoundary|componentDidCatch',
                    r'try.*catch.*render',
                    r'error.*state'
                ],
                'typescript': [
                    r'ErrorBoundary|componentDidCatch',
                    r'try.*catch.*render',
                    r'error.*state'
                ]
            },
            'ui_error_tools': {
                'javascript': [
                    r'Sentry\.|@sentry',
                    r'Rollbar\.|rollbar',
                    r'Bugsnag\.|@bugsnag'
                ],
                'typescript': [
                    r'Sentry\.|@sentry',
                    r'Rollbar\.|rollbar',
                    r'Bugsnag\.|@bugsnag'
                ]
            },
            'http_codes': {
                'java': [
                    r'HttpStatus\.|ResponseEntity',
                    r'@ResponseStatus',
                    r'return.*status'
                ],
                'python': [
                    r'status_code|status=',
                    r'HTTPException|abort',
                    r'return.*status'
                ],
                'javascript': [
                    r'res\.status\s*\(',
                    r'response\.status',
                    r'statusCode'
                ],
                'typescript': [
                    r'res\.status\s*\(',
                    r'response\.status',
                    r'statusCode'
                ],
                'dotnet': [
                    r'HttpStatusCode\.',
                    r'StatusCode\s*=',
                    r'return.*StatusCode'
                ]
            }
        }
    
    def validate_config(self) -> Dict[str, GateValidationResult]:
        """Validate the entire gate configuration"""
        results = {}
        
        if 'hard_gates' not in self.config:
            raise Exception("No 'hard_gates' section found in configuration")
        
        for gate_config in self.config['hard_gates']:
            gate_id = gate_config.get('id')
            gate_name = gate_config.get('name', f'Gate {gate_id}')
            
            result = self._validate_gate(gate_config)
            results[f"gate_{gate_id}"] = result
        
        return results
    
    def _validate_gate(self, gate_config: Dict[str, Any]) -> GateValidationResult:
        """Validate a single gate configuration"""
        gate_id = gate_config.get('id')
        gate_name = gate_config.get('name', f'Gate {gate_id}')
        
        issues = []
        pattern_coverage = {}
        recommendations = []
        
        # Check basic structure
        if not gate_config.get('description'):
            issues.append(ValidationIssue(
                gate_id=gate_id,
                gate_name=gate_name,
                language='all',
                severity=ValidationSeverity.MEDIUM,
                issue_type='missing_description',
                description='Gate description is missing',
                recommendation='Add a clear description explaining what this gate validates'
            ))
        
        if not gate_config.get('validation_method'):
            issues.append(ValidationIssue(
                gate_id=gate_id,
                gate_name=gate_name,
                language='all',
                severity=ValidationSeverity.MEDIUM,
                issue_type='missing_validation_method',
                description='Validation method is missing',
                recommendation='Add validation method description'
            ))
        
        # Validate patterns for each language
        patterns = gate_config.get('patterns', {})
        gate_key = self._get_gate_key_from_name(gate_name)
        
        for language in self.language_extensions.keys():
            if language == 'all_languages':
                continue
                
            lang_patterns = patterns.get(language, [])
            coverage = self._analyze_pattern_coverage(gate_key, language, lang_patterns)
            pattern_coverage[language] = coverage
            
            # Check for missing essential patterns
            if coverage.missing_patterns:
                issues.append(ValidationIssue(
                    gate_id=gate_id,
                    gate_name=gate_name,
                    language=language,
                    severity=ValidationSeverity.HIGH if coverage.coverage_percentage < 50 else ValidationSeverity.MEDIUM,
                    issue_type='missing_patterns',
                    description=f'Missing {len(coverage.missing_patterns)} essential patterns for {language}',
                    recommendation=f'Add missing patterns: {", ".join(coverage.missing_patterns[:3])}{"..." if len(coverage.missing_patterns) > 3 else ""}',
                    missing_patterns=coverage.missing_patterns
                ))
        
        # Check for all_languages patterns
        if 'all_languages' in patterns:
            all_lang_patterns = patterns['all_languages']
            coverage = self._analyze_pattern_coverage(gate_key, 'all_languages', all_lang_patterns)
            pattern_coverage['all_languages'] = coverage
        
        # Generate recommendations
        recommendations.extend(self._generate_gate_recommendations(gate_config, issues, pattern_coverage))
        
        is_valid = not any(issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH] for issue in issues)
        
        return GateValidationResult(
            gate_id=gate_id,
            gate_name=gate_name,
            is_valid=is_valid,
            issues=issues,
            pattern_coverage=pattern_coverage,
            recommendations=recommendations
        )
    
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
    
    def _analyze_pattern_coverage(self, gate_key: str, language: str, patterns: List[str]) -> PatternCoverage:
        """Analyze pattern coverage for a gate/language combination"""
        essential_patterns = self.essential_patterns.get(gate_key, {}).get(language, [])
        
        if not essential_patterns:
            # No essential patterns defined for this combination
            return PatternCoverage(
                total_patterns=len(patterns),
                covered_patterns=len(patterns),
                missing_patterns=[],
                coverage_percentage=100.0,
                quality_score=100.0
            )
        
        # Check which essential patterns are covered
        covered_patterns = []
        missing_patterns = []
        
        for essential_pattern in essential_patterns:
            pattern_covered = False
            for config_pattern in patterns:
                try:
                    # Check if the essential pattern is similar to or covered by config pattern
                    if self._patterns_similar(essential_pattern, config_pattern):
                        pattern_covered = True
                        break
                except re.error:
                    # Skip invalid regex patterns
                    continue
            
            if pattern_covered:
                covered_patterns.append(essential_pattern)
            else:
                missing_patterns.append(essential_pattern)
        
        coverage_percentage = (len(covered_patterns) / len(essential_patterns)) * 100 if essential_patterns else 100
        quality_score = self._calculate_quality_score(len(covered_patterns), len(essential_patterns), len(patterns))
        
        return PatternCoverage(
            total_patterns=len(patterns),
            covered_patterns=len(covered_patterns),
            missing_patterns=missing_patterns,
            coverage_percentage=coverage_percentage,
            quality_score=quality_score
        )
    
    def _patterns_similar(self, essential_pattern: str, config_pattern: str) -> bool:
        """Check if two patterns are similar or if config pattern covers essential pattern"""
        # Simple similarity check - can be enhanced with more sophisticated matching
        essential_clean = essential_pattern.replace(r'\s*', '').replace(r'\(', '').replace(r'\)', '')
        config_clean = config_pattern.replace(r'\s*', '').replace(r'\(', '').replace(r'\)', '')
        
        # Check for key terms overlap
        essential_terms = set(re.findall(r'\w+', essential_clean.lower()))
        config_terms = set(re.findall(r'\w+', config_clean.lower()))
        
        overlap = len(essential_terms.intersection(config_terms))
        return overlap > 0 and overlap >= len(essential_terms) * 0.5
    
    def _calculate_quality_score(self, covered: int, total_essential: int, total_patterns: int) -> float:
        """Calculate quality score based on coverage and pattern count"""
        if total_essential == 0:
            return 100.0
        
        coverage_score = (covered / total_essential) * 70  # 70% weight for coverage
        pattern_bonus = min(total_patterns * 2, 30)  # 30% weight for having many patterns
        
        return min(coverage_score + pattern_bonus, 100.0)
    
    def _generate_gate_recommendations(self, gate_config: Dict[str, Any], 
                                     issues: List[ValidationIssue], 
                                     pattern_coverage: Dict[str, PatternCoverage]) -> List[str]:
        """Generate recommendations for improving gate configuration"""
        recommendations = []
        
        # Recommendations based on issues
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == ValidationSeverity.HIGH]
        
        if critical_issues:
            recommendations.append(f"🔴 CRITICAL: Fix {len(critical_issues)} critical issues immediately")
        
        if high_issues:
            recommendations.append(f"🟡 HIGH: Address {len(high_issues)} high-priority issues")
        
        # Recommendations based on pattern coverage
        low_coverage_langs = [lang for lang, coverage in pattern_coverage.items() 
                            if coverage.coverage_percentage < 70]
        
        if low_coverage_langs:
            recommendations.append(f"📊 Improve pattern coverage for: {', '.join(low_coverage_langs)}")
        
        # Specific recommendations for missing patterns
        for lang, coverage in pattern_coverage.items():
            if coverage.missing_patterns:
                recommendations.append(f"🔍 Add missing {lang} patterns: {', '.join(coverage.missing_patterns[:2])}")
        
        return recommendations
    
    def generate_coverage_report(self) -> str:
        """Generate a comprehensive coverage report"""
        validation_results = self.validate_config()
        
        report = []
        report.append("# Gate Configuration Coverage Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        total_gates = len(validation_results)
        valid_gates = sum(1 for result in validation_results.values() if result.is_valid)
        critical_issues = sum(len([i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]) 
                            for result in validation_results.values())
        high_issues = sum(len([i for i in result.issues if i.severity == ValidationSeverity.HIGH]) 
                        for result in validation_results.values())
        
        report.append(f"## Summary")
        report.append(f"- Total Gates: {total_gates}")
        report.append(f"- Valid Gates: {valid_gates}")
        report.append(f"- Critical Issues: {critical_issues}")
        report.append(f"- High Priority Issues: {high_issues}")
        report.append("")
        
        # Detailed results
        for gate_key, result in validation_results.items():
            report.append(f"## Gate {result.gate_id}: {result.gate_name}")
            report.append(f"Status: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
            report.append("")
            
            # Pattern coverage
            if result.pattern_coverage:
                report.append("### Pattern Coverage")
                for lang, coverage in result.pattern_coverage.items():
                    status = "✅" if coverage.coverage_percentage >= 80 else "⚠️" if coverage.coverage_percentage >= 50 else "❌"
                    report.append(f"- {lang}: {status} {coverage.coverage_percentage:.1f}% ({coverage.covered_patterns}/{len(coverage.missing_patterns) + coverage.covered_patterns})")
                report.append("")
            
            # Issues
            if result.issues:
                report.append("### Issues")
                for issue in result.issues:
                    severity_emoji = {
                        ValidationSeverity.CRITICAL: "🔴",
                        ValidationSeverity.HIGH: "🟡",
                        ValidationSeverity.MEDIUM: "🟠",
                        ValidationSeverity.LOW: "🟢",
                        ValidationSeverity.INFO: "ℹ️"
                    }
                    report.append(f"- {severity_emoji[issue.severity]} {issue.description}")
                    report.append(f"  💡 {issue.recommendation}")
                report.append("")
            
            # Recommendations
            if result.recommendations:
                report.append("### Recommendations")
                for rec in result.recommendations:
                    report.append(f"- {rec}")
                report.append("")
            
            report.append("---")
            report.append("")
        
        return "\n".join(report)
    
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
    
    def validate_pattern_syntax(self) -> List[ValidationIssue]:
        """Validate regex pattern syntax"""
        issues = []
        
        for gate_config in self.config['hard_gates']:
            gate_id = gate_config.get('id')
            gate_name = gate_config.get('name', f'Gate {gate_id}')
            patterns = gate_config.get('patterns', {})
            
            for language, lang_patterns in patterns.items():
                for pattern in lang_patterns:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        issues.append(ValidationIssue(
                            gate_id=gate_id,
                            gate_name=gate_name,
                            language=language,
                            severity=ValidationSeverity.HIGH,
                            issue_type='invalid_regex',
                            description=f'Invalid regex pattern: {pattern}',
                            recommendation=f'Fix regex syntax error: {str(e)}'
                        ))
        
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
    
    validator = GateConfigValidator(args.config)
    
    if args.report:
        print(validator.generate_coverage_report())
    elif args.missing:
        print(validator.generate_missing_patterns_file())
    elif args.syntax:
        issues = validator.validate_pattern_syntax()
        if issues:
            print(f"Found {len(issues)} syntax issues:")
            for issue in issues:
                print(f"- {issue.description}")
        else:
            print("No syntax issues found")
    else:
        results = validator.validate_config()
        print(f"Validated {len(results)} gates")
        for gate_key, result in results.items():
            status = "✅ VALID" if result.is_valid else "❌ INVALID"
            print(f"{gate_key}: {status}")


if __name__ == "__main__":
    main() 