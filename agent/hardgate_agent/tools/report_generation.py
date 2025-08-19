"""
Report Generation Tool
Generates comprehensive security and compliance reports
"""

import os
import sys
import asyncio
import json
from datetime import datetime
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


class ReportGenerationTool(BaseTool):
    """Tool for generating comprehensive security and compliance reports"""
    
    name = "generate_report"
    description = "Generate comprehensive security and compliance reports in various formats including JSON, HTML, and Markdown"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Generate comprehensive report"""
        try:
            report_type = args.get("report_type", "comprehensive")
            analysis_data = args.get("analysis_data", {})
            output_format = args.get("output_format", "json")
            output_path = args.get("output_path")
            
            if not analysis_data:
                return {
                    "success": False,
                    "error": "Analysis data is required for report generation"
                }
            
            # Generate report based on type
            if report_type == "comprehensive":
                report = await self._generate_comprehensive_report(analysis_data)
            elif report_type == "executive":
                report = await self._generate_executive_report(analysis_data)
            elif report_type == "technical":
                report = await self._generate_technical_report(analysis_data)
            elif report_type == "compliance":
                report = await self._generate_compliance_report(analysis_data)
            else:
                report = await self._generate_comprehensive_report(analysis_data)
            
            # Format and save report
            formatted_report = await self._format_report(report, output_format)
            
            if output_path:
                await self._save_report(formatted_report, output_path, output_format)
            
            return {
                "success": True,
                "report_type": report_type,
                "output_format": output_format,
                "report": report,
                "formatted_report": formatted_report,
                "output_path": output_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Report generation failed: {str(e)}"
            }
    
    async def _generate_comprehensive_report(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate comprehensive security report"""
        report = {
            "report_metadata": self._generate_report_metadata(),
            "executive_summary": await self._generate_executive_summary(analysis_data),
            "repository_analysis": analysis_data.get("repository_analysis", {}),
            "security_scan": analysis_data.get("security_scan", {}),
            "gate_validation": analysis_data.get("gate_validation", {}),
            "evidence_collection": analysis_data.get("evidence_collection", {}),
            "security_analysis": analysis_data.get("security_analysis", {}),
            "compliance_check": analysis_data.get("compliance_check", {}),
            "llm_analysis": analysis_data.get("llm_analysis", {}),
            "recommendations": await self._generate_recommendations(analysis_data),
            "action_items": await self._generate_action_items(analysis_data),
            "appendix": await self._generate_appendix(analysis_data)
        }
        
        return report
    
    async def _generate_executive_report(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate executive summary report"""
        report = {
            "report_metadata": self._generate_report_metadata(),
            "executive_summary": await self._generate_executive_summary(analysis_data),
            "key_findings": await self._extract_key_findings(analysis_data),
            "risk_assessment": self._extract_risk_assessment(analysis_data),
            "compliance_status": self._extract_compliance_status(analysis_data),
            "recommendations": await self._generate_executive_recommendations(analysis_data),
            "next_steps": await self._generate_next_steps(analysis_data)
        }
        
        return report
    
    async def _generate_technical_report(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate technical detailed report"""
        report = {
            "report_metadata": self._generate_report_metadata(),
            "technical_summary": await self._generate_technical_summary(analysis_data),
            "detailed_analysis": {
                "repository_analysis": analysis_data.get("repository_analysis", {}),
                "security_scan": analysis_data.get("security_scan", {}),
                "gate_validation": analysis_data.get("gate_validation", {}),
                "evidence_collection": analysis_data.get("evidence_collection", {})
            },
            "vulnerability_details": await self._extract_vulnerability_details(analysis_data),
            "gate_details": await self._extract_gate_details(analysis_data),
            "technical_recommendations": await self._generate_technical_recommendations(analysis_data),
            "implementation_guide": await self._generate_implementation_guide(analysis_data)
        }
        
        return report
    
    async def _generate_compliance_report(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate compliance-focused report"""
        report = {
            "report_metadata": self._generate_report_metadata(),
            "compliance_summary": await self._generate_compliance_summary(analysis_data),
            "compliance_results": analysis_data.get("compliance_check", {}),
            "compliance_gaps": await self._extract_compliance_gaps(analysis_data),
            "remediation_plan": await self._generate_remediation_plan(analysis_data),
            "compliance_recommendations": await self._generate_compliance_recommendations(analysis_data),
            "audit_trail": await self._generate_audit_trail(analysis_data)
        }
        
        return report
    
    def _generate_report_metadata(self) -> dict:
        """Generate report metadata"""
        return {
            "report_id": f"SEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0",
            "tool_version": "HardGate Agent 1.0.0",
            "generator": "HardGate Analysis Agent"
        }
    
    async def _generate_executive_summary(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate executive summary"""
        # Extract key metrics
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        compliance_results = analysis_data.get("compliance_check", {}).get("compliance_results", {})
        
        # Calculate metrics
        total_gates = len(gate_results)
        passed_gates = len([g for g in gate_results if g.get("status") == "PASS"])
        failed_gates = len([g for g in gate_results if g.get("status") == "FAIL"])
        
        total_vulns = 0
        high_vulns = 0
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            total_vulns = vulns.get("total_vulnerabilities", 0)
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
        
        # Calculate compliance score
        compliance_score = 0
        if compliance_results:
            total_score = sum(result.get("overall_score", 0) for result in compliance_results.values())
            compliance_score = total_score / len(compliance_results)
        
        return {
            "overall_security_score": self._calculate_overall_security_score(analysis_data),
            "gate_compliance_rate": round((passed_gates / max(1, total_gates)) * 100, 2),
            "total_vulnerabilities": total_vulns,
            "critical_vulnerabilities": high_vulns,
            "compliance_score": round(compliance_score, 2),
            "risk_level": self._determine_overall_risk_level(analysis_data),
            "key_findings": await self._extract_key_findings(analysis_data),
            "critical_issues": await self._extract_critical_issues(analysis_data)
        }
    
    async def _extract_key_findings(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract key findings from analysis data"""
        findings = []
        
        # Gate validation findings
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        failed_gates = [g for g in gate_results if g.get("status") == "FAIL"]
        if failed_gates:
            findings.append(f"{len(failed_gates)} security gates failed validation")
        
        # Security scan findings
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            if high_vulns > 0:
                findings.append(f"{high_vulns} high severity vulnerabilities detected")
        
        # Evidence collection findings
        evidence_data = analysis_data.get("evidence_collection", {}).get("evidence_data", {})
        failed_evidence = sum(1 for data in evidence_data.values() if not data.get("success", False))
        if failed_evidence > 0:
            findings.append(f"{failed_evidence} evidence collection sources failed")
        
        return findings
    
    def _extract_risk_assessment(self, analysis_data: Dict[str, Any]) -> dict:
        """Extract risk assessment from analysis data"""
        risk_assessment = analysis_data.get("security_analysis", {}).get("analysis_results", {}).get("risk_assessment", {})
        
        return {
            "risk_level": risk_assessment.get("risk_level", "Unknown"),
            "risk_score": risk_assessment.get("risk_score", 0),
            "risk_factors": risk_assessment.get("risk_factors", []),
            "risk_mitigation": risk_assessment.get("risk_mitigation", [])
        }
    
    def _extract_compliance_status(self, analysis_data: Dict[str, Any]) -> dict:
        """Extract compliance status from analysis data"""
        compliance_results = analysis_data.get("compliance_check", {}).get("compliance_results", {})
        
        status_summary = {}
        for framework, result in compliance_results.items():
            status_summary[framework] = {
                "status": result.get("compliance_status", "Unknown"),
                "score": result.get("overall_score", 0)
            }
        
        return status_summary
    
    async def _generate_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive recommendations"""
        recommendations = []
        
        # Security analysis recommendations
        security_analysis = analysis_data.get("security_analysis", {}).get("analysis_results", {})
        if "security_recommendations" in security_analysis:
            recs = security_analysis["security_recommendations"]
            recommendations.extend(recs.get("priority_recommendations", []))
        
        # Compliance recommendations
        compliance_results = analysis_data.get("compliance_check", {}).get("compliance_results", {})
        for framework, result in compliance_results.items():
            if result.get("compliance_status") != "Compliant":
                recommendations.append({
                    "category": f"{framework} Compliance",
                    "priority": "High",
                    "recommendation": f"Achieve {framework} compliance",
                    "impact": "High",
                    "effort": "High"
                })
        
        # Gate-specific recommendations
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
        
        return recommendations
    
    async def _generate_action_items(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable items"""
        action_items = []
        
        # Critical vulnerabilities
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("vulnerabilities", [])
            for vuln in high_vulns[:5]:  # Top 5 critical vulnerabilities
                action_items.append({
                    "priority": "Critical",
                    "action": f"Fix {vuln.get('type', 'vulnerability')} in {vuln.get('file', 'unknown')}",
                    "deadline": "Immediate",
                    "owner": "Development Team",
                    "description": vuln.get("line_content", "")
                })
        
        # Failed gates
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        for gate in gate_results:
            if gate.get("status") == "FAIL":
                action_items.append({
                    "priority": "High",
                    "action": f"Implement {gate.get('gate_name')} gate requirements",
                    "deadline": "1 week",
                    "owner": "Development Team",
                    "description": f"Gate {gate.get('gate_name')} failed with score {gate.get('score', 0)}%"
                })
        
        return action_items
    
    async def _generate_appendix(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate report appendix"""
        return {
            "methodology": "This report was generated using the HardGate Analysis Agent with comprehensive security analysis tools",
            "tools_used": [
                "Repository Analysis Tool",
                "Security Scanning Tool",
                "Gate Validation Tool",
                "Evidence Collection Tool",
                "Security Analysis Tool",
                "Compliance Check Tool",
                "LLM Analysis Tool"
            ],
            "frameworks_referenced": [
                "SOC2",
                "ISO27001",
                "NIST Cybersecurity Framework",
                "Enterprise Security Standards"
            ],
            "glossary": {
                "Hard Gates": "Enterprise security requirements that must be met",
                "Compliance": "Adherence to security standards and frameworks",
                "Risk Assessment": "Evaluation of security risks and their impact",
                "Vulnerability": "Security weakness that could be exploited"
            }
        }
    
    def _calculate_overall_security_score(self, analysis_data: Dict[str, Any]) -> int:
        """Calculate overall security score (0-100)"""
        score = 100
        
        # Deduct for failed gates
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        failed_gates = len([g for g in gate_results if g.get("status") == "FAIL"])
        score -= failed_gates * 5  # 5 points per failed gate
        
        # Deduct for vulnerabilities
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            score -= high_vulns * 10  # 10 points per high vulnerability
        
        return max(0, score)
    
    def _determine_overall_risk_level(self, analysis_data: Dict[str, Any]) -> str:
        """Determine overall risk level"""
        risk_assessment = analysis_data.get("security_analysis", {}).get("analysis_results", {}).get("risk_assessment", {})
        return risk_assessment.get("risk_level", "Unknown")
    
    async def _extract_critical_issues(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract critical issues from analysis data"""
        issues = []
        
        # High severity vulnerabilities
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            if high_vulns > 0:
                issues.append(f"{high_vulns} critical vulnerabilities require immediate attention")
        
        # Failed critical gates
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        critical_gates = ["AUTHENTICATION", "AUTHORIZATION", "ALERTING_ACTIONABLE"]
        failed_critical = [g for g in gate_results if g.get("gate_name") in critical_gates and g.get("status") == "FAIL"]
        if failed_critical:
            issues.append(f"{len(failed_critical)} critical security gates failed")
        
        return issues
    
    async def _format_report(self, report: dict, output_format: str) -> str:
        """Format report for output"""
        if output_format == "json":
            return json.dumps(report, indent=2)
        elif output_format == "html":
            return await self._generate_html_report(report)
        elif output_format == "markdown":
            return await self._generate_markdown_report(report)
        else:
            return json.dumps(report, indent=2)
    
    async def _generate_html_report(self, report: dict) -> str:
        """Generate HTML report"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>HardGate Security Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .critical { border-left: 5px solid #ff0000; }
                .high { border-left: 5px solid #ff6600; }
                .medium { border-left: 5px solid #ffcc00; }
                .low { border-left: 5px solid #00cc00; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>HardGate Security Analysis Report</h1>
                <p>Generated: {generated_at}</p>
                <p>Report ID: {report_id}</p>
            </div>
        """.format(
            generated_at=report.get("report_metadata", {}).get("generated_at", ""),
            report_id=report.get("report_metadata", {}).get("report_id", "")
        )
        
        # Add sections
        if "executive_summary" in report:
            html += f"""
            <div class="section">
                <h2>Executive Summary</h2>
                <p>Overall Security Score: {report['executive_summary'].get('overall_security_score', 0)}%</p>
                <p>Risk Level: {report['executive_summary'].get('risk_level', 'Unknown')}</p>
            </div>
            """
        
        html += "</body></html>"
        return html
    
    async def _generate_markdown_report(self, report: dict) -> str:
        """Generate Markdown report"""
        md = f"""
        # HardGate Security Analysis Report
        
        **Report ID:** {report.get("report_metadata", {}).get("report_id", "")}  
        **Generated:** {report.get("report_metadata", {}).get("generated_at", "")}
        
        ## Executive Summary
        
        """
        
        if "executive_summary" in report:
            summary = report["executive_summary"]
            md += f"""
        - **Overall Security Score:** {summary.get('overall_security_score', 0)}%
        - **Risk Level:** {summary.get('risk_level', 'Unknown')}
        - **Gate Compliance Rate:** {summary.get('gate_compliance_rate', 0)}%
        - **Total Vulnerabilities:** {summary.get('total_vulnerabilities', 0)}
        - **Critical Vulnerabilities:** {summary.get('critical_vulnerabilities', 0)}
        
        """
        
        return md
    
    async def _save_report(self, formatted_report: str, output_path: str, output_format: str):
        """Save report to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_report)
        except Exception as e:
            print(f"Warning: Could not save report to {output_path}: {e}")
    
    # Additional helper methods for specific report types
    async def _generate_executive_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate executive-level recommendations"""
        recommendations = []
        
        # High-level recommendations based on analysis
        gate_results = analysis_data.get("gate_validation", {}).get("validation_results", [])
        failed_gates = len([g for g in gate_results if g.get("status") == "FAIL"])
        
        if failed_gates > 0:
            recommendations.append(f"Address {failed_gates} failed security gates")
        
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            high_vulns = vulns.get("severity_breakdown", {}).get("High", 0)
            if high_vulns > 0:
                recommendations.append(f"Fix {high_vulns} critical vulnerabilities")
        
        return recommendations
    
    async def _generate_next_steps(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate next steps"""
        return [
            "Review and prioritize security recommendations",
            "Create remediation plan for critical issues",
            "Implement immediate security fixes",
            "Schedule follow-up security assessment",
            "Establish ongoing security monitoring"
        ]
    
    async def _generate_technical_summary(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate technical summary"""
        return {
            "total_files_analyzed": analysis_data.get("repository_analysis", {}).get("structure", {}).get("total_files", 0),
            "technologies_detected": analysis_data.get("repository_analysis", {}).get("technologies", {}),
            "security_patterns_found": len(analysis_data.get("gate_validation", {}).get("validation_results", [])),
            "vulnerability_distribution": analysis_data.get("security_scan", {}).get("scan_results", {}).get("vulnerabilities", {}).get("severity_breakdown", {})
        }
    
    async def _extract_vulnerability_details(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed vulnerability information"""
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            return scan_results["vulnerabilities"].get("vulnerabilities", [])
        return []
    
    async def _extract_gate_details(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed gate information"""
        return analysis_data.get("gate_validation", {}).get("validation_results", [])
    
    async def _generate_technical_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate technical recommendations"""
        recommendations = []
        
        # Technical recommendations based on vulnerabilities
        scan_results = analysis_data.get("security_scan", {}).get("scan_results", {})
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"].get("vulnerabilities", [])
            for vuln in vulns:
                recommendations.append({
                    "type": "Vulnerability Fix",
                    "file": vuln.get("file", ""),
                    "line": vuln.get("line", 0),
                    "recommendation": vuln.get("recommendation", ""),
                    "severity": vuln.get("severity", "Low")
                })
        
        return recommendations
    
    async def _generate_implementation_guide(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate implementation guide"""
        return {
            "immediate_actions": [
                "Fix critical vulnerabilities",
                "Address failed security gates",
                "Implement missing security controls"
            ],
            "short_term_actions": [
                "Enhance monitoring and logging",
                "Implement automated security scanning",
                "Conduct security training"
            ],
            "long_term_actions": [
                "Establish security governance",
                "Implement DevSecOps practices",
                "Regular security assessments"
            ]
        }
    
    async def _generate_compliance_summary(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate compliance summary"""
        compliance_results = analysis_data.get("compliance_check", {}).get("compliance_results", {})
        
        summary = {
            "frameworks_checked": list(compliance_results.keys()),
            "compliant_frameworks": [],
            "non_compliant_frameworks": [],
            "overall_compliance_score": 0
        }
        
        total_score = 0
        for framework, result in compliance_results.items():
            if result.get("compliance_status") == "Compliant":
                summary["compliant_frameworks"].append(framework)
            else:
                summary["non_compliant_frameworks"].append(framework)
            total_score += result.get("overall_score", 0)
        
        if compliance_results:
            summary["overall_compliance_score"] = total_score / len(compliance_results)
        
        return summary
    
    async def _extract_compliance_gaps(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract compliance gaps"""
        compliance_results = analysis_data.get("compliance_check", {}).get("compliance_results", {})
        all_gaps = []
        
        for framework, result in compliance_results.items():
            gaps = result.get("gaps", [])
            for gap in gaps:
                gap["framework"] = framework
                all_gaps.append(gap)
        
        return all_gaps
    
    async def _generate_remediation_plan(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate remediation plan"""
        return {
            "immediate_remediation": [
                "Fix critical compliance gaps",
                "Address high-priority security issues",
                "Implement missing controls"
            ],
            "short_term_remediation": [
                "Achieve compliance for all frameworks",
                "Implement monitoring and alerting",
                "Establish audit trails"
            ],
            "long_term_remediation": [
                "Maintain ongoing compliance",
                "Regular compliance assessments",
                "Continuous improvement"
            ]
        }
    
    async def _generate_compliance_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations"""
        compliance_results = analysis_data.get("compliance_check", {}).get("compliance_results", {})
        recommendations = []
        
        for framework, result in compliance_results.items():
            if result.get("compliance_status") != "Compliant":
                recommendations.append(f"Achieve {framework} compliance")
        
        return recommendations
    
    async def _generate_audit_trail(self, analysis_data: Dict[str, Any]) -> dict:
        """Generate audit trail"""
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "tools_used": [
                "Repository Analysis Tool",
                "Security Scanning Tool",
                "Gate Validation Tool",
                "Evidence Collection Tool",
                "Security Analysis Tool",
                "Compliance Check Tool",
                "LLM Analysis Tool"
            ],
            "data_sources": [
                "Code Repository",
                "Security Scans",
                "External Evidence",
                "Compliance Frameworks"
            ]
        } 