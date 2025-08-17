"""
JIRA Integration Tool
Comprehensive JIRA integration for report uploads and issue management
"""

import os
import sys
import json
import requests
import urllib3
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


class JIRAIntegration:
    """Handles JIRA integration for CodeGates report uploads"""
    
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_user = os.getenv("JIRA_USER")
        self.jira_token = os.getenv("JIRA_TOKEN")
        self.jira_password = os.getenv("JIRA_PASSWORD")
        self.ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() == "true"
        
        # Disable SSL warnings if verification is disabled
        if not self.ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            print("⚠️ SSL verification disabled for JIRA requests")
        else:
            print("🔒 SSL verification enabled for JIRA requests")
    
    def is_configured(self) -> bool:
        """Check if JIRA is properly configured"""
        if not self.jira_url:
            print("[JIRAIntegration] ⚠️ Warning: No JIRA URL provided. Please set JIRA_URL.")
            return False
        if not self.jira_token and (not self.jira_user or not self.jira_password):
            print("[JIRAIntegration] ⚠️ Warning: No authentication credentials provided. Please set JIRA_TOKEN or JIRA_USER/JIRA_PASSWORD.")
            return False
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for JIRA API"""
        if self.jira_token:
            return {
                "Authorization": f"Bearer {self.jira_token}",
                "Content-Type": "application/json"
            }
        else:
            return {
                "Content-Type": "application/json"
            }
    
    def upload_report_to_jira(self, app_id: str, report_path: str, report_type: str = "html",
                             jira_ticket_id: Optional[str] = None, gate_number: Optional[str] = None,
                             comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload report to JIRA stories for the app_id, or to a specific JIRA ticket.
        
        Args:
            app_id: Application ID to find related stories
            report_path: Path to the report file
            report_type: Type of report (html, json, pdf)
            jira_ticket_id: Optional specific JIRA ticket ID to upload to
            gate_number: Optional gate number for individual gate upload
            comment: Optional additional comment to add
            
        Returns:
            Dictionary containing upload results
        """
        if not self.is_configured():
            return {
                "success": False,
                "message": "JIRA not configured. Set JIRA_URL and authentication credentials.",
                "results": []
            }
        
        try:
            # Determine which JIRA tickets to upload to
            if jira_ticket_id:
                # Upload to specific JIRA ticket
                stories = [jira_ticket_id]
                print(f"📋 Uploading to specific JIRA ticket: {jira_ticket_id}")
            else:
                # Upload to all stories for the app_id
                stories = self._fetch_jira_stories(app_id)
                print(f"📋 Found {len(stories)} JIRA stories for app_id: {app_id}")
            
            if not stories:
                return {
                    "success": False,
                    "message": f"No JIRA stories found for app_id {app_id}",
                    "results": []
                }
            
            if not os.path.exists(report_path):
                return {
                    "success": False,
                    "message": f"Report file not found: {report_path}",
                    "results": []
                }
            
            # Read the report file
            with open(report_path, 'rb') as f:
                report_data = f.read()
            filename = os.path.basename(report_path)
            
            # Generate appropriate summary/comment
            if gate_number and comment:
                summary = f"CodeGates Gate {gate_number} Analysis\n\n{comment}\n\nSee attached report for detailed analysis."
            elif gate_number:
                summary = f"CodeGates Gate {gate_number} Analysis\n\nSee attached report for detailed security gate analysis."
            elif comment:
                summary = f"CodeGates Security Analysis\n\n{comment}\n\nSee attached report for detailed analysis."
            else:
                summary = self._extract_report_summary(report_path)
            
            # Upload to each story
            results = []
            for story_id in stories:
                result = self._upload_to_jira_ticket(
                    story_id, report_data, filename, summary, report_type
                )
                results.append(result)
            
            return {
                "success": True,
                "message": f"Successfully uploaded report to {len(stories)} JIRA stories",
                "results": results
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"JIRA upload failed: {str(e)}",
                "results": []
            }
    
    def _fetch_jira_stories(self, app_id: str) -> List[str]:
        """Fetch JIRA stories for the given app_id"""
        try:
            # This is a simplified version - in the real implementation, this would query a database
            # For now, we'll return an empty list and let the user specify a ticket ID
            return []
        except Exception as e:
            print(f"Error fetching JIRA stories: {str(e)}")
            return []
    
    def _upload_to_jira_ticket(self, ticket_id: str, report_data: bytes, filename: str, 
                              summary: str, report_type: str) -> Dict[str, Any]:
        """Upload report to a specific JIRA ticket"""
        try:
            # Determine authentication method
            if self.jira_token:
                auth = None
                headers = self.get_auth_headers()
            else:
                auth = (self.jira_user, self.jira_password)
                headers = {"Content-Type": "application/json"}
            
            # Create comment with attachment
            comment_data = {
                "body": summary
            }
            
            comment_url = f"{self.jira_url}/rest/api/2/issue/{ticket_id}/comment"
            
            response = requests.post(
                comment_url,
                headers=headers,
                auth=auth,
                json=comment_data,
                verify=self.ssl_verify
            )
            
            if response.status_code != 201:
                return {
                    "ticket_id": ticket_id,
                    "success": False,
                    "message": f"Failed to create comment: {response.status_code} - {response.text}"
                }
            
            comment_id = response.json().get("id")
            
            # Upload attachment
            attachment_url = f"{self.jira_url}/rest/api/2/issue/{ticket_id}/attachments"
            
            files = {
                'file': (filename, report_data, self._get_content_type(report_type))
            }
            
            # Remove Content-Type header for multipart upload
            upload_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
            
            response = requests.post(
                attachment_url,
                headers=upload_headers,
                auth=auth,
                files=files,
                verify=self.ssl_verify
            )
            
            if response.status_code == 200:
                return {
                    "ticket_id": ticket_id,
                    "comment_id": comment_id,
                    "success": True,
                    "message": f"Successfully uploaded {filename} to ticket {ticket_id}"
                }
            else:
                return {
                    "ticket_id": ticket_id,
                    "comment_id": comment_id,
                    "success": False,
                    "message": f"Failed to upload attachment: {response.status_code} - {response.text}"
                }
        
        except Exception as e:
            return {
                "ticket_id": ticket_id,
                "success": False,
                "message": f"Error uploading to ticket: {str(e)}"
            }
    
    def _extract_report_summary(self, report_path: str) -> str:
        """Extract a summary from the HTML or JSON report file"""
        if report_path.endswith('.json'):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                score = data.get('overall_score') or data.get('summary', {}).get('overall_score')
                total_gates = data.get('summary', {}).get('total_gates') or len(data.get('gates', []))
                passed = data.get('summary', {}).get('passed_gates')
                failed = data.get('summary', {}).get('failed_gates')
                warning = data.get('summary', {}).get('warning_gates')
                summary = f"Hard Gate Assessment Summary:\n"
                if score is not None:
                    summary += f"- Compliance Score: {score:.1f}%\n"
                if total_gates is not None:
                    summary += f"- Total Gates: {total_gates}\n"
                if passed is not None:
                    summary += f"- Gates Met: {passed}\n"
                if warning is not None:
                    summary += f"- Partially Met: {warning}\n"
                if failed is not None:
                    summary += f"- Not Met: {failed}\n"
                summary += "\nSee attached report for full details."
                return summary
            except Exception as ex:
                return f"Hard Gate Assessment completed. See attached report for details. (Summary extraction failed: {ex})"
        else:
            return "Hard Gate Assessment completed. See attached HTML report for full details."
    
    def _get_content_type(self, report_type: str) -> str:
        """Get content type for the report type"""
        content_types = {
            "html": "text/html",
            "json": "application/json",
            "pdf": "application/pdf",
            "markdown": "text/markdown"
        }
        return content_types.get(report_type, "application/octet-stream")
    
    def create_jira_issue(self, project_key: str, summary: str, description: str, 
                         issue_type: str = "Task", priority: str = "Medium") -> Dict[str, Any]:
        """Create a new JIRA issue"""
        if not self.is_configured():
            return {
                "success": False,
                "message": "JIRA not configured. Set JIRA_URL and authentication credentials."
            }
        
        try:
            # Determine authentication method
            if self.jira_token:
                auth = None
                headers = self.get_auth_headers()
            else:
                auth = (self.jira_user, self.jira_password)
                headers = {"Content-Type": "application/json"}
            
            # Create issue data
            issue_data = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": summary,
                    "description": description,
                    "issuetype": {
                        "name": issue_type
                    },
                    "priority": {
                        "name": priority
                    }
                }
            }
            
            # Create issue
            create_url = f"{self.jira_url}/rest/api/2/issue"
            
            response = requests.post(
                create_url,
                headers=headers,
                auth=auth,
                json=issue_data,
                verify=self.ssl_verify
            )
            
            if response.status_code == 201:
                issue_data = response.json()
                return {
                    "success": True,
                    "message": f"Successfully created JIRA issue: {issue_data.get('key')}",
                    "issue_key": issue_data.get('key'),
                    "issue_id": issue_data.get('id')
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to create JIRA issue: {response.status_code} - {response.text}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating JIRA issue: {str(e)}"
            }


