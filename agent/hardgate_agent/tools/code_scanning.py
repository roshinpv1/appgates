"""
Code Scanning Tool
Performs comprehensive security scanning of the codebase
"""

import os
import sys
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


class CodeScanningTool(BaseTool):
    """Tool for comprehensive code security scanning"""
    
    name = "scan_code"
    description = "Perform comprehensive security scanning including vulnerabilities, dependencies, configuration, secrets, and authentication"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Perform comprehensive security scanning"""
        try:
            repository_path = args.get("repository_path")
            scan_type = args.get("scan_type", "comprehensive")
            
            if not repository_path:
                return {
                    "success": False,
                    "error": "Repository path is required"
                }
            
            # Perform different types of scans
            scan_results = {}
            
            if scan_type in ["comprehensive", "vulnerabilities"]:
                scan_results["vulnerabilities"] = await self._scan_vulnerabilities(repository_path)
            
            if scan_type in ["comprehensive", "dependencies"]:
                scan_results["dependencies"] = await self._scan_dependencies(repository_path)
            
            if scan_type in ["comprehensive", "configuration"]:
                scan_results["configuration"] = await self._scan_configuration(repository_path)
            
            if scan_type in ["comprehensive", "secrets"]:
                scan_results["secrets"] = await self._scan_secrets(repository_path)
            
            if scan_type in ["comprehensive", "authentication"]:
                scan_results["authentication"] = await self._scan_authentication(repository_path)
            
            # Generate summary
            summary = await self._generate_scan_summary(scan_results)
            
            return {
                "success": True,
                "repository_path": repository_path,
                "scan_type": scan_type,
                "scan_results": scan_results,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Security scanning failed: {str(e)}"
            }
    
    async def _scan_vulnerabilities(self, repo_path: str) -> dict:
        """Scan for code vulnerabilities"""
        vulnerabilities = []
        
        # Scan for common security vulnerabilities
        vulnerability_patterns = [
            {"pattern": r"eval\s*\(", "type": "Code Injection", "severity": "High"},
            {"pattern": r"exec\s*\(", "type": "Code Injection", "severity": "High"},
            {"pattern": r"sql.*injection", "type": "SQL Injection", "severity": "High"},
            {"pattern": r"xss|cross.*site.*scripting", "type": "XSS", "severity": "Medium"},
            {"pattern": r"password.*=.*['\"][^'\"]*['\"]", "type": "Hardcoded Password", "severity": "High"},
            {"pattern": r"api.*key.*=.*['\"][^'\"]*['\"]", "type": "Hardcoded API Key", "severity": "High"},
            {"pattern": r"http://", "type": "Insecure Protocol", "severity": "Medium"},
            {"pattern": r"console\.log.*password", "type": "Password Logging", "severity": "Medium"},
            {"pattern": r"innerHTML.*=.*\$\{", "type": "Template Injection", "severity": "Medium"},
            {"pattern": r"document\.write.*\$\{", "type": "DOM XSS", "severity": "Medium"}
        ]
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            for file in files:
                if self._should_scan_file(file):
                    file_path = os.path.join(root, file)
                    file_vulns = await self._scan_file_for_vulnerabilities(file_path, vulnerability_patterns)
                    vulnerabilities.extend(file_vulns)
        
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "severity_breakdown": self._get_severity_breakdown(vulnerabilities)
        }
    
    async def _scan_dependencies(self, repo_path: str) -> dict:
        """Scan for dependency security issues"""
        dependency_issues = []
        
        # Check for dependency files
        dependency_files = [
            "package.json", "requirements.txt", "pom.xml", "build.gradle", 
            "go.mod", "Cargo.toml", "Gemfile", "composer.json"
        ]
        
        for dep_file in dependency_files:
            file_path = os.path.join(repo_path, dep_file)
            if os.path.exists(file_path):
                issues = await self._analyze_dependency_file(file_path)
                dependency_issues.extend(issues)
        
        return {
            "total_issues": len(dependency_issues),
            "dependency_issues": dependency_issues,
            "files_analyzed": [f for f in dependency_files if os.path.exists(os.path.join(repo_path, f))]
        }
    
    async def _scan_configuration(self, repo_path: str) -> dict:
        """Scan for configuration security issues"""
        config_issues = []
        
        # Check for configuration files
        config_files = [
            ".env", "config.json", "application.properties", "application.yml",
            "docker-compose.yml", "Dockerfile", "kubernetes.yaml", "k8s.yaml"
        ]
        
        for config_file in config_files:
            file_path = os.path.join(repo_path, config_file)
            if os.path.exists(file_path):
                issues = await self._analyze_config_file(file_path)
                config_issues.extend(issues)
        
        return {
            "total_issues": len(config_issues),
            "configuration_issues": config_issues,
            "files_analyzed": [f for f in config_files if os.path.exists(os.path.join(repo_path, f))]
        }
    
    async def _scan_secrets(self, repo_path: str) -> dict:
        """Scan for secrets and sensitive data"""
        secrets_found = []
        
        # Common secret patterns
        secret_patterns = [
            r"password.*=.*['\"][^'\"]{8,}['\"]",
            r"secret.*=.*['\"][^'\"]{8,}['\"]",
            r"token.*=.*['\"][^'\"]{8,}['\"]",
            r"key.*=.*['\"][^'\"]{8,}['\"]",
            r"api_key.*=.*['\"][^'\"]{8,}['\"]",
            r"private_key.*=.*['\"][^'\"]{8,}['\"]",
            r"aws_access_key.*=.*['\"][^'\"]{8,}['\"]",
            r"aws_secret_key.*=.*['\"][^'\"]{8,}['\"]"
        ]
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            for file in files:
                if self._should_scan_file(file):
                    file_path = os.path.join(root, file)
                    file_secrets = await self._scan_file_for_secrets(file_path, secret_patterns)
                    secrets_found.extend(file_secrets)
        
        return {
            "total_secrets": len(secrets_found),
            "secrets": secrets_found,
            "risk_level": "High" if len(secrets_found) > 0 else "Low"
        }
    
    async def _scan_authentication(self, repo_path: str) -> dict:
        """Scan for authentication and authorization issues"""
        auth_issues = []
        
        # Authentication patterns
        auth_patterns = [
            {"pattern": r"authentication.*disabled", "type": "Auth Disabled", "severity": "High"},
            {"pattern": r"authorization.*disabled", "type": "AuthZ Disabled", "severity": "High"},
            {"pattern": r"skip.*auth|bypass.*auth", "type": "Auth Bypass", "severity": "High"},
            {"pattern": r"admin.*=.*true", "type": "Hardcoded Admin", "severity": "High"},
            {"pattern": r"role.*=.*admin", "type": "Hardcoded Admin Role", "severity": "High"},
            {"pattern": r"jwt.*secret.*=.*['\"][^'\"]*['\"]", "type": "Weak JWT Secret", "severity": "Medium"}
        ]
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            for file in files:
                if self._should_scan_file(file):
                    file_path = os.path.join(root, file)
                    file_auth_issues = await self._scan_file_for_auth_issues(file_path, auth_patterns)
                    auth_issues.extend(file_auth_issues)
        
        return {
            "total_issues": len(auth_issues),
            "authentication_issues": auth_issues,
            "severity_breakdown": self._get_severity_breakdown(auth_issues)
        }
    
    def _should_scan_file(self, filename: str) -> bool:
        """Determine if file should be scanned"""
        return any(filename.endswith(ext) for ext in [
            '.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.cs', '.php', '.rb', '.scala', '.kt', '.swift',
            '.json', '.yaml', '.yml', '.toml', '.xml', '.properties', '.conf', '.config', '.env'
        ])
    
    async def _scan_file_for_vulnerabilities(self, file_path: str, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan a file for vulnerabilities"""
        vulnerabilities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern_info in patterns:
                        pattern = pattern_info["pattern"]
                        vuln_type = pattern_info["type"]
                        severity = pattern_info["severity"]
                        
                        if re.search(pattern, line, re.IGNORECASE):
                            vulnerabilities.append({
                                "file": file_path,
                                "line": line_num,
                                "line_content": line.strip(),
                                "type": vuln_type,
                                "severity": severity,
                                "pattern": pattern
                            })
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return vulnerabilities
    
    async def _scan_file_for_secrets(self, file_path: str, patterns: List[str]) -> List[Dict[str, Any]]:
        """Scan a file for secrets"""
        secrets = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            secrets.append({
                                "file": file_path,
                                "line": line_num,
                                "line_content": line.strip(),
                                "pattern": pattern,
                                "severity": "High"
                            })
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return secrets
    
    async def _scan_file_for_auth_issues(self, file_path: str, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan a file for authentication issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern_info in patterns:
                        pattern = pattern_info["pattern"]
                        issue_type = pattern_info["type"]
                        severity = pattern_info["severity"]
                        
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append({
                                "file": file_path,
                                "line": line_num,
                                "line_content": line.strip(),
                                "type": issue_type,
                                "severity": severity,
                                "pattern": pattern
                            })
        except Exception as e:
            # Skip files that can't be read
            pass
        
        return issues
    
    async def _analyze_dependency_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze dependency file for security issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for common issues
                if "latest" in content.lower():
                    issues.append({
                        "file": file_path,
                        "type": "Latest Version",
                        "severity": "Medium",
                        "description": "Using 'latest' version can lead to unexpected updates"
                    })
                
                if "0.0.0" in content or "0.0.1" in content:
                    issues.append({
                        "file": file_path,
                        "type": "Development Version",
                        "severity": "Medium",
                        "description": "Using development versions in production"
                    })
                
                # Add more dependency-specific checks as needed
                
        except Exception as e:
            issues.append({
                "file": file_path,
                "type": "File Read Error",
                "severity": "Low",
                "description": f"Could not read dependency file: {str(e)}"
            })
        
        return issues
    
    async def _analyze_config_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze configuration file for security issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for common configuration issues
                if "debug.*=.*true" in content.lower():
                    issues.append({
                        "file": file_path,
                        "type": "Debug Mode",
                        "severity": "Medium",
                        "description": "Debug mode enabled in configuration"
                    })
                
                if "password.*=.*['\"][^'\"]*['\"]" in content.lower():
                    issues.append({
                        "file": file_path,
                        "type": "Hardcoded Password",
                        "severity": "High",
                        "description": "Hardcoded password in configuration"
                    })
                
                # Add more configuration-specific checks as needed
                
        except Exception as e:
            issues.append({
                "file": file_path,
                "type": "File Read Error",
                "severity": "Low",
                "description": f"Could not read configuration file: {str(e)}"
            })
        
        return issues
    
    def _get_severity_breakdown(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of issues by severity"""
        breakdown = {"High": 0, "Medium": 0, "Low": 0}
        
        for issue in issues:
            severity = issue.get("severity", "Low")
            if severity in breakdown:
                breakdown[severity] += 1
        
        return breakdown
    
    async def _generate_scan_summary(self, scan_results: Dict[str, Any]) -> dict:
        """Generate summary of all scan results"""
        total_issues = 0
        high_severity = 0
        medium_severity = 0
        low_severity = 0
        
        for scan_type, results in scan_results.items():
            if "vulnerabilities" in results:
                total_issues += results["total_vulnerabilities"]
                breakdown = results.get("severity_breakdown", {})
                high_severity += breakdown.get("High", 0)
                medium_severity += breakdown.get("Medium", 0)
                low_severity += breakdown.get("Low", 0)
            
            if "total_issues" in results:
                total_issues += results["total_issues"]
            
            if "total_secrets" in results:
                total_issues += results["total_secrets"]
                if results["total_secrets"] > 0:
                    high_severity += results["total_secrets"]
        
        return {
            "total_issues": total_issues,
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "low_severity": low_severity,
            "risk_level": self._calculate_risk_level(high_severity, medium_severity),
            "recommendations": self._generate_scan_recommendations(scan_results)
        }
    
    def _calculate_risk_level(self, high_count: int, medium_count: int) -> str:
        """Calculate overall risk level"""
        if high_count > 5:
            return "Critical"
        elif high_count > 0 or medium_count > 10:
            return "High"
        elif medium_count > 5:
            return "Medium"
        else:
            return "Low"
    
    def _generate_scan_recommendations(self, scan_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on scan results"""
        recommendations = []
        
        for scan_type, results in scan_results.items():
            if scan_type == "vulnerabilities" and results.get("total_vulnerabilities", 0) > 0:
                recommendations.append("Address high and medium severity vulnerabilities immediately")
                recommendations.append("Implement secure coding practices and code review")
            
            if scan_type == "secrets" and results.get("total_secrets", 0) > 0:
                recommendations.append("Remove hardcoded secrets and use environment variables")
                recommendations.append("Implement secret management solution")
            
            if scan_type == "dependencies" and results.get("total_issues", 0) > 0:
                recommendations.append("Update dependencies to stable versions")
                recommendations.append("Implement dependency vulnerability scanning")
            
            if scan_type == "configuration" and results.get("total_issues", 0) > 0:
                recommendations.append("Review and secure configuration files")
                recommendations.append("Use configuration management best practices")
            
            if scan_type == "authentication" and results.get("total_issues", 0) > 0:
                recommendations.append("Implement proper authentication and authorization")
                recommendations.append("Review access control mechanisms")
        
        if not recommendations:
            recommendations.append("Continue monitoring for security issues")
            recommendations.append("Implement automated security scanning in CI/CD")
        
        return recommendations 