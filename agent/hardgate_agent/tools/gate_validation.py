"""
Gate Validation Tool
Validates hard gates against the codebase using pattern matching and analysis
"""

import os
import sys
import re
import asyncio
import tempfile
import shutil
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
    from gates.utils.hard_gates import HARD_GATES, get_gate_number, GATE_NUMBER_MAPPING
    from gates.criteria_evaluator import EnhancedGateEvaluator
    from gates.utils.file_scanner import scan_directory
    from gates.utils.pattern_cache import get_cached_compiled_pattern
    # Optional cloning utilities (preferred to avoid shelling out)
    try:
        from gates.utils.git_operations import clone_repository, cleanup_repository
    except Exception:
        clone_repository = None
        cleanup_repository = None
    CODEGATES_AVAILABLE = True
except ImportError as e:
    CODEGATES_AVAILABLE = False
    clone_repository = None
    cleanup_repository = None
    print(f"⚠️ CodeGates functionality not available: {e}")

from agent.hardgate_agent.util.codegates_bridge import ensure_local_repo as _bridge_ensure_local_repo, cleanup_temp_dir as _bridge_cleanup


class GateValidationTool(BaseTool):
    """Tool for validating hard gates against the codebase"""
    
    name = "validate_gates"
    description = "Validate hard gates against the codebase using pattern matching and analysis"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Validate hard gates against the codebase"""
        temp_dir = None
        try:
            repository_path = args.get("repository_path")
            repository_url = args.get("repository_url")
            branch = args.get("branch", "main")
            github_token = args.get("github_token")
            gates_to_validate = args.get("gates", [])
            scan_depth = args.get("scan_depth", "comprehensive")
            validation_config = args.get("validation_config", {})
            
            # Ensure we have a local path (auto-clone if needed) via bridge
            repository_path, temp_dir, _ = _bridge_ensure_local_repo(
                repository_path=repository_path,
                repository_url=repository_url,
                branch=branch,
                github_token=github_token,
            )
            
            if not gates_to_validate:
                gates_to_validate = list(GATE_NUMBER_MAPPING.keys()) if CODEGATES_AVAILABLE else self._get_default_gates()
            
            validation_results = []
            for gate_name in gates_to_validate:
                gate_result = await self._validate_single_gate(repository_path, gate_name, scan_depth, validation_config)
                validation_results.append(gate_result)
            
            summary = await self._generate_validation_summary(validation_results)
            
            return {
                "success": True,
                "repository_path": repository_path,
                "gates_validated": gates_to_validate,
                "validation_results": validation_results,
                "summary": summary,
                "total_gates": len(validation_results),
                "passed_gates": len([r for r in validation_results if r.get("status") == "PASS"]),
                "failed_gates": len([r for r in validation_results if r.get("status") == "FAIL"]),
                "pass_rate": (len([r for r in validation_results if r.get("status") == "PASS"]) / len(validation_results) * 100) if validation_results else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Gate validation failed: {str(e)}"
            }
        finally:
            _bridge_cleanup(temp_dir)
    
    async def _validate_single_gate(self, repo_path: str, gate_name: str, scan_depth: str, validation_config: dict) -> dict:
        """Validate a single hard gate"""
        try:
            if CODEGATES_AVAILABLE:
                return await self._validate_with_codegates(repo_path, gate_name, scan_depth, validation_config)
            else:
                return await self._validate_with_patterns(repo_path, gate_name, scan_depth, validation_config)
        except Exception as e:
            return {
                "gate_name": gate_name,
                "display_name": gate_name,
                "status": "ERROR",
                "score": 0.0,
                "error": str(e),
                "evidence": [],
                "recommendations": [],
                "category": "Unknown",
                "priority": "Unknown"
            }
    
    async def _validate_with_codegates(self, repo_path: str, gate_name: str, scan_depth: str, validation_config: dict) -> dict:
        """Validate using CodeGates framework"""
        try:
            # Get gate configuration from HARD_GATES
            gate_config = None
            for gate in HARD_GATES:
                if gate.get("name") == gate_name:
                    gate_config = gate
                    break
            
            if not gate_config:
                return {
                    "gate_name": gate_name,
                    "display_name": gate_name,
                    "status": "NOT_APPLICABLE",
                    "score": 0.0,
                    "error": f"Gate {gate_name} not found in configuration",
                    "evidence": [],
                    "recommendations": [],
                    "category": "Unknown",
                    "priority": "Unknown"
                }
            
            # Use the actual file scanner and pattern matching logic
            evidence = []
            patterns_found = 0
            files_analyzed = 0
            
            # Get patterns for this gate
            patterns = gate_config.get("patterns", {})
            
            # Scan repository for patterns
            if patterns:
                evidence, patterns_found, files_analyzed = await self._scan_repository_for_patterns(
                    repo_path, gate_name, patterns, scan_depth
                )
            
            # Calculate score based on patterns found
            score = await self._calculate_gate_score(patterns_found, files_analyzed, gate_config, evidence)
            status = await self._determine_gate_status(score, patterns_found, gate_config)
            
            # Generate recommendations
            recommendations = await self._generate_gate_recommendations(gate_name, patterns_found, evidence, gate_config)
            
            return {
                "gate_name": gate_name,
                "display_name": gate_config.get("display_name", gate_name),
                "description": gate_config.get("description", ""),
                "category": gate_config.get("category", "Unknown"),
                "priority": gate_config.get("priority", "Unknown"),
                "status": status,
                "score": score,
                "evidence": evidence,
                "recommendations": recommendations,
                "patterns_found": patterns_found,
                "files_analyzed": files_analyzed,
                "gate_number": get_gate_number(gate_name)
            }
            
        except Exception as e:
            return {
                "gate_name": gate_name,
                "display_name": gate_name,
                "status": "ERROR",
                "score": 0.0,
                "error": str(e),
                "evidence": [],
                "recommendations": [],
                "category": "Unknown",
                "priority": "Unknown"
            }
    
    async def _scan_repository_for_patterns(self, repo_path: str, gate_name: str, patterns: dict, scan_depth: str) -> tuple:
        """Scan repository for gate-specific patterns using actual logic"""
        evidence = []
        patterns_found = 0
        files_analyzed = 0
        
        # Define file extensions to scan based on gate
        file_extensions = self._get_file_extensions_for_gate(gate_name)
        
        for root, dirs, files in os.walk(repo_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv']]
            
            for file in files:
                if self._should_analyze_file(file, file_extensions, scan_depth):
                    file_path = os.path.join(root, file)
                    file_evidence = await self._analyze_file_for_gate_patterns(file_path, gate_name, patterns)
                    
                    if file_evidence:
                        evidence.extend(file_evidence)
                        patterns_found += len(file_evidence)
                    
                    files_analyzed += 1
        
        return evidence, patterns_found, files_analyzed
    
    async def _analyze_file_for_gate_patterns(self, file_path: str, gate_name: str, patterns: dict) -> List[Dict[str, Any]]:
        """Analyze a single file for gate-specific patterns"""
        evidence = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check positive patterns (good practices)
            positive_patterns = patterns.get("positive", [])
            for pattern in positive_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    evidence.append({
                        "type": "positive",
                        "pattern": pattern,
                        "file": file_path,
                        "line": line_num,
                        "matched_text": match.group(),
                        "description": f"Good practice found: {pattern}"
                    })
            
            # Check negative patterns (violations)
            negative_patterns = patterns.get("negative", [])
            for pattern in negative_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    evidence.append({
                        "type": "negative",
                        "pattern": pattern,
                        "file": file_path,
                        "line": line_num,
                        "matched_text": match.group(),
                        "description": f"Violation found: {pattern}"
                    })
            
            # Check violation patterns (security issues)
            violation_patterns = patterns.get("violations", [])
            for pattern in violation_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    evidence.append({
                        "type": "violation",
                        "pattern": pattern,
                        "file": file_path,
                        "line": line_num,
                        "matched_text": match.group(),
                        "description": f"Security violation found: {pattern}"
                    })
        
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return evidence
    
    def _get_file_extensions_for_gate(self, gate_name: str) -> List[str]:
        """Get relevant file extensions for a specific gate"""
        # Define file extensions based on gate type
        gate_extensions = {
            "STRUCTURED_LOGS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "AVOID_LOGGING_SECRETS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".conf", ".env", ".yaml", ".yml"],
            "ALERTING_ACTIONABLE": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".yaml", ".yml", ".json"],
            "AUDIT_TRAIL": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "CORRELATION_ID": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "LOG_API_CALLS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "CLIENT_UI_ERRORS": [".js", ".ts", ".jsx", ".tsx", ".vue", ".html"],
            "RETRY_LOGIC": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "TIMEOUT_IO": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "THROTTLING": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "CIRCUIT_BREAKERS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "HTTP_ERROR_CODES": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
            "URL_MONITORING": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".yaml", ".yml"],
            "AUTOMATED_TESTS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".test.js", ".spec.js", ".test.py", ".spec.py"],
            "AUTO_SCALE": [".yaml", ".yml", ".json", ".tf", ".py", ".js", ".ts"]
        }
        
        return gate_extensions.get(gate_name, [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"])
    
    def _should_analyze_file(self, filename: str, extensions: List[str], scan_depth: str) -> bool:
        """Determine if a file should be analyzed based on scan depth and extensions"""
        if scan_depth == "minimal":
            # Only analyze main source files
            return any(filename.endswith(ext) for ext in [".py", ".js", ".ts", ".java"])
        elif scan_depth == "standard":
            # Analyze source files and config files
            return any(filename.endswith(ext) for ext in extensions)
        else:  # comprehensive
            # Analyze all relevant files
            return any(filename.endswith(ext) for ext in extensions)
    
    async def _calculate_gate_score(self, patterns_found: int, files_analyzed: int, gate_config: dict, evidence: List[Dict]) -> float:
        """Calculate score for a gate based on patterns found"""
        if files_analyzed == 0:
            return 0.0
        
        # Get expected coverage from gate config
        expected_coverage = gate_config.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 80)
        
        # Calculate score based on positive vs negative patterns
        positive_patterns = len([e for e in evidence if e.get("type") == "positive"])
        negative_patterns = len([e for e in evidence if e.get("type") == "negative"])
        violation_patterns = len([e for e in evidence if e.get("type") == "violation"])
        
        # Base score starts at expected percentage
        score = expected_percentage
        
        # Bonus for positive patterns
        score += (positive_patterns * 2)
        
        # Penalty for negative patterns
        score -= (negative_patterns * 5)
        
        # Heavy penalty for violations
        score -= (violation_patterns * 20)
        
        # Ensure score is within bounds
        score = max(0.0, min(100.0, score))
        
        return round(score, 1)
    
    async def _determine_gate_status(self, score: float, patterns_found: int, gate_config: dict) -> str:
        """Determine the status of a gate based on score and patterns"""
        if score >= 80:
            return "PASS"
        elif score >= 60:
            return "WARNING"
        else:
            return "FAIL"
    
    async def _generate_gate_recommendations(self, gate_name: str, patterns_found: int, evidence: List[Dict], gate_config: dict) -> List[str]:
        """Generate recommendations for a gate"""
        recommendations = []
        
        # Get gate-specific recommendations
        gate_recommendations = {
            "STRUCTURED_LOGS": [
                "Use structured logging frameworks (log4j, logback, winston, pino)",
                "Replace print statements with proper logging calls",
                "Include context information in log messages",
                "Use JSON format for log output"
            ],
            "AVOID_LOGGING_SECRETS": [
                "Never log passwords, tokens, or API keys",
                "Use environment variables for sensitive data",
                "Implement log filtering to prevent accidental secret logging",
                "Use secure secret management systems"
            ],
            "ALERTING_ACTIONABLE": [
                "Ensure all alerts have clear action items",
                "Configure proper alert thresholds",
                "Set up escalation procedures",
                "Include relevant context in alert messages"
            ],
            "AUDIT_TRAIL": [
                "Log all user actions and system events",
                "Include user context in audit logs",
                "Ensure audit logs are tamper-proof",
                "Implement log retention policies"
            ],
            "CORRELATION_ID": [
                "Generate unique correlation IDs for each request",
                "Propagate correlation IDs across service calls",
                "Include correlation IDs in all log messages",
                "Use correlation IDs for request tracing"
            ],
            "LOG_API_CALLS": [
                "Log all API requests and responses",
                "Include request/response metadata",
                "Log API performance metrics",
                "Monitor API usage patterns"
            ],
            "CLIENT_UI_ERRORS": [
                "Implement proper error handling in UI components",
                "Log client-side errors with context",
                "Provide user-friendly error messages",
                "Track error patterns and frequencies"
            ],
            "RETRY_LOGIC": [
                "Implement exponential backoff for retries",
                "Set maximum retry attempts",
                "Log retry attempts and failures",
                "Handle different types of failures appropriately"
            ],
            "TIMEOUT_IO": [
                "Set appropriate timeout values for I/O operations",
                "Handle timeout exceptions gracefully",
                "Log timeout occurrences",
                "Implement circuit breakers for repeated timeouts"
            ],
            "THROTTLING": [
                "Implement rate limiting for API endpoints",
                "Use token bucket or leaky bucket algorithms",
                "Return appropriate HTTP status codes for throttled requests",
                "Monitor throttling metrics"
            ],
            "CIRCUIT_BREAKERS": [
                "Implement circuit breaker pattern for external dependencies",
                "Configure appropriate thresholds for circuit breaker",
                "Monitor circuit breaker state changes",
                "Provide fallback mechanisms when circuit is open"
            ],
            "HTTP_ERROR_CODES": [
                "Use appropriate HTTP status codes",
                "Return consistent error response formats",
                "Include error details in response body",
                "Log HTTP errors with context"
            ],
            "URL_MONITORING": [
                "Set up URL monitoring for critical endpoints",
                "Configure appropriate monitoring intervals",
                "Set up alerts for URL failures",
                "Monitor response times and availability"
            ],
            "AUTOMATED_TESTS": [
                "Write unit tests for all critical functions",
                "Implement integration tests for API endpoints",
                "Set up automated test execution in CI/CD",
                "Maintain good test coverage"
            ],
            "AUTO_SCALE": [
                "Configure auto-scaling policies",
                "Set appropriate scaling thresholds",
                "Monitor scaling events and performance",
                "Test auto-scaling behavior"
            ]
        }
        
        # Add gate-specific recommendations
        if gate_name in gate_recommendations:
            recommendations.extend(gate_recommendations[gate_name])
        
        # Add general recommendations based on evidence
        violations = [e for e in evidence if e.get("type") == "violation"]
        if violations:
            recommendations.append(f"Fix {len(violations)} security violations found in the codebase")
        
        negative_patterns = [e for e in evidence if e.get("type") == "negative"]
        if negative_patterns:
            recommendations.append(f"Address {len(negative_patterns)} code quality issues")
        
        if not evidence:
            recommendations.append("No patterns found - ensure the gate requirements are properly implemented")
        
        return recommendations
    
    async def _validate_with_patterns(self, repo_path: str, gate_name: str, scan_depth: str, validation_config: dict) -> dict:
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
                    if self._should_analyze_file(file, [".py", ".js", ".ts", ".java"], scan_depth):
                        file_path = os.path.join(root, file)
                        file_evidence = await self._analyze_file_fallback(file_path, patterns)
                        
                        if file_evidence:
                            evidence.extend(file_evidence)
                            patterns_found += len(file_evidence)
                        
                        files_analyzed += 1
            
            # Calculate score and status
            score = await self._calculate_gate_score(patterns_found, files_analyzed, {}, evidence)
            status = await self._determine_gate_status(score, patterns_found, {})
            
            # Generate recommendations
            recommendations = await self._generate_gate_recommendations(gate_name, patterns_found, evidence, {})
            
            return {
                "gate_name": gate_name,
                "display_name": gate_name,
                "status": status,
                "score": score,
                "evidence": evidence,
                "recommendations": recommendations,
                "patterns_found": patterns_found,
                "files_analyzed": files_analyzed,
                "category": "Unknown",
                "priority": "Unknown"
            }
            
        except Exception as e:
            return {
                "gate_name": gate_name,
                "display_name": gate_name,
                "status": "ERROR",
                "score": 0.0,
                "error": str(e),
                "evidence": [],
                "recommendations": [],
                "category": "Unknown",
                "priority": "Unknown"
            }
    
    def _get_gate_patterns(self, gate_name: str) -> List[Dict[str, Any]]:
        """Get patterns for a specific gate (fallback)"""
        patterns = {
            "STRUCTURED_LOGS": [
                {"pattern": r"logger\.(info|warn|error|debug)", "description": "Structured logging calls"},
                {"pattern": r"log4j|logback|winston|pino", "description": "Logging frameworks"},
                {"pattern": r"JSON\.stringify|json\.dumps", "description": "JSON logging"}
            ],
            "AVOID_LOGGING_SECRETS": [
                {"pattern": r"password.*=.*['\"][^'\"]+['\"]", "description": "Hardcoded password"},
                {"pattern": r"api_key.*=.*['\"][^'\"]+['\"]", "description": "Hardcoded API key"},
                {"pattern": r"secret.*=.*['\"][^'\"]+['\"]", "description": "Hardcoded secret"}
            ],
            "ALERTING_ACTIONABLE": [
                {"pattern": r"alert|notification|monitoring", "description": "Alerting configuration"},
                {"pattern": r"splunk|appdynamics|thousandeyes", "description": "Monitoring tools"}
            ]
        }
        
        return patterns.get(gate_name, [])
    
    def _analyze_file_fallback(self, file_path: str, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze a single file for patterns (fallback)"""
        evidence = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern_info in patterns:
                    pattern = pattern_info["pattern"]
                    description = pattern_info["description"]
                    
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        evidence.append({
                            "type": "pattern",
                            "pattern": pattern,
                            "file": file_path,
                            "line": line_num,
                            "matched_text": match.group(),
                            "description": description
                        })
        
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return evidence
    
    def _get_default_gates(self) -> List[str]:
        """Get default gates when CodeGates is not available"""
        return [
            "STRUCTURED_LOGS",
            "AVOID_LOGGING_SECRETS",
            "ALERTING_ACTIONABLE",
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
            "AUTO_SCALE"
        ]
    
    async def _generate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> dict:
        """Generate summary of validation results"""
        total_gates = len(validation_results)
        passed_gates = len([r for r in validation_results if r.get("status") == "PASS"])
        failed_gates = len([r for r in validation_results if r.get("status") == "FAIL"])
        warning_gates = len([r for r in validation_results if r.get("status") == "WARNING"])
        error_gates = len([r for r in validation_results if r.get("status") == "ERROR"])
        
        # Calculate average score
        scores = [r.get("score", 0) for r in validation_results if r.get("score") is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Group by category
        categories = {}
        for result in validation_results:
            category = result.get("category", "Unknown")
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
            
            categories[category]["total"] += 1
            if result.get("status") == "PASS":
                categories[category]["passed"] += 1
            elif result.get("status") == "FAIL":
                categories[category]["failed"] += 1
            elif result.get("status") == "WARNING":
                categories[category]["warnings"] += 1
        
        return {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "warning_gates": warning_gates,
            "error_gates": error_gates,
            "pass_rate": (passed_gates / total_gates * 100) if total_gates > 0 else 0,
            "average_score": round(average_score, 1),
            "categories": categories,
            "overall_status": "PASS" if failed_gates == 0 else "FAIL"
        }


# Create wrapper functions for Google ADK compatibility
def validate_gates(repository_path: Optional[str] = None,
                   repository_url: Optional[str] = None,
                   gates: Optional[List[str]] = None,
                   scan_depth: str = "comprehensive",
                   validation_config: Optional[dict] = None,
                   branch: str = "main",
                   github_token: Optional[str] = None,
                   tool_context = None) -> Dict[str, Any]:
    """
    Validate hard gates against the codebase using pattern matching and analysis.
    
    Args:
        repository_path: Path to the repository to validate
        repository_url: Remote URL to clone if local path not provided
        gates: List of gates to validate (if None, validates all gates)
        scan_depth: Depth of scanning (minimal, standard, comprehensive)
        validation_config: Additional validation configuration
        branch: Branch to clone when repository_url is used
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing gate validation results
    """
    temp_dir = None
    try:
        repository_path, temp_dir, _ = _bridge_ensure_local_repo(
            repository_path=repository_path,
            repository_url=repository_url,
            branch=branch,
            github_token=github_token,
        )
        if not gates:
            gates = list(GATE_NUMBER_MAPPING.keys()) if CODEGATES_AVAILABLE else _get_default_gates()
        validation_results = []
        for gate_name in gates:
            gate_result = _validate_single_gate(repository_path, gate_name, scan_depth, validation_config or {})
            validation_results.append(gate_result)
        summary = _generate_validation_summary(validation_results)
        return {
            "success": True,
            "repository_path": repository_path,
            "gates_validated": gates,
            "validation_results": validation_results,
            "summary": summary,
            "total_gates": len(validation_results),
            "passed_gates": len([r for r in validation_results if r.get("status") == "PASS"]),
            "failed_gates": len([r for r in validation_results if r.get("status") == "FAIL"]),
            "pass_rate": (len([r for r in validation_results if r.get("status") == "PASS"]) / len(validation_results) * 100) if validation_results else 0
        }
    except Exception as e:
        return {"success": False, "error": f"Gate validation failed: {str(e)}"}
    finally:
        _bridge_cleanup(temp_dir)


def _validate_single_gate(repo_path: str, gate_name: str, scan_depth: str, validation_config: dict) -> dict:
    """Validate a single hard gate using actual hard gates logic"""
    try:
        if CODEGATES_AVAILABLE:
            return _validate_with_codegates(repo_path, gate_name, scan_depth, validation_config)
        else:
            return _validate_with_patterns(repo_path, gate_name, scan_depth, validation_config)
    except Exception as e:
        return {
            "gate_name": gate_name,
            "display_name": gate_name,
            "status": "ERROR",
            "score": 0.0,
            "error": str(e),
            "evidence": [],
            "recommendations": [],
            "category": "Unknown",
            "priority": "Unknown"
        }


def _validate_with_codegates(repo_path: str, gate_name: str, scan_depth: str, validation_config: dict) -> dict:
    """Validate using actual CodeGates framework"""
    try:
        # Get gate configuration from HARD_GATES
        gate_config = None
        for gate in HARD_GATES:
            if gate.get("name") == gate_name:
                gate_config = gate
                break
        
        if not gate_config:
            return {
                "gate_name": gate_name,
                "display_name": gate_name,
                "status": "NOT_APPLICABLE",
                "score": 0.0,
                "error": f"Gate {gate_name} not found in configuration",
                "evidence": [],
                "recommendations": [],
                "category": "Unknown",
                "priority": "Unknown"
            }
        
        # Use the actual file scanner and pattern matching logic
        evidence = []
        patterns_found = 0
        files_analyzed = 0
        
        # Get patterns for this gate
        patterns = gate_config.get("patterns", {})
        
        # Scan repository for patterns
        if patterns:
            evidence, patterns_found, files_analyzed = _scan_repository_for_patterns(
                repo_path, gate_name, patterns, scan_depth
            )
        
        # Calculate score based on patterns found
        score = _calculate_gate_score(patterns_found, files_analyzed, gate_config, evidence)
        status = _determine_gate_status(score, patterns_found, gate_config)
        
        # Generate recommendations
        recommendations = _generate_gate_recommendations(gate_name, patterns_found, evidence, gate_config)
        
        return {
            "gate_name": gate_name,
            "display_name": gate_config.get("display_name", gate_name),
            "description": gate_config.get("description", ""),
            "category": gate_config.get("category", "Unknown"),
            "priority": gate_config.get("priority", "Unknown"),
            "status": status,
            "score": score,
            "evidence": evidence,
            "recommendations": recommendations,
            "patterns_found": patterns_found,
            "files_analyzed": files_analyzed,
            "gate_number": get_gate_number(gate_name)
        }
        
    except Exception as e:
        return {
            "gate_name": gate_name,
            "display_name": gate_name,
            "status": "ERROR",
            "score": 0.0,
            "error": str(e),
            "evidence": [],
            "recommendations": [],
            "category": "Unknown",
            "priority": "Unknown"
        }


def _scan_repository_for_patterns(repo_path: str, gate_name: str, patterns: dict, scan_depth: str) -> tuple:
    """Scan repository for gate-specific patterns using actual logic"""
    evidence = []
    patterns_found = 0
    files_analyzed = 0
    
    # Define file extensions to scan based on gate
    file_extensions = _get_file_extensions_for_gate(gate_name)
    
    for root, dirs, files in os.walk(repo_path):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', '.venv']]
        
        for file in files:
            if _should_analyze_file(file, file_extensions, scan_depth):
                file_path = os.path.join(root, file)
                file_evidence = _analyze_file_for_gate_patterns(file_path, gate_name, patterns)
                
                if file_evidence:
                    evidence.extend(file_evidence)
                    patterns_found += len(file_evidence)
                
                files_analyzed += 1
    
    return evidence, patterns_found, files_analyzed


def _analyze_file_for_gate_patterns(file_path: str, gate_name: str, patterns: dict) -> List[Dict[str, Any]]:
    """Analyze a single file for gate-specific patterns"""
    evidence = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check positive patterns (good practices)
        positive_patterns = patterns.get("positive", [])
        for pattern in positive_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                evidence.append({
                    "type": "positive",
                    "pattern": pattern,
                    "file": file_path,
                    "line": line_num,
                    "matched_text": match.group(),
                    "description": f"Good practice found: {pattern}"
                })
        
        # Check negative patterns (violations)
        negative_patterns = patterns.get("negative", [])
        for pattern in negative_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                evidence.append({
                    "type": "negative",
                    "pattern": pattern,
                    "file": file_path,
                    "line": line_num,
                    "matched_text": match.group(),
                    "description": f"Violation found: {pattern}"
                })
        
        # Check violation patterns (security issues)
        violation_patterns = patterns.get("violations", [])
        for pattern in violation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                evidence.append({
                    "type": "violation",
                    "pattern": pattern,
                    "file": file_path,
                    "line": line_num,
                    "matched_text": match.group(),
                    "description": f"Security violation found: {pattern}"
                })
    
    except Exception as e:
        # Skip files that can't be read
        pass
    
    return evidence


def _get_file_extensions_for_gate(gate_name: str) -> List[str]:
    """Get relevant file extensions for a specific gate"""
    # Define file extensions based on gate type
    gate_extensions = {
        "STRUCTURED_LOGS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "AVOID_LOGGING_SECRETS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".conf", ".env", ".yaml", ".yml"],
        "ALERTING_ACTIONABLE": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".yaml", ".yml", ".json"],
        "AUDIT_TRAIL": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "CORRELATION_ID": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "LOG_API_CALLS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "CLIENT_UI_ERRORS": [".js", ".ts", ".jsx", ".tsx", ".vue", ".html"],
        "RETRY_LOGIC": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "TIMEOUT_IO": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "THROTTLING": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "CIRCUIT_BREAKERS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "HTTP_ERROR_CODES": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"],
        "URL_MONITORING": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".yaml", ".yml"],
        "AUTOMATED_TESTS": [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go", ".test.js", ".spec.js", ".test.py", ".spec.py"],
        "AUTO_SCALE": [".yaml", ".yml", ".json", ".tf", ".py", ".js", ".ts"]
    }
    
    return gate_extensions.get(gate_name, [".py", ".js", ".ts", ".java", ".cs", ".php", ".rb", ".go"])


