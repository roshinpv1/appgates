"""
LLM Client Utility - Comprehensive LLM Integration
Based on the existing CodeGates LLM architecture with local, enterprise, and Apigee support
"""

import os
import json
import time
import uuid
import base64
import logging
import threading
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    LOCAL = "local"
    ENTERPRISE = "enterprise"
    APIGEE = "apigee"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 300


@dataclass
class TokenInfo:
    """Token information with expiry tracking"""
    token: str
    expires_at: datetime
    refresh_token: Optional[str] = None


class ApigeeTokenManager:
    """Manages Apigee Bearer Token with automatic refresh"""
    
    def __init__(self):
        self.apigee_login_url = os.getenv("APIGEE_NONPROD_LOGIN_URL")
        self.apigee_consumer_key = os.getenv("APIGEE_CONSUMER_KEY")
        self.apigee_consumer_secret = os.getenv("APIGEE_CONSUMER_SECRET")
        
        # Token cache with thread safety
        self._apigee_token_cache = {
            "token": None,
            "expires_at": 0
        }
        self._apigee_token_lock = threading.Lock()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not all([self.apigee_login_url, self.apigee_consumer_key, self.apigee_consumer_secret]):
            raise ValueError("Apigee configuration incomplete. Required: APIGEE_NONPROD_LOGIN_URL, APIGEE_CONSUMER_KEY, APIGEE_CONSUMER_SECRET")
    
    def _generate_apigee_token(self) -> dict:
        """Generate a new Apigee Bearer Token"""
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
            response.raise_for_status()
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
    
    def get_apigee_token(self) -> str:
        """Get a valid Apigee token, refreshing if necessary"""
        with self._apigee_token_lock:
            current_time = time.time()
            
            # Check if we have a valid cached token
            if (self._apigee_token_cache["token"] and 
                current_time < self._apigee_token_cache["expires_at"]):
                return self._apigee_token_cache["token"]
            
            # Generate new token
            token_data = self._generate_apigee_token()
            
            # Cache the token
            self._apigee_token_cache["token"] = token_data["access_token"]
            self._apigee_token_cache["expires_at"] = current_time + token_data["expires_in"] - 60  # 1 minute buffer
            
            return token_data["access_token"]


class EnterpriseTokenManager:
    """Manages enterprise token with automatic refresh"""
    
    def __init__(self):
        self.refresh_url = os.getenv("ENTERPRISE_LLM_REFRESH_URL")
        self.client_id = os.getenv("ENTERPRISE_LLM_CLIENT_ID")
        self.client_secret = os.getenv("ENTERPRISE_LLM_CLIENT_SECRET")
        self.refresh_token = os.getenv("ENTERPRISE_LLM_REFRESH_TOKEN")
        
        # Token management
        self.token_info = None
        self.token_lock = threading.Lock()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Load initial token if provided
        initial_token = os.getenv("ENTERPRISE_LLM_TOKEN")
        if initial_token:
            expires_in_hours = int(os.getenv("ENTERPRISE_LLM_TOKEN_EXPIRY_HOURS", "24"))
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            self.token_info = TokenInfo(
                token=initial_token,
                expires_at=expires_at,
                refresh_token=self.refresh_token
            )
    
    def get_valid_token(self) -> str:
        """Get a valid token, refreshing if necessary"""
        with self.token_lock:
            if not self.token_info:
                raise ValueError("No enterprise token configured. Set ENTERPRISE_LLM_TOKEN in environment")
            
            # Check if token is expired or will expire in the next 5 minutes
            if datetime.now() >= (self.token_info.expires_at - timedelta(minutes=5)):
                self.logger.info("Enterprise token expired or expiring soon, refreshing...")
                self._refresh_token()
            
            return self.token_info.token
    
    def _refresh_token(self):
        """Refresh the enterprise token"""
        if not self.refresh_url:
            raise ValueError("No refresh URL configured. Set ENTERPRISE_LLM_REFRESH_URL in environment")
        
        if not self.refresh_token and not (self.client_id and self.client_secret):
            raise ValueError("No refresh credentials configured")
        
        try:
            headers = {"Content-Type": "application/json"}
            
            if self.refresh_token:
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token
                }
            else:
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            
            response = requests.post(
                self.refresh_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token_info = TokenInfo(
                    token=token_data["access_token"],
                    expires_at=datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600)),
                    refresh_token=token_data.get("refresh_token", self.refresh_token)
                )
                self.logger.info("Successfully refreshed enterprise token")
            else:
                raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to refresh enterprise token: {e}")
            raise


