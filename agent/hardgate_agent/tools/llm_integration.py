"""
LLM Integration Tool
Comprehensive LLM integration with multi-provider support and pattern generation
"""

import os
import sys
import json
import time
import uuid
import base64
import logging
import threading
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
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


class LLMProvider:
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    LOCAL = "local"
    ENTERPRISE = "enterprise"
    APIGEE = "apigee"


class LLMConfig:
    """LLM configuration"""
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None, 
                 base_url: Optional[str] = None, temperature: float = 0.1, 
                 max_tokens: int = 4000, timeout: int = 300):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout


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
    
    def get_valid_token(self) -> Optional[str]:
        """Get a valid Apigee token, refreshing if necessary"""
        with self._apigee_token_lock:
            now = datetime.now()
            
            # Check if we have a valid cached token
            if (self._apigee_token_cache["token"] and 
                self._apigee_token_cache["expires_at"] > now.timestamp()):
                return self._apigee_token_cache["token"]
            
            # Need to refresh token
            return self._refresh_token()
    
    def _refresh_token(self) -> Optional[str]:
        """Refresh the Apigee token"""
        try:
            if not all([self.apigee_login_url, self.apigee_consumer_key, self.apigee_consumer_secret]):
                self.logger.error("Missing Apigee configuration")
                return None
            
            # Create basic auth header
            credentials = f"{self.apigee_consumer_key}:{self.apigee_consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(
                self.apigee_login_url,
                headers=headers,
                data=data,
                timeout=30,
                verify=False  # Disable SSL verification for enterprise environments
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                
                if access_token:
                    # Cache token with expiry
                    self._apigee_token_cache["token"] = access_token
                    self._apigee_token_cache["expires_at"] = datetime.now().timestamp() + expires_in - 300  # 5 min buffer
                    
                    self.logger.info("Successfully refreshed Apigee token")
                    return access_token
            
            self.logger.error(f"Failed to refresh Apigee token: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error refreshing Apigee token: {str(e)}")
            return None