def _should_analyze_file(filename: str, extensions: List[str], scan_depth: str) -> bool:
    """Determine if a file should be analyzed based on scan depth and extensions"""
    if scan_depth == "minimal":
        # Only analyze main source files
        return any(filename.endswith(ext) for ext in [".py", ".js", ".ts", ".java"])
    elif scan_depth == "standard":
        # Analyze source files and config files
        return any(filename.endswith(ext) for ext in extensions)
    else:  # comprehensive
        # Analyze all relevant files
        return any(filename.endswith(ext) for ext in extensions)


def _calculate_gate_score(patterns_found: int, files_analyzed: int, gate_config: dict, evidence: List[Dict]) -> float:
    """Calculate score for a gate based on patterns found"""
    if files_analyzed == 0:
        return 0.0
    
    # Get expected coverage from gate config
    expected_coverage = gate_config.get("expected_coverage", {})
    expected_percentage = expected_coverage.get("percentage", 80)
    
    # Calculate score based on positive vs negative patterns
    positive_patterns = len([e for e in evidence if e.get("type") == "positive"])
    negative_patterns = len([e for e in evidence if e.get("type") == "negative"])
    violation_patterns = len([e for e in evidence if e.get("type") == "violation"])
    
    # Base score starts at expected percentage
    score = expected_percentage
    
    # Bonus for positive patterns
    score += (positive_patterns * 2)
    
    # Penalty for negative patterns
    score -= (negative_patterns * 5)
    
    # Heavy penalty for violations
    score -= (violation_patterns * 20)
    
    # Ensure score is within bounds
    score = max(0.0, min(100.0, score))
    
    return round(score, 1)


