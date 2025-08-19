"""
HardGate Agent Configuration
Configuration settings for the HardGate agent
"""

import os
from typing import Dict, Any, Optional


class HardGateConfig:
    """Configuration manager for HardGate agent"""
    
    def __init__(self):
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from environment variables and defaults"""
        # LiteLLM Configuration
        self.litellm_config = {
            "model": os.getenv("LITELLM_MODEL", "gpt-3.5-turbo"),
            "base_url": os.getenv("LITELLM_BASE_URL", "http://localhost:1234/v1"),
            "api_key": os.getenv("LITELLM_API_KEY", "sdsd"),
            "provider": os.getenv("LITELLM_PROVIDER", "openai"),
            "temperature": float(os.getenv("LITELLM_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("LITELLM_MAX_TOKENS", "2000")),
            "timeout": int(os.getenv("LITELLM_TIMEOUT", "60"))
        }
        
        # Agent Configuration
        self.agent_config = {
            "name": "hardgate_agent",
            "description": "Enterprise-grade code security analysis agent",
            "version": "1.0.0",
            "max_concurrent_analyses": int(os.getenv("HARDGATE_MAX_CONCURRENT", "5")),
            "analysis_timeout": int(os.getenv("HARDGATE_ANALYSIS_TIMEOUT", "300")),
            "default_scan_depth": os.getenv("HARDGATE_SCAN_DEPTH", "comprehensive")
        }
        
        # Security Configuration
        self.security_config = {
            "default_gates": [
                "ALERTING_ACTIONABLE",
                "STRUCTURED_LOGS",
                "AVOID_LOGGING_SECRETS",
                "AUDIT_TRAIL",
                "CORRELATION_ID",
                "LOG_API_CALLS",
                "CLIENT_UI_ERRORS",
                "RETRY_LOGIC",
                "TIMEOUT_IO",
                "THROTTLING",
                "CIRCUIT_BREAKERS",
                "HTTP_ERROR_CODES",
                "URL_MONITORING",
                "AUTOMATED_TESTS",
                "AUTO_SCALE"
            ],
            "compliance_frameworks": [
                "SOC2",
                "ISO27001", 
                "NIST",
                "Enterprise"
            ],
            "risk_thresholds": {
                "critical": 50,
                "high": 30,
                "medium": 15,
                "low": 0
            }
        }
        
        # External Integrations
        self.integrations_config = {
            "splunk": {
                "enabled": os.getenv("SPLUNK_ENABLED", "false").lower() == "true",
                "url": os.getenv("SPLUNK_URL"),
                "username": os.getenv("SPLUNK_USERNAME"),
                "password": os.getenv("SPLUNK_PASSWORD")
            },
            "appdynamics": {
                "enabled": os.getenv("APPDYNAMICS_ENABLED", "false").lower() == "true",
                "url": os.getenv("APPDYNAMICS_URL"),
                "username": os.getenv("APPDYNAMICS_USERNAME"),
                "password": os.getenv("APPDYNAMICS_PASSWORD")
            },
            "jira": {
                "enabled": os.getenv("JIRA_ENABLED", "false").lower() == "true",
                "url": os.getenv("JIRA_URL"),
                "username": os.getenv("JIRA_USERNAME"),
                "api_token": os.getenv("JIRA_API_TOKEN")
            }
        }
        
        # Report Configuration
        self.report_config = {
            "default_format": os.getenv("HARDGATE_REPORT_FORMAT", "json"),
            "output_directory": os.getenv("HARDGATE_OUTPUT_DIR", "./reports"),
            "include_appendix": os.getenv("HARDGATE_INCLUDE_APPENDIX", "true").lower() == "true",
            "include_evidence": os.getenv("HARDGATE_INCLUDE_EVIDENCE", "true").lower() == "true"
        }
    
    def get_litellm_config(self) -> Dict[str, Any]:
        """Get LiteLLM configuration"""
        return self.litellm_config.copy()
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return self.agent_config.copy()
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.security_config.copy()
    
    def get_integrations_config(self) -> Dict[str, Any]:
        """Get integrations configuration"""
        return self.integrations_config.copy()
    
    def get_report_config(self) -> Dict[str, Any]:
        """Get report configuration"""
        return self.report_config.copy()
    
    def update_litellm_config(self, **kwargs):
        """Update LiteLLM configuration"""
        self.litellm_config.update(kwargs)
    
    def update_agent_config(self, **kwargs):
        """Update agent configuration"""
        self.agent_config.update(kwargs)
    
    def update_security_config(self, **kwargs):
        """Update security configuration"""
        self.security_config.update(kwargs)
    
    def is_integration_enabled(self, integration_name: str) -> bool:
        """Check if an integration is enabled"""
        integration = self.integrations_config.get(integration_name, {})
        return integration.get("enabled", False)
    
    def get_integration_config(self, integration_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific integration"""
        return self.integrations_config.get(integration_name)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate LiteLLM configuration
        if not self.litellm_config.get("model"):
            validation_results["errors"].append("LiteLLM model not configured")
            validation_results["valid"] = False
        
        if not self.litellm_config.get("base_url"):
            validation_results["warnings"].append("LiteLLM base URL not configured")
        
        # Validate integrations
        for integration_name, config in self.integrations_config.items():
            if config.get("enabled"):
                if not config.get("url"):
                    validation_results["errors"].append(f"{integration_name} URL not configured")
                    validation_results["valid"] = False
        
        return validation_results


# Global configuration instance
config = HardGateConfig()


def get_config() -> HardGateConfig:
    """Get global configuration instance"""
    return config


def load_config_from_file(config_file: str):
    """Load configuration from a file"""
    # This could be extended to load from YAML/JSON files
    pass


def save_config_to_file(config_file: str):
    """Save configuration to a file"""
    # This could be extended to save to YAML/JSON files
    pass 