class LLMClient:
    """Comprehensive LLM client with multi-provider support"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.apigee_manager = ApigeeTokenManager() if config.provider == LLMProvider.APIGEE else None
    
    def generate_patterns(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate patterns using LLM for gate validation"""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                return self._call_openai(prompt, context)
            elif self.config.provider == LLMProvider.ANTHROPIC:
                return self._call_anthropic(prompt, context)
            elif self.config.provider == LLMProvider.GEMINI:
                return self._call_gemini(prompt, context)
            elif self.config.provider == LLMProvider.OLLAMA:
                return self._call_ollama(prompt, context)
            elif self.config.provider == LLMProvider.LOCAL:
                return self._call_local(prompt, context)
            elif self.config.provider == LLMProvider.ENTERPRISE:
                return self._call_enterprise(prompt, context)
            elif self.config.provider == LLMProvider.APIGEE:
                return self._call_apigee(prompt, context)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
        
        except Exception as e:
            self.logger.error(f"Error generating patterns: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "patterns": {},
                "recommendations": []
            }
    
    def _call_openai(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        
        try:
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a security analysis expert specializing in code pattern generation for enterprise security gates."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content, context)
        
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _call_anthropic(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Anthropic API"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available")
        
        try:
            client = anthropic.Anthropic(api_key=self.config.api_key)
            
            response = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return self._parse_llm_response(content, context)
        
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _call_gemini(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Google Gemini API"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI library not available")
        
        try:
            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model)
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens
                )
            )
            
            content = response.text
            return self._parse_llm_response(content, context)
        
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _call_ollama(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Ollama local LLM"""
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama library not available")
        
        try:
            client = ollama.Client(host=self.config.base_url or "http://localhost:11434")
            
            response = client.chat(
                model=self.config.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            )
            
            content = response["message"]["content"]
            return self._parse_llm_response(content, context)
        
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _call_local(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call local LLM via HTTP API"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": "You are a security analysis expert specializing in code pattern generation for enterprise security gates."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                self.config.base_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
                verify=False  # Disable SSL verification for local deployments
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_llm_response(content, context)
            else:
                raise Exception(f"Local LLM API error: {response.status_code} - {response.text}")
        
        except Exception as e:
            raise Exception(f"Local LLM error: {str(e)}")
    
    def _call_enterprise(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call enterprise LLM"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": "You are a security analysis expert specializing in code pattern generation for enterprise security gates."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                self.config.base_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
                verify=False  # Disable SSL verification for enterprise environments
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_llm_response(content, context)
            else:
                raise Exception(f"Enterprise LLM API error: {response.status_code} - {response.text}")
        
        except Exception as e:
            raise Exception(f"Enterprise LLM error: {str(e)}")
    
    def _call_apigee(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Apigee LLM"""
        try:
            token = self.apigee_manager.get_valid_token()
            if not token:
                raise Exception("Failed to obtain Apigee token")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": "You are a security analysis expert specializing in code pattern generation for enterprise security gates."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                self.config.base_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
                verify=False  # Disable SSL verification for enterprise environments
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_llm_response(content, context)
            else:
                raise Exception(f"Apigee LLM API error: {response.status_code} - {response.text}")
        
        except Exception as e:
            raise Exception(f"Apigee LLM error: {str(e)}")
    
    def _parse_llm_response(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response and extract patterns and recommendations"""
        try:
            # Try to parse as JSON first
            if content.strip().startswith("{"):
                data = json.loads(content)
                return {
                    "success": True,
                    "patterns": data.get("patterns", {}),
                    "recommendations": data.get("recommendations", []),
                    "analysis": data.get("analysis", {}),
                    "source": self.config.provider,
                    "model": self.config.model
                }
            
            # Fallback: extract patterns using regex
            patterns = self._extract_patterns_from_text(content)
            recommendations = self._extract_recommendations_from_text(content)
            
            return {
                "success": True,
                "patterns": patterns,
                "recommendations": recommendations,
                "analysis": {"raw_response": content},
                "source": self.config.provider,
                "model": self.config.model
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to parse LLM response: {str(e)}",
                "patterns": {},
                "recommendations": [],
                "raw_response": content
            }
    
    def _extract_patterns_from_text(self, text: str) -> Dict[str, Any]:
        """Extract patterns from text using regex"""
        patterns = {}
        
        # Look for pattern sections
        import re
        
        # Extract positive patterns
        positive_match = re.search(r'positive.*patterns?.*?:(.*?)(?=negative|violation|$)', text, re.IGNORECASE | re.DOTALL)
        if positive_match:
            positive_text = positive_match.group(1).strip()
            patterns["positive"] = [p.strip() for p in positive_text.split('\n') if p.strip()]
        
        # Extract negative patterns
        negative_match = re.search(r'negative.*patterns?.*?:(.*?)(?=positive|violation|$)', text, re.IGNORECASE | re.DOTALL)
        if negative_match:
            negative_text = negative_match.group(1).strip()
            patterns["negative"] = [p.strip() for p in negative_text.split('\n') if p.strip()]
        
        # Extract violation patterns
        violation_match = re.search(r'violation.*patterns?.*?:(.*?)(?=positive|negative|$)', text, re.IGNORECASE | re.DOTALL)
        if violation_match:
            violation_text = violation_match.group(1).strip()
            patterns["violations"] = [p.strip() for p in violation_text.split('\n') if p.strip()]
        
        return patterns
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from text"""
        recommendations = []
        
        # Look for recommendation sections
        import re
        
        rec_match = re.search(r'recommendations?.*?:(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if rec_match:
            rec_text = rec_match.group(1).strip()
            recommendations = [r.strip() for r in rec_text.split('\n') if r.strip() and not r.strip().startswith('-')]
        
        return recommendations


class LLMIntegrationTool(BaseTool):
    """Tool for LLM-powered pattern generation and analysis"""
    
    name = "llm_integration"
    description = "Generate AI-powered patterns for gate validation and provide intelligent recommendations"
    
    def __init__(self):
        super().__init__(name=self.name, description=self.description)
    
    async def run_async(self, args: dict, tool_context: ToolContext) -> dict:
        """Generate patterns using LLM"""
        try:
            repository_path = args.get("repository_path")
            gate_name = args.get("gate_name")
            context = args.get("context", {})
            llm_config = args.get("llm_config", {})
            
            if not repository_path or not gate_name:
                return {
                    "success": False,
                    "error": "Repository path and gate name are required"
                }
            
            # Create LLM client
            config = LLMConfig(
                provider=llm_config.get("provider", "openai"),
                model=llm_config.get("model", "gpt-3.5-turbo"),
                api_key=llm_config.get("api_key"),
                base_url=llm_config.get("base_url"),
                temperature=llm_config.get("temperature", 0.1),
                max_tokens=llm_config.get("max_tokens", 4000)
            )
            
            client = LLMClient(config)
            
            # Generate prompt for the specific gate
            prompt = self._generate_gate_prompt(gate_name, context)
            
            # Generate patterns
            result = client.generate_patterns(prompt, context)
            
            return {
                "success": True,
                "gate_name": gate_name,
                "patterns": result.get("patterns", {}),
                "recommendations": result.get("recommendations", []),
                "analysis": result.get("analysis", {}),
                "source": result.get("source", "unknown"),
                "model": result.get("model", "unknown")
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM integration failed: {str(e)}"
            }
    
    def _generate_gate_prompt(self, gate_name: str, context: Dict[str, Any]) -> str:
        """Generate a comprehensive prompt for gate pattern generation"""
        
        prompt = f"""
You are a security analysis expert specializing in code pattern generation for enterprise security gates.

GATE: {gate_name}

CONTEXT:
- Repository: {context.get('repository_path', 'Unknown')}
- Languages: {', '.join(context.get('languages', []))}
- Technologies: {', '.join(context.get('technologies', []))}
- Codebase Type: {context.get('codebase_type', 'Unknown')}

TASK:
Generate comprehensive patterns for validating the {gate_name} gate. Include:

1. POSITIVE PATTERNS: Code patterns that indicate good implementation
2. NEGATIVE PATTERNS: Code patterns that indicate poor implementation
3. VIOLATION PATTERNS: Code patterns that indicate security violations

For each pattern, provide:
- Regex pattern for matching
- Description of what it detects
- Severity level (High/Medium/Low)

Also provide:
- Specific recommendations for implementing this gate
- Common pitfalls to avoid
- Best practices for this gate

RESPONSE FORMAT:
Return your response as a JSON object with the following structure:
{{
    "patterns": {{
        "positive": [
            {{
                "pattern": "regex_pattern",
                "description": "What this pattern detects",
                "severity": "High/Medium/Low"
            }}
        ],
        "negative": [...],
        "violations": [...]
    }},
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ],
    "analysis": {{
        "gate_importance": "High/Medium/Low",
        "implementation_complexity": "High/Medium/Low",
        "common_issues": ["Issue 1", "Issue 2"]
    }}
}}

Focus on practical, actionable patterns that can be used for automated code analysis.
"""
        
        return prompt


# Create wrapper function for Google ADK compatibility
def llm_integration(repository_path: str, gate_name: str, context: Optional[Dict[str, Any]] = None, 
                   llm_config: Optional[Dict[str, Any]] = None, tool_context = None) -> Dict[str, Any]:
    """
    Generate AI-powered patterns for gate validation using LLM.
    
    Args:
        repository_path: Path to the repository
        gate_name: Name of the gate to generate patterns for
        context: Additional context about the codebase
        llm_config: LLM configuration (provider, model, api_key, etc.)
        tool_context: The ADK tool context
    
    Returns:
        Dictionary containing generated patterns and recommendations
    """
    try:
        if not repository_path or not gate_name:
            return {
                "success": False,
                "error": "Repository path and gate name are required"
            }
        
        # Create LLM client
        config = LLMConfig(
            provider=llm_config.get("provider", "openai") if llm_config else "openai",
            model=llm_config.get("model", "gpt-3.5-turbo") if llm_config else "gpt-3.5-turbo",
            api_key=llm_config.get("api_key") if llm_config else None,
            base_url=llm_config.get("base_url") if llm_config else None,
            temperature=llm_config.get("temperature", 0.1) if llm_config else 0.1,
            max_tokens=llm_config.get("max_tokens", 4000) if llm_config else 4000
        )
        
        client = LLMClient(config)
        
        # Generate prompt for the specific gate
        context = context or {}
        prompt = _generate_gate_prompt(gate_name, context)
        
        # Generate patterns
        result = client.generate_patterns(prompt, context)
        
        return {
            "success": True,
            "gate_name": gate_name,
            "patterns": result.get("patterns", {}),
            "recommendations": result.get("recommendations", []),
            "analysis": result.get("analysis", {}),
            "source": result.get("source", "unknown"),
            "model": result.get("model", "unknown")
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"LLM integration failed: {str(e)}"
        }


def _generate_gate_prompt(gate_name: str, context: Dict[str, Any]) -> str:
    """Generate a comprehensive prompt for gate pattern generation"""
    
    prompt = f"""
You are a security analysis expert specializing in code pattern generation for enterprise security gates.

GATE: {gate_name}

CONTEXT:
- Repository: {context.get('repository_path', 'Unknown')}
- Languages: {', '.join(context.get('languages', []))}
- Technologies: {', '.join(context.get('technologies', []))}
- Codebase Type: {context.get('codebase_type', 'Unknown')}

TASK:
Generate comprehensive patterns for validating the {gate_name} gate. Include:

1. POSITIVE PATTERNS: Code patterns that indicate good implementation
2. NEGATIVE PATTERNS: Code patterns that indicate poor implementation
3. VIOLATION PATTERNS: Code patterns that indicate security violations

For each pattern, provide:
- Regex pattern for matching
- Description of what it detects
- Severity level (High/Medium/Low)

Also provide:
- Specific recommendations for implementing this gate
- Common pitfalls to avoid
- Best practices for this gate

RESPONSE FORMAT:
Return your response as a JSON object with the following structure:
{{
    "patterns": {{
        "positive": [
            {{
                "pattern": "regex_pattern",
                "description": "What this pattern detects",
                "severity": "High/Medium/Low"
            }}
        ],
        "negative": [...],
        "violations": [...]
    }},
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ],
    "analysis": {{
        "gate_importance": "High/Medium/Low",
        "implementation_complexity": "High/Medium/Low",
        "common_issues": ["Issue 1", "Issue 2"]
    }}
}}

Focus on practical, actionable patterns that can be used for automated code analysis.
"""
    
    return prompt 