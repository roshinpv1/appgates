#!/usr/bin/env python3
"""
HTML Report Service for CodeGates Scan Results
Uses the same template as the gates system
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from models.scan_models import ScanResult, GateResult, GateStatus


class HTMLReportService:
    """Service for generating HTML reports using the same template as gates"""
    
    def __init__(self):
        pass
    
    def generate_html_report(self, scan_result: ScanResult) -> str:
        """Generate HTML report that matches the gates report structure exactly"""
        
        # Extract project information using gates logic
        app_id = self._extract_app_id(scan_result.repo_url)
        project_name = self._extract_project_name(scan_result.repo_url)
        branch_name = scan_result.branch
        # Create display name with App Id, Repo Url, and Branch (same as gates)
        project_display_name = f"{app_id} - {project_name} ({branch_name})"
        
        # Calculate summary statistics
        total_gates = scan_result.total_gates
        passed_gates = scan_result.passed_gates
        failed_gates = scan_result.failed_gates
        partial_gates = scan_result.partial_gates
        skipped_gates = scan_result.skipped_gates
        
        # Calculate overall compliance score
        applicable_gates = total_gates - skipped_gates
        if applicable_gates > 0:
            overall_score = (passed_gates / applicable_gates) * 100
        else:
            overall_score = 0.0
        
        # Get timestamp
        timestamp = self._get_timestamp_formatted()
        
        # Report type display
        report_type_display = "Enhanced Scan"
        
        # Generate gates table HTML
        gates_table_html = self._generate_gates_table_html(scan_result.gate_results)
        
        # Generate the HTML template that matches gates exactly
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hard Gate Assessment ({report_type_display}) - {project_display_name}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script>
    function toggleDetails(button, detailsId) {{
        const details = document.getElementById(detailsId);
        const isExpanded = button.getAttribute('aria-expanded') === 'true';
        
        button.setAttribute('aria-expanded', !isExpanded);
        details.setAttribute('aria-hidden', isExpanded);
        
        // Smooth scroll to expanded content
        if (!isExpanded) {{
            setTimeout(() => {{
                details.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}, 100);
        }}
    }}
    </script>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{project_display_name}</h1>
            <div class="report-badge summary-badge">{report_type_display} Report</div>
            <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report</p>
        </div>
        
        <h2>Executive Summary</h2>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{total_gates}</div>
                <div class="stat-label">Total Gates Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{passed_gates}</div>
                <div class="stat-label">Gates Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{partial_gates}</div>
                <div class="stat-label">Partially Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{failed_gates}</div>
                <div class="stat-label">Not Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{skipped_gates}</div>
                <div class="stat-label">Not Applicable</div>
            </div>
        </div>
        
        <h3>Overall Compliance</h3>
        <div class="compliance-bar">
            <div class="compliance-fill" style="width: {overall_score:.1f}%"></div>
        </div>
        <p><strong>{overall_score:.1f}% Hard Gates Compliance</strong></p>
        <p style="color: #6b7280; font-size: 0.9em; margin-top: 5px;">
            <em>Percentage calculated based on {applicable_gates} applicable gates (excluding {skipped_gates} N/A gates)</em>
        </p>
        
        <h2>Hard Gates Analysis</h2>
        {gates_table_html}
        
        <footer style="margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p>Hard Gate Assessment {report_type_display} Report generated on {timestamp}</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html_template
    
    def _calculate_summary_stats(self, gate_results: List[GateResult]) -> Dict[str, int]:
        """Calculate summary statistics from gate results"""
        stats = {
            'total_gates': len(gate_results),
            'passed_gates': 0,
            'partial_gates': 0,
            'failed_gates': 0,
            'skipped_gates': 0
        }
        
        for gate in gate_results:
            if gate.status == GateStatus.PASS:
                stats['passed_gates'] += 1
            elif gate.status == GateStatus.PARTIAL:
                stats['partial_gates'] += 1
            elif gate.status == GateStatus.FAIL:
                stats['failed_gates'] += 1
            elif gate.status == GateStatus.SKIPPED:
                stats['skipped_gates'] += 1
        
        return stats
    
    def _calculate_overall_score(self, gate_results: List[GateResult]) -> float:
        """Calculate overall compliance score"""
        if not gate_results:
            return 0.0
        
        applicable_gates = [g for g in gate_results if g.status != GateStatus.SKIPPED]
        if not applicable_gates:
            return 0.0
        
        passed_gates = len([g for g in applicable_gates if g.status == GateStatus.PASS])
        partial_gates = len([g for g in applicable_gates if g.status == GateStatus.PARTIAL])
        
        # Count partial gates as 0.5
        total_score = passed_gates + (partial_gates * 0.5)
        return (total_score / len(applicable_gates)) * 100
    
    def _generate_gates_table_html(self, gate_results: List[GateResult]) -> str:
        """Generate gates table HTML that matches the gates report structure exactly"""
        
        if not gate_results:
            return "<p>No gate results available.</p>"
        
        # Define the actual gates in scope categories
        predefined_categories = {
            'Auditability': ['1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7'],
            'Error Handling': ['1.1', '1.3', '2.4'],
            'Availability': ['1.5', '1.12', '3.6', '3.9', '3.18'],
            'Testing': ['2']
        }
        
        # Group gates by predefined categories
        categories = {}
        for category_name, gate_ids in predefined_categories.items():
            categories[category_name] = []
            for gate in gate_results:
                if gate.gate_id in gate_ids:
                    categories[category_name].append(gate)
        
        # Also add any gates that don't match predefined categories
        unmatched_gates = []
        for gate in gate_results:
            matched = False
            for gate_ids in predefined_categories.values():
                if gate.gate_id in gate_ids:
                    matched = True
                    break
            if not matched:
                unmatched_gates.append(gate)
        
        if unmatched_gates:
            categories['Other'] = unmatched_gates
        
        html_parts = []
        html_parts.append('<div class="gates-analysis">')
        
        # Generate HTML for each category
        for category_name, gates in categories.items():
            if not gates:
                continue
                
            html_parts.append(f'''
                <div class="gate-category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-content">
                        <table class="gates-table">
                            <thead>
                                <tr>
                                    <th style="width: 80px">Gate #</th>
                                    <th>Practice</th>
                                    <th>Status</th>
                                    <th>Evidence</th>
                                    <th>Recommendation</th>
                                </tr>
                            </thead>
                            <tbody>''')
            
            # Generate rows for each gate in this category
            for i, gate in enumerate(gates):
                # Get status info
                status_class = self._get_status_class(gate.status)
                status_text = gate.status.value.upper()
                
                # Format evidence
                evidence = self._format_evidence(gate)
                
                # Get recommendation
                recommendation = self._get_recommendation(gate)
                
                # Generate the table row
                gate_html = f'''
                                    <tr>
                                        <td style="text-align: center">
                                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                                <button class="details-toggle" onclick="toggleDetails(this, 'details-{category_name.lower().replace(' ', '-')}-{gate.gate_id}-{i}')" aria-expanded="false" aria-label="Show details for {gate.gate_name}">+</button>
                                                <span style="font-weight: bold; color: #374151; font-size: 0.9em;">{gate.gate_id}</span>
                                            </div>
                                        </td>
                                        <td><strong>{gate.gate_name}</strong></td>
                                        <td><span class="status-{status_class}">{status_text}</span></td>
                                        <td>{evidence}</td>
                                        <td>{recommendation}</td>
                                    </tr>
                                    <tr id="details-{category_name.lower().replace(' ', '-')}-{gate.gate_id}-{i}" class="gate-details" aria-hidden="true">
                                        <td colspan="5" class="details-content">
                                            <h4>Gate Details</h4>
                                            <div class="metrics-grid">
                                                <div class="metric-card">
                                                    <strong>Expected Count:</strong> {gate.expected_count}
                                                </div>
                                                <div class="metric-card">
                                                    <strong>Actual Count:</strong> {gate.actual_count}
                                                </div>
                                                <div class="metric-card">
                                                    <strong>Threshold:</strong> {gate.threshold}
                                                </div>
                                                <div class="metric-card">
                                                    <strong>Confidence Score:</strong> {gate.confidence_score:.2f}
                                                </div>
                                            </div>
                                            <div class="gate-details-section">
                                                <h5>Reasoning</h5>
                                                <p>{gate.reasoning}</p>
                                            </div>
                                            {self._generate_patterns_html(gate.patterns_found)}
                                            {self._generate_gate_recommendations_html(gate.recommendations)}
                                        </td>
                                    </tr>'''
                
                html_parts.append(gate_html)
            
            html_parts.append('''
                            </tbody>
                        </table>
                    </div>
                </div>''')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _generate_patterns_html(self, patterns: List[str]) -> str:
        """Generate patterns found HTML"""
        if not patterns:
            return ""
        
        html = "<h4>Patterns Found</h4><ul>"
        for pattern in patterns[:10]:  # Limit to 10 patterns
            html += f"<li><code>{pattern}</code></li>"
        if len(patterns) > 10:
            html += f"<li><em>... and {len(patterns) - 10} more patterns</em></li>"
        html += "</ul>"
        return html
    
    def _generate_recommendations_html(self, recommendations: List[Any]) -> str:
        """Generate contextual recommendations HTML"""
        if not recommendations:
            return ""
        
        html = """
        <h2>Contextual Recommendations</h2>
        <div class="recommendations-section">
        """
        
        for i, rec in enumerate(recommendations[:10]):  # Limit to 10 recommendations
            # Handle both string recommendations (from gates) and object recommendations (from main scan)
            if isinstance(rec, str):
                # Simple string recommendation from gate
                html += f"""
                <div class="recommendation-card">
                    <h4>Recommendation {i+1}</h4>
                    <p>{rec}</p>
                    <div class="recommendation-meta">
                        <span class="recommendation-type">General</span>
                        <span class="recommendation-priority">MEDIUM</span>
                        <span class="recommendation-confidence">0.50</span>
                    </div>
                </div>
                """
            else:
                # Object recommendation with full structure
                try:
                    html += f"""
                    <div class="recommendation-card">
                        <h4>{getattr(rec, 'title', f'Recommendation {i+1}')}</h4>
                        <p>{getattr(rec, 'description', str(rec))}</p>
                        <div class="recommendation-meta">
                            <span class="recommendation-type">{getattr(rec, 'recommendation_type', 'General')}</span>
                            <span class="recommendation-priority">{getattr(rec, 'priority', 'MEDIUM')}</span>
                            <span class="recommendation-confidence">{getattr(rec, 'confidence_score', 0.5):.2f}</span>
                        </div>
                    </div>
                    """
                except Exception as e:
                    # Fallback for any other format
                    html += f"""
                    <div class="recommendation-card">
                        <h4>Recommendation {i+1}</h4>
                        <p>{str(rec)}</p>
                        <div class="recommendation-meta">
                            <span class="recommendation-type">General</span>
                            <span class="recommendation-priority">MEDIUM</span>
                            <span class="recommendation-confidence">0.50</span>
                        </div>
                    </div>
                    """
        
        html += "</div>"
        return html
    
    def _extract_category(self, gate_name: str) -> str:
        """Extract category from gate name"""
        if any(word in gate_name.upper() for word in ['SECURITY', 'AUTH', 'PASSWORD']):
            return 'Security'
        elif any(word in gate_name.upper() for word in ['PERFORMANCE', 'OPTIMIZATION']):
            return 'Performance'
        elif any(word in gate_name.upper() for word in ['QUALITY', 'STANDARD']):
            return 'Code Quality'
        else:
            return 'General'
    
    def _get_status_class(self, status: GateStatus) -> str:
        """Get CSS class for status"""
        if status == GateStatus.PASS:
            return 'pass'
        elif status == GateStatus.PARTIAL:
            return 'warning'
        elif status == GateStatus.FAIL:
            return 'fail'
        else:
            return 'not_applicable'
    
    def _get_risk_description(self, risk_score: float) -> str:
        """Get risk description based on score"""
        if risk_score <= 0.3:
            return "Low Risk - Good security posture"
        elif risk_score <= 0.6:
            return "Medium Risk - Some security concerns identified"
        else:
            return "High Risk - Significant security issues found"
    
    def _extract_app_id(self, repository_url: str) -> str:
        """Extract App Id from repository URL using /app-XYZ/ pattern. Returns XYZ or <APP> if not found."""
        import re
        try:
            # Remove .git if present
            if repository_url.endswith('.git'):
                repository_url = repository_url[:-4]
            # Find /app-XYZ or /app-XYZ/ in the path
            match = re.search(r"/app-([A-Za-z0-9_-]+)(/|$)", repository_url)
            if match:
                return match.group(1)
            else:
                return "APP ID"
        except Exception:
            return "APP ID"
    
    def _extract_project_name(self, repository_url: str) -> str:
        """Extract project name from repository URL"""
        try:
            # Handle various URL formats
            if repository_url.endswith('.git'):
                repository_url = repository_url[:-4]
            
            # Split by / and get the last part
            parts = repository_url.rstrip('/').split('/')
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
            elif len(parts) >= 1:
                return parts[-1]
            else:
                return "Repository Scan Results"
        except Exception:
            return "Repository Scan Results"
    
    def _get_timestamp_formatted(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    def _get_css_styles(self) -> str:
        """Get CSS styles that match the gates template"""
        return """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f3f4f6; }
        h1 { font-size: 2em; color: #1f2937; border-bottom: 3px solid #2563eb; padding-bottom: 15px; margin-bottom: 30px; }
        h2 { color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 40px; }
        h3 { color: #374151; margin-top: 30px; }
        
        /* Report Badge Styles */
        .report-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 15px;
        }
        .summary-badge { background: #059669; color: #fff; }
        
        /* Summary Stats */
        .summary-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .stat-card { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2563eb; }
        .stat-label { color: #6b7280; margin-top: 5px; }
        
        /* Compliance Bar */
        .compliance-bar { width: 100%; height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .compliance-fill { height: 100%; background: linear-gradient(90deg, #dc2626 0%, #d97706 50%, #059669 100%); transition: width 0.3s ease; }
        
        /* Risk Score */
        .risk-score { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; margin: 20px 0; }
        .risk-number { font-size: 3em; font-weight: bold; color: #dc2626; }
        .risk-label { color: #6b7280; margin-top: 5px; font-weight: 600; }
        .risk-description { color: #374151; margin-top: 10px; }
        
        /* Gates Analysis Styling */
        .gates-analysis { margin-top: 30px; }
        .gate-category-section { margin-bottom: 40px; }
        .category-title {
            color: #1f2937;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }
        .category-content {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        /* Table Styles */
        table { width: 100%; border-collapse: collapse; margin: 0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #2563eb; color: #fff; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        tr:hover { background: #f9fafb; }
        
        /* Status Styles */
        .status-pass { color: #059669 !important; background: #ecfdf5; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-warning { color: #d97706 !important; background: #fffbeb; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-fail { color: #dc2626 !important; background: #fef2f2; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-not_applicable { color: #6b7280 !important; background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        
        /* Expandable Details Styling */
        .details-toggle {
            background: none;
            border: none;
            color: #2563eb;
            cursor: pointer;
            padding: 4px 8px;
            font-size: 1.1em;
            transition: transform 0.2s;
        }
        .details-toggle:hover { color: #1d4ed8; }
        .details-toggle[aria-expanded="true"] { transform: rotate(45deg); }
        
        .gate-details {
            display: none;
            background: #f8fafc;
            border-top: 1px solid #e5e7eb;
            padding: 0;
            margin: 0;
        }
        .gate-details[aria-hidden="false"] { display: table-row; }
        
        .details-content {
            padding: 16px;
            color: #4b5563;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }
        
        .metric-card {
            background: white;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
        }
        
        /* Recommendations */
        .recommendations-section { margin-top: 30px; }
        .recommendation-card {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        .recommendation-meta {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .recommendation-type, .recommendation-priority, .recommendation-confidence {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 500;
        }
        .recommendation-type { background: #e0f2fe; color: #0277bd; }
        .recommendation-priority { background: #fff3e0; color: #f57c00; }
        .recommendation-confidence { background: #f3e5f5; color: #7b1fa2; }
        """

    def _format_evidence(self, gate: GateResult) -> str:
        """Format evidence for gate display"""
        if gate.actual_count > 0:
            return f"{gate.actual_count} implementations found"
        else:
            return "No implementations found"
    
    def _get_recommendation(self, gate: GateResult) -> str:
        """Get recommendation for gate display"""
        if gate.status == GateStatus.PASS:
            return "Good implementation"
        elif gate.status == GateStatus.PARTIAL:
            return "Enhance implementation"
        elif gate.status == GateStatus.FAIL:
            return "Implement required"
        else:
            return "Not applicable"
    
    def _generate_gate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate recommendations HTML for gate details"""
        if not recommendations:
            return ""
        
        html = """
                                            <div class="gate-details-section">
                                                <h5>Recommendations</h5>
                                                <ul>"""
        
        for rec in recommendations[:5]:  # Limit to 5 recommendations
            html += f"<li>{rec}</li>"
        
        if len(recommendations) > 5:
            html += f"<li><em>... and {len(recommendations) - 5} more recommendations</em></li>"
        
        html += """
                                                </ul>
                                            </div>"""
        
        return html
