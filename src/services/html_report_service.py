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
        
        # Generate project summary from vector database
        project_summary_html = self._generate_project_summary_html(scan_result)
        
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
            <div class="report-badge summary-badge">Hard Gate Assessment Report {timestamp}</div>
            <h1>{project_display_name}</h1>
            
        </div>
        
        <h2>Executive Summary</h2>
        
        <div class="hard-gates-notice" style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
            <h3 style="color: #92400e; margin-top: 0; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5em;">⚠️</span>
                Hard Gates Assessment - Primary Focus
            </h3>
            <p style="color: #92400e; margin-bottom: 0; font-weight: 500;">
                This report focuses on the evaluation of <strong>16 critical hard gates</strong> across Auditability, Error Handling, Availability, and Testing categories. 
                These gates represent the primary compliance requirements and must be addressed for production deployment.
            </p>
        </div>
        
        {project_summary_html}
        
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
        """Generate gates table HTML with hard gates as primary focus"""
        
        if not gate_results:
            return "<p>No gate results available.</p>"
        
        # Get hard gates and predefined categories from centralized registry
        from models.gate_definitions import get_hard_gate_ids, get_predefined_categories, get_gate
        
        hard_gate_ids = set(get_hard_gate_ids())
        predefined_categories = get_predefined_categories()
        
        # Group gates by predefined categories, prioritizing hard gates
        categories = {}
        for category_name, gate_ids in predefined_categories.items():
            categories[category_name] = []
            for gate in gate_results:
                if gate.gate_id in gate_ids:
                    # Mark hard gates for special emphasis
                    gate.is_hard_gate = gate.gate_id in hard_gate_ids
                    categories[category_name].append(gate)
        
        # Sort gates within each category to prioritize hard gates first
        for category_name in categories:
            categories[category_name].sort(key=lambda x: (not getattr(x, 'is_hard_gate', False), x.gate_id))
        
        # Filter out gates that don't match predefined categories (only show hard gates)
        # unmatched_gates = []
        # for gate in gate_results:
        #     matched = False
        #     for gate_ids in predefined_categories.values():
        #         if gate.gate_id in gate_ids:
        #             matched = True
        #             break
        #     if not matched:
        #         gate.is_hard_gate = False
        #         unmatched_gates.append(gate)
        # 
        # if unmatched_gates:
        #     categories['Other'] = unmatched_gates
        
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
                
                # Check if this is a hard gate for special styling
                is_hard_gate = getattr(gate, 'is_hard_gate', False)
                hard_gate_class = "hard-gate-row" if is_hard_gate else ""
                hard_gate_badge = '<span class="hard-gate-badge">HARD GATE</span>' if is_hard_gate else ""
                
                # Generate the table row
                gate_html = f'''
                                    <tr class="{hard_gate_class}">
                                        <td style="text-align: center">
                                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                                <button class="details-toggle" onclick="toggleDetails(this, 'details-{category_name.lower().replace(' ', '-')}-{gate.gate_id}-{i}')" aria-expanded="false" aria-label="Show details for {gate.gate_name}">+</button>
                                                <span style="font-weight: bold; color: #374151; font-size: 0.9em;">{gate.gate_id}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <div style="display: flex; align-items: center; gap: 8px;">
                                                <strong>{gate.gate_name}</strong>
                                                {hard_gate_badge}
                                            </div>
                                        </td>
                                        <td><span class="status-{status_class}">{status_text}</span></td>
                                        <td>{evidence}</td>
                                        <td>{recommendation}</td>
                                    </tr>
                                    <tr id="details-{category_name.lower().replace(' ', '-')}-{gate.gate_id}-{i}" class="gate-details {hard_gate_class}" aria-hidden="true">
                                        <td colspan="5" class="details-content">
                                            <h4>Gate Details {hard_gate_badge}</h4>
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
                                            {self._generate_detailed_pattern_matches_html(gate)}
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
    
    def _generate_detailed_pattern_matches_html(self, gate_result) -> str:
        """Generate detailed pattern matches table HTML"""
        if not hasattr(gate_result, 'detailed_matches') or not gate_result.detailed_matches:
            return ""
        
        # Limit to first 20 matches to avoid overwhelming the report
        matches = gate_result.detailed_matches[:20]
        
        html = """
        <h4>Detailed Pattern Matches</h4>
        <div style="max-height: 300px; overflow-y: auto; overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb;">
            <table style="width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.9em;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 350px; white-space: pre-line;">File</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 80px; white-space: pre-line;">Line</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 250px; white-space: pre-line;">Pattern Match</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; max-width: 250px; white-space: pre-line;">Actual Pattern</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for match in matches:
            # Truncate match text if too long
            match_text = match.match_text
            if len(match_text) > 200:
                match_text = match_text[:200] + "..."
            
            # Escape HTML in match text
            match_text = match_text.replace('<', '&lt;').replace('>', '&gt;')
            
            html += f"""
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; color: #1f2937; word-break: break-all; max-width: 350px; white-space: pre-line;">{match.file_path}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center; color: #6b7280; word-break: break-all; max-width: 80px; white-space: pre-line;">{match.line_number}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; color: #059669; background: #ecfdf5; border-radius: 3px; word-break: break-all; max-width: 250px; white-space: pre-line;">{match_text}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; color: #374151; background: #f3f4f6; border-radius: 3px; word-break: break-all; max-width: 250px; white-space: pre-line;">{match.pattern}</td>
                    </tr>
            """
        
        if len(gate_result.detailed_matches) > 20:
            html += f"""
                    <tr>
                        <td colspan="4" style="padding: 8px; text-align: center; color: #6b7280; font-style: italic;">
                            ... and {len(gate_result.detailed_matches) - 20} more matches
                        </td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
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
        
        /* Hard Gate Styling */
        .hard-gate-row {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 4px solid #f59e0b;
        }
        .hard-gate-row:hover {
            background: linear-gradient(135deg, #fde68a 0%, #fbbf24 100%);
        }
        .hard-gate-badge {
            background: #dc2626;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .hard-gate-row .details-content {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }
        
        /* Project Summary Styling */
        .project-summary-section {
            background: #fff;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        .project-description {
            color: #374151;
            line-height: 1.6;
            margin-bottom: 20px;
            font-size: 1.1em;
        }
        
        .project-details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .detail-card {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 15px;
        }
        
        .detail-card h4 {
            color: #1f2937;
            margin: 0 0 10px 0;
            font-size: 1em;
            font-weight: 600;
        }
        
        .tech-tags, .file-type-tags, .dependency-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        
        .tech-tag, .file-type-tag, .dependency-tag {
            background: #2563eb;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .file-type-tag {
            background: #059669;
        }
        
        .dependency-tag {
            background: #7c3aed;
        }
        
        .no-data {
            color: #6b7280;
            font-style: italic;
            font-size: 0.9em;
        }
        
        .stats-info {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.9em;
        }
        
        .stat-value {
            color: #1f2937;
            font-weight: 600;
        }
        
        /* Enhanced Project Summary Styling */
        .tech-stack-info, .architecture-info, .practices-info, .infrastructure-info {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .tech-item, .arch-item, .practice-item, .infra-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .tech-item strong, .arch-item strong, .practice-item strong, .infra-item strong {
            color: #374151;
            font-size: 0.9em;
        }
        
        .features-list, .recommendations-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .feature-item, .recommendation-item {
            color: #374151;
            font-size: 0.9em;
            line-height: 1.4;
            padding: 4px 0;
        }
        
        .recommendations-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }
        
        .recommendations-section h4 {
            color: #1f2937;
            margin: 0 0 10px 0;
            font-size: 1.1em;
            font-weight: 600;
        }
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
    
    def _generate_project_summary_html(self, scan_result: ScanResult) -> str:
        """Generate project summary HTML section from LLM-based analysis"""
        try:
            # Get project summary from scan metadata (pre-generated during scan)
            project_info = scan_result.metadata.get("project_summary")
            
            # If not available, return fallback
            if not project_info:
                return self._generate_fallback_project_summary_html(scan_result)
            
            # Create HTML for enhanced LLM-based project summary section
            html = f"""
        <h2>Project Summary</h2>
        
        <div class="project-summary-section">
            <div class="summary-content">
                <p class="project-description">{project_info.get('summary', 'Project analysis completed.')}</p>
            </div>
            
            <div class="project-details-grid">
                <div class="detail-card">
                    <h4>Technology Stack</h4>
                    <div class="tech-stack-info">
                        <div class="tech-item">
                            <strong>Primary Language:</strong> {project_info.get('technology_stack', {}).get('primary_language', 'Unknown')}
                        </div>
                        <div class="tech-item">
                            <strong>Frameworks:</strong>
                            <div class="tech-tags">
                                {self._generate_tech_tags_html(project_info.get('technology_stack', {}).get('frameworks', []))}
                            </div>
                        </div>
                        <div class="tech-item">
                            <strong>Build Tools:</strong>
                            <div class="tech-tags">
                                {self._generate_tech_tags_html(project_info.get('technology_stack', {}).get('build_tools', []))}
                            </div>
                        </div>
                        <div class="tech-item">
                            <strong>Databases:</strong>
                            <div class="tech-tags">
                                {self._generate_tech_tags_html(project_info.get('technology_stack', {}).get('databases', []))}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="detail-card">
                    <h4>Architecture & Design</h4>
                    <div class="architecture-info">
                        <div class="arch-item">
                            <strong>Pattern:</strong> {project_info.get('architecture', {}).get('pattern', 'Unknown')}
                        </div>
                        <div class="arch-item">
                            <strong>Layers:</strong>
                            <div class="tech-tags">
                                {self._generate_tech_tags_html(project_info.get('architecture', {}).get('layers', []))}
                            </div>
                        </div>
                        <div class="arch-item">
                            <strong>Application Type:</strong> {project_info.get('application_type', 'Unknown')}
                        </div>
                    </div>
                </div>
                
                <div class="detail-card">
                    <h4>Key Features</h4>
                    <div class="features-list">
                        {self._generate_features_html(project_info.get('key_features', []))}
                    </div>
                </div>
                
                <div class="detail-card">
                    <h4>Development Practices</h4>
                    <div class="practices-info">
                        <div class="practice-item">
                            <strong>Testing:</strong> {project_info.get('development_practices', {}).get('testing', 'Unknown')}
                        </div>
                        <div class="practice-item">
                            <strong>Logging:</strong> {project_info.get('development_practices', {}).get('logging', 'Unknown')}
                        </div>
                        <div class="practice-item">
                            <strong>Security:</strong> {project_info.get('development_practices', {}).get('security', 'Unknown')}
                        </div>
                    </div>
                </div>
                
                <div class="detail-card">
                    <h4>Infrastructure</h4>
                    <div class="infrastructure-info">
                        <div class="infra-item">
                            <strong>Deployment:</strong> {project_info.get('infrastructure', {}).get('deployment', 'Unknown')}
                        </div>
                        <div class="infra-item">
                            <strong>Monitoring:</strong> {project_info.get('infrastructure', {}).get('monitoring', 'Unknown')}
                        </div>
                        <div class="infra-item">
                            <strong>Scalability:</strong> {project_info.get('infrastructure', {}).get('scalability', 'Unknown')}
                        </div>
                    </div>
                </div>
                
                <div class="detail-card">
                    <h4>Analysis Stats</h4>
                    <div class="stats-info">
                        <div class="stat-item">
                            <span class="stat-label">Files Analyzed:</span>
                            <span class="stat-value">{project_info.get('vector_analysis', {}).get('total_files_analyzed', 0)}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Java Files:</span>
                            <span class="stat-value">{project_info.get('vector_analysis', {}).get('java_files_analyzed', 0)}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Config Files:</span>
                            <span class="stat-value">{project_info.get('vector_analysis', {}).get('config_files_analyzed', 0)}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Analysis Time:</span>
                            <span class="stat-value">{project_info.get('analysis_timestamp', 'Unknown')}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="recommendations-section">
                <h4>Recommendations</h4>
                <div class="recommendations-list">
                    {self._generate_recommendations_html(project_info.get('recommendations', []))}
                </div>
            </div>
        </div>
"""
            
            return html
            
        except Exception as e:
            print(f"⚠️ Failed to generate project summary HTML: {e}")
            return self._generate_fallback_project_summary_html(scan_result)
    
    def _generate_fallback_project_summary_html(self, scan_result: ScanResult) -> str:
        """Generate fallback project summary HTML"""
        return f"""
        <h2>Project Summary</h2>
        
        <div class="project-summary-section">
            <div class="summary-content">
                <p class="project-description">Project analysis for {scan_result.repo_url}. The codebase has been analyzed for compliance with hard gates across auditability, error handling, availability, and testing categories. Detailed analysis results are provided in the gate evaluation sections below.</p>
            </div>
        </div>
"""
    
    def _generate_features_html(self, features: List[str]) -> str:
        """Generate HTML for key features list"""
        if not features:
            return '<span class="no-data">No key features identified</span>'
        
        features_html = []
        for feature in features[:5]:  # Limit to 5 features
            features_html.append(f'<div class="feature-item">• {feature}</div>')
        
        return ''.join(features_html)
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations list"""
        if not recommendations:
            return '<span class="no-data">No recommendations available</span>'
        
        recommendations_html = []
        for rec in recommendations[:5]:  # Limit to 5 recommendations
            recommendations_html.append(f'<div class="recommendation-item">• {rec}</div>')
        
        return ''.join(recommendations_html)
    
    def _generate_tech_tags_html(self, technologies: List[str]) -> str:
        """Generate HTML for technology tags"""
        if not technologies:
            return '<span class="no-data">No technologies detected</span>'
        
        tags_html = []
        for tech in technologies[:8]:  # Limit to 8 technologies
            tags_html.append(f'<span class="tech-tag">{tech}</span>')
        
        return ''.join(tags_html)
    
    def _generate_file_type_tags_html(self, file_types: List[str]) -> str:
        """Generate HTML for file type tags"""
        if not file_types:
            return '<span class="no-data">No file types detected</span>'
        
        tags_html = []
        for file_type in file_types[:6]:  # Limit to 6 file types
            tags_html.append(f'<span class="file-type-tag">{file_type}</span>')
        
        return ''.join(tags_html)
    
    def _generate_dependency_tags_html(self, dependencies: List[str]) -> str:
        """Generate HTML for dependency tags"""
        if not dependencies:
            return '<span class="no-data">No dependencies detected</span>'
        
        tags_html = []
        for dep in dependencies[:6]:  # Limit to 6 dependencies
            tags_html.append(f'<span class="dependency-tag">{dep}</span>')
        
        return ''.join(tags_html)
