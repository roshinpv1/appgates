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

class AppDynamicsIntegration:
    """AppDynamics Integration class for querying and validating AppDynamics data"""
    
    def __init__(self):
        self.appd_url = os.getenv("APPDYNAMICS_URL")
        self.username = os.getenv("APPDYNAMICS_USERNAME")
        self.password = os.getenv("APPDYNAMICS_PASSWORD")
        self.client_id = os.getenv("APPDYNAMICS_CLIENT_ID")
        self.client_secret = os.getenv("APPDYNAMICS_CLIENT_SECRET")
        self.account_name = os.getenv("APPDYNAMICS_ACCOUNT_NAME")
        self.verify_ssl = os.getenv("CODEGATES_SSL_VERIFY", "false").lower() == "true"
        self.timeout = int(os.getenv("CODEGATES_APPDYNAMICS_REQUEST_TIMEOUT", "300"))
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.verify = self.verify_ssl
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Authentication token
        self.auth_token = None
        self.token_expiry = None
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Get authentication header based on available credentials"""
        if self.auth_token and self.token_expiry and datetime.now() < self.token_expiry:
            return {"Authorization": f"Bearer {self.auth_token}"}
        elif self.username and self.password:
            # Basic authentication for enterprise AppDynamics
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded_credentials}"}
        
        return {}
    
    def _authenticate(self) -> bool:
        """Authenticate with AppDynamics and get access token"""
        try:
            if self.client_id and self.client_secret:
                # OAuth2 authentication for AppDynamics Cloud
                auth_url = f"{self.appd_url}/oauth/access_token"
                auth_data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
                
                response = self.session.post(
                    auth_url,
                    data=auth_data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.auth_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status_code}")
                    return False
            else:
                # Basic auth for enterprise
                return True
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test AppDynamics connection and return status"""
        if not self.appd_url:
            return {"status": "error", "message": "APPDYNAMICS_URL not configured"}
        
        try:
            # Authenticate first
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed"}
            
            # Test basic connectivity - try to get controller info
            response = self.session.get(
                f"{self.appd_url}/controller/rest/serverstatus",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                server_info = response.json()
                return {
                    "status": "success",
                    "message": f"Connected to AppDynamics successfully",
                    "appd_version": server_info.get('version', 'Unknown'),
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
    
    def get_applications(self) -> Dict[str, Any]:
        """Get list of applications from AppDynamics"""
        try:
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed", "applications": []}
            
            response = self.session.get(
                f"{self.appd_url}/controller/rest/applications",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                applications = response.json()
                return {
                    "status": "success",
                    "applications": applications,
                    "total_applications": len(applications)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get applications: {response.status_code}",
                    "applications": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting applications: {str(e)}",
                "applications": []
            }
    
    def get_application_by_name(self, app_name: str) -> Dict[str, Any]:
        """Get specific application by name"""
        try:
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed"}
            
            response = self.session.get(
                f"{self.appd_url}/controller/rest/applications",
                headers=self._get_auth_header(),
                params={"name": app_name},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                applications = response.json()
                if applications:
                    return {
                        "status": "success",
                        "application": applications[0]
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Application '{app_name}' not found"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get application: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting application: {str(e)}"
            }
    
    def get_application_metrics(self, app_id: int, metric_path: str = "Business Transaction Performance|Business Transactions|*|*|Calls per Minute") -> Dict[str, Any]:
        """Get application metrics from AppDynamics"""
        try:
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed", "metrics": []}
            
            # Get metrics for the last hour
            end_time = int(time.time() * 1000)
            start_time = end_time - (60 * 60 * 1000)  # 1 hour ago
            
            response = self.session.get(
                f"{self.appd_url}/controller/rest/applications/{app_id}/metric-data",
                headers=self._get_auth_header(),
                params={
                    "metric-path": metric_path,
                    "time-range-type": "BEFORE_NOW",
                    "duration-in-mins": "60",
                    "rollup": "true"
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                metrics = response.json()
                return {
                    "status": "success",
                    "metrics": metrics,
                    "app_id": app_id,
                    "metric_path": metric_path
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get metrics: {response.status_code}",
                    "metrics": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting metrics: {str(e)}",
                "metrics": []
            }
    
    def get_health_rules(self, app_id: int) -> Dict[str, Any]:
        """Get health rules for an application"""
        try:
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed", "health_rules": []}
            
            response = self.session.get(
                f"{self.appd_url}/controller/rest/applications/{app_id}/health-rules",
                headers=self._get_auth_header(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                health_rules = response.json()
                return {
                    "status": "success",
                    "health_rules": health_rules,
                    "app_id": app_id,
                    "total_health_rules": len(health_rules)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get health rules: {response.status_code}",
                    "health_rules": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting health rules: {str(e)}",
                "health_rules": []
            }
    
    def get_errors(self, app_id: int, time_range: str = "60") -> Dict[str, Any]:
        """Get error information for an application"""
        try:
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed", "errors": []}
            
            response = self.session.get(
                f"{self.appd_url}/controller/rest/applications/{app_id}/errors",
                headers=self._get_auth_header(),
                params={"time-range-type": "BEFORE_NOW", "duration-in-mins": time_range},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                errors = response.json()
                return {
                    "status": "success",
                    "errors": errors,
                    "app_id": app_id,
                    "total_errors": len(errors)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get errors: {response.status_code}",
                    "errors": []
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting errors: {str(e)}",
                "errors": []
            }
    
    def get_performance_data(self, app_id: int, time_range: str = "60") -> Dict[str, Any]:
        """Get performance data for an application"""
        try:
            if not self._authenticate():
                return {"status": "error", "message": "Authentication failed", "performance": {}}
            
            # Get various performance metrics
            metrics = {
                "response_time": "Business Transaction Performance|Business Transactions|*|*|Average Response Time (ms)",
                "throughput": "Business Transaction Performance|Business Transactions|*|*|Calls per Minute",
                "error_rate": "Business Transaction Performance|Business Transactions|*|*|Errors per Minute",
                "cpu_usage": "Hardware Resources|*|*|*|CPU Used %",
                "memory_usage": "Hardware Resources|*|*|*|Memory Used %"
            }
            
            performance_data = {}
            
            for metric_name, metric_path in metrics.items():
                response = self.session.get(
                    f"{self.appd_url}/controller/rest/applications/{app_id}/metric-data",
                    headers=self._get_auth_header(),
                    params={
                        "metric-path": metric_path,
                        "time-range-type": "BEFORE_NOW",
                        "duration-in-mins": time_range,
                        "rollup": "true"
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    metric_data = response.json()
                    performance_data[metric_name] = metric_data
                else:
                    performance_data[metric_name] = {"error": f"Failed to get {metric_name}"}
            
            return {
                "status": "success",
                "performance": performance_data,
                "app_id": app_id,
                "time_range": time_range
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting performance data: {str(e)}",
                "performance": {}
            }
    
    def _analyze_performance_metrics(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics for insights"""
        analysis = {
            "overall_status": "unknown",
            "response_time_status": "unknown",
            "throughput_status": "unknown",
            "error_rate_status": "unknown",
            "resource_status": "unknown"
        }
        
        # Analyze response time
        if "response_time" in performance_data and isinstance(performance_data["response_time"], list):
            response_times = []
            for metric in performance_data["response_time"]:
                if "metricValues" in metric:
                    for value in metric["metricValues"]:
                        if "value" in value and value["value"]:
                            response_times.append(float(value["value"]))
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time < 100:
                    analysis["response_time_status"] = "excellent"
                elif avg_response_time < 500:
                    analysis["response_time_status"] = "good"
                elif avg_response_time < 1000:
                    analysis["response_time_status"] = "fair"
                else:
                    analysis["response_time_status"] = "poor"
        
        # Analyze throughput
        if "throughput" in performance_data and isinstance(performance_data["throughput"], list):
            throughput_values = []
            for metric in performance_data["throughput"]:
                if "metricValues" in metric:
                    for value in metric["metricValues"]:
                        if "value" in value and value["value"]:
                            throughput_values.append(float(value["value"]))
            
            if throughput_values:
                avg_throughput = sum(throughput_values) / len(throughput_values)
                if avg_throughput > 100:
                    analysis["throughput_status"] = "excellent"
                elif avg_throughput > 50:
                    analysis["throughput_status"] = "good"
                elif avg_throughput > 10:
                    analysis["throughput_status"] = "fair"
                else:
                    analysis["throughput_status"] = "poor"
        
        # Analyze error rate
        if "error_rate" in performance_data and isinstance(performance_data["error_rate"], list):
            error_rates = []
            for metric in performance_data["error_rate"]:
                if "metricValues" in metric:
                    for value in metric["metricValues"]:
                        if "value" in value and value["value"]:
                            error_rates.append(float(value["value"]))
            
            if error_rates:
                avg_error_rate = sum(error_rates) / len(error_rates)
                if avg_error_rate == 0:
                    analysis["error_rate_status"] = "excellent"
                elif avg_error_rate < 1:
                    analysis["error_rate_status"] = "good"
                elif avg_error_rate < 5:
                    analysis["error_rate_status"] = "fair"
                else:
                    analysis["error_rate_status"] = "poor"
        
        # Determine overall status
        statuses = [
            analysis["response_time_status"],
            analysis["throughput_status"],
            analysis["error_rate_status"]
        ]
        
        if all(status == "excellent" for status in statuses):
            analysis["overall_status"] = "excellent"
        elif all(status in ["excellent", "good"] for status in statuses):
            analysis["overall_status"] = "good"
        elif any(status == "poor" for status in statuses):
            analysis["overall_status"] = "poor"
        else:
            analysis["overall_status"] = "fair"
        
        return analysis
    
    def validate_application(self, app_name: str, time_range: str = "60") -> Dict[str, Any]:
        """Validate application in AppDynamics"""
        try:
            results = {
                "app_name": app_name,
                "time_range": time_range,
                "validation_timestamp": datetime.now().isoformat(),
                "overall_status": "unknown"
            }
            
            # Get application details
            app_result = self.get_application_by_name(app_name)
            if app_result["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Application '{app_name}' not found",
                    "app_name": app_name
                }
            
            app_id = app_result["application"]["id"]
            results["app_id"] = app_id
            results["app_details"] = app_result["application"]
            
            # Get health rules
            health_rules_result = self.get_health_rules(app_id)
            results["health_rules"] = health_rules_result
            
            # Get errors
            errors_result = self.get_errors(app_id, time_range)
            results["errors"] = errors_result
            
            # Get performance data
            performance_result = self.get_performance_data(app_id, time_range)
            results["performance"] = performance_result
            
            # Analyze performance
            if performance_result["status"] == "success":
                performance_analysis = self._analyze_performance_metrics(performance_result["performance"])
                results["performance_analysis"] = performance_analysis
                results["overall_status"] = performance_analysis["overall_status"]
            
            results["status"] = "success"
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating application: {str(e)}",
                "app_name": app_name,
                "overall_status": "unknown"
            }
    
    def comprehensive_app_validation(self, app_name: str, time_range: str = "60") -> Dict[str, Any]:
        """Perform comprehensive validation of app data in AppDynamics"""
        try:
            results = {
                "app_name": app_name,
                "time_range": time_range,
                "validation_timestamp": datetime.now().isoformat(),
                "overall_status": "unknown"
            }
            
            # Validate application
            validation_result = self.validate_application(app_name, time_range)
            
            if validation_result["status"] == "success":
                results.update(validation_result)
                
                # Additional analysis
                health_rules_count = len(validation_result.get("health_rules", {}).get("health_rules", []))
                error_count = validation_result.get("errors", {}).get("total_errors", 0)
                
                results["summary"] = {
                    "health_rules_count": health_rules_count,
                    "error_count": error_count,
                    "has_health_rules": health_rules_count > 0,
                    "has_errors": error_count > 0
                }
                
                # Determine overall status based on multiple factors
                performance_status = validation_result.get("performance_analysis", {}).get("overall_status", "unknown")
                has_health_rules = results["summary"]["has_health_rules"]
                has_errors = results["summary"]["has_errors"]
                
                if performance_status == "excellent" and has_health_rules and not has_errors:
                    results["overall_status"] = "excellent"
                elif performance_status in ["excellent", "good"] and has_health_rules:
                    results["overall_status"] = "good"
                elif performance_status == "poor" or has_errors:
                    results["overall_status"] = "poor"
                else:
                    results["overall_status"] = "fair"
            else:
                results["status"] = "error"
                results["message"] = validation_result["message"]
            
            return results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in comprehensive validation: {str(e)}",
                "app_name": app_name,
                "overall_status": "unknown"
            }


# Global instance
appdynamics_integration = AppDynamicsIntegration() 