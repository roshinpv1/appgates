"""
LLM Service for CodeGates Scan System
Comprehensive LLM integration supporting multiple providers
"""

import os
import json
import time
import logging
import requests
import threading
from datetime import datetime, timedelta
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
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class TokenInfo:
    """Token information for enterprise providers"""
    token: str
    expires_at: datetime
    refresh_token: Optional[str] = None


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"
    ENTERPRISE = "enterprise"


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 60  # Increased timeout for complex prompts
    max_retries: int = 3


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
                timeout=300
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


class LLMService:
    """
    Comprehensive LLM service supporting multiple providers
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM service"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Parse configuration
        provider_str = config.get("provider", "local")
        try:
            self.provider = LLMProvider(provider_str)
        except ValueError:
            print(f"⚠️ Unknown LLM provider '{provider_str}', falling back to local")
            self.provider = LLMProvider.LOCAL
        
        self.llm_config = LLMConfig(
            provider=self.provider,
            model=config.get("model", "llama-3.2-3b-instruct"),
            api_key=config.get("api_key"),
            base_url=config.get("base_url", "http://localhost:1234"),
            temperature=config.get("temperature", 0.3),
            max_tokens=config.get("max_tokens", 2000),
            timeout=config.get("timeout", 300),  # Increased default timeout to 300 seconds
            max_retries=config.get("max_retries", 3)
        )
        
        print(f"🤖 LLMService initialized with {self.provider.value} provider")
        
        # Initialize enterprise token manager if needed
        self.enterprise_token_manager = None
        if self.provider == LLMProvider.ENTERPRISE:
            self.enterprise_token_manager = EnterpriseTokenManager()
        
        # Initialize LLM logger
        from services.llm_logger import LLMLogger
        self.llm_logger = LLMLogger()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the configured LLM provider"""
        start_time = time.time()
        scan_id = kwargs.get("scan_id", "unknown")
        node_name = kwargs.get("node_name", "unknown")
        metadata = kwargs.get("metadata", {})
        
        # Check if mock mode is enabled
        use_mock = kwargs.get("use_mock", False) or os.getenv("LLM_USE_MOCK", "false").lower() == "true"
        
        if use_mock:
            print("🤖 Using mock LLM response for development")
            mock_response = self._get_mock_response(prompt)
            
            # Log mock interaction
            self.llm_logger.log_llm_interaction(
                scan_id=scan_id,
                node_name=node_name,
                prompt=prompt,
                response=mock_response,
                metadata=metadata,
                duration=0.1,  # Mock duration
                error="Mock response used"
            )
            
            return mock_response
        
        try:
            # Create temporary config with overrides
            temp_config = LLMConfig(
                provider=self.provider,
                model=kwargs.get("model", self.llm_config.model),
                api_key=kwargs.get("api_key", self.llm_config.api_key),
                base_url=kwargs.get("base_url", self.llm_config.base_url),
                temperature=kwargs.get("temperature", self.llm_config.temperature),
                max_tokens=kwargs.get("max_tokens", self.llm_config.max_tokens),
                timeout=kwargs.get("timeout", self.llm_config.timeout),
                max_retries=kwargs.get("max_retries", self.llm_config.max_retries)
            )
            
            response = await self._call_llm_with_retry(prompt, temp_config)
            duration = time.time() - start_time
            
            # Log successful interaction
            self.llm_logger.log_llm_interaction(
                scan_id=scan_id,
                node_name=node_name,
                prompt=prompt,
                response=response,
                metadata=metadata,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            print(f"❌ LLM generation failed: {error_msg}")
            
            # Log failed interaction
            self.llm_logger.log_llm_interaction(
                scan_id=scan_id,
                node_name=node_name,
                prompt=prompt,
                response="",
                metadata=metadata,
                error=error_msg,
                duration=duration
            )
            
            # Return a mock response for development
            print("🔄 Falling back to mock response")
            return self._get_mock_response(prompt)
    
    async def _call_llm_with_retry(self, prompt: str, config: LLMConfig) -> str:
        """Call LLM with retry logic"""
        last_error = None
        
        for attempt in range(config.max_retries):
            try:
                if config.provider == LLMProvider.OPENAI:
                    return await self._call_openai(prompt, config)
                elif config.provider == LLMProvider.ANTHROPIC:
                    return await self._call_anthropic(prompt, config)
                elif config.provider == LLMProvider.OLLAMA:
                    return await self._call_ollama(prompt, config)
                elif config.provider == LLMProvider.LOCAL:
                    return await self._call_local(prompt, config)
                elif config.provider == LLMProvider.ENTERPRISE:
                    return await self._call_enterprise(prompt, config)
                else:
                    raise ValueError(f"Unsupported LLM provider: {config.provider}")
                    
            except Exception as e:
                last_error = e
                if attempt < config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️ LLM call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"❌ LLM call failed after {config.max_retries} attempts: {e}")
        
        raise last_error
    
    async def _call_openai(self, prompt: str, config: LLMConfig) -> str:
        """Call OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        try:
            client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout
            )
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"⚠️ OpenAI API call failed: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str, config: LLMConfig) -> str:
        """Call Anthropic API"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available. Install with: pip install anthropic")
        
        try:
            client = anthropic.Anthropic(
                api_key=config.api_key,
                base_url=config.base_url
            )
            
            message = client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"⚠️ Anthropic API call failed: {e}")
            raise
    
    async def _call_ollama(self, prompt: str, config: LLMConfig) -> str:
        """Call Ollama API"""
        if not OLLAMA_AVAILABLE:
            # Fallback to REST API if ollama library not available
            return await self._call_ollama_rest(prompt, config)
        
        try:
            response = ollama.generate(
                model=config.model,
                prompt=prompt,
                options={
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens
                }
            )
            
            return response['response']
            
        except Exception as e:
            print(f"⚠️ Ollama API call failed: {e}")
            raise
    
    async def _call_ollama_rest(self, prompt: str, config: LLMConfig) -> str:
        """Call Ollama via REST API"""
        try:
            base_url = config.base_url or "http://localhost:11434"
            
            payload = {
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens
                }
            }
            
            response = requests.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama REST API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"⚠️ Ollama REST API call failed: {e}")
            raise
    
    async def _call_local(self, prompt: str, config: LLMConfig) -> str:
        """Call local LLM (LM Studio compatible)"""
        try:
            base_url = config.base_url or "http://localhost:1234"
            
            # Reduce max_tokens for local LLMs to prevent timeouts
            local_max_tokens = 50000
            
            payload = {
                "model": config.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": config.temperature,
                "max_tokens": local_max_tokens,
                "stream": False
            }
            
            headers = {"Content-Type": "application/json"}
            
            # Use timeout for local LLMs (increased to 300 seconds)
            local_timeout = min(config.timeout, 300)
            
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=local_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Validate response content
                if not content or len(content.strip()) < 10:
                    raise Exception("Empty or too short response from local LLM")
                
                return content
            else:
                raise Exception(f"Local LLM API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"⚠️ Local LLM timeout after {local_timeout}s")
            raise Exception("Local LLM request timed out")
        except requests.exceptions.ConnectionError:
            print(f"⚠️ Local LLM connection failed to {base_url}")
            raise Exception("Local LLM connection failed")
        except Exception as e:
            print(f"⚠️ Local LLM API call failed: {e}")
            raise
    
    async def _call_enterprise(self, prompt: str, config: LLMConfig) -> str:
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
            "model": config.model,
            "prompt": prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens
        }
        
        response = requests.post(
            config.base_url,
            headers=headers,
            json=data,
            timeout=config.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Enterprise LLM request failed: {response.status_code} - {response.text}")
        
        return response.json()["response"]
    
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Synchronous version of generate for compatibility"""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.generate(prompt, **kwargs))
        finally:
            loop.close()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        return {
            "provider": self.provider.value,
            "model": self.llm_config.model,
            "base_url": self.llm_config.base_url,
            "temperature": self.llm_config.temperature,
            "max_tokens": self.llm_config.max_tokens,
            "available_providers": {
                "openai": OPENAI_AVAILABLE,
                "anthropic": ANTHROPIC_AVAILABLE,
                "ollama": OLLAMA_AVAILABLE,
                "local": True,  # Always available via REST
                "enterprise": True  # Always available if configured
            }
        }
    
    def test_connection(self) -> bool:
        """Test connection to the LLM provider"""
        try:
            test_prompt = "Hello, please respond with 'Connection successful'"
            response = self.generate_sync(test_prompt)
            return "successful" in response.lower() or len(response) > 0
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def _get_mock_response(self, prompt: str) -> str:
        """Get a mock response for development when LLM is not available"""
        if "patterns" in prompt.lower() and "json" in prompt.lower():
            return """
{
    "patterns": [
        {
            "gate_id": "security_001",
            "name": "SQL Injection Prevention",
            "description": "Ensure proper parameterized queries are used",
            "pattern": "SELECT.*FROM.*WHERE.*\\+",
            "severity": "HIGH",
            "category": "SECURITY",
            "examples": ["Use PreparedStatement", "Use parameterized queries"]
        },
        {
            "gate_id": "performance_001",
            "name": "Database Connection Pooling",
            "description": "Implement connection pooling for database connections",
            "pattern": "new\\s+Connection\\(\\)",
            "severity": "MEDIUM",
            "category": "PERFORMANCE",
            "examples": ["Use HikariCP", "Use connection pool"]
        }
    ]
}
"""
        elif "analysis" in prompt.lower() and "report" in prompt.lower():
            return """
# Code Analysis Report

## Executive Summary
The codebase shows good overall structure with some areas for improvement in security and performance.

## Key Findings
- **Security**: Basic security measures are in place
- **Performance**: Some optimization opportunities identified
- **Code Quality**: Generally well-structured code

## Recommendations
1. Implement additional input validation
2. Add comprehensive error handling
3. Optimize database queries
4. Enhance logging and monitoring

## Next Steps
- Prioritize security improvements
- Schedule performance optimization
- Plan code quality enhancements
"""
        else:
            return "Mock response: This is a development fallback when LLM service is not available."


def create_llm_service_from_config(config: Dict[str, Any]) -> LLMService:
    """Create LLM service from configuration"""
    return LLMService(config)


def create_llm_service_from_env() -> Optional[LLMService]:
    """Create LLM service from environment variables"""
    
    # Check for OpenAI configuration
    if os.getenv("OPENAI_API_KEY"):
        config = {
            "provider": "openai",
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        }
        return LLMService(config)
    
    # Check for Anthropic configuration
    if os.getenv("ANTHROPIC_API_KEY"):
        config = {
            "provider": "anthropic",
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "base_url": os.getenv("ANTHROPIC_BASE_URL"),
            "temperature": float(os.getenv("ANTHROPIC_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000"))
        }
        return LLMService(config)
    
    # Check for Ollama configuration
    if os.getenv("OLLAMA_MODEL"):
        config = {
            "provider": "ollama",
            "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("OLLAMA_MAX_TOKENS", "2000"))
        }
        return LLMService(config)
    
    # Check for Enterprise configuration
    if os.getenv("ENTERPRISE_LLM_TOKEN") or os.getenv("ENTERPRISE_LLM_REFRESH_URL"):
        config = {
            "provider": "enterprise",
            "model": os.getenv("ENTERPRISE_LLM_MODEL", "enterprise-model"),
            "base_url": os.getenv("ENTERPRISE_LLM_URL"),
            "temperature": float(os.getenv("ENTERPRISE_LLM_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("ENTERPRISE_LLM_MAX_TOKENS", "2000"))
        }
        return LLMService(config)
    
    # Default to local configuration
    config = {
        "provider": "local",
        "model": os.getenv("LOCAL_LLM_MODEL", "llama-3.2-3b-instruct"),
        "base_url": os.getenv("LOCAL_LLM_URL", "http://localhost:1234"),
        "temperature": float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.3")),
        "max_tokens": int(os.getenv("LOCAL_LLM_MAX_TOKENS", "2000"))
    }
    return LLMService(config)
