import os
import json
import base64
import requests
import urllib3
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# Disable SSL warnings and certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class JiraIntegration:
    """JIRA Integration class for posting reports to JIRA issues"""
    
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.username = os.getenv("JIRA_USERNAME")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        self.verify_ssl = os.getenv("CODEGATES_SSL_VERIFY", "false").lower() == "true"
        self.timeout = int(os.getenv("CODEGATES_JIRA_REQUEST_TIMEOUT", "300"))
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Set authentication
        if self.username and self.api_token:
            self.session.auth = (self.username, self.api_token)
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authentication header based on available credentials"""
        if self.username and self.api_token:
            # Basic authentication
            credentials = f"{self.username}:{self.api_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded_credentials}"}
        else:
            # Try Personal Access Token (PAT) if available
            pat_token = os.getenv("JIRA_PAT_TOKEN")
            if pat_token:
                return {"Authorization": f"Bearer {pat_token}"}
        
        return {}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test JIRA connection and return status"""
        if not self.jira_url:
            return {"status": "error", "message": "JIRA_URL not configured"}
        
        try:
            # Test basic connectivity
            response = self.session.get(
                f"{self.jira_url}/rest/api/2/myself",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "status": "success",
                    "message": f"Connected to JIRA as {user_info.get('displayName', 'Unknown')}",
                    "jira_version": response.headers.get('X-AUSERNAME', 'Unknown'),
                    "server_info": user_info
                }
            elif response.status_code == 401:
                return {"status": "error", "message": "Authentication failed - check credentials"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Access denied - check permissions"}
            else:
                return {"status": "error", "message": f"Connection failed: {response.status_code}"}
                
        except requests.exceptions.SSLError as e:
            return {"status": "error", "message": f"SSL Error: {str(e)}"}
        except requests.exceptions.ConnectionError as e:
            return {"status": "error", "message": f"Connection Error: {str(e)}"}
        except requests.exceptions.Timeout as e:
            return {"status": "error", "message": f"Timeout Error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get JIRA issue details"""
        try:
            response = self.session.get(
                f"{self.jira_url}/rest/api/2/issue/{issue_key}",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get issue {issue_key}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {str(e)}")
            return None
    
    def add_comment(self, issue_key: str, comment_body: str) -> Optional[Dict[str, Any]]:
        """Add comment to JIRA issue"""
        try:
            comment_data = {
                "body": comment_body
            }
            
            response = self.session.post(
                f"{self.jira_url}/rest/api/2/issue/{issue_key}/comment",
                headers=self._get_auth_header(),
                json=comment_data,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Failed to add comment to {issue_key}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding comment to {issue_key}: {str(e)}")
            return None
    
    def attach_file(self, issue_key: str, file_path: str, filename: Optional[str] = None) -> bool:
        """Attach file to JIRA issue"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            if not filename:
                filename = os.path.basename(file_path)
            
            # Prepare file for upload
            with open(file_path, 'rb') as file:
                files = {'file': (filename, file, 'application/octet-stream')}
                
                response = self.session.post(
                    f"{self.jira_url}/rest/api/2/issue/{issue_key}/attachments",
                    headers=self._get_auth_header(),
                    files=files,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                logger.info(f"Successfully attached {filename} to {issue_key}")
                return True
            else:
                logger.error(f"Failed to attach file to {issue_key}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error attaching file to {issue_key}: {str(e)}")
            return False
    
    def create_issue(self, summary: str, description: str, issue_type: str = "Task") -> Optional[str]:
        """Create a new JIRA issue"""
        try:
            issue_data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
            }
            
            response = self.session.post(
                f"{self.jira_url}/rest/api/2/issue",
                headers=self._get_auth_header(),
                json=issue_data,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                issue_info = response.json()
                return issue_info.get('key')
            else:
                logger.error(f"Failed to create issue: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            return None
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search JIRA issues using JQL"""
        try:
            search_data = {
                "jql": jql,
                "maxResults": max_results,
                "fields": ["key", "summary", "status", "assignee"]
            }
            
            response = self.session.post(
                f"{self.jira_url}/rest/api/2/search",
                headers=self._get_auth_header(),
                json=search_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('issues', [])
            else:
                logger.error(f"Failed to search issues: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching issues: {str(e)}")
            return []
    
    def post_report_to_jira(self, app_id: str, report_path: str, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Post scan report to JIRA stories associated with the app_id"""
        try:
            # Get JIRA stories for this app_id
            from .db_integration import fetch_jira_stories
            jira_stories = fetch_jira_stories(app_id=app_id)
            
            if not jira_stories:
                return {
                    "status": "warning",
                    "message": f"No JIRA stories found for app_id: {app_id}",
                    "stories_processed": 0
                }
            
            results = []
            for story_key in jira_stories:
                try:
                    # Verify the issue exists
                    issue = self.get_issue(story_key)
                    if not issue:
                        logger.warning(f"JIRA issue {story_key} not found or not accessible")
                        continue
                    
                    # Create comment with scan summary
                    comment_body = self._create_scan_comment(scan_results, app_id)
                    
                    # Add comment
                    comment_result = self.add_comment(story_key, comment_body)
                    if not comment_result:
                        logger.error(f"Failed to add comment to {story_key}")
                        continue
                    
                    # Attach HTML report if available
                    attachment_success = False
                    if os.path.exists(report_path):
                        attachment_success = self.attach_file(story_key, report_path, f"codegates_report_{app_id}.html")
                    
                    results.append({
                        "story_key": story_key,
                        "comment_added": True,
                        "attachment_added": attachment_success,
                        "issue_summary": issue.get('fields', {}).get('summary', 'Unknown')
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing story {story_key}: {str(e)}")
                    results.append({
                        "story_key": story_key,
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "message": f"Posted report to {len(results)} JIRA stories for app_id: {app_id}",
                "stories_processed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error posting report to JIRA: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to post report to JIRA: {str(e)}",
                "stories_processed": 0
            }
    
    def _create_scan_comment(self, scan_results: Dict[str, Any], app_id: str) -> str:
        """Create a formatted comment for JIRA with scan results"""
        overall_score = scan_results.get('overall_score', 0)
        total_gates = scan_results.get('total_gates', 0)
        passed_gates = scan_results.get('passed_gates', 0)
        failed_gates = scan_results.get('failed_gates', 0)
        warning_gates = scan_results.get('warning_gates', 0)
        
        # Create color-coded status
        if overall_score >= 80:
            status_emoji = "🟢"
            status_text = "PASS"
        elif overall_score >= 60:
            status_emoji = "🟡"
            status_text = "WARNING"
        else:
            status_emoji = "🔴"
            status_text = "FAIL"
        
        comment = f"""
{status_emoji} **CodeGates Scan Report for {app_id}**

**Overall Score:** {overall_score:.1f}% ({status_text})

**Gate Summary:**
• ✅ Passed: {passed_gates}
• ⚠️ Warnings: {warning_gates}
• ❌ Failed: {failed_gates}
• 📊 Total Gates: {total_gates}

**Details:**
• Scan completed at: {scan_results.get('completed_at', 'Unknown')}
• Total files analyzed: {scan_results.get('total_files', 0)}
• Total lines of code: {scan_results.get('total_lines', 0)}

*This report was automatically generated by CodeGates. Please review the attached HTML report for detailed analysis.*
        """
        
        return comment.strip()


# Global instance
jira_integration = JiraIntegration() 