def _determine_gate_status(score: float, patterns_found: int, gate_config: dict) -> str:
    """Determine the status of a gate based on score and patterns"""
    if score >= 80:
        return "PASS"
    elif score >= 60:
        return "WARNING"
    else:
        return "FAIL"


def _generate_gate_recommendations(gate_name: str, patterns_found: int, evidence: List[Dict], gate_config: dict) -> List[str]:
    """Generate recommendations for a gate"""
    recommendations = []
    
    # Get gate-specific recommendations
    gate_recommendations = {
        "STRUCTURED_LOGS": [
            "Use structured logging frameworks (log4j, logback, winston, pino)",
            "Replace print statements with proper logging calls",
            "Include context information in log messages",
            "Use JSON format for log output"
        ],
        "AVOID_LOGGING_SECRETS": [
            "Never log passwords, tokens, or API keys",
            "Use environment variables for sensitive data",
            "Implement log filtering to prevent accidental secret logging",
            "Use secure secret management systems"
        ],
        "ALERTING_ACTIONABLE": [
            "Ensure all alerts have clear action items",
            "Configure proper alert thresholds",
            "Set up escalation procedures",
            "Include relevant context in alert messages"
        ],
        "AUDIT_TRAIL": [
            "Log all user actions and system events",
            "Include user context in audit logs",
            "Ensure audit logs are tamper-proof",
            "Implement log retention policies"
        ],
        "CORRELATION_ID": [
            "Generate unique correlation IDs for each request",
            "Propagate correlation IDs across service calls",
            "Include correlation IDs in all log messages",
            "Use correlation IDs for request tracing"
        ],
        "LOG_API_CALLS": [
            "Log all API requests and responses",
            "Include request/response metadata",
            "Log API performance metrics",
            "Monitor API usage patterns"
        ],
        "CLIENT_UI_ERRORS": [
            "Implement proper error handling in UI components",
            "Log client-side errors with context",
            "Provide user-friendly error messages",
            "Track error patterns and frequencies"
        ],
        "RETRY_LOGIC": [
            "Implement exponential backoff for retries",
            "Set maximum retry attempts",
            "Log retry attempts and failures",
            "Handle different types of failures appropriately"
        ],
        "TIMEOUT_IO": [
            "Set appropriate timeout values for I/O operations",
            "Handle timeout exceptions gracefully",
            "Log timeout occurrences",
            "Implement circuit breakers for repeated timeouts"
        ],
        "THROTTLING": [
            "Implement rate limiting for API endpoints",
            "Use token bucket or leaky bucket algorithms",
            "Return appropriate HTTP status codes for throttled requests",
            "Monitor throttling metrics"
        ],
        "CIRCUIT_BREAKERS": [
            "Implement circuit breaker pattern for external dependencies",
            "Configure appropriate thresholds for circuit breaker",
            "Monitor circuit breaker state changes",
            "Provide fallback mechanisms when circuit is open"
        ],
        "HTTP_ERROR_CODES": [
            "Use appropriate HTTP status codes",
            "Return consistent error response formats",
            "Include error details in response body",
            "Log HTTP errors with context"
        ],
        "URL_MONITORING": [
            "Set up URL monitoring for critical endpoints",
            "Configure appropriate monitoring intervals",
            "Set up alerts for URL failures",
            "Monitor response times and availability"
        ],
        "AUTOMATED_TESTS": [
            "Write unit tests for all critical functions",
            "Implement integration tests for API endpoints",
            "Set up automated test execution in CI/CD",
            "Maintain good test coverage"
        ],
        "AUTO_SCALE": [
            "Configure auto-scaling policies",
            "Set appropriate scaling thresholds",
            "Monitor scaling events and performance",
            "Test auto-scaling behavior"
        ]
    }
    
    # Add gate-specific recommendations
    if gate_name in gate_recommendations:
        recommendations.extend(gate_recommendations[gate_name])
    
    # Add general recommendations based on evidence
    violations = [e for e in evidence if e.get("type") == "violation"]
    if violations:
        recommendations.append(f"Fix {len(violations)} security violations found in the codebase")
    
    negative_patterns = [e for e in evidence if e.get("type") == "negative"]
    if negative_patterns:
        recommendations.append(f"Address {len(negative_patterns)} code quality issues")
    
    if not evidence:
        recommendations.append("No patterns found - ensure the gate requirements are properly implemented")
    
    return recommendations


