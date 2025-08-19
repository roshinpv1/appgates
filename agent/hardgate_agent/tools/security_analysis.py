"""
Security Analysis Tool
Performs comprehensive security analysis and risk assessment
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


class SecurityAnalysisTool(BaseTool):
    """Tool for comprehensive security analysis and risk assessment"""
    
    name = "analyze_security"
    description = "Perform comprehensive security analysis including risk assessment, threat modeling, and security posture evaluation"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Perform comprehensive security analysis"""
        try:
            analysis_data = args.get("analysis_data", {})
            analysis_type = args.get("analysis_type", "comprehensive")
            
            if not analysis_data:
                return {
                    "success": False,
                    "error": "Analysis data is required"
                }
            
            # Perform different types of analysis
            analysis_results = {}
            
            if analysis_type in ["comprehensive", "risk_assessment"]:
                analysis_results["risk_assessment"] = await self._perform_risk_assessment(analysis_data)
            
            if analysis_type in ["comprehensive", "threat_modeling"]:
                analysis_results["threat_modeling"] = await self._perform_threat_modeling(analysis_data)
            
            if analysis_type in ["comprehensive", "vulnerability_analysis"]:
                analysis_results["vulnerability_analysis"] = await self._perform_vulnerability_analysis(analysis_data)
            
            if analysis_type in ["comprehensive", "security_recommendations"]:
                analysis_results["security_recommendations"] = await self._generate_security_recommendations(analysis_data)
            
            # Generate comprehensive security report
            security_report = await self._generate_security_report(analysis_results)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "analysis_results": analysis_results,
                "security_report": security_report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Security analysis failed: {str(e)}"
            }
    
    async def _perform_risk_assessment(self, analysis_data: Dict[str, Any]) -> dict:
        """Perform risk assessment"""
        risk_factors = []
        risk_score = 0
        
        # Analyze gate validation results
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        for gate in gate_results:
            if gate.get("status") == "FAIL":
                risk_score += 10
                risk_factors.append({
                    "factor": f"Failed gate: {gate.get('gate_name')}",
                    "impact": "High",
                    "probability": "High"
                })
            elif gate.get("status") == "WARNING":
                risk_score += 5
                risk_factors.append({
                    "factor": f"Warning gate: {gate.get('gate_name')}",
                    "impact": "Medium",
                    "probability": "Medium"
                })
        
        # Analyze security scan results
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            medium_vulns = vulns.get("severity_breakdown", {}).get("Medium", 0)
            
            risk_score += high_vulns * 15
            risk_score += medium_vulns * 8
            
            if high_vulns > 0:
                risk_factors.append({
                    "factor": f"{high_vulns} high severity vulnerabilities",
                    "impact": "High",
                    "probability": "High"
                })
        
        # Analyze evidence collection results
        evidence_data = analysis_data.get("evidence_collection", {}).get("evidence_data", {})
        for source, data in evidence_data.items():
            if not data.get("success", False):
                risk_score += 5
                risk_factors.append({
                    "factor": f"Failed {source} evidence collection",
                    "impact": "Medium",
                    "probability": "Medium"
                })
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "risk_mitigation": self._generate_risk_mitigation(risk_factors)
        }
    
    async def _perform_threat_modeling(self, analysis_data: Dict[str, Any]) -> dict:
        """Perform threat modeling"""
        threats = []
        
        # Identify threats based on analysis data
        technologies = analysis_data.get("repository_analysis", {}).get("technologies", {})
        
        # Web application threats
        if any(tech in technologies.get("frameworks", {}) for tech in ["nodejs", "python", "java"]):
            threats.extend([
                {
                    "threat": "SQL Injection",
                    "likelihood": "Medium",
                    "impact": "High",
                    "mitigation": "Use parameterized queries and input validation"
                },
                {
                    "threat": "Cross-Site Scripting (XSS)",
                    "likelihood": "Medium",
                    "impact": "Medium",
                    "mitigation": "Implement proper input sanitization and CSP headers"
                },
                {
                    "threat": "Authentication Bypass",
                    "likelihood": "Low",
                    "impact": "High",
                    "mitigation": "Implement strong authentication and authorization"
                }
            ])
        
        # API threats
        if technologies.get("frameworks"):
            threats.extend([
                {
                    "threat": "API Rate Limiting Bypass",
                    "likelihood": "Medium",
                    "impact": "Medium",
                    "mitigation": "Implement proper rate limiting and throttling"
                },
                {
                    "threat": "Insecure API Endpoints",
                    "likelihood": "Medium",
                    "impact": "High",
                    "mitigation": "Secure all API endpoints with proper authentication"
                }
            ])
        
        # Container threats
        if technologies.get("containers", {}).get("docker"):
            threats.extend([
                {
                    "threat": "Container Escape",
                    "likelihood": "Low",
                    "impact": "High",
                    "mitigation": "Use non-root containers and security scanning"
                },
                {
                    "threat": "Image Vulnerabilities",
                    "likelihood": "Medium",
                    "impact": "Medium",
                    "mitigation": "Regular vulnerability scanning and updates"
                }
            ])
        
        return {
            "total_threats": len(threats),
            "threats": threats,
            "threat_matrix": self._create_threat_matrix(threats)
        }
    
    async def _perform_vulnerability_analysis(self, analysis_data: Dict[str, Any]) -> dict:
        """Perform vulnerability analysis"""
        vulnerabilities = []
        
        # Analyze security scan results
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        
        for scan_type, results in scan_results.items():
            if scan_type == "vulnerabilities" and "vulnerabilities" in results:
                for vuln in results["vulnerabilities"]:
                    vulnerabilities.append({
                        "type": vuln.get("type", "Unknown"),
                        "severity": vuln.get("severity", "Low"),
                        "file": vuln.get("file", "Unknown"),
                        "line": vuln.get("line", 0),
                        "description": vuln.get("line_content", ""),
                        "recommendation": self._get_vulnerability_recommendation(vuln.get("type", ""))
                    })
            
            elif scan_type == "secrets" and "secrets" in results:
                for secret in results["secrets"]:
                    vulnerabilities.append({
                        "type": "Hardcoded Secret",
                        "severity": "High",
                        "file": secret.get("file", "Unknown"),
                        "line": secret.get("line", 0),
                        "description": "Hardcoded secret found",
                        "recommendation": "Remove hardcoded secrets and use environment variables"
                    })
        
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "severity_distribution": self._get_severity_distribution(vulnerabilities),
            "critical_vulnerabilities": [v for v in vulnerabilities if v["severity"] == "High"]
        }
    
    async def _generate_security_recommendations(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate security recommendations"""
        recommendations = []
        priority_recommendations = []
        
        # Generate recommendations based on analysis data
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        for gate in gate_results:
            if gate.get("status") == "FAIL":
                recommendations.append({
                    "category": "Gate Compliance",
                    "priority": "High",
                    "recommendation": f"Fix {gate.get('gate_name')} gate failure",
                    "impact": "High",
                    "effort": "Medium"
                })
        
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            if high_vulns > 0:
                recommendations.append({
                    "category": "Vulnerability Management",
                    "priority": "Critical",
                    "recommendation": f"Address {high_vulns} high severity vulnerabilities immediately",
                    "impact": "High",
                    "effort": "High"
                })
        
        if "secrets" in scan_results:
            secrets = scan_results["secrets"]
            if secrets.get("total_secrets", 0) > 0:
                recommendations.append({
                    "category": "Secret Management",
                    "priority": "High",
                    "recommendation": "Implement secret management solution",
                    "impact": "High",
                    "effort": "Medium"
                })
        
        # Add general security recommendations
        recommendations.extend([
            {
                "category": "Security Monitoring",
                "priority": "Medium",
                "recommendation": "Implement comprehensive security monitoring",
                "impact": "Medium",
                "effort": "High"
            },
            {
                "category": "Code Review",
                "priority": "Medium",
                "recommendation": "Implement automated security code review",
                "impact": "Medium",
                "effort": "Medium"
            },
            {
                "category": "Training",
                "priority": "Low",
                "recommendation": "Provide security training to development team",
                "impact": "Low",
                "effort": "Medium"
            }
        ])
        
        # Prioritize recommendations
        priority_recommendations = [r for r in recommendations if r["priority"] in ["Critical", "High"]]
        
        return {
            "total_recommendations": len(recommendations),
            "priority_recommendations": priority_recommendations,
            "all_recommendations": recommendations,
            "implementation_plan": self._create_implementation_plan(recommendations)
        }
    
    async def _generate_security_report(self, analysis_results: Dict[str, Any]) -> dict:
        """Generate comprehensive security report"""
        risk_assessment = analysis_results.get("risk_assessment", {})
        threat_modeling = analysis_results.get("threat_modeling", {})
        vulnerability_analysis = analysis_results.get("vulnerability_analysis", {})
        security_recommendations = analysis_results.get("security_recommendations", {})
        
        # Calculate overall security score
        security_score = self._calculate_security_score(analysis_results)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(analysis_results)
        
        return {
            "security_score": security_score,
            "executive_summary": executive_summary,
            "risk_assessment": risk_assessment,
            "threat_modeling": threat_modeling,
            "vulnerability_analysis": vulnerability_analysis,
            "security_recommendations": security_recommendations,
            "next_steps": self._generate_next_steps(analysis_results)
        }
    
    def _determine_risk_level(self, risk_score: int) -> str:
        """Determine risk level based on score"""
        if risk_score >= 50:
            return "Critical"
        elif risk_score >= 30:
            return "High"
        elif risk_score >= 15:
            return "Medium"
        else:
            return "Low"
    
    def _generate_risk_mitigation(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation strategies"""
        mitigations = []
        
        for factor in risk_factors:
            if "Failed gate" in factor["factor"]:
                mitigations.append("Implement missing security gates and patterns")
            elif "vulnerabilities" in factor["factor"]:
                mitigations.append("Address vulnerabilities through code fixes and updates")
            elif "evidence collection" in factor["factor"]:
                mitigations.append("Fix monitoring and logging infrastructure")
        
        return mitigations
    
    def _create_threat_matrix(self, threats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create threat matrix"""
        matrix = {
            "High_Impact": {"High_Likelihood": [], "Medium_Likelihood": [], "Low_Likelihood": []},
            "Medium_Impact": {"High_Likelihood": [], "Medium_Likelihood": [], "Low_Likelihood": []},
            "Low_Impact": {"High_Likelihood": [], "Medium_Likelihood": [], "Low_Likelihood": []}
        }
        
        for threat in threats:
            impact = threat.get("impact", "Low")
            likelihood = threat.get("likelihood", "Low")
            matrix[f"{impact}_Impact"][f"{likelihood}_Likelihood"].append(threat)
        
        return matrix
    
    def _get_vulnerability_recommendation(self, vuln_type: str) -> str:
        """Get recommendation for vulnerability type"""
        recommendations = {
            "Code Injection": "Use parameterized queries and input validation",
            "SQL Injection": "Use prepared statements and input sanitization",
            "XSS": "Implement proper input sanitization and CSP headers",
            "Hardcoded Password": "Use environment variables and secret management",
            "Insecure Protocol": "Use HTTPS and secure protocols",
            "Password Logging": "Remove password logging and use secure logging"
        }
        
        return recommendations.get(vuln_type, "Review and fix according to security best practices")
    
    def _get_severity_distribution(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of vulnerabilities by severity"""
        distribution = {"High": 0, "Medium": 0, "Low": 0}
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "Low")
            if severity in distribution:
                distribution[severity] += 1
        
        return distribution
    
    def _create_implementation_plan(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation plan for recommendations"""
        plan = {
            "immediate": [],
            "short_term": [],
            "long_term": []
        }
        
        for rec in recommendations:
            if rec["priority"] == "Critical":
                plan["immediate"].append(rec)
            elif rec["priority"] == "High":
                plan["short_term"].append(rec)
            else:
                plan["long_term"].append(rec)
        
        return plan
    
    def _calculate_security_score(self, analysis_results: Dict[str, Any]) -> int:
        """Calculate overall security score (0-100)"""
        score = 100
        
        # Deduct points for risks
        risk_assessment = analysis_results.get("risk_assessment", {})
        risk_score = risk_assessment.get("risk_score", 0)
        score -= min(risk_score, 50)  # Max deduction of 50 points
        
        # Deduct points for vulnerabilities
        vulnerability_analysis = analysis_results.get("vulnerability_analysis", {})
        high_vulns = len(vulnerability_analysis.get("critical_vulnerabilities", []))
        score -= high_vulns * 5  # 5 points per high vulnerability
        
        return max(0, score)
    
    def _generate_executive_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate executive summary"""
        risk_assessment = analysis_results.get("risk_assessment", {})
        vulnerability_analysis = analysis_results.get("vulnerability_analysis", {})
        
        risk_level = risk_assessment.get("risk_level", "Unknown")
        total_vulns = vulnerability_analysis.get("total_vulnerabilities", 0)
        critical_vulns = len(vulnerability_analysis.get("critical_vulnerabilities", []))
        
        summary = f"""
        Security Analysis Summary:
        
        Overall Risk Level: {risk_level}
        Total Vulnerabilities: {total_vulns}
        Critical Vulnerabilities: {critical_vulns}
        
        Key Findings:
        - Risk assessment indicates {risk_level.lower()} risk level
        - {critical_vulns} critical vulnerabilities require immediate attention
        - {total_vulns} total security issues identified
        
        Recommendations:
        - Address critical vulnerabilities immediately
        - Implement missing security gates
        - Enhance monitoring and logging
        - Conduct regular security assessments
        """
        
        return summary.strip()
    
    def _generate_next_steps(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate next steps"""
        next_steps = [
            "Review and prioritize security recommendations",
            "Create remediation plan for critical issues",
            "Implement immediate security fixes",
            "Schedule follow-up security assessment",
            "Establish ongoing security monitoring"
        ]
        
        return next_steps 