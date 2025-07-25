"""
Splunk Integration for CodeGates
Provides functionality to execute Splunk queries and analyze results

Preferred configuration (token-based authentication):

    SPLUNK_URL=https://your-splunk-instance.com:8089
    SPLUNK_TOKEN=your-splunk-access-token
    # CODEGATES_SSL_VERIFY=false  # Optional: for self-signed certs

Username/password is supported as a fallback for legacy/enterprise Splunk, but token-based authentication is recommended for all new deployments.
"""

import os
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

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
            search_url = f"{self.splunk_url.rstrip('/')}/services/search/jobs"
            response = requests.post(
                search_url,
                auth=auth,
                headers=headers,
                data=search_payload,
                verify=self.ssl_verify,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                # Search job created successfully
                job_id = response.headers.get("Location", "").split("/")[-1]
                
                # Wait for job to complete and get results
                return self._get_job_results(job_id, auth, headers)
            else:
                return {
                    "status": "error",
                    "message": f"Splunk search failed: {response.status_code} - {response.text}",
                    "results": [],
                    "total_results": 0
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Splunk query execution failed: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
    def _get_job_results(self, job_id: str, auth: Optional[tuple], headers: Dict[str, str]) -> Dict[str, Any]:
        """Get results from a Splunk search job"""
        try:
            # Check job status
            status_url = f"{self.splunk_url.rstrip('/')}/services/search/jobs/{job_id}"
            
            # Wait for job completion (with timeout)
            max_wait_time = 120  # seconds
            wait_time = 0
            while wait_time < max_wait_time:
                status_response = requests.get(
                    status_url,
                    auth=auth,
                    headers=headers,
                    params={"output_mode": "json"},
                    verify=self.ssl_verify,
                    timeout=30
                )
                
                print("Job status response text:", status_response.text)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    is_done = status_data.get("entry", [{}])[0].get("content", {}).get("isDone", False)
                    
                    if is_done:
                        # Get results
                        results_url = f"{status_url}/results"
                        results_response = requests.get(
                            results_url,
                            auth=auth,
                            headers=headers,
                            params={"output_mode": "json"},
                            verify=self.ssl_verify,
                            timeout=30
                        )
                        
                        print("Job results response text:", results_response.text)
                        
                        if results_response.status_code == 200:
                            results_data = results_response.json()
                            results = results_data.get("results", [])
                            
                            return {
                                "status": "success",
                                "message": "Splunk query executed successfully",
                                "results": results,
                                "total_results": len(results),
                                "job_id": job_id,
                                "query": status_data.get("entry", [{}])[0].get("content", {}).get("search", "")
                            }
                        else:
                            return {
                                "status": "error",
                                "message": f"Failed to get results: {results_response.status_code}",
                                "results": [],
                                "total_results": 0
                            }
                
                # Wait before checking again
                import time
                time.sleep(2)
                wait_time += 2
            
            return {
                "status": "error",
                "message": "Splunk job timed out",
                "results": [],
                "total_results": 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get job results: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
    def analyze_log_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze Splunk results for log patterns and insights
        
        Args:
            results: List of Splunk search results
            
        Returns:
            Dictionary containing analysis results
        """
        if not results:
            return {
                "total_events": 0,
                "error_count": 0,
                "warning_count": 0,
                "info_count": 0,
                "common_patterns": [],
                "error_types": [],
                "performance_metrics": {}
            }
        
        analysis = {
            "total_events": len(results),
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "common_patterns": [],
            "error_types": [],
            "performance_metrics": {}
        }
        
        # Analyze each result
        for result in results:
            # Extract log level and message
            log_level = result.get("level", "").lower()
            message = result.get("message", "").lower()
            
            # Count by log level
            if "error" in log_level or "error" in message:
                analysis["error_count"] += 1
            elif "warn" in log_level or "warning" in message:
                analysis["warning_count"] += 1
            elif "info" in log_level:
                analysis["info_count"] += 1
            
            # Extract error types
            if "error" in log_level or "error" in message:
                # Simple error type extraction
                if "timeout" in message:
                    analysis["error_types"].append("timeout")
                elif "connection" in message:
                    analysis["error_types"].append("connection")
                elif "permission" in message:
                    analysis["error_types"].append("permission")
                elif "not found" in message:
                    analysis["error_types"].append("not_found")
        
        # Remove duplicates from error types
        analysis["error_types"] = list(set(analysis["error_types"]))
        
        return analysis

# Global instance
splunk_integration = SplunkIntegration()

def execute_splunk_query(query: str, app_id: Optional[str] = None, earliest_time: str = "-24h", latest_time: str = "now") -> Dict[str, Any]:
    """
    Execute a Splunk query and return results
    
    Args:
        query: The SPL query to execute
        app_id: Optional app_id for filtering
        earliest_time: Start time for search (default: -24h)
        latest_time: End time for search (default: now)
        
    Returns:
        Dictionary containing query results and analysis
    """
    if not query:
        return {
            "status": "skipped",
            "message": "No Splunk query provided",
            "results": [],
            "analysis": {}
        }
    
    # Execute the query
    result = splunk_integration.execute_query(query, app_id, earliest_time, latest_time)
    
    if result["status"] == "success":
        # Analyze the results
        analysis = splunk_integration.analyze_log_patterns(result["results"])
        result["analysis"] = analysis
    
    return result 