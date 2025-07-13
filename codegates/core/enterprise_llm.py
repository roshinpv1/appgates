"""
Enterprise LLM Integration with Apigee Authentication
Enhanced with proper token management and enterprise security features
"""

import os
import json
import time
import uuid
import base64
import logging
import threading
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
import httpx
from openai import OpenAI

from ..models import Language
from ..utils.env_loader import EnvironmentLoader


@dataclass
class ApigeeTokenInfo:
    """Apigee token information with expiry tracking"""
    token: str
    expires_at: float
    issued_at: float


class ApigeeTokenManager:
    """Manages Apigee Bearer Token with automatic refresh"""
    
    def __init__(self):
        # Apigee configuration
        self.apigee_login_url = self._get_env_var("APIGEE_NONPROD_LOGIN_URL")
        self.apigee_consumer_key = self._get_env_var("APIGEE_CONSUMER_KEY")
        self.apigee_consumer_secret = self._get_env_var("APIGEE_CONSUMER_SECRET")
        
        # Token cache with thread safety
        self._apigee_token_cache = {
            "token": None,
            "expires_at": 0
        }
        self._apigee_token_lock = threading.Lock()
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with error handling"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} is required but not set")
        return value
    
    def _generate_apigee_token(self) -> dict:
        """
        Generates a new Apigee Bearer Token by making an API call to the authentication endpoint.
        Retrieves consumer key and secret from environment variables.
        Returns a dictionary containing 'access_token' and 'expires_in':
        """
        # Encode consumer key and secret for Basic Authorization header
        apigee_creds = f"{self.apigee_consumer_key}:{self.apigee_consumer_secret}"
        apigee_cred_b64 = base64.b64encode(apigee_creds.encode("utf-8")).decode("utf-8")
        
        payload = 'grant_type=client_credentials'
        headers = {
            'Authorization': f'Basic {apigee_cred_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        self.logger.info("Attempting to generate new Apigee token...")
        
        try:
            response = requests.post(
                self.apigee_login_url, 
                headers=headers, 
                data=payload, 
                verify=False, 
                timeout=10
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            token_data = response.json()
            self.logger.info("Successfully generated Apigee token.")
            return token_data

        except requests.exceptions.Timeout:
            self.logger.error("Request to Apigee token endpoint timed out after 10 seconds.")
            raise
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Could not connect to Apigee token endpoint: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error generating Apigee token: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from Apigee token response. Response: {response.text}")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during Apigee token generation: {e}")
            raise

    def get_apigee_token(self) -> str:
        """
        Retrieves the Apigee Bearer Token, using a cached token if available and not expired.
        Refreshes the token proactively if it's nearing expiration (e.g., within 60 seconds).
        """
        with self._apigee_token_lock:
            current_time = time.time()
            
            # Refresh token if it's not set or expires within the next 60 seconds
            if (not self._apigee_token_cache["token"] or 
                self._apigee_token_cache["expires_at"] < current_time + 60):
                
                self.logger.info("Apigee token is missing or nearing expiration. Refreshing...")
                try:
                    token_data = self._generate_apigee_token()
                    self._apigee_token_cache["token"] = token_data.get("access_token")
                    
                    # Store expiration time, subtracting a small buffer (e.g., 5 seconds)
                    # to account for network latency or clock skew.
                    self._apigee_token_cache["expires_at"] = (
                        token_data.get("issued_at", current_time * 1000) / 1000 + 
                        token_data.get("expires_in", 3600) - 5
                    )
                    
                    if not self._apigee_token_cache["token"]:
                        raise ValueError("Access token not found in Apigee response.")
                        
                except Exception as e:
                    self.logger.critical(f"Failed to refresh Apigee token: {e}")
                    raise
            else:
                self.logger.info("Using cached Apigee token.")
            
            return self._apigee_token_cache["token"]


class EnterpriseLLMClient:
    """Enterprise LLM client with Apigee authentication"""
    
    def __init__(self):
        # Enterprise configuration
        self.enterprise_base_url = self._get_env_var("ENTERPRISE_BASE_URL")
        self.wf_use_case_id = self._get_env_var("WF_USE_CASE_ID")
        self.wf_client_id = self._get_env_var("WF_CLIENT_ID")
        self.wf_api_key = self._get_env_var("WF_API_KEY")
        
        # Initialize token manager
        self.token_manager = ApigeeTokenManager()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
    
    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with error handling"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} is required but not set")
        return value
    
    def initialize_openai_client(self, apigee_access_token: str):
        """
        Initializes the OpenAI client with required headers for the Apigee proxy.
        All necessary configuration values are retrieved from environment variables.
        """
        request_headers = {
            "x-w-request-date": datetime.now(datetime.timezone.utc).isoformat(),
            "Authorization": f"Bearer {apigee_access_token}",  # Apigee token proxy authentication
            "x-request-id": str(uuid.uuid4()),
            "x-correlation-id": str(uuid.uuid4()),
            "X-YY-client-id": self.wf_client_id,
            "X-YY-api-key": self.wf_api_key,
            "X-YY-usecase-id": self.wf_use_case_id,
        }
        
        self.logger.info(f"Initializing OpenAI client with base URL: {self.enterprise_base_url}")
        
        # IMPORTANT: verify=False is used for development/testing with self-signed certs or proxies.
        # For production environments, it is highly recommended to use verify=True
        # and ensure proper CA certificates are configured.
        client = OpenAI(
            api_key=apigee_access_token,  # Actual OpenAI API key (or proxy's expected API key)
            base_url=self.enterprise_base_url,
            http_client=httpx.Client(verify=False),
        )
        
        return client, request_headers
    
    def call_enterprise_llm(self, prompt: str, model: str = "gpt-4", 
                          temperature: float = 0.1, max_tokens: int = 4000) -> str:
        """
        Call the enterprise LLM with proper authentication and error handling
        """
        try:
            # Get valid Apigee token
            apigee_token = self.token_manager.get_apigee_token()
            
            # Initialize OpenAI client
            client, headers = self.initialize_openai_client(apigee_token)
            
            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Enterprise LLM call failed: {str(e)}")
            raise Exception(f"Enterprise LLM call failed: {str(e)}")


