import os
import json
import base64
import requests
import urllib3
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Disable SSL warnings and certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class SplunkIntegration:
    """Splunk Integration class for querying and validating Splunk data"""
    
    def __init__(self):
        self.splunk_url = os.getenv("SPLUNK_URL")
        self.username = os.getenv("SPLUNK_USERNAME")
        self.password = os.getenv("SPLUNK_PASSWORD")
        self.token = os.getenv("SPLUNK_TOKEN")
        self.verify_ssl = os.getenv("CODEGATES_SSL_VERIFY", "false").lower() == "true"
        self.timeout = int(os.getenv("CODEGATES_SPLUNK_REQUEST_TIMEOUT", "300"))
        self.max_results = int(os.getenv("CODEGATES_SPLUNK_MAX_RESULTS", "1000"))
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Set authentication
        if self.token:
            self.session.headers.update({"Authorization": f"Splunk {self.token}"})
        elif self.username and self.password:
            # Basic auth for enterprise Splunk
            self.session.auth = (self.username, self.password)
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authentication header based on available credentials"""
        if self.token:
            return {"Authorization": f"Splunk {self.token}"}
        elif self.username and self.password:
            # Basic authentication for enterprise Splunk
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded_credentials}"}
        
        return {}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Splunk connection and return status"""
        if not self.splunk_url:
            return {"status": "error", "message": "SPLUNK_URL not configured"}
        
        try:
            # Test basic connectivity - try to get server info
            response = self.session.get(
                f"{self.splunk_url}/services/server/info",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                server_info = response.json()
                return {
                    "status": "success",
                    "message": f"Connected to Splunk successfully",
                    "splunk_version": server_info.get('entry', [{}])[0].get('content', {}).get('version', 'Unknown'),
                    "server_info": server_info
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
    
    def execute_search(self, query: str, earliest_time: str = "-24h", latest_time: str = "now", 
                      output_mode: str = "json", max_results: Optional[int] = None) -> Dict[str, Any]:
        """Execute a Splunk search query"""
        try:
            if not max_results:
                max_results = self.max_results
            
            # Prepare search parameters
            search_params = {
                "search": query,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "output_mode": output_mode,
                "max_results": max_results,
                "exec_mode": "oneshot"  # For immediate results
            }
            
            response = self.session.post(
                f"{self.splunk_url}/services/search/jobs",
                headers=self._get_auth_header(),
                data=search_params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "results": result.get('results', []),
                    "total_results": len(result.get('results', [])),
                    "query": query,
                    "execution_time": result.get('executionTime', 0)
                }
            else:
                logger.error(f"Failed to execute search: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Search execution failed: {response.status_code}",
                    "results": [],
                    "total_results": 0
                }
                
        except Exception as e:
            logger.error(f"Error executing Splunk search: {str(e)}")
            return {
                "status": "error",
                "message": f"Search execution error: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
    def execute_search_job(self, query: str, earliest_time: str = "-24h", latest_time: str = "now") -> Optional[str]:
        """Start a Splunk search job and return job ID"""
        try:
            search_params = {
                "search": query,
                "earliest_time": earliest_time,
                "latest_time": latest_time,
                "output_mode": "json"
            }
            
            response = self.session.post(
                f"{self.splunk_url}/services/search/jobs",
                headers=self._get_auth_header(),
                data=search_params,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                # Extract job ID from response
                job_id = response.headers.get('Location', '').split('/')[-1]
                return job_id
            else:
                logger.error(f"Failed to start search job: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting search job: {str(e)}")
            return None
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a Splunk search job"""
        try:
            response = self.session.get(
                f"{self.splunk_url}/services/search/jobs/{job_id}",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                job_info = response.json()
                return {
                    "status": "success",
                    "job_id": job_id,
                    "is_done": job_info.get('entry', [{}])[0].get('content', {}).get('isDone', False),
                    "progress": job_info.get('entry', [{}])[0].get('content', {}).get('progress', 0),
                    "result_count": job_info.get('entry', [{}])[0].get('content', {}).get('resultCount', 0)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get job status: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting job status: {str(e)}"
            }
    
    def get_job_results(self, job_id: str, offset: int = 0, count: int = 1000) -> Dict[str, Any]:
        """Get results from a completed Splunk search job"""
        try:
            response = self.session.get(
                f"{self.splunk_url}/services/search/jobs/{job_id}/results",
                headers=self._get_auth_header(),
                params={"offset": offset, "count": count},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "results": result.get('results', []),
                    "total_results": len(result.get('results', [])),
                    "offset": offset,
                    "count": count
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get job results: {response.status_code}",
                    "results": [],
                    "total_results": 0
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting job results: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
    def validate_app_logs(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Validate application logs in Splunk for a specific app_id"""
        try:
            # Search for application logs
            query = f'search index=* app_id="{app_id}" OR source="*{app_id}*" | head 1000'
            
            result = self.execute_search(query, earliest_time=time_range)
            
            if result["status"] == "success":
                log_count = result["total_results"]
                
                # Analyze log patterns
                log_analysis = self._analyze_log_patterns(result["results"])
                
                return {
                    "status": "success",
                    "app_id": app_id,
                    "log_count": log_count,
                    "time_range": time_range,
                    "log_analysis": log_analysis,
                    "has_logs": log_count > 0
                }
            else:
                return {
                    "status": "error",
                    "message": result["message"],
                    "app_id": app_id,
                    "log_count": 0,
                    "has_logs": False
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating app logs: {str(e)}",
                "app_id": app_id,
                "log_count": 0,
                "has_logs": False
            }
    
    def validate_error_logs(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Validate error logs in Splunk for a specific app_id"""
        try:
            # Search for error logs
            query = f'search index=* (app_id="{app_id}" OR source="*{app_id}*") (level=ERROR OR level=error OR severity=ERROR OR severity=error OR "ERROR" OR "error") | head 1000'
            
            result = self.execute_search(query, earliest_time=time_range)
            
            if result["status"] == "success":
                error_count = result["total_results"]
                
                # Analyze error patterns
                error_analysis = self._analyze_error_patterns(result["results"])
                
                return {
                    "status": "success",
                    "app_id": app_id,
                    "error_count": error_count,
                    "time_range": time_range,
                    "error_analysis": error_analysis,
                    "has_errors": error_count > 0
                }
            else:
                return {
                    "status": "error",
                    "message": result["message"],
                    "app_id": app_id,
                    "error_count": 0,
                    "has_errors": False
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating error logs: {str(e)}",
                "app_id": app_id,
                "error_count": 0,
                "has_errors": False
            }
    
    def validate_performance_metrics(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Validate performance metrics in Splunk for a specific app_id"""
        try:
            # Search for performance metrics
            query = f'search index=* (app_id="{app_id}" OR source="*{app_id}*") (response_time OR latency OR duration OR "response time" OR "response_time") | head 1000'
            
            result = self.execute_search(query, earliest_time=time_range)
            
            if result["status"] == "success":
                metric_count = result["total_results"]
                
                # Analyze performance patterns
                performance_analysis = self._analyze_performance_patterns(result["results"])
                
                return {
                    "status": "success",
                    "app_id": app_id,
                    "metric_count": metric_count,
                    "time_range": time_range,
                    "performance_analysis": performance_analysis,
                    "has_metrics": metric_count > 0
                }
            else:
                return {
                    "status": "error",
                    "message": result["message"],
                    "app_id": app_id,
                    "metric_count": 0,
                    "has_metrics": False
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating performance metrics: {str(e)}",
                "app_id": app_id,
                "metric_count": 0,
                "has_metrics": False
            }
    
    def _analyze_log_patterns(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze log patterns for insights"""
        if not logs:
            return {"total_logs": 0, "log_levels": {}, "sources": []}
        
        log_levels = {}
        sources = set()
        
        for log in logs:
            # Extract log level
            level = log.get('level', log.get('severity', 'INFO')).upper()
            log_levels[level] = log_levels.get(level, 0) + 1
            
            # Extract source
            source = log.get('source', 'unknown')
            sources.add(source)
        
        return {
            "total_logs": len(logs),
            "log_levels": log_levels,
            "sources": list(sources),
            "most_common_level": max(log_levels.items(), key=lambda x: x[1])[0] if log_levels else "INFO"
        }
    
    def _analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns for insights"""
        if not errors:
            return {"total_errors": 0, "error_types": {}, "error_messages": []}
        
        error_types = {}
        error_messages = []
        
        for error in errors:
            # Extract error type
            error_type = error.get('error_type', error.get('exception', 'UNKNOWN'))
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Extract error message
            message = error.get('message', error.get('_raw', ''))
            if message:
                error_messages.append(message[:200])  # Truncate long messages
        
        return {
            "total_errors": len(errors),
            "error_types": error_types,
            "error_messages": error_messages[:10],  # Top 10 error messages
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else "UNKNOWN"
        }
    
    def _analyze_performance_patterns(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance patterns for insights"""
        if not metrics:
            return {"total_metrics": 0, "avg_response_time": 0, "performance_ranges": {}}
        
        response_times = []
        
        for metric in metrics:
            # Extract response time
            response_time = metric.get('response_time', metric.get('duration', metric.get('latency', 0)))
            if response_time and isinstance(response_time, (int, float)):
                response_times.append(float(response_time))
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # Categorize performance ranges
            performance_ranges = {
                "excellent": len([rt for rt in response_times if rt < 100]),
                "good": len([rt for rt in response_times if 100 <= rt < 500]),
                "fair": len([rt for rt in response_times if 500 <= rt < 1000]),
                "poor": len([rt for rt in response_times if rt >= 1000])
            }
        else:
            avg_response_time = max_response_time = min_response_time = 0
            performance_ranges = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        
        return {
            "total_metrics": len(metrics),
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "performance_ranges": performance_ranges
        }
    
    def comprehensive_app_validation(self, app_id: str, time_range: str = "-24h") -> Dict[str, Any]:
        """Perform comprehensive validation of app data in Splunk"""
        try:
            results = {
                "app_id": app_id,
                "time_range": time_range,
                "validation_timestamp": datetime.now().isoformat(),
                "overall_status": "unknown"
            }
            
            # Validate app logs
            log_validation = self.validate_app_logs(app_id, time_range)
            results["log_validation"] = log_validation
            
            # Validate error logs
            error_validation = self.validate_error_logs(app_id, time_range)
            results["error_validation"] = error_validation
            
            # Validate performance metrics
            performance_validation = self.validate_performance_metrics(app_id, time_range)
            results["performance_validation"] = performance_validation
            
            # Determine overall status
            has_logs = log_validation.get("has_logs", False)
            has_errors = error_validation.get("has_errors", False)
            has_metrics = performance_validation.get("has_metrics", False)
            
            if has_logs and not has_errors and has_metrics:
                results["overall_status"] = "excellent"
            elif has_logs and not has_errors:
                results["overall_status"] = "good"
            elif has_logs:
                results["overall_status"] = "fair"
            else:
                results["overall_status"] = "poor"
            
            results["status"] = "success"
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in comprehensive validation: {str(e)}",
                "app_id": app_id,
                "overall_status": "unknown"
            }


# Global instance
splunk_integration = SplunkIntegration() 