#!/usr/bin/env python3
"""
JIRA Integration - Configuration-driven JIRA integration for posting reports
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import base64

from ..models import ValidationResult
from ..utils.env_loader import EnvironmentLoader


class JiraIntegration:
    """Handles JIRA integration for posting Hard Gate Assessment reports"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize JIRA integration with configuration
        
        Args:
            config: Optional configuration dict. If None, loads from environment
        """
        self.config = config or self._load_config()
        self.enabled = self._is_enabled()
        
        if self.enabled:
            self.jira_url = self.config.get('jira_url', '').rstrip('/')
            self.username = self.config.get('username')
            self.api_token = self.config.get('api_token')
            self.project_key = self.config.get('project_key')
            self.issue_key = self.config.get('issue_key')
            self.comment_format = self.config.get('comment_format', 'markdown')
            self.include_details = self.config.get('include_details', True)
            self.include_recommendations = self.config.get('include_recommendations', True)
            self.custom_fields = self.config.get('custom_fields', {})
            
            # Validate required fields
            if not all([self.jira_url, self.username, self.api_token]):
                print("⚠️ JIRA integration disabled: Missing required configuration (jira_url, username, api_token)")
                self.enabled = False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load JIRA configuration from environment variables and config files"""
        
        config = {}
        
        # Load from environment variables
        env_loader = EnvironmentLoader()
        
        # Check if JIRA integration is enabled
        if env_loader.get('JIRA_ENABLED', 'false').lower() in ['true', '1', 'yes']:
            config.update({
                'enabled': True,
                'jira_url': env_loader.get('JIRA_URL'),
                'username': env_loader.get('JIRA_USERNAME'),
                'api_token': env_loader.get('JIRA_API_TOKEN'),
                'project_key': env_loader.get('JIRA_PROJECT_KEY'),
                'issue_key': env_loader.get('JIRA_ISSUE_KEY'),
                'comment_format': env_loader.get('JIRA_COMMENT_FORMAT', 'markdown'),
                'include_details': env_loader.get('JIRA_INCLUDE_DETAILS', 'true').lower() in ['true', '1', 'yes'],
                'include_recommendations': env_loader.get('JIRA_INCLUDE_RECOMMENDATIONS', 'true').lower() in ['true', '1', 'yes']
            })
        
        # Load from config file if exists
        config_file = Path('config/jira_config.json')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"⚠️ Failed to load JIRA config file: {e}")
        
        return config
    
    def _is_enabled(self) -> bool:
        """Check if JIRA integration is enabled"""
        return self.config.get('enabled', False)
    
    def is_available(self) -> bool:
        """Check if JIRA integration is available and properly configured"""
        return self.enabled
    
    def post_report_comment(self, validation_result: ValidationResult, 
                          issue_key: Optional[str] = None,
                          additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Post a Hard Gate Assessment report as a comment to a JIRA issue
        
        Args:
            validation_result: The validation result to post
            issue_key: Optional issue key to override config
            additional_context: Additional context like repository URL, branch, etc.
            
        Returns:
            Dict with success status and details
        """
        
        if not self.enabled:
            return {
                'success': False,
                'message': 'JIRA integration is not enabled or configured',
                'posted': False
            }
        
        try:
            # Use provided issue key or fall back to config
            target_issue = issue_key or self.issue_key
            if not target_issue:
                return {
                    'success': False,
                    'message': 'No JIRA issue key provided',
                    'posted': False
                }
            
            # Generate comment content
            comment_content = self._generate_comment(validation_result, additional_context)
            
            # Post comment to JIRA
            response = self._post_comment_to_jira(target_issue, comment_content)
            
            return {
                'success': True,
                'message': f'Report posted to JIRA issue {target_issue}',
                'posted': True,
                'jira_issue': target_issue,
                'comment_id': response.get('id'),
                'comment_url': f"{self.jira_url}/browse/{target_issue}?focusedCommentId={response.get('id')}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to post to JIRA: {str(e)}',
                'posted': False,
                'error': str(e)
            }
    
    def _generate_comment(self, validation_result: ValidationResult, 
                         additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate comment content based on format configuration"""
        
        if self.comment_format.lower() == 'markdown':
            return self._generate_markdown_comment(validation_result, additional_context)
        elif self.comment_format.lower() == 'text':
            return self._generate_text_comment(validation_result, additional_context)
        else:
            # Default to markdown
            return self._generate_markdown_comment(validation_result, additional_context)
    
    def _generate_markdown_comment(self, validation_result: ValidationResult,
                                 additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate markdown-formatted comment"""
        
        context = additional_context or {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        comment = f"## 🛡️ Hard Gate Assessment Report\n\n"
        comment += f"**Generated:** {timestamp}\n"
        
        if context.get('repository_url'):
            comment += f"**Repository:** {context['repository_url']}\n"
        if context.get('branch'):
            comment += f"**Branch:** {context['branch']}\n"
        if context.get('scan_id'):
            comment += f"**Scan ID:** {context['scan_id']}\n"
        
        comment += "\n---\n\n"
        
        # Summary
        applicable_gates = [g for g in validation_result.gate_scores if g.status != "NOT_APPLICABLE"]
        implemented = len([g for g in applicable_gates if g.status == "PASS"])
        partial = len([g for g in applicable_gates if g.status == "WARNING"])
        failed = len([g for g in applicable_gates if g.status in ["FAIL", "FAILED"]])
        not_applicable = len([g for g in validation_result.gate_scores if g.status == "NOT_APPLICABLE"])
        
        comment += f"### 📊 Executive Summary\n\n"
        comment += f"| Metric | Value |\n"
        comment += f"|--------|-------|\n"
        comment += f"| **Overall Score** | **{validation_result.overall_score:.1f}%** |\n"
        comment += f"| Total Gates | {len(validation_result.gate_scores)} |\n"
        comment += f"| ✅ Implemented | {implemented} |\n"
        comment += f"| ⚠️ Partial | {partial} |\n"
        comment += f"| ❌ Failed | {failed} |\n"
        comment += f"| 🚫 Not Applicable | {not_applicable} |\n"
        comment += f"| Files Analyzed | {validation_result.total_files} |\n"
        comment += f"| Lines of Code | {validation_result.total_lines:,} |\n\n"
        
        # Compliance indicator
        if validation_result.overall_score >= 80:
            comment += f"🟢 **HIGH COMPLIANCE** - Excellent gate coverage\n\n"
        elif validation_result.overall_score >= 60:
            comment += f"🟡 **MODERATE COMPLIANCE** - Some improvements needed\n\n"
        else:
            comment += f"🔴 **LOW COMPLIANCE** - Significant improvements required\n\n"
        
        # Gate Details (if enabled)
        if self.include_details:
            comment += f"### 🔍 Gate Details\n\n"
            
            # Group by category
            categories = {
                "Auditability": ["structured_logs", "avoid_logging_secrets", "audit_trail", "correlation_id", "log_api_calls", "log_background_jobs", "ui_errors"],
                "Availability": ["retry_logic", "timeouts", "throttling", "circuit_breakers"],
                "Error Handling": ["error_logs", "http_codes", "ui_error_tools"],
                "Testing": ["automated_tests"]
            }
            
            gate_map = {g.gate.value: g for g in validation_result.gate_scores}
            
            for category, gate_names in categories.items():
                category_gates = [gate_map[name] for name in gate_names if name in gate_map]
                if category_gates:
                    comment += f"#### {category}\n\n"
                    comment += f"| Gate | Status | Score | Coverage |\n"
                    comment += f"|------|--------|-------|----------|\n"
                    
                    for gate in category_gates:
                        status_emoji = self._get_status_emoji(gate.status)
                        gate_name = gate.gate.value.replace('_', ' ').title()
                        comment += f"| {gate_name} | {status_emoji} {gate.status} | {gate.final_score:.1f}% | {gate.coverage:.1f}% |\n"
                    
                    comment += "\n"
        
        # Recommendations (if enabled)
        if self.include_recommendations and validation_result.recommendations:
            comment += f"### 💡 Recommendations\n\n"
            for i, rec in enumerate(validation_result.recommendations[:5], 1):
                comment += f"{i}. {rec}\n"
            comment += "\n"
        
        # Critical Issues
        if validation_result.critical_issues:
            comment += f"### ⚠️ Critical Issues\n\n"
            for issue in validation_result.critical_issues:
                comment += f"- 🚨 {issue}\n"
            comment += "\n"
        
        # Footer
        comment += "---\n"
        comment += f"*Report generated by CodeGates Hard Gate Assessment*"
        
        if context.get('report_url'):
            comment += f" | [View Detailed Report]({context['report_url']})"
        
        return comment
    
    def _generate_text_comment(self, validation_result: ValidationResult,
                             additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate plain text comment"""
        
        context = additional_context or {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        comment = f"HARD GATE ASSESSMENT REPORT\n"
        comment += f"="*50 + "\n\n"
        comment += f"Generated: {timestamp}\n"
        
        if context.get('repository_url'):
            comment += f"Repository: {context['repository_url']}\n"
        if context.get('branch'):
            comment += f"Branch: {context['branch']}\n"
        
        comment += "\n"
        comment += f"OVERALL SCORE: {validation_result.overall_score:.1f}%\n"
        comment += f"FILES ANALYZED: {validation_result.total_files}\n"
        comment += f"LINES OF CODE: {validation_result.total_lines:,}\n\n"
        
        # Gate summary
        applicable_gates = [g for g in validation_result.gate_scores if g.status != "NOT_APPLICABLE"]
        implemented = len([g for g in applicable_gates if g.status == "PASS"])
        failed = len([g for g in applicable_gates if g.status in ["FAIL", "FAILED"]])
        
        comment += f"GATE SUMMARY:\n"
        comment += f"- Implemented: {implemented}\n"
        comment += f"- Failed: {failed}\n"
        comment += f"- Total Applicable: {len(applicable_gates)}\n\n"
        
        # Recommendations
        if self.include_recommendations and validation_result.recommendations:
            comment += f"RECOMMENDATIONS:\n"
            for i, rec in enumerate(validation_result.recommendations[:3], 1):
                comment += f"{i}. {rec}\n"
            comment += "\n"
        
        comment += f"Report generated by CodeGates Hard Gate Assessment"
        
        return comment
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for gate status"""
        emoji_map = {
            "PASS": "✅",
            "WARNING": "⚠️",
            "FAIL": "❌",
            "FAILED": "❌",
            "NOT_APPLICABLE": "🚫"
        }
        return emoji_map.get(status, "❓")
    
    def _post_comment_to_jira(self, issue_key: str, comment_content: str) -> Dict[str, Any]:
        """Post comment to JIRA issue using REST API"""
        
        url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/comment"
        
        # Create authentication header
        auth_string = f"{self.username}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            'body': comment_content
        }
        
        # Add custom fields if configured
        if self.custom_fields:
            payload.update(self.custom_fields)
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_msg = f"JIRA API error: {response.status_code} - {response.text}"
            raise Exception(error_msg)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test JIRA connection and authentication"""
        
        if not self.enabled:
            return {
                'success': False,
                'message': 'JIRA integration is not enabled'
            }
        
        try:
            url = f"{self.jira_url}/rest/api/2/myself"
            
            auth_string = f"{self.username}:{self.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    'success': True,
                    'message': f'Successfully connected to JIRA as {user_info.get("displayName", "unknown")}',
                    'user': user_info.get('displayName'),
                    'email': user_info.get('emailAddress')
                }
            else:
                return {
                    'success': False,
                    'message': f'JIRA connection failed: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'JIRA connection error: {str(e)}'
            } 