class JIRAIntegrationTool(BaseTool):
    """Tool for JIRA integration and report uploads"""
    
    name = "jira_integration"
    description = "Upload reports to JIRA and manage issues"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
        self.jira = JIRAIntegration()
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Upload report to JIRA or create issue"""
        try:
            action = args.get("action", "upload_report")
            
            if action == "upload_report":
                return await self._upload_report(args)
            elif action == "create_issue":
                return await self._create_issue(args)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"JIRA integration failed: {str(e)}"
            }
    
    async def _upload_report(self, args: dict) -> dict:
        """Upload report to JIRA"""
        app_id = args.get("app_id")
        report_path = args.get("report_path")
        report_type = args.get("report_type", "html")
        jira_ticket_id = args.get("jira_ticket_id")
        gate_number = args.get("gate_number")
        comment = args.get("comment")
        
        if not app_id or not report_path:
            return {
                "success": False,
                "error": "App ID and report path are required"
            }
        
        result = self.jira.upload_report_to_jira(
            app_id=app_id,
            report_path=report_path,
            report_type=report_type,
            jira_ticket_id=jira_ticket_id,
            gate_number=gate_number,
            comment=comment
        )
        
        return result
    
    async def _create_issue(self, args: dict) -> dict:
        """Create JIRA issue"""
        project_key = args.get("project_key")
        summary = args.get("summary")
        description = args.get("description")
        issue_type = args.get("issue_type", "Task")
        priority = args.get("priority", "Medium")
        
        if not project_key or not summary or not description:
            return {
                "success": False,
                "error": "Project key, summary, and description are required"
            }
        
        result = self.jira.create_jira_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority
        )
        
        return result


# Create wrapper function for Google ADK compatibility
def jira_integration(action: str, app_id: Optional[str] = None, report_path: Optional[str] = None,
                    report_type: str = "html", jira_ticket_id: Optional[str] = None,
                    gate_number: Optional[str] = None, comment: Optional[str] = None,
                    project_key: Optional[str] = None, summary: Optional[str] = None,
                    description: Optional[str] = None, issue_type: str = "Task",
                    priority: str = "Medium", tool_context = None) -> Dict[str, Any]:
    """
    Upload reports to JIRA or create issues.
    
    Args:
        action: Action to perform ("upload_report" or "create_issue")
        app_id: Application ID for report uploads
        report_path: Path to the report file
        report_type: Type of report (html, json, pdf)
        jira_ticket_id: Optional specific JIRA ticket ID
        gate_number: Optional gate number for individual gate upload
        comment: Optional additional comment
        project_key: Project key for creating issues
        summary: Issue summary for creating issues
        description: Issue description for creating issues
        issue_type: Issue type for creating issues
        priority: Issue priority for creating issues
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing operation results
    """
    try:
        jira = JIRAIntegration()
        
        if action == "upload_report":
            if not app_id or not report_path:
                return {
                    "success": False,
                    "error": "App ID and report path are required for upload_report"
                }
            
            result = jira.upload_report_to_jira(
                app_id=app_id,
                report_path=report_path,
                report_type=report_type,
                jira_ticket_id=jira_ticket_id,
                gate_number=gate_number,
                comment=comment
            )
            
            return result
        
        elif action == "create_issue":
            if not project_key or not summary or not description:
                return {
                    "success": False,
                    "error": "Project key, summary, and description are required for create_issue"
                }
            
            result = jira.create_jira_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority=priority
            )
            
            return result
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"JIRA integration failed: {str(e)}"
        } 