class LLMClient:
    """Comprehensive LLM client supporting multiple providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize provider-specific managers
        self.apigee_token_manager = None
        self.enterprise_token_manager = None
        
        if config.provider == LLMProvider.APIGEE:
            self.apigee_token_manager = ApigeeTokenManager()
        elif config.provider == LLMProvider.ENTERPRISE:
            self.enterprise_token_manager = EnterpriseTokenManager()
    
    def call_llm(self, prompt: str) -> str:
        """Call LLM with the given prompt"""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                return self._call_openai(prompt)
            elif self.config.provider == LLMProvider.ANTHROPIC:
                return self._call_anthropic(prompt)
            elif self.config.provider == LLMProvider.GEMINI:
                return self._call_gemini(prompt)
            elif self.config.provider == LLMProvider.OLLAMA:
                return self._call_ollama(prompt)
            elif self.config.provider == LLMProvider.LOCAL:
                return self._call_local(prompt)
            elif self.config.provider == LLMProvider.ENTERPRISE:
                return self._call_enterprise(prompt)
            elif self.config.provider == LLMProvider.APIGEE:
                return self._call_apigee(prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
        
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            raise Exception(f"LLM call failed: {str(e)}")
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )
        
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available. Install with: pip install anthropic")
        
        client = anthropic.Anthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = client.messages.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )
        
        return response.content[0].text
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI library not available. Install with: pip install google-generativeai")
        
        genai.configure(api_key=self.config.api_key)
        if self.config.base_url:
            genai.configure(api_base=self.config.base_url)
        
        model = genai.GenerativeModel(self.config.model)
        response = model.generate_content(prompt)
        
        return response.text
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama library not available. Install with: pip install ollama")
        
        if self.config.base_url:
            ollama.base_url = self.config.base_url
        
        response = ollama.chat(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature
        )
        
        return response.message.content
    
    def _call_local(self, prompt: str) -> str:
        """Call local LLM API (OpenAI-compatible)"""
        if not self.config.base_url:
            raise ValueError("Local LLM URL not configured")
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key and self.config.api_key != "not-needed":
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        data = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        response = requests.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Local LLM request failed: {response.status_code} - {response.text}")
        
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to parse local LLM response: {e}")
    
    def _call_enterprise(self, prompt: str) -> str:
        """Call enterprise LLM API"""
        if not self.enterprise_token_manager:
            raise ValueError("Enterprise token manager not initialized")
        
        token = self.enterprise_token_manager.get_valid_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Add any additional enterprise headers
        enterprise_headers_str = os.getenv("ENTERPRISE_LLM_HEADERS", "{}")
        try:
            additional_headers = json.loads(enterprise_headers_str)
            headers.update(additional_headers)
        except json.JSONDecodeError:
            pass
        
        data = {
            "model": self.config.model,
            "prompt": prompt,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        response = requests.post(
            self.config.base_url,
            headers=headers,
            json=data,
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Enterprise LLM request failed: {response.status_code} - {response.text}")
        
        return response.json()["response"]
    
    def _call_apigee(self, prompt: str) -> str:
        """Call Apigee enterprise LLM API"""
        if not self.apigee_token_manager:
            raise ValueError("Apigee token manager not initialized")
        
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx library not available. Install with: pip install httpx")
        
        # Get Apigee token
        apigee_token = self.apigee_token_manager.get_apigee_token()
        
        # Enterprise configuration
        enterprise_base_url = os.getenv("ENTERPRISE_BASE_URL")
        wf_use_case_id = os.getenv("WF_USE_CASE_ID")
        wf_client_id = os.getenv("WF_CLIENT_ID")
        wf_api_key = os.getenv("WF_API_KEY")
        
        if not all([enterprise_base_url, wf_use_case_id, wf_client_id, wf_api_key]):
            raise ValueError("Apigee enterprise configuration incomplete")
        
        # Prepare headers
        headers = {
            "x-w-request-date": datetime.now(timezone.utc).isoformat(),
            "Authorization": f"Bearer {apigee_token}",
            "x-request-id": str(uuid.uuid4()),
            "x-correlation-id": str(uuid.uuid4()),
            "X-YY-client-id": wf_client_id,
            "X-YY-api-key": wf_api_key,
            "X-YY-usecase-id": wf_use_case_id,
            "Content-Type": "application/json"
        }
        
        # Initialize OpenAI client with enterprise settings
        client = openai.OpenAI(
            api_key=apigee_token,
            base_url=enterprise_base_url,
            http_client=httpx.Client(verify=False)
        )
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        try:
            # For cloud providers, check if we have the required config
            if self.config.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GEMINI]:
                return bool(self.config.api_key)
            
            # For local providers, assume available unless proven otherwise
            elif self.config.provider in [LLMProvider.LOCAL, LLMProvider.OLLAMA]:
                return bool(self.config.base_url)
            
            # For enterprise providers, check token availability
            elif self.config.provider == LLMProvider.ENTERPRISE:
                return bool(self.enterprise_token_manager and self.enterprise_token_manager.token_info)
            
            # For Apigee, check if all required env vars are set
            elif self.config.provider == LLMProvider.APIGEE:
                required_vars = [
                    "APIGEE_NONPROD_LOGIN_URL", "APIGEE_CONSUMER_KEY", "APIGEE_CONSUMER_SECRET",
                    "ENTERPRISE_BASE_URL", "WF_USE_CASE_ID", "WF_CLIENT_ID", "WF_API_KEY"
                ]
                return all(os.getenv(var) for var in required_vars)
            
            return False
        
        except Exception:
            return False


def create_llm_client_from_env() -> Optional[LLMClient]:
    """Create LLM client from environment variables"""
    
    # Check providers in priority order
    providers = [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GEMINI, "GEMINI_API_KEY"),
        (LLMProvider.APIGEE, "APIGEE_NONPROD_LOGIN_URL"),
        (LLMProvider.ENTERPRISE, "ENTERPRISE_LLM_URL"),
        (LLMProvider.LOCAL, "LOCAL_LLM_URL"),
        (LLMProvider.OLLAMA, "OLLAMA_HOST")
    ]
    
    for provider, env_var in providers:
        if os.getenv(env_var):
            try:
                config = _create_config_for_provider(provider)
                client = LLMClient(config)
                if client.is_available():
                    return client
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to create {provider.value} client: {e}")
                continue
    
    return None


def _create_config_for_provider(provider: LLMProvider) -> LLMConfig:
    """Create configuration for a specific provider"""
    
    if provider == LLMProvider.OPENAI:
        return LLMConfig(
            provider=provider,
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
        )
    
    elif provider == LLMProvider.ANTHROPIC:
        return LLMConfig(
            provider=provider,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000"))
        )
    
    elif provider == LLMProvider.GEMINI:
        return LLMConfig(
            provider=provider,
            model=os.getenv("GEMINI_MODEL", "gemini-pro"),
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url=os.getenv("GEMINI_BASE_URL"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "4000"))
        )
    
    elif provider == LLMProvider.LOCAL:
        return LLMConfig(
            provider=provider,
            model=os.getenv("LOCAL_LLM_MODEL", "llama-3.2-3b-instruct"),
            api_key=os.getenv("LOCAL_LLM_API_KEY", "not-needed"),
            base_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1"),
            temperature=float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("LOCAL_LLM_MAX_TOKENS", "4000"))
        )
    
    elif provider == LLMProvider.OLLAMA:
        return LLMConfig(
            provider=provider,
            model=os.getenv("OLLAMA_MODEL", "llama-3.2-3b-instruct"),
            api_key=None,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("OLLAMA_NUM_PREDICT", "4000"))
        )
    
    elif provider == LLMProvider.ENTERPRISE:
        return LLMConfig(
            provider=provider,
            model=os.getenv("ENTERPRISE_LLM_MODEL", "llama-3.2-3b-instruct"),
            api_key=os.getenv("ENTERPRISE_LLM_API_KEY"),
            base_url=os.getenv("ENTERPRISE_LLM_URL"),
            temperature=float(os.getenv("ENTERPRISE_LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("ENTERPRISE_LLM_MAX_TOKENS", "4000"))
        )
    
    elif provider == LLMProvider.APIGEE:
        return LLMConfig(
            provider=provider,
            model=os.getenv("APIGEE_MODEL", "gpt-4"),
            api_key=os.getenv("APIGEE_CONSUMER_KEY"),
            base_url=os.getenv("ENTERPRISE_BASE_URL"),
            temperature=float(os.getenv("APIGEE_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("APIGEE_MAX_TOKENS", "4000"))
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")


if __name__ == "__main__":
    # Test the LLM client
    print("🧪 Testing LLM Client...")
    
    client = create_llm_client_from_env()
    if client:
        print(f"✅ Created {client.config.provider.value} client")
        print(f"   Model: {client.config.model}")
        print(f"   Available: {client.is_available()}")
        
        # Test with a simple prompt
        try:
            response = client.call_llm("Hello, world! Please respond with 'Hello from LLM!'")
            print(f"✅ Test response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print("❌ No LLM client could be created from environment") 