class EnterpriseLLMAnalyzer:
    """Enhanced LLM analyzer with enterprise support"""
    
    def __init__(self):
        self.enterprise_client = EnterpriseLLMClient()
        self.logger = logging.getLogger(__name__)
    
    def analyze_gate_implementation(self, gate_name: str, code_samples: List[str], 
                                  language: Language, technologies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze gate implementation using enterprise LLM"""
        
        if not code_samples:
            return self._provide_general_recommendations(gate_name, language, technologies)
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(gate_name, code_samples, language, technologies)
        
        try:
            # Call enterprise LLM
            response = self.enterprise_client.call_enterprise_llm(prompt)
            
            # Parse response
            return self._parse_analysis_response(response)
            
        except Exception as e:
            self.logger.error(f"Enterprise LLM analysis failed for {gate_name}: {str(e)}")
            return self._provide_general_recommendations(gate_name, language, technologies)
    
    def _build_analysis_prompt(self, gate_name: str, code_samples: List[str], 
                              language: Language, technologies: Dict[str, List[str]]) -> str:
        """Build analysis prompt for enterprise LLM"""
        
        prompt = f"""
        Analyze the following code implementation for the gate "{gate_name}" in {language.value}:
        
        Code Samples:
        {chr(10).join(f"- {sample}" for sample in code_samples[:5])}
        
        Technologies Detected:
        {chr(10).join(f"- {tech}: {', '.join(items)}" for tech, items in technologies.items())}
        
        Please provide a JSON response with the following structure:
        {{
            "quality_score": <float between 0-100>,
            "recommendations": ["list", "of", "recommendations"],
            "security_issues": ["list", "of", "security", "concerns"],
            "best_practices": ["list", "of", "best", "practices"],
            "improvement_areas": ["areas", "for", "improvement"]
        }}
        
        Focus on:
        1. Code quality and adherence to best practices
        2. Security considerations
        3. Performance implications
        4. Maintainability and readability
        5. Specific recommendations for improvement
        """
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse enterprise LLM response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {
                    "quality_score": 50.0,
                    "recommendations": ["Review implementation"],
                    "security_issues": [],
                    "best_practices": [],
                    "improvement_areas": ["Code quality"]
                }
        except Exception as e:
            self.logger.error(f"Failed to parse enterprise LLM response: {str(e)}")
            return {
                "quality_score": 50.0,
                "recommendations": ["Review implementation"],
                "security_issues": [],
                "best_practices": [],
                "improvement_areas": ["Code quality"]
            }
    
    def _provide_general_recommendations(self, gate_name: str, language: Language, 
                                       technologies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Provide general recommendations when no code samples are available"""
        return {
            "quality_score": 0.0,
            "recommendations": [
                f"Implement {gate_name} for {language.value}",
                "Follow best practices for the technology stack",
                "Add comprehensive testing"
            ],
            "security_issues": [],
            "best_practices": [],
            "improvement_areas": ["Implementation needed"]
        }


# Global instance for easy access
_enterprise_analyzer = None


def get_enterprise_analyzer() -> EnterpriseLLMAnalyzer:
    """Get the global enterprise analyzer instance"""
    global _enterprise_analyzer
    if _enterprise_analyzer is None:
        _enterprise_analyzer = EnterpriseLLMAnalyzer()
    return _enterprise_analyzer 