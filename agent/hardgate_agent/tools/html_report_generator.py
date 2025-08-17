"""
HTML Report Generator Tool
Creates comprehensive, interactive HTML reports for hard gate validation results
"""

import os
import sys
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
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


class HTMLReportGenerator:
    """Generates comprehensive HTML reports for hard gate validation results"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
    
    def generate_html_report(self, analysis_data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive HTML report"""
        try:
            # Extract data from analysis
            repository_analysis = analysis_data.get("repository_analysis", {})
            gate_validation = analysis_data.get("gate_validation", {})
            security_scan = analysis_data.get("security_scan", {})
            compliance_check = analysis_data.get("compliance_check", {})
            evidence_collection = analysis_data.get("evidence_collection", {})
            
            # Generate HTML content
            html_content = self._generate_html_content(
                repository_analysis, gate_validation, security_scan, 
                compliance_check, evidence_collection
            )
            
            # Save to file if output path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            return {
                "success": True,
                "html_content": html_content,
                "output_path": output_path,
                "report_size": len(html_content)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"HTML report generation failed: {str(e)}"
            }
    
    def _generate_html_content(self, repository_analysis: Dict[str, Any], 
                              gate_validation: Dict[str, Any], security_scan: Dict[str, Any],
                              compliance_check: Dict[str, Any], evidence_collection: Dict[str, Any]) -> str:
        """Generate the complete HTML content"""
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(gate_validation, security_scan, compliance_check)
        
        # Generate gate cards
        gate_cards = self._generate_gate_cards(gate_validation.get("validation_results", []))
        
        # Generate metrics
        metrics = self._generate_metrics(repository_analysis, gate_validation, security_scan, compliance_check)
        
        # Generate compliance summary
        compliance_summary = self._generate_compliance_summary(compliance_check)
        
        # Generate security summary
        security_summary = self._generate_security_summary(security_scan)
        
        # Generate evidence summary
        evidence_summary = self._generate_evidence_summary(evidence_collection)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hard Gates Security Analysis Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #0d6efd;
            --success-color: #198754;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #0dcaf0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
        }}
        
        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .app-header {{
            background: linear-gradient(135deg, var(--primary-color), #0056b3);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .app-title {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .app-subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .score-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .score-circle {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 2.5rem;
            font-weight: bold;
            color: white;
            position: relative;
        }}
        
        .score-excellent {{ background: linear-gradient(135deg, var(--success-color), #20c997); }}
        .score-good {{ background: linear-gradient(135deg, var(--info-color), #17a2b8); }}
        .score-warning {{ background: linear-gradient(135deg, var(--warning-color), #fd7e14); }}
        .score-danger {{ background: linear-gradient(135deg, var(--danger-color), #e83e8c); }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #6c757d;
            font-size: 0.9rem;
        }}
        
        .gates-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .gates-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .gate-card {{
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .gate-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .gate-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .gate-name {{
            font-weight: bold;
            font-size: 1.1rem;
        }}
        
        .gate-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        
        .status-pass {{ background-color: #d1e7dd; color: #0f5132; }}
        .status-fail {{ background-color: #f8d7da; color: #721c24; }}
        .status-warning {{ background-color: #fff3cd; color: #856404; }}
        
        .gate-score {{
            font-size: 1.5rem;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .gate-description {{
            color: #6c757d;
            margin-bottom: 15px;
            font-size: 0.9rem;
        }}
        
        .gate-evidence {{
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 0.85rem;
        }}
        
        .gate-recommendations {{
            margin-top: 15px;
        }}
        
        .recommendation-item {{
            background-color: #e7f3ff;
            border-left: 4px solid var(--primary-color);
            padding: 8px 12px;
            margin-bottom: 5px;
            font-size: 0.85rem;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
        }}
        
        .summary-section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .main-container {{
                padding: 10px;
            }}
            
            .app-title {{
                font-size: 2rem;
            }}
            
            .gates-grid {{
                grid-template-columns: 1fr;
            }}
            
            .metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Header -->
        <div class="app-header">
            <h1 class="app-title">
                <i class="fas fa-shield-alt"></i>
                Hard Gates Security Analysis
            </h1>
            <p class="app-subtitle">Enterprise-grade code security validation report</p>
            <p class="mb-0">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <!-- Overall Score -->
        <div class="score-card">
            <div class="score-circle {self._get_score_class(overall_score)}">
                {overall_score:.1f}%
            </div>
            <h2>Overall Security Score</h2>
            <p class="text-muted">Based on hard gate validation, security scanning, and compliance checks</p>
        </div>
        
        <!-- Metrics Grid -->
        <div class="metrics-grid">
            {metrics}
        </div>
        
        <!-- Gates Analysis -->
        <div class="gates-container">
            <h2 class="section-title">
                <i class="fas fa-shield-alt"></i>
                Hard Gates Analysis
            </h2>
            <div class="gates-grid">
                {gate_cards}
            </div>
        </div>
        
        <!-- Security Summary -->
        <div class="summary-section">
            <h2 class="section-title">
                <i class="fas fa-bug"></i>
                Security Analysis Summary
            </h2>
            {security_summary}
        </div>
        
        <!-- Compliance Summary -->
        <div class="summary-section">
            <h2 class="section-title">
                <i class="fas fa-certificate"></i>
                Compliance Summary
            </h2>
            {compliance_summary}
        </div>
        
        <!-- Evidence Summary -->
        <div class="summary-section">
            <h2 class="section-title">
                <i class="fas fa-search"></i>
                Evidence Collection Summary
            </h2>
            {evidence_summary}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Report generated by Hard Gates Security Analysis Agent</p>
            <p>For questions or support, contact your security team</p>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Add interactive features
        document.addEventListener('DOMContentLoaded', function() {{
            // Add click handlers for gate cards
            document.querySelectorAll('.gate-card').forEach(card => {{
                card.addEventListener('click', function() {{
                    // Toggle detailed view
                    const evidence = this.querySelector('.gate-evidence');
                    if (evidence) {{
                        evidence.style.display = evidence.style.display === 'none' ? 'block' : 'none';
                    }}
                }});
            }});
            
            // Add smooth scrolling
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({{
                        behavior: 'smooth'
                    }});
                }});
            }});
        }});
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _calculate_overall_score(self, gate_validation: Dict[str, Any], 
                                security_scan: Dict[str, Any], 
                                compliance_check: Dict[str, Any]) -> float:
        """Calculate overall security score"""
        scores = []
        
        # Gate validation score
        if gate_validation.get("validation_results"):
            gate_scores = [gate.get("score", 0) for gate in gate_validation["validation_results"]]
            if gate_scores:
                scores.append(sum(gate_scores) / len(gate_scores))
        
        # Security scan score (inverse of vulnerabilities)
        if security_scan.get("scan_results"):
            vulns = security_scan["scan_results"].get("vulnerabilities", {})
            total_vulns = vulns.get("total_vulnerabilities", 0)
            if total_vulns > 0:
                # Convert vulnerabilities to score (fewer vulns = higher score)
                vuln_score = max(0, 100 - (total_vulns * 5))
                scores.append(vuln_score)
        
        # Compliance score
        if compliance_check.get("compliance_results"):
            compliance_scores = []
            for framework, result in compliance_check["compliance_results"].items():
                if isinstance(result, dict) and "overall_score" in result:
                    compliance_scores.append(result["overall_score"])
            if compliance_scores:
                scores.append(sum(compliance_scores) / len(compliance_scores))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_score_class(self, score: float) -> str:
        """Get CSS class for score styling"""
        if score >= 90:
            return "score-excellent"
        elif score >= 75:
            return "score-good"
        elif score >= 60:
            return "score-warning"
        else:
            return "score-danger"
    
    def _generate_metrics(self, repository_analysis: Dict[str, Any], 
                         gate_validation: Dict[str, Any], 
                         security_scan: Dict[str, Any],
                         compliance_check: Dict[str, Any]) -> str:
        """Generate metrics cards"""
        metrics = []
        
        # Repository metrics
        if repository_analysis:
            metrics.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{repository_analysis.get('analysis', {}).get('structure', {}).get('total_files', 0)}</div>
                    <div class="metric-label">Total Files</div>
                </div>
            """)
            
            metrics.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{len(repository_analysis.get('analysis', {}).get('technologies', {}).get('programming_languages', []))}</div>
                    <div class="metric-label">Languages</div>
                </div>
            """)
        
        # Gate validation metrics
        if gate_validation.get("validation_results"):
            passed_gates = len([g for g in gate_validation["validation_results"] if g.get("status") == "PASS"])
            total_gates = len(gate_validation["validation_results"])
            
            metrics.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{passed_gates}/{total_gates}</div>
                    <div class="metric-label">Gates Passed</div>
                </div>
            """)
        
        # Security metrics
        if security_scan.get("scan_results"):
            vulns = security_scan["scan_results"].get("vulnerabilities", {})
            total_vulns = vulns.get("total_vulnerabilities", 0)
            
            metrics.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{total_vulns}</div>
                    <div class="metric-label">Vulnerabilities</div>
                </div>
            """)
        
        # Compliance metrics
        if compliance_check.get("compliance_results"):
            compliant_frameworks = 0
            total_frameworks = len(compliance_check["compliance_results"])
            for framework, result in compliance_check["compliance_results"].items():
                if isinstance(result, dict) and result.get("compliance_status") == "Compliant":
                    compliant_frameworks += 1
            
            metrics.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{compliant_frameworks}/{total_frameworks}</div>
                    <div class="metric-label">Compliant Frameworks</div>
                </div>
            """)
        
        return "".join(metrics)
    
    def _generate_gate_cards(self, validation_results: List[Dict[str, Any]]) -> str:
        """Generate gate cards HTML"""
        if not validation_results:
            return '<p class="text-muted">No gate validation results available.</p>'
        
        cards = []
        for gate in validation_results:
            status_class = f"status-{gate.get('status', 'unknown').lower()}"
            status_text = gate.get('status', 'UNKNOWN')
            
            evidence_html = ""
            if gate.get("evidence"):
                evidence_items = []
                for evidence in gate["evidence"][:3]:  # Show first 3 evidence items
                    evidence_items.append(f"<div>• {evidence.get('description', 'Evidence found')}</div>")
                evidence_html = f"""
                    <div class="gate-evidence">
                        <strong>Evidence:</strong>
                        {''.join(evidence_items)}
                    </div>
                """
            
            recommendations_html = ""
            if gate.get("recommendations"):
                rec_items = []
                for rec in gate["recommendations"][:3]:  # Show first 3 recommendations
                    rec_items.append(f'<div class="recommendation-item">{rec}</div>')
                recommendations_html = f"""
                    <div class="gate-recommendations">
                        <strong>Recommendations:</strong>
                        {''.join(rec_items)}
                    </div>
                """
            
            cards.append(f"""
                <div class="gate-card">
                    <div class="gate-header">
                        <div class="gate-name">{gate.get('display_name', gate.get('gate_name', 'Unknown Gate'))}</div>
                        <span class="gate-status {status_class}">{status_text}</span>
                    </div>
                    <div class="gate-score">{gate.get('score', 0):.1f}%</div>
                    <div class="gate-description">{gate.get('description', 'No description available')}</div>
                    {evidence_html}
                    {recommendations_html}
                </div>
            """)
        
        return "".join(cards)
    
    def _generate_security_summary(self, security_scan: Dict[str, Any]) -> str:
        """Generate security summary HTML"""
        if not security_scan:
            return '<p class="text-muted">No security scan results available.</p>'
        
        scan_results = security_scan.get("scan_results", {})
        
        summary_html = '<div class="row">'
        
        # Vulnerabilities summary
        if "vulnerabilities" in scan_results:
            vulns = scan_results["vulnerabilities"]
            total_vulns = vulns.get("total_vulnerabilities", 0)
            severity_breakdown = vulns.get("severity_breakdown", {})
            
            summary_html += f"""
                <div class="col-md-6">
                    <h4>Vulnerabilities</h4>
                    <p><strong>Total:</strong> {total_vulns}</p>
                    <ul>
                        <li>High: {severity_breakdown.get('High', 0)}</li>
                        <li>Medium: {severity_breakdown.get('Medium', 0)}</li>
                        <li>Low: {severity_breakdown.get('Low', 0)}</li>
                    </ul>
                </div>
            """
        
        # Security analysis summary
        if "security_analysis" in scan_results:
            sec_analysis = scan_results["security_analysis"]
            summary_html += f"""
                <div class="col-md-6">
                    <h4>Security Analysis</h4>
                    <p><strong>Risk Level:</strong> {sec_analysis.get('risk_level', 'Unknown')}</p>
                    <p><strong>Security Score:</strong> {sec_analysis.get('security_score', 0)}%</p>
                </div>
            """
        
        summary_html += '</div>'
        return summary_html
    
    def _generate_compliance_summary(self, compliance_check: Dict[str, Any]) -> str:
        """Generate compliance summary HTML"""
        if not compliance_check:
            return '<p class="text-muted">No compliance check results available.</p>'
        
        compliance_results = compliance_check.get("compliance_results", {})
        
        if not compliance_results:
            return '<p class="text-muted">No compliance results available.</p>'
        
        summary_html = '<div class="row">'
        
        for framework, result in compliance_results.items():
            if isinstance(result, dict):
                status = result.get("compliance_status", "Unknown")
                score = result.get("overall_score", 0)
                status_class = "text-success" if status == "Compliant" else "text-danger"
                
                summary_html += f"""
                    <div class="col-md-4 mb-3">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">{framework}</h5>
                                <p class="card-text">
                                    <strong>Status:</strong> <span class="{status_class}">{status}</span><br>
                                    <strong>Score:</strong> {score:.1f}%
                                </p>
                            </div>
                        </div>
                    </div>
                """
        
        summary_html += '</div>'
        return summary_html
    
    def _generate_evidence_summary(self, evidence_collection: Dict[str, Any]) -> str:
        """Generate evidence collection summary HTML"""
        if not evidence_collection:
            return '<p class="text-muted">No evidence collection results available.</p>'
        
        evidence_data = evidence_collection.get("evidence_data", {})
        
        if not evidence_data:
            return '<p class="text-muted">No evidence data available.</p>'
        
        summary_html = '<div class="row">'
        
        for source, data in evidence_data.items():
            if isinstance(data, dict):
                success = data.get("success", False)
                total_results = data.get("total_results", 0)
                status_class = "text-success" if success else "text-danger"
                status_text = "Success" if success else "Failed"
                
                summary_html += f"""
                    <div class="col-md-4 mb-3">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">{source.title()}</h5>
                                <p class="card-text">
                                    <strong>Status:</strong> <span class="{status_class}">{status_text}</span><br>
                                    <strong>Results:</strong> {total_results}
                                </p>
                            </div>
                        </div>
                    </div>
                """
        
        summary_html += '</div>'
        return summary_html


class HTMLReportGeneratorTool(BaseTool):
    """Tool for generating comprehensive HTML reports"""
    
    name = "html_report_generator"
    description = "Generate comprehensive, interactive HTML reports for hard gate validation results"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
        self.generator = HTMLReportGenerator()
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Generate HTML report"""
        try:
            analysis_data = args.get("analysis_data", {})
            output_path = args.get("output_path")
            
            if not analysis_data:
                return {
                    "success": False,
                    "error": "Analysis data is required"
                }
            
            result = self.generator.generate_html_report(analysis_data, output_path)
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": f"HTML report generation failed: {str(e)}"
            }


# Create wrapper function for Google ADK compatibility
def html_report_generator(analysis_data: Dict[str, Any], output_path: Optional[str] = None, 
                         tool_context = None) -> Dict[str, Any]:
    """
    Generate comprehensive, interactive HTML reports for hard gate validation results.
    
    Args:
        analysis_data: Complete analysis data from all tools
        output_path: Optional path to save the HTML file
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing HTML report generation results
    """
    try:
        if not analysis_data:
            return {
                "success": False,
                "error": "Analysis data is required"
            }
        
        generator = HTMLReportGenerator()
        result = generator.generate_html_report(analysis_data, output_path)
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"HTML report generation failed: {str(e)}"
        } 