def _validate_with_patterns(repo_path: str, gate_name: str, scan_depth: str, validation_config: dict) -> dict:
    """Validate using pattern matching (fallback)"""
    try:
        # Define patterns for each gate
        patterns = _get_gate_patterns(gate_name)
        
        # Scan files for patterns
        evidence = []
        patterns_found = 0
        files_analyzed = 0
        
        for root, dirs, files in os.walk(repo_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache']]
            
            for file in files:
                if _should_analyze_file(file, [".py", ".js", ".ts", ".java"], scan_depth):
                    file_path = os.path.join(root, file)
                    file_evidence = _analyze_file_fallback(file_path, patterns)
                    
                    if file_evidence:
                        evidence.extend(file_evidence)
                        patterns_found += len(file_evidence)
                    
                    files_analyzed += 1
        
        # Calculate score and status
        score = _calculate_gate_score(patterns_found, files_analyzed, {}, evidence)
        status = _determine_gate_status(score, patterns_found, {})
        
        # Generate recommendations
        recommendations = _generate_gate_recommendations(gate_name, patterns_found, evidence, {})
        
        return {
            "gate_name": gate_name,
            "display_name": gate_name,
            "status": status,
            "score": score,
            "evidence": evidence,
            "recommendations": recommendations,
            "patterns_found": patterns_found,
            "files_analyzed": files_analyzed,
            "category": "Unknown",
            "priority": "Unknown"
        }
        
    except Exception as e:
        return {
            "gate_name": gate_name,
            "display_name": gate_name,
            "status": "ERROR",
            "score": 0.0,
            "error": str(e),
            "evidence": [],
            "recommendations": [],
            "category": "Unknown",
            "priority": "Unknown"
        }


def _get_gate_patterns(gate_name: str) -> List[Dict[str, Any]]:
    """Get patterns for a specific gate (fallback)"""
    patterns = {
        "STRUCTURED_LOGS": [
            {"pattern": r"logger\.(info|warn|error|debug)", "description": "Structured logging calls"},
            {"pattern": r"log4j|logback|winston|pino", "description": "Logging frameworks"},
            {"pattern": r"JSON\.stringify|json\.dumps", "description": "JSON logging"}
        ],
        "AVOID_LOGGING_SECRETS": [
            {"pattern": r"password.*=.*['\"][^'\"]+['\"]", "description": "Hardcoded password"},
            {"pattern": r"api_key.*=.*['\"][^'\"]+['\"]", "description": "Hardcoded API key"},
            {"pattern": r"secret.*=.*['\"][^'\"]+['\"]", "description": "Hardcoded secret"}
        ],
        "ALERTING_ACTIONABLE": [
            {"pattern": r"alert|notification|monitoring", "description": "Alerting configuration"},
            {"pattern": r"splunk|appdynamics|thousandeyes", "description": "Monitoring tools"}
        ]
    }
    
    return patterns.get(gate_name, [])


def _analyze_file_fallback(file_path: str, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze a single file for patterns (fallback)"""
    evidence = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                description = pattern_info["description"]
                
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    evidence.append({
                        "type": "pattern",
                        "pattern": pattern,
                        "file": file_path,
                        "line": line_num,
                        "matched_text": match.group(),
                        "description": description
                    })
    
    except Exception as e:
        # Skip files that can't be read
        pass
    
    return evidence


def _get_default_gates() -> List[str]:
    """Get default gates when CodeGates is not available"""
    return [
        "STRUCTURED_LOGS",
        "AVOID_LOGGING_SECRETS",
        "ALERTING_ACTIONABLE",
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
        "AUTO_SCALE"
    ]


def _generate_validation_summary(validation_results: List[Dict[str, Any]]) -> dict:
    """Generate summary of validation results"""
    total_gates = len(validation_results)
    passed_gates = len([r for r in validation_results if r.get("status") == "PASS"])
    failed_gates = len([r for r in validation_results if r.get("status") == "FAIL"])
    warning_gates = len([r for r in validation_results if r.get("status") == "WARNING"])
    error_gates = len([r for r in validation_results if r.get("status") == "ERROR"])
    
    # Calculate average score
    scores = [r.get("score", 0) for r in validation_results if r.get("score") is not None]
    average_score = sum(scores) / len(scores) if scores else 0
    
    # Group by category
    categories = {}
    for result in validation_results:
        category = result.get("category", "Unknown")
        if category not in categories:
            categories[category] = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
        
        categories[category]["total"] += 1
        if result.get("status") == "PASS":
            categories[category]["passed"] += 1
        elif result.get("status") == "FAIL":
            categories[category]["failed"] += 1
        elif result.get("status") == "WARNING":
            categories[category]["warnings"] += 1
    
    return {
        "total_gates": total_gates,
        "passed_gates": passed_gates,
        "failed_gates": failed_gates,
        "warning_gates": warning_gates,
        "error_gates": error_gates,
        "pass_rate": (passed_gates / total_gates * 100) if total_gates > 0 else 0,
        "average_score": round(average_score, 1),
        "categories": categories,
        "overall_status": "PASS" if failed_gates == 0 else "FAIL"
        } 

# Backward-compatible alias for callers using 'gate_validation'

def gate_validation(repository_path: Optional[str] = None,
                    repository_url: Optional[str] = None,
                    gates: Optional[List[str]] = None,
                    scan_depth: str = "comprehensive",
                    validation_config: Optional[dict] = None,
                    branch: str = "main",
                    github_token: Optional[str] = None,
                    tool_context = None) -> Dict[str, Any]:
    return validate_gates(
        repository_path=repository_path,
        repository_url=repository_url,
        gates=gates,
        scan_depth=scan_depth,
        validation_config=validation_config,
        branch=branch,
        github_token=github_token,
        tool_context=tool_context,
    ) 