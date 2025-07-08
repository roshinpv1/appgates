"""
Report Generator - Creates validation reports in multiple formats
Uses the same exact logic as VS Code extension for consistency
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from .models import ValidationResult, ReportConfig


class SharedReportGenerator:
    """Shared report generation logic used by both VS Code extension and HTML generator"""
    
    @staticmethod
    def get_clean_repository_name(url: str) -> str:
        """Extract clean repository name from URL"""
        try:
            # Handle various URL formats
            parsed_url = urlparse(url)
            
            # Get path without .git suffix
            path = parsed_url.path.rstrip('/')
            if path.endswith('.git'):
                path = path[:-4]
                
            # Split path and get last component
            parts = [p for p in path.split('/') if p]
            if not parts:
                return 'Repository Scan Results'
                
            # For owner/repo format, use both
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
            
            # Otherwise just use the last part
            return parts[-1]
            
        except Exception:
            return 'Repository Scan Results'

    @staticmethod
    def transform_result_to_extension_format(result: ValidationResult, report_mode: str = "summary") -> Dict[str, Any]:
        """Transform ValidationResult to extension format"""
        
        # Get clean repository name
        repo_name = SharedReportGenerator.get_clean_repository_name(result.project_path)
        
        # Basic metadata
        transformed = {
            "scan_metadata": {
                "scan_duration": result.scan_duration,
                "total_files": result.total_files,
                "total_lines": result.total_lines,
                "timestamp": result.timestamp.isoformat(),
                "project_name": repo_name,  # Use clean repository name
                "project_path": result.project_path,
                "repository_url": getattr(result, 'repository_url', None)  # Add repository URL if available
            },
            "languages_detected": [result.language],  # Add detected languages
            "gates": [],
            "score": round(result.overall_score, 2)  # Add overall score
        }
        
        # Transform gate scores
        for gate_score in result.gate_scores:
            # Deduplicate details using a set
            details_set = set()
            if gate_score.details:
                for detail in gate_score.details:
                    details_set.add(detail)
            
            gate_data = {
                "name": gate_score.gate.value,
                "status": gate_score.status,
                "score": round(gate_score.final_score, 2),
                "details": list(details_set),  # Convert back to list after deduplication
                "expected": gate_score.expected,
                "found": gate_score.found,
                "coverage": round(gate_score.coverage, 2),
                "quality_score": round(gate_score.quality_score, 2),
                "matches": gate_score.matches
            }
            transformed["gates"].append(gate_data)
        
        # Add overall metrics
        transformed["overall_score"] = round(result.overall_score, 2)
        transformed["passed_gates"] = result.passed_gates
        transformed["warning_gates"] = result.warning_gates
        transformed["failed_gates"] = result.failed_gates
        
        # Add recommendations
        transformed["critical_issues"] = result.critical_issues
        transformed["recommendations"] = result.recommendations
        
        return transformed
    
    @staticmethod
    def _extract_patterns_attempted(gate_score) -> Dict[str, Any]:
        """Extract patterns attempted for a gate, focusing only on actual matches"""
        patterns_info = {
            "total_patterns_tried": 0,
            "successful_patterns": [],
            "failed_patterns": [],
            "pattern_details": [],
            "actual_matches_count": 0
        }
        
        if not gate_score.matches:
            patterns_info["status"] = "no_matches_found"
            return patterns_info
        
        # Filter out non-matching patterns
        actual_matches = []
        for match in gate_score.matches:
            file_path = match.get('file_path', match.get('file', ''))
            matched_text = match.get('matched_text', match.get('match', ''))
            line_number = match.get('line_number', match.get('line', 0))
            
            # Only include actual matches
            if (file_path and file_path != 'N/A - No matches found' and 
                file_path != 'unknown' and matched_text.strip() and 
                line_number > 0):
                actual_matches.append(match)
        
        if not actual_matches:
            patterns_info["status"] = "no_actual_matches"
            return patterns_info
        
        # Group actual matches by pattern
        pattern_groups = {}
        for match in actual_matches:
            pattern = match.get('pattern', 'unknown')
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(match)
        
        patterns_info["total_patterns_tried"] = len(pattern_groups)
        patterns_info["actual_matches_count"] = len(actual_matches)
        
        for pattern, matches in pattern_groups.items():
            # Only include patterns that actually matched
            files_affected = []
            for match in matches:
                file_path = match.get('file_path', match.get('file', ''))
                if file_path and file_path not in files_affected:
                    files_affected.append(file_path)
            
            pattern_detail = {
                "pattern": pattern,
                "matches_count": len(matches),
                "files_affected": files_affected,
                "sample_matches": matches[:3] if len(matches) > 3 else matches  # First 3 matches as samples
            }
            
            patterns_info["successful_patterns"].append(pattern)
            patterns_info["pattern_details"].append(pattern_detail)
        
        patterns_info["status"] = "matches_found"
        return patterns_info
    
    @staticmethod
    def calculate_summary_stats(result_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate summary statistics - exact same logic as VS Code extension with logical consistency fixes"""
        gates = result_data.get("gates", [])
        
        # Calculate stats with fixed logical consistency
        total_gates = len(gates)
        implemented_gates = 0
        partial_gates = 0
        not_implemented_gates = 0
        
        # Apply same logical consistency fixes as extension
        for gate in gates:
            found = gate.get("found", 0)
            status = gate.get("status")
            
            # Special handling for avoid_logging_secrets
            if found > 0 and gate.get("name") == 'avoid_logging_secrets':
                # Secrets violations should be counted as not implemented
                not_implemented_gates += 1
            # Standard status-based counting
            elif status == 'PASS':
                implemented_gates += 1
            elif status == 'WARNING':
                partial_gates += 1
            elif status in ['FAIL', 'FAILED']:
                not_implemented_gates += 1
            else:
                # Default fallback
                not_implemented_gates += 1
        
        return {
            "total_gates": total_gates,
            "implemented_gates": implemented_gates,
            "partial_gates": partial_gates,
            "not_implemented_gates": not_implemented_gates,
            "not_applicable_gates": 0  # Not used in extension
        }
    
    @staticmethod
    def extract_project_name(result_data: Dict[str, Any]) -> str:
        """Extract project name - exact same logic as VS Code extension"""
        default_name = 'Repository Scan Results'
        
        # First check scan_metadata
        scan_metadata = result_data.get('scan_metadata', {})
        
        # Try to get a clean name from project path first
        project_path = scan_metadata.get('repository_url', '')
        if project_path:
            # Get the last part of the path
            path_parts = project_path.rstrip('/').split('/')
            if path_parts:
                clean_name = path_parts[-1]
                # Remove any generated suffixes (e.g. _git_1751809820382341_16149_0_xan92jj3)
                clean_name = clean_name.split('_git_')[0]
                if clean_name:
                    return clean_name
        
        # Check scan_metadata project_name
        if scan_metadata.get('project_name'):
            project_name = scan_metadata['project_name']
            # Clean up generated suffixes if present
            if '_git_' in project_name:
                project_name = project_name.split('_git_')[0]
            return project_name
            
        # Fallback to repository URL if available
        if result_data.get('repository_url'):
            url_parts = result_data['repository_url'].split('/')
            project_name = url_parts[-1] or default_name
            if project_name.endswith('.git'):
                project_name = project_name[:-4]
            return project_name
            
        # Finally check top-level project_name
        if result_data.get('project_name'):
            project_name = result_data['project_name']
            # Clean up generated suffixes if present
            if '_git_' in project_name:
                project_name = project_name.split('_git_')[0]
            return project_name
            
        return default_name
    
    @staticmethod
    def generate_tech_stack(result_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate technology stack - exact same logic as VS Code extension"""
        tech_stack = []
        if result_data.get('languages_detected'):
            for lang in result_data['languages_detected']:
                tech_stack.append({
                    'type': 'Languages',
                    'name': lang.capitalize(),
                    'version': 'N/A',
                    'purpose': 'detected'
                })
        return tech_stack
    
    @staticmethod
    def analyze_secrets(result_data: Dict[str, Any]) -> Dict[str, str]:
        """Analyze secrets - exact same logic as VS Code extension"""
        gates = result_data.get("gates", [])
        secrets_gate = next((g for g in gates if g.get("name") == 'avoid_logging_secrets'), None)
        
        if secrets_gate:
            # Simple status-based logic like VS Code extension
            if secrets_gate.get("found", 0) > 0:
                return {
                    'status': 'warning',
                    'message': f'Found {secrets_gate["found"]} potential confidential data logging violations'
                }
            elif secrets_gate.get("status") == 'PASS':
                return {
                    'status': 'safe',
                    'message': 'No secrets or confidential data detected'
                }
        
        return {
            'status': 'unknown',
            'message': 'Secrets analysis not available'
        }
    
    @staticmethod
    def get_gate_categories() -> Dict[str, List[str]]:
        """Get gate categories - exact same as VS Code extension"""
        return {
            'Auditability': ['structured_logs', 'avoid_logging_secrets', 'audit_trail', 'correlation_id', 'log_api_calls', 'log_background_jobs', 'ui_errors'],
            'Availability': ['retry_logic', 'timeouts', 'throttling', 'circuit_breakers'],
            'Error Handling': ['error_logs', 'http_codes', 'ui_error_tools'],
            'Testing': ['automated_tests']
        }
    
    @staticmethod
    def get_gate_name_map() -> Dict[str, str]:
        """Get gate name mapping - exact same as VS Code extension"""
        return {
            'structured_logs': 'Logs Searchable Available',
            'avoid_logging_secrets': 'Avoid Logging Confidential Data',
            'audit_trail': 'Create Audit Trail Logs',
            'correlation_id': 'Tracking ID For Log Messages',
            'log_api_calls': 'Log Rest API Calls',
            'log_background_jobs': 'Log Application Messages',
            'ui_errors': 'Client UI Errors Logged',
            'retry_logic': 'Retry Logic',
            'timeouts': 'Set Timeouts IO Operations',
            'throttling': 'Throttling Drop Request',
            'circuit_breakers': 'Circuit Breakers Outgoing Requests',
            'error_logs': 'Log System Errors',
            'http_codes': 'Use HTTP Standard Error Codes',
            'ui_error_tools': 'Include Client Error Tracking',
            'automated_tests': 'Automated Regression Testing'
        }
    
    @staticmethod
    def get_gate_comment(gate_name: str, comments: Dict[str, str] = None) -> str:
        """Get comment for a gate from comments dictionary"""
        if not comments:
            return ""
        return comments.get(gate_name, "")
    
    @staticmethod
    def format_gate_name(name: str) -> str:
        """Format gate name - exact same logic as VS Code extension"""
        gate_name_map = SharedReportGenerator.get_gate_name_map()
        if name in gate_name_map:
            return gate_name_map[name]
        # Fallback formatting - fix the .map() error
        return ' '.join(word.capitalize() for word in name.split('_'))
    
    @staticmethod
    def get_status_info(status: str, gate: Dict[str, Any] = None) -> Dict[str, str]:
        """Get status info - exact same logic as VS Code extension with logical consistency fixes"""
        # Apply logical consistency fixes for status display - exact same as extension
        if gate:
            found = gate.get("found", 0)
            
            # Only show violations for avoid_logging_secrets when found > 0
            if found > 0 and gate.get("name") == 'avoid_logging_secrets':
                return {'class': 'not-implemented', 'text': '✗ Violations Found'}
        
        # Default status mapping
        if status == 'PASS':
            return {'class': 'implemented', 'text': '✓ Implemented'}
        elif status == 'WARNING':
            return {'class': 'partial', 'text': '⚬ Partial'}
        elif status == 'NOT_APPLICABLE':
            return {'class': 'partial', 'text': 'N/A'}
        else:
            return {'class': 'not-implemented', 'text': '✗ Missing'}
    
    @staticmethod
    def format_evidence(gate: Dict[str, Any]) -> str:
        """Format evidence - exact same logic as VS Code extension"""
        if gate.get("status") == 'NOT_APPLICABLE':
            return 'Not applicable to this project type'
        
        found = gate.get("found", 0)
        coverage = gate.get("coverage", 0)
        
        if found > 0:
            return f"Found {found} implementations with {coverage:.1f}% coverage"
        else:
            return 'No relevant patterns found in codebase'
    
    @staticmethod
    def get_recommendation(gate: Dict[str, Any], gate_name: str) -> str:
        """Get recommendation - exact same logic as VS Code extension with logical consistency fixes"""
        found = gate.get("found", 0)
        status = gate.get("status")
        
        # Fix logical inconsistency: if there are violations, recommend fixing them - exact same as extension
        if found > 0:
            if gate.get("name") == 'avoid_logging_secrets':
                return f"Fix confidential data logging violations in {gate_name.lower()}"
            elif status == 'PASS':
                return f"Address identified issues in {gate_name.lower()}"
        
        # Default recommendation mapping
        if status == 'PASS':
            return 'Continue maintaining good practices'
        elif status == 'WARNING':
            return f"Expand implementation of {gate_name.lower()}"
        elif status == 'NOT_APPLICABLE':
            return 'Not applicable to this project type'
        else:
            return f"Implement {gate_name.lower()}"


class ReportGenerator:
    """Generates validation reports in multiple formats using shared logic"""
    
    def __init__(self, config: ReportConfig):
        self.config = config

    def _get_extension_css_styles(self) -> str:
        """Get CSS styles that exactly match VS Code extension"""
        return """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f3f4f6; }
        h1 { font-size: 2em; color: #1f2937; border-bottom: 3px solid #2563eb; padding-bottom: 15px; margin-bottom: 30px; }
        h2 { color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 40px; }
        h3 { color: #374151; margin-top: 30px; }
        
        /* Quick Overview Section */
        .summary-highlights {
            background: #fff;
            border-radius: 12px;
            padding: 24px;
            margin: 30px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .summary-highlights h3 {
            margin-top: 0;
            color: #1f2937;
            font-size: 1.5em;
            margin-bottom: 20px;
        }
        
        .quick-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 24px;
        }
        
        .quick-stat {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .quick-stat:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        .quick-stat-value {
            font-size: 2em;
            font-weight: 600;
            color: #2563eb;
            margin-bottom: 8px;
        }
        
        .quick-stat-label {
            color: #6b7280;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .quick-stat-details {
            margin-top: 8px;
            color: #4b5563;
            font-size: 0.9em;
        }
        
        /* Detailed Section */
        .detailed-section {
            background: #fff;
            border-radius: 12px;
            padding: 24px;
            margin: 30px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 24px;
        }
        
        .metadata-item {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
        }
        
        .metadata-label {
            color: #6b7280;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        
        .metadata-value {
            color: #1f2937;
            font-size: 1.2em;
            font-weight: 500;
        }
        
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
        
        .metric-label {
            color: #6b7280;
            font-size: 0.9em;
            margin-bottom: 4px;
        }
        
        .metric-value {
            color: #1f2937;
            font-weight: 500;
            font-size: 1.1em;
        }
        
        .details-section {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
        }
        
        .details-section-title {
            color: #1f2937;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .match-item {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            padding: 12px;
            margin: 8px 0;
        }
        
        .match-file {
            color: #2563eb;
            font-family: monospace;
            margin-bottom: 4px;
        }
        
        .match-code {
            background: #f1f5f9;
            padding: 8px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
        }
        
        table { width: 100%; border-collapse: collapse; margin: 0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #2563eb; color: #fff; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        tr:hover { background: #f9fafb; }
        .status-implemented { color: #059669; background: #ecfdf5; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-partial { color: #d97706; background: #fffbeb; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .status-not-implemented { color: #dc2626; background: #fef2f2; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .summary-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .stat-card { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2563eb; }
        .stat-label { color: #6b7280; margin-top: 5px; }
        .compliance-bar { width: 100%; height: 20px; background: #e5e7eb; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .compliance-fill { height: 100%; background: linear-gradient(90deg, #dc2626 0%, #d97706 50%, #059669 100%); transition: width 0.3s ease; }
        .comment-cell { font-style: italic; color: #6b7280; max-width: 250px; word-wrap: break-word; background: #f9fafb; }
        .secrets-unknown { color: #6b7280; background: #f9fafb; padding: 15px; border-radius: 8px; border-left: 4px solid #6b7280; margin: 10px 0; }
        
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
        .detailed-badge { background: #1f2937; color: #fff; }
        """

    def _get_mode_specific_styles(self, report_mode: str) -> str:
        """Get mode-specific styles"""
        return ""  # Base styles include all necessary styling now

    def _generate_mode_specific_content(self, result_data: Dict[str, Any], report_mode: str) -> str:
        """Generate mode-specific content sections"""
        if report_mode == "detailed":
            # Generate detailed metadata section
            scan_metadata = result_data.get("scan_metadata", {})
            
            return f"""
            <div class="detailed-section">
                <h3>📊 Detailed Scan Information</h3>
                <div class="metadata-grid">
                    <div class="metadata-item">
                        <div class="metadata-label">Scan Duration</div>
                        <div class="metadata-value">{scan_metadata.get('scan_duration', 0):.2f} seconds</div>
                    </div>
                    <div class="metadata-item">
                        <div class="metadata-label">Files Analyzed</div>
                        <div class="metadata-value">{scan_metadata.get('total_files', 0)} files</div>
                    </div>
                    <div class="metadata-item">
                        <div class="metadata-label">Lines of Code</div>
                        <div class="metadata-value">{scan_metadata.get('total_lines', 0):,} lines</div>
                    </div>
                    <div class="metadata-item">
                        <div class="metadata-label">Languages Detected</div>
                        <div class="metadata-value">{', '.join(result_data.get('languages_detected', []))}</div>
                    </div>
                </div>
            </div>
            """
        else:
            # Generate summary highlights
            quick_stats = {
                "scan_duration": result_data.get("scan_metadata", {}).get("scan_duration", 0),
                "total_files": result_data.get("scan_metadata", {}).get("total_files", 0),
                "total_lines": result_data.get("scan_metadata", {}).get("total_lines", 0)
            }
            
            # Try to get quick stats from result data
            if "quick_stats" in result_data:
                quick_stats.update(result_data["quick_stats"])
            
            # Get detected languages
            languages = result_data.get('languages_detected', [])
            languages_str = ', '.join(lang.capitalize() for lang in languages) if languages else 'None detected'
            
            return f"""
            <div class="summary-highlights">
                <h3>🎯 Quick Overview</h3>
                <div class="quick-stats">
                    <div class="quick-stat">
                        <div class="quick-stat-value">{quick_stats['scan_duration']:.1f}s</div>
                        <div class="quick-stat-label">Scan Time</div>
                    </div>
                    <div class="quick-stat">
                        <div class="quick-stat-value">{quick_stats['total_files']}</div>
                        <div class="quick-stat-label">Files</div>
                    </div>
                    <div class="quick-stat">
                        <div class="quick-stat-value">{quick_stats['total_lines']:,}</div>
                        <div class="quick-stat-label">Lines</div>
                    </div>
                    <div class="quick-stat">
                        <div class="quick-stat-value">{len(languages)}</div>
                        <div class="quick-stat-label">Languages</div>
                        <div class="quick-stat-details">{languages_str}</div>
                    </div>
                </div>
            </div>
            """
    
    def generate(self, result: ValidationResult, report_mode: str = "summary") -> List[str]:
        """Generate reports in specified format(s)
        
        Args:
            result: ValidationResult object
            report_mode: "summary", "detailed", or "both"
        """
        
        output_dir = Path(self.config.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate both summary and detailed reports if requested
        if report_mode == "both":
            # Generate summary reports
            if self.config.format in ['json', 'all']:
                json_file = self._generate_json_report(result, output_dir, "summary")
                generated_files.append(json_file)
            
            if self.config.format in ['html', 'all']:
                html_file = self._generate_html_report(result, output_dir, "summary")
                generated_files.append(html_file)
            
            # Generate detailed reports
            if self.config.format in ['json', 'all']:
                json_file = self._generate_json_report(result, output_dir, "detailed")
                generated_files.append(json_file)
            
            if self.config.format in ['html', 'all']:
                html_file = self._generate_html_report(result, output_dir, "detailed")
                generated_files.append(html_file)
        else:
            # Generate single report type
            if self.config.format in ['json', 'all']:
                json_file = self._generate_json_report(result, output_dir, report_mode)
                generated_files.append(json_file)
            
            if self.config.format in ['html', 'all']:
                html_file = self._generate_html_report(result, output_dir, report_mode)
                generated_files.append(html_file)
        
        return generated_files
    
    def generate_summary_report(self, result: ValidationResult) -> List[str]:
        """Generate summary report only"""
        return self.generate(result, "summary")
    
    def generate_detailed_report(self, result: ValidationResult) -> List[str]:
        """Generate detailed report only"""
        return self.generate(result, "detailed")
    
    def generate_both_reports(self, result: ValidationResult) -> List[str]:
        """Generate both summary and detailed reports"""
        return self.generate(result, "both")
    
    def _generate_json_report(self, result: ValidationResult, output_dir: Path, report_mode: str = "summary") -> str:
        """Generate JSON report with specified detail level"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_suffix = "_detailed" if report_mode == "detailed" else "_summary"
        filename = f"codegates_report{mode_suffix}_{timestamp}.json"
        filepath = output_dir / filename
        
        # Use shared logic to transform result with specified mode
        result_data = SharedReportGenerator.transform_result_to_extension_format(result, report_mode)
        
        # Create base report structure
        report_data = {
            "report_metadata": {
                "report_type": f"codegates_{report_mode}",
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "project_info": {
                "project_name": result.project_name,
                "project_path": getattr(result, 'project_path', ''),
                "language": result.language.value if hasattr(result, 'language') else 'unknown',
                "languages_detected": result_data.get("languages_detected", []),
                "repository_url": result_data.get("repository_url")
            },
            "scan_summary": {
                "overall_score": result.overall_score,
                "gate_summary": SharedReportGenerator.calculate_summary_stats(result_data)
            },
            "gates": result_data["gates"]
        }
        
        # Add detailed information only for detailed reports
        if report_mode == "detailed":
            report_data.update({
                "scan_details": result_data.get("scan_metadata", {}),
                "detailed_analysis": result_data.get("detailed_analysis", {}),
                "failed_gates_analysis": self._generate_failed_gates_analysis(result),
                "critical_issues": result_data.get("critical_issues", []),
                "performance_metrics": result_data.get("performance_metrics", {}),
                "full_recommendations": getattr(result, 'recommendations', [])
            })
        else:
            # Summary mode - minimal additional info
            report_data.update({
                "quick_stats": {
                    "scan_duration": getattr(result, 'scan_duration', 0),
                    "total_files": getattr(result, 'total_files', 0),
                    "total_lines": getattr(result, 'total_lines', 0)
                },
                "top_recommendations": getattr(result, 'recommendations', [])[:5]  # Top 5 recommendations
            })
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return str(filepath)
    
    def _generate_failed_gates_analysis(self, result: ValidationResult) -> Dict[str, Any]:
        """Generate detailed analysis of failed gates including patterns attempted"""
        failed_analysis = {
            "summary": {
                "total_failed_gates": 0,
                "total_patterns_attempted": 0,
                "common_failure_reasons": []
            },
            "detailed_analysis": []
        }
        
        failed_gates = [gs for gs in result.gate_scores if gs.status in ['FAILED', 'FAIL'] or gs.final_score < 60]
        failed_analysis["summary"]["total_failed_gates"] = len(failed_gates)
        
        for gate_score in failed_gates:
            gate_analysis = {
                "gate_name": gate_score.gate.value,
                "status": gate_score.status,
                "final_score": gate_score.final_score,
                "expected": gate_score.expected,
                "found": gate_score.found,
                "failure_reasons": [],
                "patterns_attempted": [],
                "potential_solutions": []
            }
            
            # Filter matches to only include actual matches
            if gate_score.matches:
                actual_matches = []
                for match in gate_score.matches:
                    file_path = match.get('file_path', match.get('file', ''))
                    matched_text = match.get('matched_text', match.get('match', ''))
                    line_number = match.get('line_number', match.get('line', 0))
                    
                    # Only include actual matches
                    if (file_path and file_path != 'N/A - No matches found' and 
                        file_path != 'unknown' and matched_text.strip() and 
                        line_number > 0):
                        actual_matches.append(match)
                
                # Extract patterns from actual matches only
                for match in actual_matches:
                    pattern_info = {
                        "pattern": match.get('pattern', 'unknown'),
                        "file_searched": match.get('file_path', match.get('file', '')),
                        "line_number": match.get('line_number', match.get('line', 0)),
                        "matched_text": match.get('matched_text', match.get('match', '')),
                        "context": match.get('context', [])
                    }
                    gate_analysis["patterns_attempted"].append(pattern_info)
            
            failed_analysis["detailed_analysis"].append(gate_analysis)
        
        # Identify common failure patterns
        if failed_gates:
            failure_reasons = [reason for gate in failed_analysis["detailed_analysis"] for reason in gate["failure_reasons"]]
            from collections import Counter
            common_failures = Counter(failure_reasons).most_common(3)
            failed_analysis["summary"]["common_failure_reasons"] = [{"reason": reason, "count": count} for reason, count in common_failures]
        
        return failed_analysis
    
    def _get_gate_specific_recommendations(self, gate_name: str) -> List[str]:
        """Get specific recommendations for failed gates"""
        recommendations_map = {
            "structured_logs": [
                "Use structured logging with JSON format",
                "Include relevant context fields in log messages",
                "Use logging libraries like structlog (Python) or logback (Java)"
            ],
            "avoid_logging_secrets": [
                "Review and remove any sensitive data from log statements",
                "Use log sanitization or redaction techniques",
                "Implement secret detection tools in CI/CD pipeline"
            ],
            "audit_trail": [
                "Add logging for all critical business operations",
                "Include user context and operation details",
                "Log both successful and failed operations"
            ],
            "correlation_id": [
                "Implement request tracking with correlation/trace IDs",
                "Pass correlation ID through all service calls",
                "Include correlation ID in all log messages"
            ],
            "retry_logic": [
                "Implement retry mechanisms for external service calls",
                "Use exponential backoff strategies",
                "Set appropriate retry limits and timeouts"
            ],
            "error_logs": [
                "Add comprehensive error logging in exception handlers",
                "Include stack traces and error context",
                "Log errors at appropriate severity levels"
            ],
            "automated_tests": [
                "Increase test coverage with unit and integration tests",
                "Implement test automation in CI/CD pipeline",
                "Add tests for critical business logic"
            ]
        }
        
        return recommendations_map.get(gate_name, ["Review implementation guidelines for this gate"])
    
    def _generate_html_report(self, result: ValidationResult, output_dir: Path, report_mode: str = "summary") -> str:
        """Generate HTML report with modern styling"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_suffix = "_detailed" if report_mode == "detailed" else "_summary"
        filename = f"codegates_report{mode_suffix}_{timestamp}.html"
        filepath = output_dir / filename
        
        html_content = self._generate_html_content(result, report_mode)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _generate_html_content(self, result: ValidationResult, report_mode: str = "summary", comments: Dict[str, str] = None) -> str:
        """Generate HTML content using exact same logic as VS Code extension"""
        
        # Transform result using shared logic
        result_data = SharedReportGenerator.transform_result_to_extension_format(result, report_mode)
        
        # Calculate summary statistics using shared logic
        stats = SharedReportGenerator.calculate_summary_stats(result_data)
        
        # Extract project name using shared logic
        project_name = SharedReportGenerator.extract_project_name(result_data)
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Count comments if provided
        comments_count = len(comments) if comments else 0
        
        # Report type display
        report_type_display = "Detailed" if report_mode == "detailed" else "Summary"

        # Add JavaScript for details toggle
        toggle_script = """
        <script>
        function toggleDetails(button, detailsId) {
            const details = document.getElementById(detailsId);
            const isExpanded = button.getAttribute('aria-expanded') === 'true';
            
            button.setAttribute('aria-expanded', !isExpanded);
            details.setAttribute('aria-hidden', isExpanded);
            
            // Smooth scroll to expanded content
            if (!isExpanded) {
                setTimeout(() => {
                    details.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        }
        </script>
        """
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hard Gate Assessment ({report_type_display}) - {project_name}</title>
    <style>
        {self._get_extension_css_styles()}
        {self._get_mode_specific_styles(report_mode)}
    </style>
    {toggle_script}
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{project_name}</h1>
            <div class="report-badge {report_mode}-badge">{report_type_display} Report</div>
            <p style="color: #2563eb; margin-bottom: 30px; font-weight: 500;">Hard Gate Assessment Report{(' (with ' + str(comments_count) + ' user comments)') if comments_count > 0 else ''}</p>
        </div>
        
        <h2>Executive Summary</h2>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{stats['total_gates']}</div>
                <div class="stat-label">Total Gates Evaluated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['implemented_gates']}</div>
                <div class="stat-label">Gates Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['partial_gates']}</div>
                <div class="stat-label">Partially Met</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['not_implemented_gates']}</div>
                <div class="stat-label">Not Met</div>
            </div>
        </div>
        
        <h3>Overall Compliance</h3>
        <div class="compliance-bar">
            <div class="compliance-fill" style="width: {result_data['score']:.1f}%"></div>
        </div>
        <p><strong>{result_data['score']:.1f}% Hard Gates Compliance</strong></p>
        
        {self._generate_mode_specific_content(result_data, report_mode)}
        
        <h2>Hard Gates Analysis</h2>
        {self._generate_gates_table_html(result_data, report_mode, comments)}
        
        <footer style="margin-top: 50px; text-align: center; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            <p>Hard Gate Assessment {report_type_display} Report generated on {timestamp}</p>
            {('<p style="font-size: 0.9em; color: #9ca3af;">Report includes ' + str(comments_count) + ' user comments for enhanced documentation</p>') if comments_count > 0 else ''}
        </footer>
    </div>
</body>
</html>"""
        
        return html_template

    def _generate_gate_details(self, gate: Dict[str, Any]) -> str:
        """Generate detailed content for a gate"""
        details = []
        
        # Metrics section
        metrics = [
            ('Score', f"{gate.get('score', 0):.1f}%"),
            ('Coverage', f"{gate.get('coverage', 0):.1f}%"),
            ('Expected/Found', f"{gate.get('expected', 0)} / {gate.get('found', 0)}")
        ]
        
        metrics_html = '<div class="metrics-grid">'
        for label, value in metrics:
            metrics_html += f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>"""
        metrics_html += '</div>'
        details.append(metrics_html)
        
        # Details section - deduplicate details
        if gate.get('details'):
            details_set = set(gate['details'])  # Convert to set to remove duplicates
            details_html = """
                <div class="details-section">
                    <div class="details-section-title">Implementation Details</div>
                    <div class="details-content">"""
            for detail in details_set:  # Iterate over deduplicated details
                details_html += f"<p>{detail}</p>"
            details_html += "</div></div>"
            details.append(details_html)
        
        # Sample matches section
        if gate.get('matches'):
            matches = gate['matches'][:3]  # Show first 3 matches
            matches_html = """
                <div class="details-section">
                    <div class="details-section-title">Sample Implementations</div>
                    <div class="details-content">"""
            
            for match in matches:
                file_path = match.get('file_path', match.get('file', ''))
                line_number = match.get('line_number', match.get('line', 0))
                matched_text = match.get('matched_text', match.get('match', ''))
                
                matches_html += f"""
                    <div class="match-item">
                        <div class="match-file">{file_path}:{line_number}</div>
                        <div class="match-code">{matched_text}</div>
                    </div>"""
            
            if len(gate['matches']) > 3:
                matches_html += f"""
                    <p><em>... and {len(gate['matches']) - 3} more implementations</em></p>"""
            
            matches_html += "</div></div>"
            details.append(matches_html)
        
        return ''.join(details)

    def _generate_gates_table_html(self, result_data: Dict[str, Any], report_mode: str, comments: Dict[str, str] = None) -> str:
        """Generate gates table HTML with mode-specific details"""
        gates = result_data.get("gates", [])
        gate_categories = SharedReportGenerator.get_gate_categories()
        
        html = """<div class="gates-analysis">"""
        
        for category_name, gate_names in gate_categories.items():
            category_gates = [g for g in gates if g.get("name") in gate_names]
            
            if not category_gates:
                continue
            
            html += f"""
                <div class="gate-category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-content">
                        <table class="gates-table">
                            <thead>
                                <tr>
                                    <th style="width: 30px"></th>
                                    <th>Practice</th>
                                    <th>Status</th>
                                    <th>Evidence</th>
                                    <th>Recommendation</th>"""
            
            if comments:
                html += """
                                    <th>Comments</th>"""
            
            html += """
                                </tr>
                            </thead>
                            <tbody>"""
            
            for i, gate in enumerate(category_gates):
                gate_id = f"{category_name.lower()}-{gate.get('name', '')}-{i}"
                gate_name = SharedReportGenerator.format_gate_name(gate.get("name", ""))
                status_info = SharedReportGenerator.get_status_info(gate.get("status", ""), gate)
                evidence = SharedReportGenerator.format_evidence(gate)
                recommendation = SharedReportGenerator.get_recommendation(gate, gate_name)
                comment = SharedReportGenerator.get_gate_comment(gate.get("name", ""), comments) if comments else ""
                
                # Generate detailed content
                details_content = self._generate_gate_details(gate)
                
                html += f"""
                                <tr>
                                    <td style="text-align: center">
                                        <button class="details-toggle" onclick="toggleDetails(this, 'details-{gate_id}')" aria-expanded="false" aria-label="Show details for {gate_name}">+</button>
                                    </td>
                                    <td><strong>{gate_name}</strong></td>
                                    <td><span class="status-{status_info['class']}">{status_info['text']}</span></td>
                                    <td>{evidence}</td>
                                    <td>{recommendation}</td>"""
                
                if comments:
                    html += f"""
                                    <td class="comment-cell">{comment if comment else 'No comments'}</td>"""
                
                html += """
                                </tr>"""
                
                # Add details row (hidden by default)
                html += f"""
                                <tr id="details-{gate_id}" class="gate-details" aria-hidden="true">
                                    <td colspan="{6 if comments else 5}" class="details-content">
                                        {details_content}
                                    </td>
                                </tr>"""
            
            html += """
                            </tbody>
                        </table>
                    </div>
                </div>"""
        
        html += """</div>"""
        return html
    
    def _format_detailed_matches(self, matches) -> str:
        """Format detailed match information for HTML display"""
        if not matches or (isinstance(matches, int) and matches == 0):
            return "<em>No matches found</em>"
        
        if isinstance(matches, int):
            return f"<strong>{matches} matches found</strong>"
        
        if not isinstance(matches, list):
            return "<em>Invalid match data</em>"
        
        html = f"<strong>{len(matches)} matches:</strong><br>"
        
        # Show first 3 matches in detail
        for i, match in enumerate(matches[:3]):
            file_path = match.get('file_path', match.get('file', 'unknown'))
            line_number = match.get('line_number', match.get('line', 0))
            matched_text = match.get('matched_text', match.get('match', ''))
            
            # Truncate long file paths
            display_path = file_path
            if len(display_path) > 30:
                display_path = "..." + display_path[-27:]
            
            # Truncate long matched text
            display_text = matched_text
            if len(display_text) > 50:
                display_text = display_text[:47] + "..."
            
            html += f"""
                <div class="match-item">
                    <div class="match-file">{display_path}:{line_number}</div>
                    <div class="match-code">{display_text}</div>
                </div>"""
        
        # Show count of remaining matches
        if len(matches) > 3:
            html += f"<p><em>... and {len(matches) - 3} more matches</em></p>"
        
        return html 
    
    def _generate_simple_gates_table_html(self, result_data: Dict[str, Any], comments: Dict[str, str] = None) -> str:
        """Generate simplified gates table HTML for summary mode"""
        gates = result_data.get("gates", [])
        gate_categories = SharedReportGenerator.get_gate_categories()
        
        html = ""
        
        for category_name, gate_names in gate_categories.items():
            category_gates = [g for g in gates if g.get("name") in gate_names]
            
            if not category_gates:
                continue
            
            html += f"""
                <div class="gate-category">
                    <h3>{category_name}</h3>
                    <table class="gates-table">
                        <thead>
                            <tr>
                                <th>Practice</th>
                                <th>Status</th>
                                <th>Evidence</th>
                                <th>Recommendation</th>"""
            
            # Add Comments column only if comments are provided
            if comments:
                html += """
                                <th>Comments</th>"""
            
            html += """
                            </tr>
                        </thead>
                        <tbody>"""
            
            for gate in category_gates:
                gate_name = SharedReportGenerator.format_gate_name(gate.get("name", ""))
                status_info = SharedReportGenerator.get_status_info(gate.get("status", ""), gate)
                evidence = SharedReportGenerator.format_evidence(gate)
                recommendation = SharedReportGenerator.get_recommendation(gate, gate_name)
                comment = SharedReportGenerator.get_gate_comment(gate.get("name", ""), comments) if comments else ""
                
                html += f"""
                            <tr>
                                <td><strong>{gate_name}</strong></td>
                                <td><span class="status-{status_info['class']}">{status_info['text']}</span></td>
                                <td>{evidence}</td>
                                <td>{recommendation}</td>"""
                
                # Add comment cell only if comments are provided
                if comments:
                    html += f"""
                                <td class="comment-cell">{comment if comment else 'No comments'}</td>"""
                
                html += """
                            </tr>"""
        
        return html 


def generate_report(result: ValidationResult) -> str:
    """Generate report in the expected format"""
    
    # Generate scan ID
    scan_id = str(uuid.uuid4())
    
    # Convert gate scores to expected format
    gates = []
    for score in result.gate_scores:
        if not isinstance(score.gate, GateType):
            continue
            
        gate = {
            "name": score.gate.value,
            "status": score.status,
            "score": round(score.final_score, 2),
            "details": score.details if score.details else [f"No {score.gate.value} details available"],
            "expected": score.expected,
            "found": score.found,
            "coverage": round(score.coverage, 2),
            "quality_score": round(score.quality_score, 2),
            "matches": [
                {
                    "file": match.get("file_path", match.get("file", "unknown")),
                    "line": match.get("line_number", match.get("line", 0)),
                    "content": match.get("matched_text", match.get("match", ""))
                }
                for match in score.matches
            ] if score.matches else []
        }
        gates.append(gate)
    
    # Generate recommendations
    recommendations = []
    for score in result.gate_scores:
        if score.status != "PASS" and score.recommendations:
            recommendations.extend(score.recommendations)
    
    # Ensure we have at least one recommendation
    if not recommendations:
        recommendations = ["Review implementation of failing gates"]
    
    # Create report with scan metadata
    report = {
        "scan_id": scan_id,
        "status": "completed",
        "score": round(result.overall_score, 2),
        "gates": gates,
        "recommendations": list(set(recommendations)),  # Remove duplicates
        "report_url": f"http://localhost:8000/api/v1/reports/{scan_id}",
        "jira_result": None,
        "scan_metadata": {
            "scan_duration": round(result.scan_duration, 2),
            "total_files": result.total_files,
            "total_lines": result.total_lines,
            "timestamp": datetime.now().isoformat(),
            "languages_detected": [lang.value for lang in result.languages] if result.languages else []
        }
    }
    
    # Convert to JSON
    return json.dumps(report, indent=4) 