"""
Splunk Integration Tool
Comprehensive Splunk integration for evidence collection and log analysis
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
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


class SplunkIntegration:
    """Handles Splunk integration for CodeGates validation"""
    
    def __init__(self):
        self.splunk_url = os.getenv("SPLUNK_URL")
        self.splunk_token = os.getenv("SPLUNK_TOKEN")
        self.splunk_username = os.getenv("SPLUNK_USERNAME")
        self.splunk_password = os.getenv("SPLUNK_PASSWORD")
        self.ssl_verify = False  # Force SSL verification off for Splunk
        self.timeout = int(os.getenv("CODEGATES_SPLUNK_REQUEST_TIMEOUT", "300"))
        self.max_results = int(os.getenv("CODEGATES_SPLUNK_MAX_RESULTS", "1000"))
    
    def is_configured(self) -> bool:
        """Check if Splunk is properly configured"""
        if not self.splunk_url:
            print("[SplunkIntegration] ⚠️ Warning: No Splunk URL provided. Please set SPLUNK_URL.")
            return False
        # Token-based authentication is preferred
        if not self.splunk_token and (not self.splunk_username or not self.splunk_password):
            print("[SplunkIntegration] ⚠️ Warning: No authentication credentials provided. Please set SPLUNK_TOKEN or SPLUNK_USERNAME/SPLUNK_PASSWORD.")
            return False
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Splunk API"""
        if self.splunk_token:
            return {
                "Authorization": f"Bearer {self.splunk_token}",
                "Content-Type": "application/json"
            }
        else:
            print("[SplunkIntegration] ⚠️ Warning: Using username/password authentication. Token-based authentication is preferred.")
            return {
                "Content-Type": "application/json"
            }
    
    def execute_query(self, query: str, app_id: Optional[str] = None, 
                     earliest_time: str = "-24h", latest_time: str = "now") -> Dict[str, Any]:
        """
        Execute a Splunk query and return results
        
        Args:
            query: The SPL query to execute
            app_id: Optional app_id to append to query
            earliest_time: Start time for search (default: -24h)
            latest_time: End time for search (default: now)
            
        Returns:
            Dictionary containing query results and metadata
        """
        if not self.is_configured():
            return {
                "status": "error",
                "message": "Splunk not configured. Set SPLUNK_URL and authentication credentials.",
                "results": [],
                "total_results": 0
            }
        
        try:
            # Build search payload
            search_payload = {
                "search": query,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "max_results": self.max_results,
                "output_mode": "json"
            }
            
            # Determine authentication method
            if self.splunk_token:
                # Token-based authentication
                auth = None
                headers = self.get_auth_headers()
            else:
                # Username/password authentication
                auth = (self.splunk_username, self.splunk_password)
                headers = {"Content-Type": "application/json"}
            
            # Execute search
            search_url = f"{self.splunk_url}/services/search/jobs/export"
            
            response = requests.post(
                search_url,
                headers=headers,
                auth=auth,
                data=search_payload,
                timeout=self.timeout,
                verify=self.ssl_verify
            )
            
            if response.status_code == 200:
                # Parse results
                results = []
                for line in response.text.strip().split('\n'):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            results.append(result)
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "status": "success",
                    "message": "Query executed successfully",
                    "results": results,
                    "total_results": len(results),
                    "query": query,
                    "time_range": f"{earliest_time} to {latest_time}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Splunk API error: {response.status_code} - {response.text}",
                    "results": [],
                    "total_results": 0
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Splunk query failed: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
    def get_structured_logs_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for structured logging gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_json=if(match(_raw, "\\{{[^}}]*\\}}"), 1, 0)
        | eval has_timestamp=if(match(_raw, "\\d{{4}}-\\d{{2}}-\\d{{2}}.*\\d{{2}}:\\d{{2}}:\\d{{2}}"), 1, 0)
        | eval has_level=if(match(_raw, "(INFO|WARN|ERROR|DEBUG|FATAL)"), 1, 0)
        | eval has_context=if(match(_raw, "(user_id|session_id|request_id|correlation_id)"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_json) as json_logs,
            sum(has_timestamp) as timestamp_logs,
            sum(has_level) as level_logs,
            sum(has_context) as context_logs
        | eval 
            json_percentage=round((json_logs/total_logs)*100, 2),
            timestamp_percentage=round((timestamp_logs/total_logs)*100, 2),
            level_percentage=round((level_logs/total_logs)*100, 2),
            context_percentage=round((context_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)
    
    def get_secret_logging_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for secret logging gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_password=if(match(_raw, "(?i)(password|passwd|pwd).*=.*['\"][^'\"]+['\"]"), 1, 0)
        | eval has_token=if(match(_raw, "(?i)(token|api_key|secret).*=.*['\"][^'\"]+['\"]"), 1, 0)
        | eval has_credential=if(match(_raw, "(?i)(credential|auth).*=.*['\"][^'\"]+['\"]"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_password) as password_logs,
            sum(has_token) as token_logs,
            sum(has_credential) as credential_logs
        | eval 
            password_percentage=round((password_logs/total_logs)*100, 2),
            token_percentage=round((token_logs/total_logs)*100, 2),
            credential_percentage=round((credential_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)
    
    def get_alerting_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for alerting gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_alert=if(match(_raw, "(?i)(alert|alarm|critical|warning)"), 1, 0)
        | eval has_action=if(match(_raw, "(?i)(action|remediation|fix|resolve)"), 1, 0)
        | eval has_threshold=if(match(_raw, "(?i)(threshold|limit|max|min)"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_alert) as alert_logs,
            sum(has_action) as action_logs,
            sum(has_threshold) as threshold_logs
        | eval 
            alert_percentage=round((alert_logs/total_logs)*100, 2),
            action_percentage=round((action_logs/total_logs)*100, 2),
            threshold_percentage=round((threshold_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)
    
    def get_audit_trail_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for audit trail gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_user_action=if(match(_raw, "(?i)(user.*action|login|logout|create|update|delete)"), 1, 0)
        | eval has_timestamp=if(match(_raw, "\\d{{4}}-\\d{{2}}-\\d{{2}}.*\\d{{2}}:\\d{{2}}:\\d{{2}}"), 1, 0)
        | eval has_user_id=if(match(_raw, "(?i)(user_id|username|user.*id)"), 1, 0)
        | eval has_resource=if(match(_raw, "(?i)(resource|file|database|api)"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_user_action) as user_action_logs,
            sum(has_timestamp) as timestamp_logs,
            sum(has_user_id) as user_id_logs,
            sum(has_resource) as resource_logs
        | eval 
            user_action_percentage=round((user_action_logs/total_logs)*100, 2),
            timestamp_percentage=round((timestamp_logs/total_logs)*100, 2),
            user_id_percentage=round((user_id_logs/total_logs)*100, 2),
            resource_percentage=round((resource_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)
    
    def get_correlation_id_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for correlation ID gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_correlation=if(match(_raw, "(?i)(correlation_id|request_id|trace_id|span_id)"), 1, 0)
        | eval has_session=if(match(_raw, "(?i)(session_id|session.*id)"), 1, 0)
        | eval has_transaction=if(match(_raw, "(?i)(transaction_id|txn_id)"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_correlation) as correlation_logs,
            sum(has_session) as session_logs,
            sum(has_transaction) as transaction_logs
        | eval 
            correlation_percentage=round((correlation_logs/total_logs)*100, 2),
            session_percentage=round((session_logs/total_logs)*100, 2),
            transaction_percentage=round((transaction_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)
    
    def get_api_logs_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for API logging gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_api_call=if(match(_raw, "(?i)(api|endpoint|request|response)"), 1, 0)
        | eval has_method=if(match(_raw, "(GET|POST|PUT|DELETE|PATCH)"), 1, 0)
        | eval has_status=if(match(_raw, "(?i)(status.*code|http.*status)"), 1, 0)
        | eval has_duration=if(match(_raw, "(?i)(duration|response.*time|latency)"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_api_call) as api_call_logs,
            sum(has_method) as method_logs,
            sum(has_status) as status_logs,
            sum(has_duration) as duration_logs
        | eval 
            api_call_percentage=round((api_call_logs/total_logs)*100, 2),
            method_percentage=round((method_logs/total_logs)*100, 2),
            status_percentage=round((status_logs/total_logs)*100, 2),
            duration_percentage=round((duration_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)
    
    def get_error_handling_evidence(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Get evidence for error handling gate"""
        query = f"""
        search index=* app_id="{app_id}" 
        | eval has_error=if(match(_raw, "(?i)(error|exception|fail|failure)"), 1, 0)
        | eval has_stack_trace=if(match(_raw, "(?i)(stack.*trace|stacktrace)"), 1, 0)
        | eval has_error_code=if(match(_raw, "(?i)(error.*code|exception.*code)"), 1, 0)
        | eval has_error_message=if(match(_raw, "(?i)(error.*message|exception.*message)"), 1, 0)
        | stats 
            count as total_logs,
            sum(has_error) as error_logs,
            sum(has_stack_trace) as stack_trace_logs,
            sum(has_error_code) as error_code_logs,
            sum(has_error_message) as error_message_logs
        | eval 
            error_percentage=round((error_logs/total_logs)*100, 2),
            stack_trace_percentage=round((stack_trace_logs/total_logs)*100, 2),
            error_code_percentage=round((error_code_logs/total_logs)*100, 2),
            error_message_percentage=round((error_message_logs/total_logs)*100, 2)
        """
        
        return self.execute_query(query, app_id, time_range)


class SplunkIntegrationTool(BaseTool):
    """Tool for Splunk integration and evidence collection"""
    
    name = "splunk_integration"
    description = "Execute Splunk queries and collect evidence for gate validation"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
        self.splunk = SplunkIntegration()
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Execute Splunk queries and collect evidence"""
        try:
            app_id = args.get("app_id")
            query = args.get("query")
            gate_name = args.get("gate_name")
            time_range = args.get("time_range", "-24h")
            
            if not app_id:
                return {
                    "success": False,
                    "error": "App ID is required for Splunk queries"
                }
            
            # Execute specific gate query or custom query
            if gate_name:
                result = self._execute_gate_query(gate_name, app_id, time_range)
            elif query:
                result = self.splunk.execute_query(query, app_id, time_range)
            else:
                return {
                    "success": False,
                    "error": "Either gate_name or query is required"
                }
            
            return {
                "success": result.get("status") == "success",
                "app_id": app_id,
                "gate_name": gate_name,
                "query": query,
                "time_range": time_range,
                "results": result.get("results", []),
                "total_results": result.get("total_results", 0),
                "message": result.get("message", "")
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Splunk integration failed: {str(e)}"
            }
    
    def _execute_gate_query(self, gate_name: str, app_id: str, time_range: str) -> Dict[str, Any]:
        """Execute query for specific gate"""
        gate_queries = {
            "STRUCTURED_LOGS": self.splunk.get_structured_logs_evidence,
            "AVOID_LOGGING_SECRETS": self.splunk.get_secret_logging_evidence,
            "ALERTING_ACTIONABLE": self.splunk.get_alerting_evidence,
            "AUDIT_TRAIL": self.splunk.get_audit_trail_evidence,
            "CORRELATION_ID": self.splunk.get_correlation_id_evidence,
            "LOG_API_CALLS": self.splunk.get_api_logs_evidence,
            "ERROR_HANDLING": self.splunk.get_error_handling_evidence
        }
        
        if gate_name in gate_queries:
            return gate_queries[gate_name](app_id, time_range)
        else:
            return {
                "status": "error",
                "message": f"No predefined query for gate: {gate_name}",
                "results": [],
                "total_results": 0
            }


# Create wrapper function for Google ADK compatibility
def splunk_integration(app_id: str, query: Optional[str] = None, gate_name: Optional[str] = None, 
                      time_range: str = "-24h", tool_context = None) -> Dict[str, Any]:
    """
    Execute Splunk queries and collect evidence for gate validation.
    
    Args:
        app_id: Application ID for filtering logs
        query: Custom SPL query to execute
        gate_name: Name of the gate for predefined queries
        time_range: Time range for the query (default: -24h)
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing query results and evidence
    """
    try:
        if not app_id:
            return {
                "success": False,
                "error": "App ID is required for Splunk queries"
            }
        
        splunk = SplunkIntegration()
        
        # Execute specific gate query or custom query
        if gate_name:
            result = _execute_gate_query(gate_name, app_id, time_range, splunk)
        elif query:
            result = splunk.execute_query(query, app_id, time_range)
        else:
            return {
                "success": False,
                "error": "Either gate_name or query is required"
            }
        
        return {
            "success": result.get("status") == "success",
            "app_id": app_id,
            "gate_name": gate_name,
            "query": query,
            "time_range": time_range,
            "results": result.get("results", []),
            "total_results": result.get("total_results", 0),
            "message": result.get("message", "")
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Splunk integration failed: {str(e)}"
        }


def _execute_gate_query(gate_name: str, app_id: str, time_range: str, splunk: SplunkIntegration) -> Dict[str, Any]:
    """Execute query for specific gate"""
    gate_queries = {
        "STRUCTURED_LOGS": splunk.get_structured_logs_evidence,
        "AVOID_LOGGING_SECRETS": splunk.get_secret_logging_evidence,
        "ALERTING_ACTIONABLE": splunk.get_alerting_evidence,
        "AUDIT_TRAIL": splunk.get_audit_trail_evidence,
        "CORRELATION_ID": splunk.get_correlation_id_evidence,
        "LOG_API_CALLS": splunk.get_api_logs_evidence,
        "ERROR_HANDLING": splunk.get_error_handling_evidence
    }
    
    if gate_name in gate_queries:
        return gate_queries[gate_name](app_id, time_range)
    else:
        return {
            "status": "error",
            "message": f"No predefined query for gate: {gate_name}",
            "results": [],
            "total_results": 0
        } 