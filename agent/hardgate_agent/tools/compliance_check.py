"""
Compliance Check Tool
Performs compliance validation against security standards
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


class ComplianceCheckTool(BaseTool):
    """Tool for compliance validation against security standards"""
    
    name = "check_compliance"
    description = "Validate compliance against security standards including SOC2, ISO27001, NIST, and enterprise policies"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Perform compliance checks"""
        try:
            compliance_frameworks = args.get("frameworks", ["SOC2", "ISO27001", "NIST", "Enterprise"])
            analysis_data = args.get("analysis_data", {})
            
            if not analysis_data:
                return {
                    "success": False,
                    "error": "Analysis data is required for compliance checks"
                }
            
            # Perform compliance checks for each framework
            compliance_results = {}
            
            for framework in compliance_frameworks:
                compliance_results[framework] = await self._check_framework_compliance(framework, analysis_data)
            
            # Generate compliance summary
            compliance_summary = await self._generate_compliance_summary(compliance_results)
            
            return {
                "success": True,
                "frameworks_checked": compliance_frameworks,
                "compliance_results": compliance_results,
                "compliance_summary": compliance_summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Compliance check failed: {str(e)}"
            }
    
    async def _check_framework_compliance(self, framework: str, analysis_data: Dict[str, Any]) -> dict:
        """Check compliance for a specific framework"""
        if framework == "SOC2":
            return await self._check_soc2_compliance(analysis_data)
        elif framework == "ISO27001":
            return await self._check_iso27001_compliance(analysis_data)
        elif framework == "NIST":
            return await self._check_nist_compliance(analysis_data)
        elif framework == "Enterprise":
            return await self._check_enterprise_compliance(analysis_data)
        else:
            return {
                "success": False,
                "error": f"Framework {framework} not supported"
            }
    
    async def _check_soc2_compliance(self, analysis_data: Dict[str, Any]) -> dict:
        """Check SOC2 compliance"""
        controls = {
            "CC6.1": {"name": "Logical Access Security", "status": "Not Assessed", "score": 0},
            "CC6.2": {"name": "Access Control", "status": "Not Assessed", "score": 0},
            "CC6.3": {"name": "Security Monitoring", "status": "Not Assessed", "score": 0},
            "CC7.1": {"name": "System Operations", "status": "Not Assessed", "score": 0},
            "CC7.2": {"name": "Change Management", "status": "Not Assessed", "score": 0},
            "CC8.1": {"name": "Risk Assessment", "status": "Not Assessed", "score": 0},
            "CC9.1": {"name": "Security Incident Management", "status": "Not Assessed", "score": 0}
        }
        
        # Assess controls based on analysis data
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        
        # CC6.1 - Logical Access Security
        if any(gate.get("gate_name") == "AUTHENTICATION" and gate.get("status") == "PASS" for gate in gate_results):
            controls["CC6.1"]["status"] = "Compliant"
            controls["CC6.1"]["score"] = 100
        
        # CC6.2 - Access Control
        if any(gate.get("gate_name") == "AUTHORIZATION" and gate.get("status") == "PASS" for gate in gate_results):
            controls["CC6.2"]["status"] = "Compliant"
            controls["CC6.2"]["score"] = 100
        
        # CC6.3 - Security Monitoring
        if any(gate.get("gate_name") == "ALERTING_ACTIONABLE" and gate.get("status") == "PASS" for gate in gate_results):
            controls["CC6.3"]["status"] = "Compliant"
            controls["CC6.3"]["score"] = 100
        
        # CC7.1 - System Operations
        if any(gate.get("gate_name") == "STRUCTURED_LOGS" and gate.get("status") == "PASS" for gate in gate_results):
            controls["CC7.1"]["status"] = "Compliant"
            controls["CC7.1"]["score"] = 100
        
        # CC7.2 - Change Management
        if any(gate.get("gate_name") == "AUDIT_TRAIL" and gate.get("status") == "PASS" for gate in gate_results):
            controls["CC7.2"]["status"] = "Compliant"
            controls["CC7.2"]["score"] = 100
        
        # CC8.1 - Risk Assessment
        risk_assessment = analysis_data.get("security_analysis", {}).get("analysis_results", {}).get("risk_assessment", {})
        if risk_assessment.get("risk_level") in ["Low", "Medium"]:
            controls["CC8.1"]["status"] = "Compliant"
            controls["CC8.1"]["score"] = 100
        
        # CC9.1 - Security Incident Management
        if any(gate.get("gate_name") == "ERROR_HANDLING" and gate.get("status") == "PASS" for gate in gate_results):
            controls["CC9.1"]["status"] = "Compliant"
            controls["CC9.1"]["score"] = 100
        
        # Calculate overall compliance
        total_score = sum(control["score"] for control in controls.values())
        overall_score = total_score / len(controls)
        
        return {
            "framework": "SOC2",
            "overall_score": round(overall_score, 2),
            "compliance_status": "Compliant" if overall_score >= 80 else "Non-Compliant",
            "controls": controls,
            "gaps": self._identify_compliance_gaps(controls),
            "recommendations": self._generate_compliance_recommendations(controls, "SOC2")
        }
    
    async def _check_iso27001_compliance(self, analysis_data: Dict[str, Any]) -> dict:
        """Check ISO27001 compliance"""
        controls = {
            "A.9.1": {"name": "Access Control Policy", "status": "Not Assessed", "score": 0},
            "A.9.2": {"name": "User Access Management", "status": "Not Assessed", "score": 0},
            "A.9.3": {"name": "User Responsibilities", "status": "Not Assessed", "score": 0},
            "A.12.1": {"name": "Operational Procedures", "status": "Not Assessed", "score": 0},
            "A.12.2": {"name": "Protection from Malware", "status": "Not Assessed", "score": 0},
            "A.12.3": {"name": "Backup", "status": "Not Assessed", "score": 0},
            "A.12.4": {"name": "Logging and Monitoring", "status": "Not Assessed", "score": 0}
        }
        
        # Assess controls based on analysis data
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        
        # A.9.1 - Access Control Policy
        if any(gate.get("gate_name") == "AUTHENTICATION" and gate.get("status") == "PASS" for gate in gate_results):
            controls["A.9.1"]["status"] = "Compliant"
            controls["A.9.1"]["score"] = 100
        
        # A.9.2 - User Access Management
        if any(gate.get("gate_name") == "AUTHORIZATION" and gate.get("status") == "PASS" for gate in gate_results):
            controls["A.9.2"]["status"] = "Compliant"
            controls["A.9.2"]["score"] = 100
        
        # A.12.4 - Logging and Monitoring
        if any(gate.get("gate_name") == "STRUCTURED_LOGS" and gate.get("status") == "PASS" for gate in gate_results):
            controls["A.12.4"]["status"] = "Compliant"
            controls["A.12.4"]["score"] = 100
        
        # Calculate overall compliance
        total_score = sum(control["score"] for control in controls.values())
        overall_score = total_score / len(controls)
        
        return {
            "framework": "ISO27001",
            "overall_score": round(overall_score, 2),
            "compliance_status": "Compliant" if overall_score >= 80 else "Non-Compliant",
            "controls": controls,
            "gaps": self._identify_compliance_gaps(controls),
            "recommendations": self._generate_compliance_recommendations(controls, "ISO27001")
        }
    
    async def _check_nist_compliance(self, analysis_data: Dict[str, Any]) -> dict:
        """Check NIST compliance"""
        controls = {
            "AC-1": {"name": "Access Control Policy", "status": "Not Assessed", "score": 0},
            "AC-2": {"name": "Account Management", "status": "Not Assessed", "score": 0},
            "AC-3": {"name": "Access Enforcement", "status": "Not Assessed", "score": 0},
            "AU-2": {"name": "Audit Events", "status": "Not Assessed", "score": 0},
            "AU-3": {"name": "Content of Audit Records", "status": "Not Assessed", "score": 0},
            "SI-4": {"name": "Information System Monitoring", "status": "Not Assessed", "score": 0}
        }
        
        # Assess controls based on analysis data
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        
        # AC-1 - Access Control Policy
        if any(gate.get("gate_name") == "AUTHENTICATION" and gate.get("status") == "PASS" for gate in gate_results):
            controls["AC-1"]["status"] = "Compliant"
            controls["AC-1"]["score"] = 100
        
        # AC-2 - Account Management
        if any(gate.get("gate_name") == "AUTHORIZATION" and gate.get("status") == "PASS" for gate in gate_results):
            controls["AC-2"]["status"] = "Compliant"
            controls["AC-2"]["score"] = 100
        
        # AU-2 - Audit Events
        if any(gate.get("gate_name") == "AUDIT_TRAIL" and gate.get("status") == "PASS" for gate in gate_results):
            controls["AU-2"]["status"] = "Compliant"
            controls["AU-2"]["score"] = 100
        
        # SI-4 - Information System Monitoring
        if any(gate.get("gate_name") == "ALERTING_ACTIONABLE" and gate.get("status") == "PASS" for gate in gate_results):
            controls["SI-4"]["status"] = "Compliant"
            controls["SI-4"]["score"] = 100
        
        # Calculate overall compliance
        total_score = sum(control["score"] for control in controls.values())
        overall_score = total_score / len(controls)
        
        return {
            "framework": "NIST",
            "overall_score": round(overall_score, 2),
            "compliance_status": "Compliant" if overall_score >= 80 else "Non-Compliant",
            "controls": controls,
            "gaps": self._identify_compliance_gaps(controls),
            "recommendations": self._generate_compliance_recommendations(controls, "NIST")
        }
    
    async def _check_enterprise_compliance(self, analysis_data: Dict[str, Any]) -> dict:
        """Check enterprise-specific compliance"""
        controls = {
            "SEC-001": {"name": "Security Gates Implementation", "status": "Not Assessed", "score": 0},
            "SEC-002": {"name": "Vulnerability Management", "status": "Not Assessed", "score": 0},
            "SEC-003": {"name": "Monitoring and Alerting", "status": "Not Assessed", "score": 0},
            "SEC-004": {"name": "Logging and Audit", "status": "Not Assessed", "score": 0},
            "SEC-005": {"name": "Error Handling", "status": "Not Assessed", "score": 0}
        }
        
        # Assess controls based on analysis data
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        
        # SEC-001 - Security Gates Implementation
        passed_gates = len([g for g in gate_results if g.get("status") == "PASS"])
        total_gates = len(gate_results)
        if total_gates > 0 and (passed_gates / total_gates) >= 0.8:
            controls["SEC-001"]["status"] = "Compliant"
            controls["SEC-001"]["score"] = 100
        
        # SEC-002 - Vulnerability Management
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            if high_vulns == 0:
                controls["SEC-002"]["status"] = "Compliant"
                controls["SEC-002"]["score"] = 100
        
        # SEC-003 - Monitoring and Alerting
        if any(gate.get("gate_name") == "ALERTING_ACTIONABLE" and gate.get("status") == "PASS" for gate in gate_results):
            controls["SEC-003"]["status"] = "Compliant"
            controls["SEC-003"]["score"] = 100
        
        # SEC-004 - Logging and Audit
        if any(gate.get("gate_name") == "STRUCTURED_LOGS" and gate.get("status") == "PASS" for gate in gate_results):
            controls["SEC-004"]["status"] = "Compliant"
            controls["SEC-004"]["score"] = 100
        
        # SEC-005 - Error Handling
        if any(gate.get("gate_name") == "ERROR_HANDLING" and gate.get("status") == "PASS" for gate in gate_results):
            controls["SEC-005"]["status"] = "Compliant"
            controls["SEC-005"]["score"] = 100
        
        # Calculate overall compliance
        total_score = sum(control["score"] for control in controls.values())
        overall_score = total_score / len(controls)
        
        return {
            "framework": "Enterprise",
            "overall_score": round(overall_score, 2),
            "compliance_status": "Compliant" if overall_score >= 80 else "Non-Compliant",
            "controls": controls,
            "gaps": self._identify_compliance_gaps(controls),
            "recommendations": self._generate_compliance_recommendations(controls, "Enterprise")
        }
    
    def _identify_compliance_gaps(self, controls: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify compliance gaps"""
        gaps = []
        
        for control_id, control in controls.items():
            if control["status"] != "Compliant":
                gaps.append({
                    "control_id": control_id,
                    "control_name": control["name"],
                    "status": control["status"],
                    "score": control["score"],
                    "gap_description": f"Control {control_id} ({control['name']}) is not compliant"
                })
        
        return gaps
    
    def _generate_compliance_recommendations(self, controls: Dict[str, Any], framework: str) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        non_compliant_controls = [c for c in controls.values() if c["status"] != "Compliant"]
        
        if non_compliant_controls:
            recommendations.append(f"Address {len(non_compliant_controls)} non-compliant {framework} controls")
            recommendations.append("Implement missing security controls and policies")
            recommendations.append("Conduct regular compliance assessments")
        else:
            recommendations.append(f"Maintain {framework} compliance through regular monitoring")
            recommendations.append("Continue implementing security best practices")
        
        return recommendations
    
    async def _generate_compliance_summary(self, compliance_results: Dict[str, Any]) -> dict:
        """Generate compliance summary"""
        summary = {
            "total_frameworks": len(compliance_results),
            "compliant_frameworks": 0,
            "non_compliant_frameworks": 0,
            "average_compliance_score": 0,
            "overall_compliance_status": "Unknown",
            "key_gaps": [],
            "recommendations": []
        }
        
        total_score = 0
        all_gaps = []
        all_recommendations = []
        
        for framework, result in compliance_results.items():
            if result.get("compliance_status") == "Compliant":
                summary["compliant_frameworks"] += 1
            else:
                summary["non_compliant_frameworks"] += 1
            
            total_score += result.get("overall_score", 0)
            all_gaps.extend(result.get("gaps", []))
            all_recommendations.extend(result.get("recommendations", []))
        
        summary["average_compliance_score"] = round(total_score / len(compliance_results), 2) if compliance_results else 0
        
        if summary["compliant_frameworks"] == summary["total_frameworks"]:
            summary["overall_compliance_status"] = "Fully Compliant"
        elif summary["compliant_frameworks"] > 0:
            summary["overall_compliance_status"] = "Partially Compliant"
        else:
            summary["overall_compliance_status"] = "Non-Compliant"
        
        # Get top gaps
        summary["key_gaps"] = all_gaps[:5]  # Top 5 gaps
        
        # Get unique recommendations
        summary["recommendations"] = list(set(all_recommendations))[:10]  # Top 10 unique recommendations
        
        return summary 