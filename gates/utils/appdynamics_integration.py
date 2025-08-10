"""
AppDynamics Integration for CodeGates
Provides functionality to execute AppDynamics API queries and analyze results

Preferred configuration (token-based authentication):

    APPDYNAMICS_URL=https://your-appdynamics-instance.saas.appdynamics.com
    APPDYNAMICS_CLIENT_ID=your-appdynamics-client-id
    APPDYNAMICS_CLIENT_SECRET=your-appdynamics-client-secret
    APPDYNAMICS_ACCOUNT_NAME=your-account-name
    # CODEGATES_SSL_VERIFY=false  # Optional: for self-signed certs

Username/password is supported as a fallback for legacy/enterprise AppDynamics, but OAuth2 token-based authentication is recommended for all new deployments.
"""

import os
import requests
import json
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time

class AppDynamicsIntegration:
    """Handles AppDynamics integration for CodeGates validation"""
    
    def __init__(self):
        self.appd_url = os.getenv("APPDYNAMICS_URL")
        self.client_id = os.getenv("APPDYNAMICS_CLIENT_ID")
        self.client_secret = os.getenv("APPDYNAMICS_CLIENT_SECRET")
        self.account_name = os.getenv("APPDYNAMICS_ACCOUNT_NAME")
        self.username = os.getenv("APPDYNAMICS_USERNAME")
        self.password = os.getenv("APPDYNAMICS_PASSWORD")
        self.ssl_verify = os.getenv("CODEGATES_SSL_VERIFY", "true").lower() == "true"
        self.timeout = int(os.getenv("CODEGATES_APPDYNAMICS_REQUEST_TIMEOUT", "300"))
        self.max_results = int(os.getenv("CODEGATES_APPDYNAMICS_MAX_RESULTS", "1000"))
        self.access_token = None
        self.token_expires_at = None
        
    def is_configured(self) -> bool:
        """Check if AppDynamics is properly configured"""
        if not self.appd_url:
            print("[AppDynamicsIntegration] ⚠️ Warning: No AppDynamics URL provided. Please set APPDYNAMICS_URL.")
            return False
        
        # OAuth2 authentication is preferred
        if (self.client_id and self.client_secret and self.account_name):
            return True
        elif (self.username and self.password):
            print("[AppDynamicsIntegration] ⚠️ Warning: Using username/password authentication. OAuth2 authentication is preferred.")
            return True
        else:
            print("[AppDynamicsIntegration] ⚠️ Warning: No authentication credentials provided. Please set APPDYNAMICS_CLIENT_ID/CLIENT_SECRET/ACCOUNT_NAME or APPDYNAMICS_USERNAME/PASSWORD.")
            return False
    
    def _get_oauth_token(self) -> Optional[str]:
        """Get OAuth2 access token for AppDynamics API"""
        if not (self.client_id and self.client_secret and self.account_name):
            return None
        
        # Check if we have a valid token
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        try:
            # Prepare OAuth2 request
            token_url = f"{self.appd_url.rstrip('/')}/auth/oauth/token"
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials"
            }
            
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
                verify=self.ssl_verify,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # Refresh 5 minutes early
                
                print("[AppDynamicsIntegration] ✅ OAuth2 token obtained successfully")
                return self.access_token
            else:
                print(f"[AppDynamicsIntegration] ❌ Failed to get OAuth2 token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"[AppDynamicsIntegration] ❌ Error getting OAuth2 token: {str(e)}")
            return None
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for AppDynamics API"""
        if self.client_id and self.client_secret:
            # OAuth2 authentication
            token = self._get_oauth_token()
            if token:
                return {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            else:
                print("[AppDynamicsIntegration] ⚠️ Warning: OAuth2 token not available, falling back to username/password")
        
        # Username/password authentication
        if self.username and self.password:
            auth_header = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            return {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json"
            }
        
        return {"Content-Type": "application/json"}
    
    def execute_query(self, query_type: str, app_id: Optional[str] = None, 
                     time_range: str = "1_HOURS_AGO", limit: int = 100) -> Dict[str, Any]:
        """
        Execute an AppDynamics API query and return results
        
        Args:
            query_type: Type of query to execute (applications, metrics, events, etc.)
            app_id: Optional application ID to filter results
            time_range: Time range for the query (default: 1_HOURS_AGO)
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing query results and metadata
        """
        if not self.is_configured():
            return {
                "status": "error",
                "message": "AppDynamics not configured. Set APPDYNAMICS_URL and authentication credentials.",
                "results": [],
                "total_results": 0
            }
        
        try:
            headers = self._get_auth_headers()
            
            # Build API endpoint based on query type
            endpoint = self._build_endpoint(query_type, app_id)
            if not endpoint:
                return {
                    "status": "error",
                    "message": f"Unsupported query type: {query_type}",
                    "results": [],
                    "total_results": 0
                }
            
            # Prepare query parameters
            params = {
                "output": "json",
                "time-range-type": "BEFORE_NOW",
                "duration-in-mins": self._parse_time_range(time_range)
            }
            
            if limit:
                params["limit"] = limit
            
            # Execute API request
            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                verify=self.ssl_verify,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                results = response.json()
                
                return {
                    "status": "success",
                    "message": f"AppDynamics {query_type} query executed successfully",
                    "results": results,
                    "total_results": len(results) if isinstance(results, list) else 1,
                    "query_type": query_type,
                    "app_id": app_id
                }
            else:
                return {
                    "status": "error",
                    "message": f"AppDynamics API request failed: {response.status_code} - {response.text}",
                    "results": [],
                    "total_results": 0
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"AppDynamics query execution failed: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
    def _build_endpoint(self, query_type: str, app_id: Optional[str] = None) -> Optional[str]:
        """Build the appropriate API endpoint based on query type"""
        base_url = self.appd_url.rstrip('/')
        
        endpoint_map = {
            # Application Management
            "applications": f"{base_url}/controller/rest/applications",
            "application": f"{base_url}/controller/rest/applications/{app_id}",
            
            # Business Transactions
            "business_transactions": f"{base_url}/controller/rest/applications/{app_id}/business-transactions",
            "bt_summary": f"{base_url}/controller/rest/applications/{app_id}/business-transactions/summary",
            
            # Database Calls
            "database_calls": f"{base_url}/controller/rest/applications/{app_id}/database-calls",
            "db_summary": f"{base_url}/controller/rest/applications/{app_id}/database-calls/summary",
            
            # External Calls
            "external_calls": f"{base_url}/controller/rest/applications/{app_id}/external-calls",
            "external_summary": f"{base_url}/controller/rest/applications/{app_id}/external-calls/summary",
            
            # Errors
            "errors": f"{base_url}/controller/rest/applications/{app_id}/errors",
            "error_summary": f"{base_url}/controller/rest/applications/{app_id}/errors/summary",
            
            # Events
            "events": f"{base_url}/controller/rest/applications/{app_id}/events",
            "event_summary": f"{base_url}/controller/rest/applications/{app_id}/events/summary",
            
            # Health Rules
            "health_rules": f"{base_url}/controller/rest/applications/{app_id}/health-rules",
            "health_rule_violations": f"{base_url}/controller/rest/applications/{app_id}/health-rules/violations",
            
            # Metrics
            "metrics": f"{base_url}/controller/rest/applications/{app_id}/metrics",
            "metric_data": f"{base_url}/controller/rest/applications/{app_id}/metric-data",
            
            # Nodes
            "nodes": f"{base_url}/controller/rest/applications/{app_id}/nodes",
            "node_summary": f"{base_url}/controller/rest/applications/{app_id}/nodes/summary",
            
            # Policies
            "policies": f"{base_url}/controller/rest/applications/{app_id}/policies",
            "policy_violations": f"{base_url}/controller/rest/applications/{app_id}/policies/violations",
            
            # Tiers
            "tiers": f"{base_url}/controller/rest/applications/{app_id}/tiers",
            "tier_summary": f"{base_url}/controller/rest/applications/{app_id}/tiers/summary",
            
            # Backends
            "backends": f"{base_url}/controller/rest/applications/{app_id}/backends",
            "backend_summary": f"{base_url}/controller/rest/applications/{app_id}/backends/summary",
            
            # Snapshots
            "snapshots": f"{base_url}/controller/rest/applications/{app_id}/snapshots",
            "snapshot_details": f"{base_url}/controller/rest/applications/{app_id}/snapshots/details",
            
            # Infrastructure
            "infrastructure": f"{base_url}/controller/rest/infrastructure",
            "servers": f"{base_url}/controller/rest/infrastructure/servers",
            "clusters": f"{base_url}/controller/rest/infrastructure/clusters",
            
            # Controller Information
            "controller_info": f"{base_url}/controller/rest/controller-info",
            "server_time": f"{base_url}/controller/rest/server-time",
            "version": f"{base_url}/controller/rest/version"
        }
        
        return endpoint_map.get(query_type)
    
    def _build_query_params(self, query_type: str, time_range: str, limit: int, 
                           additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build query parameters based on query type"""
        params = {
            "output": "json",
            "time-range-type": "BEFORE_NOW",
            "duration-in-mins": self._parse_time_range(time_range)
        }
        
        if limit:
            params["limit"] = limit
        
        # Add query-specific parameters
        if query_type in ["metrics", "metric_data"]:
            params.update({
                "metric-path": additional_params.get("metric_path", "Application Infrastructure Performance|*"),
                "rollup": additional_params.get("rollup", "true")
            })
        
        elif query_type in ["business_transactions", "bt_summary"]:
            params.update({
                "bt-name": additional_params.get("bt_name", "*"),
                "tier-name": additional_params.get("tier_name", "*")
            })
        
        elif query_type in ["database_calls", "db_summary"]:
            params.update({
                "db-name": additional_params.get("db_name", "*"),
                "tier-name": additional_params.get("tier_name", "*")
            })
        
        elif query_type in ["external_calls", "external_summary"]:
            params.update({
                "external-type": additional_params.get("external_type", "*"),
                "tier-name": additional_params.get("tier_name", "*")
            })
        
        elif query_type in ["errors", "error_summary"]:
            params.update({
                "error-type": additional_params.get("error_type", "*"),
                "tier-name": additional_params.get("tier_name", "*")
            })
        
        elif query_type in ["events", "event_summary"]:
            params.update({
                "event-type": additional_params.get("event_type", "*"),
                "severity": additional_params.get("severity", "*")
            })
        
        elif query_type in ["health_rules", "health_rule_violations"]:
            params.update({
                "health-rule-name": additional_params.get("health_rule_name", "*"),
                "severity": additional_params.get("severity", "*")
            })
        
        elif query_type in ["snapshots", "snapshot_details"]:
            params.update({
                "bt-name": additional_params.get("bt_name", "*"),
                "tier-name": additional_params.get("tier_name", "*"),
                "user-experience": additional_params.get("user_experience", "NORMAL")
            })
        
        # Add any additional parameters
        if additional_params:
            for key, value in additional_params.items():
                if key not in params:
                    params[key] = value
        
        return params
    
    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to minutes"""
        time_range_map = {
            "15_MINUTES_AGO": 15,
            "30_MINUTES_AGO": 30,
            "1_HOURS_AGO": 60,
            "2_HOURS_AGO": 120,
            "4_HOURS_AGO": 240,
            "6_HOURS_AGO": 360,
            "12_HOURS_AGO": 720,
            "24_HOURS_AGO": 1440
        }
        return time_range_map.get(time_range, 60)
    
    # Application Management APIs
    def get_application_info(self, app_name: Optional[str] = None) -> Dict[str, Any]:
        """Get application information from AppDynamics"""
        return self.execute_query("applications", limit=self.max_results)
    
    def get_application_details(self, app_id: str) -> Dict[str, Any]:
        """Get detailed application information"""
        return self.execute_query("application", app_id=app_id)
    
    def get_application_metrics(self, app_id: str, metric_path: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific application"""
        return self.execute_query("metrics", app_id=app_id, limit=self.max_results)
    
    def get_application_events(self, app_id: str) -> Dict[str, Any]:
        """Get events for a specific application"""
        return self.execute_query("events", app_id=app_id, limit=self.max_results)
    
    def get_health_rules(self, app_id: str) -> Dict[str, Any]:
        """Get health rules for a specific application"""
        return self.execute_query("health_rules", app_id=app_id, limit=self.max_results)
    
    def get_policies(self, app_id: str) -> Dict[str, Any]:
        """Get policies for a specific application"""
        return self.execute_query("policies", app_id=app_id, limit=self.max_results)
    
    # Business Transaction APIs
    def get_business_transactions(self, app_id: str) -> Dict[str, Any]:
        """Get business transactions for an application"""
        return self.execute_query("business_transactions", app_id=app_id, limit=self.max_results)
    
    def get_business_transaction_summary(self, app_id: str) -> Dict[str, Any]:
        """Get business transaction summary"""
        return self.execute_query("bt_summary", app_id=app_id, limit=self.max_results)
    
    # Database Call APIs
    def get_database_calls(self, app_id: str) -> Dict[str, Any]:
        """Get database calls for an application"""
        return self.execute_query("database_calls", app_id=app_id, limit=self.max_results)
    
    def get_database_summary(self, app_id: str) -> Dict[str, Any]:
        """Get database call summary"""
        return self.execute_query("db_summary", app_id=app_id, limit=self.max_results)
    
    # External Call APIs
    def get_external_calls(self, app_id: str) -> Dict[str, Any]:
        """Get external calls for an application"""
        return self.execute_query("external_calls", app_id=app_id, limit=self.max_results)
    
    def get_external_summary(self, app_id: str) -> Dict[str, Any]:
        """Get external call summary"""
        return self.execute_query("external_summary", app_id=app_id, limit=self.max_results)
    
    # Error APIs
    def get_errors(self, app_id: str) -> Dict[str, Any]:
        """Get errors for an application"""
        return self.execute_query("errors", app_id=app_id, limit=self.max_results)
    
    def get_error_summary(self, app_id: str) -> Dict[str, Any]:
        """Get error summary"""
        return self.execute_query("error_summary", app_id=app_id, limit=self.max_results)
    
    # Event APIs
    def get_event_summary(self, app_id: str) -> Dict[str, Any]:
        """Get event summary"""
        return self.execute_query("event_summary", app_id=app_id, limit=self.max_results)
    
    # Health Rule APIs
    def get_health_rule_violations(self, app_id: str) -> Dict[str, Any]:
        """Get health rule violations"""
        return self.execute_query("health_rule_violations", app_id=app_id, limit=self.max_results)
    
    # Metric APIs
    def get_metric_data(self, app_id: str) -> Dict[str, Any]:
        """Get metric data for specific metrics"""
        return self.execute_query("metric_data", app_id=app_id, limit=self.max_results)
    
    # Node APIs
    def get_nodes(self, app_id: str) -> Dict[str, Any]:
        """Get nodes for an application"""
        return self.execute_query("nodes", app_id=app_id, limit=self.max_results)
    
    def get_node_summary(self, app_id: str) -> Dict[str, Any]:
        """Get node summary"""
        return self.execute_query("node_summary", app_id=app_id, limit=self.max_results)
    
    # Policy APIs
    def get_policy_violations(self, app_id: str) -> Dict[str, Any]:
        """Get policy violations"""
        return self.execute_query("policy_violations", app_id=app_id, limit=self.max_results)
    
    # Tier APIs
    def get_tiers(self, app_id: str) -> Dict[str, Any]:
        """Get tiers for an application"""
        return self.execute_query("tiers", app_id=app_id, limit=self.max_results)
    
    def get_tier_summary(self, app_id: str) -> Dict[str, Any]:
        """Get tier summary"""
        return self.execute_query("tier_summary", app_id=app_id, limit=self.max_results)
    
    # Backend APIs
    def get_backends(self, app_id: str) -> Dict[str, Any]:
        """Get backends for an application"""
        return self.execute_query("backends", app_id=app_id, limit=self.max_results)
    
    def get_backend_summary(self, app_id: str) -> Dict[str, Any]:
        """Get backend summary"""
        return self.execute_query("backend_summary", app_id=app_id, limit=self.max_results)
    
    # Snapshot APIs
    def get_snapshots(self, app_id: str) -> Dict[str, Any]:
        """Get snapshots for an application"""
        return self.execute_query("snapshots", app_id=app_id, limit=self.max_results)
    
    def get_snapshot_details(self, app_id: str) -> Dict[str, Any]:
        """Get detailed snapshot information"""
        return self.execute_query("snapshot_details", app_id=app_id, limit=self.max_results)
    
    # Infrastructure APIs
    def get_infrastructure_info(self) -> Dict[str, Any]:
        """Get infrastructure information"""
        return self.execute_query("infrastructure", limit=self.max_results)
    
    def get_servers(self) -> Dict[str, Any]:
        """Get server information"""
        return self.execute_query("servers", limit=self.max_results)
    
    def get_clusters(self) -> Dict[str, Any]:
        """Get cluster information"""
        return self.execute_query("clusters", limit=self.max_results)
    
    # Controller Information APIs
    def get_controller_info(self) -> Dict[str, Any]:
        """Get controller information"""
        return self.execute_query("controller_info")
    
    def get_server_time(self) -> Dict[str, Any]:
        """Get server time"""
        return self.execute_query("server_time")
    
    def get_version(self) -> Dict[str, Any]:
        """Get AppDynamics version"""
        return self.execute_query("version")
    
    def analyze_monitoring_coverage(self, app_id: str) -> Dict[str, Any]:
        """Analyze comprehensive monitoring coverage for an application"""
        analysis = {
            "application_found": False,
            "metrics_configured": False,
            "health_rules_configured": False,
            "policies_configured": False,
            "events_configured": False,
            "business_transactions_configured": False,
            "database_calls_configured": False,
            "external_calls_configured": False,
            "errors_configured": False,
            "nodes_configured": False,
            "tiers_configured": False,
            "backends_configured": False,
            "snapshots_configured": False,
            "coverage_score": 0.0,
            "details": [],
            "api_coverage": {}
        }
        
        try:
            # Check if application exists
            apps_result = self.get_application_info()
            if apps_result["status"] == "success":
                apps = apps_result["results"]
                app_found = any(app.get("id") == app_id or app.get("name") == app_id for app in apps)
                analysis["application_found"] = app_found
                
                if app_found:
                    analysis["details"].append("Application found in AppDynamics")
                    
                    # Test all API endpoints
                    api_tests = [
                        ("metrics", self.get_application_metrics, app_id),
                        ("health_rules", self.get_health_rules, app_id),
                        ("policies", self.get_policies, app_id),
                        ("events", self.get_application_events, app_id),
                        ("business_transactions", self.get_business_transactions, app_id),
                        ("database_calls", self.get_database_calls, app_id),
                        ("external_calls", self.get_external_calls, app_id),
                        ("errors", self.get_errors, app_id),
                        ("nodes", self.get_nodes, app_id),
                        ("tiers", self.get_tiers, app_id),
                        ("backends", self.get_backends, app_id),
                        ("snapshots", self.get_snapshots, app_id)
                    ]
                    
                    configured_items = 0
                    for api_name, api_func, *args in api_tests:
                        try:
                            result = api_func(*args)
                            analysis["api_coverage"][api_name] = {
                                "status": result["status"],
                                "total_results": result["total_results"],
                                "available": result["status"] == "success" and result["total_results"] > 0
                            }
                            
                            if result["status"] == "success" and result["total_results"] > 0:
                                configured_items += 1
                                analysis[f"{api_name}_configured"] = True
                                analysis["details"].append(f"Found {result['total_results']} {api_name.replace('_', ' ')}")
                            else:
                                analysis[f"{api_name}_configured"] = False
                                analysis["details"].append(f"No {api_name.replace('_', ' ')} configured")
                                
                        except Exception as e:
                            analysis["api_coverage"][api_name] = {
                                "status": "error",
                                "error": str(e),
                                "available": False
                            }
                            analysis[f"{api_name}_configured"] = False
                            analysis["details"].append(f"Error checking {api_name}: {str(e)}")
                    
                    # Calculate coverage score (out of 12 possible items)
                    analysis["coverage_score"] = (configured_items / 12.0) * 100.0
                else:
                    analysis["details"].append("Application not found in AppDynamics")
            else:
                analysis["details"].append(f"Failed to query applications: {apps_result['message']}")
                
        except Exception as e:
            analysis["details"].append(f"Error analyzing monitoring coverage: {str(e)}")
        
        return analysis
    
    def check_alerting_integration(self, app_id: str) -> Dict[str, Any]:
        """Check if AppDynamics alerting integration is properly configured"""
        result = {
            "integrated": False,
            "details": [],
            "health_rules": [],
            "policies": [],
            "metrics": [],
            "events": [],
            "errors": [],
            "business_transactions": [],
            "database_calls": [],
            "external_calls": [],
            "nodes": [],
            "tiers": [],
            "backends": [],
            "snapshots": []
        }
        
        try:
            # Check health rules (primary alerting mechanism)
            health_rules_result = self.get_health_rules(app_id)
            if health_rules_result["status"] == "success":
                health_rules = health_rules_result["results"]
                if health_rules:
                    result["integrated"] = True
                    result["health_rules"] = health_rules
                    result["details"].append(f"Found {len(health_rules)} health rules configured")
                    
                    # Check for critical health rules
                    critical_rules = [rule for rule in health_rules if rule.get("critical", False)]
                    if critical_rules:
                        result["details"].append(f"Found {len(critical_rules)} critical health rules")
                else:
                    result["details"].append("No health rules configured")
            else:
                result["details"].append(f"Failed to query health rules: {health_rules_result['message']}")
            
            # Check policies (secondary alerting mechanism)
            policies_result = self.get_policies(app_id)
            if policies_result["status"] == "success":
                policies = policies_result["results"]
                if policies:
                    result["policies"] = policies
                    result["details"].append(f"Found {len(policies)} policies configured")
                else:
                    result["details"].append("No policies configured")
            else:
                result["details"].append(f"Failed to query policies: {policies_result['message']}")
            
            # Check key metrics for alerting
            metrics_result = self.get_application_metrics(app_id)
            if metrics_result["status"] == "success":
                metrics = metrics_result["results"]
                if metrics:
                    result["metrics"] = metrics
                    result["details"].append(f"Found {len(metrics)} metrics configured")
                else:
                    result["details"].append("No metrics configured")
            else:
                result["details"].append(f"Failed to query metrics: {metrics_result['message']}")
            
            # Check events for alerting
            events_result = self.get_application_events(app_id)
            if events_result["status"] == "success":
                events = events_result["results"]
                if events:
                    result["events"] = events
                    result["details"].append(f"Found {len(events)} events configured")
                else:
                    result["details"].append("No events configured")
            else:
                result["details"].append(f"Failed to query events: {events_result['message']}")
            
            # Check errors for alerting
            errors_result = self.get_errors(app_id)
            if errors_result["status"] == "success":
                errors = errors_result["results"]
                if errors:
                    result["errors"] = errors
                    result["details"].append(f"Found {len(errors)} errors configured")
                else:
                    result["details"].append("No errors configured")
            else:
                result["details"].append(f"Failed to query errors: {errors_result['message']}")
            
            # Check business transactions for alerting
            bt_result = self.get_business_transactions(app_id)
            if bt_result["status"] == "success":
                bts = bt_result["results"]
                if bts:
                    result["business_transactions"] = bts
                    result["details"].append(f"Found {len(bts)} business transactions configured")
                else:
                    result["details"].append("No business transactions configured")
            else:
                result["details"].append(f"Failed to query business transactions: {bt_result['message']}")
            
            # Check database calls for alerting
            db_result = self.get_database_calls(app_id)
            if db_result["status"] == "success":
                db_calls = db_result["results"]
                if db_calls:
                    result["database_calls"] = db_calls
                    result["details"].append(f"Found {len(db_calls)} database calls configured")
                else:
                    result["details"].append("No database calls configured")
            else:
                result["details"].append(f"Failed to query database calls: {db_result['message']}")
            
            # Check external calls for alerting
            ext_result = self.get_external_calls(app_id)
            if ext_result["status"] == "success":
                ext_calls = ext_result["results"]
                if ext_calls:
                    result["external_calls"] = ext_calls
                    result["details"].append(f"Found {len(ext_calls)} external calls configured")
                else:
                    result["details"].append("No external calls configured")
            else:
                result["details"].append(f"Failed to query external calls: {ext_result['message']}")
            
            # Check nodes for alerting
            nodes_result = self.get_nodes(app_id)
            if nodes_result["status"] == "success":
                nodes = nodes_result["results"]
                if nodes:
                    result["nodes"] = nodes
                    result["details"].append(f"Found {len(nodes)} nodes configured")
                else:
                    result["details"].append("No nodes configured")
            else:
                result["details"].append(f"Failed to query nodes: {nodes_result['message']}")
            
            # Check tiers for alerting
            tiers_result = self.get_tiers(app_id)
            if tiers_result["status"] == "success":
                tiers = tiers_result["results"]
                if tiers:
                    result["tiers"] = tiers
                    result["details"].append(f"Found {len(tiers)} tiers configured")
                else:
                    result["details"].append("No tiers configured")
            else:
                result["details"].append(f"Failed to query tiers: {tiers_result['message']}")
            
            # Check backends for alerting
            backends_result = self.get_backends(app_id)
            if backends_result["status"] == "success":
                backends = backends_result["results"]
                if backends:
                    result["backends"] = backends
                    result["details"].append(f"Found {len(backends)} backends configured")
                else:
                    result["details"].append("No backends configured")
            else:
                result["details"].append(f"Failed to query backends: {backends_result['message']}")
            
            # Check snapshots for alerting
            snapshots_result = self.get_snapshots(app_id)
            if snapshots_result["status"] == "success":
                snapshots = snapshots_result["results"]
                if snapshots:
                    result["snapshots"] = snapshots
                    result["details"].append(f"Found {len(snapshots)} snapshots configured")
                else:
                    result["details"].append("No snapshots configured")
            else:
                result["details"].append(f"Failed to query snapshots: {snapshots_result['message']}")
                
        except Exception as e:
            result["details"].append(f"Error checking alerting integration: {str(e)}")
        
        return result


# Global instance
appdynamics_integration = AppDynamicsIntegration()

def execute_appdynamics_query(query_type: str, app_id: Optional[str] = None, 
                             time_range: str = "1_HOURS_AGO", limit: int = 100,
                             additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute an AppDynamics API query and return results
    
    Args:
        query_type: Type of query to execute
        app_id: Optional application ID for filtering
        time_range: Time range for the query (default: 1_HOURS_AGO)
        limit: Maximum number of results to return
        additional_params: Additional query parameters
        
    Returns:
        Dictionary containing query results and analysis
    """
    if not query_type:
        return {
            "status": "skipped",
            "message": "No AppDynamics query type provided",
            "results": [],
            "analysis": {}
        }
    
    # Execute the query
    result = appdynamics_integration.execute_query(query_type, app_id, time_range, limit, additional_params)
    
    if result["status"] == "success":
        # Add basic analysis
        result["analysis"] = {
            "query_type": query_type,
            "app_id": app_id,
            "time_range": time_range,
            "total_results": result["total_results"]
        }
    
    return result

def check_appdynamics_integration(app_id: str) -> Dict[str, Any]:
    """
    Check AppDynamics integration status for an application
    
    Args:
        app_id: Application ID to check
        
    Returns:
        Dictionary containing integration status and details
    """
    return appdynamics_integration.check_alerting_integration(app_id)

def analyze_appdynamics_coverage(app_id: str) -> Dict[str, Any]:
    """
    Analyze AppDynamics monitoring coverage for an application
    
    Args:
        app_id: Application ID to analyze
        
    Returns:
        Dictionary containing coverage analysis
    """
    return appdynamics_integration.analyze_monitoring_coverage(app_id) 