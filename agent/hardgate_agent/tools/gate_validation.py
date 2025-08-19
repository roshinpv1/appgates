"""
Gate Validation Tool
Validates hard gates against the codebase using pattern matching and analysis
"""

import os
import sys
import re
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from google.adk.tools.base_tool import BaseTool
    from google.adk.tools import ToolContext
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("⚠️ Google ADK not available")

# Import existing CodeGates functionality
try:
    from gates.utils.hard_gates import HARD_GATES, get_gate_number
    from gates.criteria_evaluator import EnhancedGateEvaluator
    CODEGATES_AVAILABLE = True
except ImportError as e:
    CODEGATES_AVAILABLE = False
    print(f"⚠️ CodeGates functionality not available: {e}")


class GateValidationTool(BaseTool):
    """Tool for validating hard gates against the codebase"""
    
    name = "validate_gates"
    description = "Validate hard gates against the codebase using pattern matching and analysis"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Validate hard gates against the codebase"""
        try:
            repository_path = args.get("repository_path")
            gates_to_validate = args.get("gates", [])
            scan_depth = args.get("scan_depth", "comprehensive")
            
            if not repository_path:
                return {
                    "success": False,
                    "error": "Repository path is required"
                }
            
            if not gates_to_validate:
                # Validate all available gates
                gates_to_validate = list(HARD_GATES.keys()) if CODEGATES_AVAILABLE else self._get_default_gates()
            
            # Validate each gate
            validation_results = []
            for gate_name in gates_to_validate:
                gate_result = await self._validate_single_gate(repository_path, gate_name, scan_depth)
                validation_results.append(gate_result)
            
            # Generate summary
            summary = await self._generate_validation_summary(validation_results)
            
            return {
                "success": True,
                "repository_path": repository_path,
                "gates_validated": gates_to_validate,
                "validation_results": validation_results,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Gate validation failed: {str(e)}"
            }
    
    async def _validate_single_gate(self, repo_path: str, gate_name: str, scan_depth: str) -> dict:
        """Validate a single hard gate"""
        try:
            if CODEGATES_AVAILABLE:
                return await self._validate_with_codegates(repo_path, gate_name, scan_depth)
            else:
                return await self._validate_with_patterns(repo_path, gate_name, scan_depth)
        except Exception as e:
            return {
                "gate_name": gate_name,
                "status": "ERROR",
                "score": 0.0,
                "error": str(e),
                "evidence": [],
                "recommendations": []
            }
    
    async def _validate_with_codegates(self, repo_path: str, gate_name: str, scan_depth: str) -> dict:
        """Validate using CodeGates framework"""
        try:
            evaluator = EnhancedGateEvaluator()
            
            # Get gate configuration
            gate_config = HARD_GATES.get(gate_name, {})
            if not gate_config:
                return {
                    "gate_name": gate_name,
                    "status": "NOT_APPLICABLE",
                    "score": 0.0,
                    "error": f"Gate {gate_name} not found in configuration",
                    "evidence": [],
                    "recommendations": []
                }
            
            # Evaluate gate
            result = await evaluator.evaluate_gate(repo_path, gate_name, gate_config)
            
            return {
                "gate_name": gate_name,
                "status": result.get("status", "UNKNOWN"),
                "score": result.get("score", 0.0),
                "evidence": result.get("evidence", []),
                "recommendations": result.get("recommendations", []),
                "patterns_found": result.get("patterns_found", 0),
                "files_analyzed": result.get("files_analyzed", 0)
            }
            
        except Exception as e:
            return {
                "gate_name": gate_name,
                "status": "ERROR",
                "score": 0.0,
                "error": str(e),
                "evidence": [],
                "recommendations": []
            }
    
    async def _validate_with_patterns(self, repo_path: str, gate_name: str, scan_depth: str) -> dict:
        """Validate using pattern matching (fallback)"""
        try:
            # Define patterns for each gate
            patterns = self._get_gate_patterns(gate_name)
            
            # Scan files for patterns
            evidence = []
            patterns_found = 0
            files_analyzed = 0
            
            for root, dirs, files in os.walk(repo_path):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache']]
                
                for file in files:
                    if self._should_analyze_file(file, scan_depth):
                        file_path = os.path.join(root, file)
                        file_evidence = await self._analyze_file_for_patterns(file_path, patterns)
                        
                        if file_evidence:
                            evidence.extend(file_evidence)
                            patterns_found += len(file_evidence)
                        
                        files_analyzed += 1
            
            # Calculate score and status
            score = self._calculate_gate_score(patterns_found, files_analyzed, gate_name)
            status = self._determine_gate_status(score, patterns_found)
            
            # Generate recommendations
            recommendations = self._generate_gate_recommendations(gate_name, patterns_found, evidence)
            
            return {
                "gate_name": gate_name,
                "status": status,
                "score": score,
                "evidence": evidence,
                "recommendations": recommendations,
                "patterns_found": patterns_found,
                "files_analyzed": files_analyzed
            }
            
        except Exception as e:
            return {
                "gate_name": gate_name,
                "status": "ERROR",
                "score": 0.0,
                "error": str(e),
                "evidence": [],
                "recommendations": []
            }
    
    def _get_gate_patterns(self, gate_name: str) -> List[Dict[str, Any]]:
        """Get patterns for a specific gate"""
        patterns = {
            "STRUCTURED_LOGS": [
                {"pattern": r"logger\.(info|warn|error|debug)", "description": "Structured logging calls"},
                {"pattern": r"log4j|logback|winston|pino", "description": "Logging frameworks"},
                {"pattern": r"JSON\.stringify|json\.dumps", "description": "JSON logging"}
            ],
            "AVOID_LOGGING_SECRETS": [
                {"pattern": r"password|secret|token|key.*log", "description": "Potential secret logging"},
                {"pattern": r"console\.log.*password|console\.log.*secret", "description": "Console logging of secrets"}
            ],
            "AUDIT_TRAIL": [
                {"pattern": r"audit|auditlog|audit_trail", "description": "Audit trail implementation"},
                {"pattern": r"user.*action|action.*log", "description": "User action logging"}
            ],
            "CORRELATION_ID": [
                {"pattern": r"correlation.*id|request.*id|trace.*id", "description": "Correlation ID implementation"},
                {"pattern": r"X-Correlation-ID|X-Request-ID", "description": "Correlation ID headers"}
            ],
            "LOG_API_CALLS": [
                {"pattern": r"api.*log|log.*api|request.*log", "description": "API call logging"},
                {"pattern": r"interceptor|middleware.*log", "description": "Request logging middleware"}
            ],
            "CLIENT_UI_ERRORS": [
                {"pattern": r"error.*tracking|error.*monitoring", "description": "Error tracking implementation"},
                {"pattern": r"sentry|rollbar|bugsnag", "description": "Error tracking services"}
            ],
            "RETRY_LOGIC": [
                {"pattern": r"retry|retryable|retry.*logic", "description": "Retry logic implementation"},
                {"pattern": r"@Retryable|@Retry|retry.*policy", "description": "Retry annotations"}
            ],
            "TIMEOUT_IO": [
                {"pattern": r"timeout|timeout.*config", "description": "Timeout configuration"},
                {"pattern": r"@Timeout|timeout.*ms", "description": "Timeout annotations"}
            ],
            "THROTTLING": [
                {"pattern": r"throttle|rate.*limit|throttling", "description": "Throttling implementation"},
                {"pattern": r"@RateLimit|rate.*limiter", "description": "Rate limiting annotations"}
            ],
            "CIRCUIT_BREAKERS": [
                {"pattern": r"circuit.*breaker|circuitbreaker", "description": "Circuit breaker implementation"},
                {"pattern": r"Hystrix|Resilience4j|Polly", "description": "Circuit breaker libraries"}
            ],
            "HTTP_ERROR_CODES": [
                {"pattern": r"HTTP.*[4-5][0-9][0-9]|status.*[4-5][0-9][0-9]", "description": "HTTP error handling"},
                {"pattern": r"@ResponseStatus|@ExceptionHandler", "description": "Error handling annotations"}
            ],
            "URL_MONITORING": [
                {"pattern": r"health.*check|healthcheck|health.*endpoint", "description": "Health check endpoints"},
                {"pattern": r"@HealthCheck|/health|/ping", "description": "Health monitoring"}
            ],
            "AUTOMATED_TESTS": [
                {"pattern": r"test.*|spec.*|.*test\.|.*spec\.", "description": "Test files"},
                {"pattern": r"@Test|describe\(|it\(|test\(|pytest", "description": "Test annotations"}
            ],
            "AUTO_SCALE": [
                {"pattern": r"autoscale|auto.*scale|scaling.*policy", "description": "Auto-scaling configuration"},
                {"pattern": r"HPA|HorizontalPodAutoscaler|autoscaling", "description": "Kubernetes auto-scaling"}
            ],
            "ALERTING_ACTIONABLE": [
                {"pattern": r"alert|alerting|notification", "description": "Alerting implementation"},
                {"pattern": r"PagerDuty|Slack|email.*alert", "description": "Alerting services"}
            ]
        }
        
        return patterns.get(gate_name, [])
    
    def _should_analyze_file(self, filename: str, scan_depth: str) -> bool:
        """Determine if file should be analyzed based on scan depth"""
        if scan_depth == "basic":
            # Only analyze main source files
            return any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.cs'])
        elif scan_depth == "comprehensive":
            # Analyze all code and config files
            return any(filename.endswith(ext) for ext in [
                '.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.cs', '.php', '.rb', '.scala', '.kt', '.swift',
                '.json', '.yaml', '.yml', '.toml', '.xml', '.properties', '.conf', '.config'
            ])
        else:  # deep
            # Analyze all files
            return True
    
    async def _analyze_file_for_patterns(self, file_path: str, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze a file for specific patterns"""
        evidence = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern_info in patterns:
                        pattern = pattern_info["pattern"]
                        description = pattern_info["description"]
                        
                        if re.search(pattern, line, re.IGNORECASE):
                            evidence.append({
                                "file": file_path,
                                "line": line_num,
                                "line_content": line.strip(),
                                "pattern": pattern,
                                "description": description
                            })
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return evidence
    
    def _calculate_gate_score(self, patterns_found: int, files_analyzed: int, gate_name: str) -> float:
        """Calculate gate score based on patterns found"""
        if files_analyzed == 0:
            return 0.0
        
        # Base score calculation
        base_score = min(100.0, (patterns_found / max(1, files_analyzed)) * 100)
        
        # Gate-specific scoring adjustments
        if gate_name == "AUTOMATED_TESTS":
            # Higher weight for test files
            test_files = patterns_found
            total_files = files_analyzed
            if total_files > 0:
                return min(100.0, (test_files / total_files) * 200)  # Double weight for tests
        
        elif gate_name == "STRUCTURED_LOGS":
            # Moderate weight for logging
            return min(100.0, base_score * 1.5)
        
        elif gate_name == "AVOID_LOGGING_SECRETS":
            # Inverse scoring - fewer patterns is better
            return max(0.0, 100.0 - base_score)
        
        return base_score
    
    def _determine_gate_status(self, score: float, patterns_found: int) -> str:
        """Determine gate status based on score and patterns"""
        if score >= 80.0:
            return "PASS"
        elif score >= 50.0:
            return "WARNING"
        elif patterns_found == 0:
            return "NOT_APPLICABLE"
        else:
            return "FAIL"
    
    def _generate_gate_recommendations(self, gate_name: str, patterns_found: int, evidence: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for gate improvement"""
        recommendations = []
        
        if gate_name == "STRUCTURED_LOGS":
            if patterns_found == 0:
                recommendations.append("Implement structured logging framework (log4j, winston, etc.)")
                recommendations.append("Use JSON format for log output")
                recommendations.append("Add log levels (INFO, WARN, ERROR, DEBUG)")
            else:
                recommendations.append("Ensure consistent logging patterns across all files")
                recommendations.append("Add correlation IDs to log entries")
        
        elif gate_name == "AVOID_LOGGING_SECRETS":
            if patterns_found > 0:
                recommendations.append("Remove or mask sensitive data from logs")
                recommendations.append("Use environment variables for secrets")
                recommendations.append("Implement log filtering for sensitive data")
            else:
                recommendations.append("Continue avoiding logging of sensitive information")
        
        elif gate_name == "AUTOMATED_TESTS":
            if patterns_found == 0:
                recommendations.append("Add unit tests for all components")
                recommendations.append("Implement integration tests")
                recommendations.append("Add test coverage reporting")
            else:
                recommendations.append("Increase test coverage to at least 80%")
                recommendations.append("Add performance and security tests")
        
        elif gate_name == "AUTO_SCALE":
            if patterns_found == 0:
                recommendations.append("Implement Kubernetes Horizontal Pod Autoscaler (HPA)")
                recommendations.append("Configure auto-scaling policies")
                recommendations.append("Add resource monitoring and alerts")
            else:
                recommendations.append("Optimize auto-scaling thresholds")
                recommendations.append("Add custom metrics for scaling decisions")
        
        # Generic recommendations
        if patterns_found == 0:
            recommendations.append(f"Implement {gate_name.replace('_', ' ').lower()} patterns")
            recommendations.append("Follow enterprise security standards")
        
        return recommendations
    
    def _get_default_gates(self) -> List[str]:
        """Get default list of gates to validate"""
        return [
            "STRUCTURED_LOGS",
            "AVOID_LOGGING_SECRETS",
            "AUDIT_TRAIL",
            "CORRELATION_ID",
            "LOG_API_CALLS",
            "CLIENT_UI_ERRORS",
            "RETRY_LOGIC",
            "TIMEOUT_IO",
            "THROTTLING",
            "CIRCUIT_BREAKERS",
            "HTTP_ERROR_CODES",
            "URL_MONITORING",
            "AUTOMATED_TESTS",
            "AUTO_SCALE",
            "ALERTING_ACTIONABLE"
        ]
    
    async def _generate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> dict:
        """Generate validation summary"""
        total_gates = len(validation_results)
        passed_gates = len([r for r in validation_results if r.get("status") == "PASS"])
        failed_gates = len([r for r in validation_results if r.get("status") == "FAIL"])
        warning_gates = len([r for r in validation_results if r.get("status") == "WARNING"])
        na_gates = len([r for r in validation_results if r.get("status") == "NOT_APPLICABLE"])
        
        avg_score = sum(r.get("score", 0) for r in validation_results) / max(1, total_gates)
        
        return {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "warning_gates": warning_gates,
            "not_applicable_gates": na_gates,
            "average_score": round(avg_score, 2),
            "compliance_rate": round((passed_gates / max(1, total_gates)) * 100, 2)
        } 