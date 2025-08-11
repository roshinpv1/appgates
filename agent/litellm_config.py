"""
LiteLLM Configuration for CodeGates Agent
Integrates LiteLLM with existing CodeGates LLM configuration
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from gates.utils.llm_client import LLMConfig, LLMProvider
    CODEGATES_LLM_AVAILABLE = True
except ImportError:
    CODEGATES_LLM_AVAILABLE = False

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class LiteLLMConfig:
    """Configuration manager for LiteLLM integration"""
    
    def __init__(self):
        self.codegates_config = None
        self.litellm_config = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load configurations from CodeGates and environment"""
        # Load CodeGates LLM configuration
        if CODEGATES_LLM_AVAILABLE:
            try:
                self.codegates_config = LLMConfig.from_env()
                print(f"✅ Loaded CodeGates LLM config: {self.codegates_config.provider}")
            except Exception as e:
                print(f"⚠️ Error loading CodeGates config: {e}")
        
        # Load LiteLLM configuration
        self._load_litellm_config()
    
    def _load_litellm_config(self):
        """Load LiteLLM configuration from environment"""
        # Default LiteLLM settings
        self.litellm_config = {
            "model": os.getenv("LITELLM_MODEL", "gpt-3.5-turbo"),
            "api_key": os.getenv("LITELLM_API_KEY"),
            "base_url": os.getenv("LITELLM_BASE_URL"),
            "temperature": float(os.getenv("LITELLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LITELLM_MAX_TOKENS", "2000")),
            "timeout": int(os.getenv("LITELLM_TIMEOUT", "60")),
            "provider": os.getenv("LITELLM_PROVIDER", "openai")
        }
    
    def configure_litellm_from_codegates(self):
        """Configure LiteLLM using CodeGates settings"""
        if not self.codegates_config:
            print("⚠️ No CodeGates configuration available")
            return False
        
        try:
            # Map CodeGates provider to LiteLLM provider
            provider_mapping = {
                LLMProvider.OPENAI: "openai",
                LLMProvider.ANTHROPIC: "anthropic", 
                LLMProvider.GOOGLE: "google",
                LLMProvider.OLLAMA: "ollama",
                LLMProvider.ENTERPRISE: "custom"
            }
            
            litellm_provider = provider_mapping.get(self.codegates_config.provider, "openai")
            
            # Set environment variables for LiteLLM
            if self.codegates_config.api_key:
                os.environ["LITELLM_API_KEY"] = self.codegates_config.api_key
            
            if self.codegates_config.base_url:
                os.environ["LITELLM_BASE_URL"] = self.codegates_config.base_url
            
            # Provider-specific configuration
            if self.codegates_config.provider == LLMProvider.OLLAMA:
                os.environ["OLLAMA_BASE_URL"] = self.codegates_config.base_url
                self.litellm_config["model"] = self.codegates_config.model
                self.litellm_config["provider"] = "ollama"
                
            elif self.codegates_config.provider == LLMProvider.OPENAI:
                os.environ["OPENAI_API_KEY"] = self.codegates_config.api_key
                if self.codegates_config.base_url:
                    os.environ["OPENAI_API_BASE"] = self.codegates_config.base_url
                self.litellm_config["model"] = self.codegates_config.model
                self.litellm_config["provider"] = "openai"
                
            elif self.codegates_config.provider == LLMProvider.ANTHROPIC:
                os.environ["ANTHROPIC_API_KEY"] = self.codegates_config.api_key
                self.litellm_config["model"] = self.codegates_config.model
                self.litellm_config["provider"] = "anthropic"
                
            elif self.codegates_config.provider == LLMProvider.GOOGLE:
                os.environ["GOOGLE_API_KEY"] = self.codegates_config.api_key
                self.litellm_config["model"] = self.codegates_config.model
                self.litellm_config["provider"] = "google"
                
            elif self.codegates_config.provider == LLMProvider.ENTERPRISE:
                # Custom enterprise LLM configuration
                self.litellm_config["model"] = self.codegates_config.model
                self.litellm_config["provider"] = "custom"
                if self.codegates_config.base_url:
                    self.litellm_config["base_url"] = self.codegates_config.base_url
            
            print(f"✅ Configured LiteLLM with provider: {self.litellm_config['provider']}")
            print(f"   Model: {self.litellm_config['model']}")
            print(f"   Base URL: {self.litellm_config.get('base_url', 'Default')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error configuring LiteLLM: {e}")
            return False
    
    def get_completion_params(self, messages: list, tools: Optional[list] = None) -> Dict[str, Any]:
        """Get completion parameters for LiteLLM"""
        params = {
            "model": self.litellm_config["model"],
            "messages": messages,
            "temperature": self.litellm_config["temperature"],
            "max_tokens": self.litellm_config["max_tokens"],
            "timeout": self.litellm_config["timeout"]
        }
        
        # Add tools if provided
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        return params
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            "provider": self.litellm_config["provider"],
            "model": self.litellm_config["model"],
            "base_url": self.litellm_config.get("base_url"),
            "temperature": self.litellm_config["temperature"],
            "max_tokens": self.litellm_config["max_tokens"]
        }


def setup_litellm_environment():
    """Setup LiteLLM environment variables"""
    print("🔧 Setting up LiteLLM environment...")
    
    # Create configuration
    config = LiteLLMConfig()
    
    # Configure from CodeGates if available
    if CODEGATES_LLM_AVAILABLE:
        success = config.configure_litellm_from_codegates()
        if success:
            print("✅ LiteLLM configured from CodeGates settings")
        else:
            print("⚠️ Using default LiteLLM configuration")
    else:
        print("⚠️ CodeGates LLM not available, using default LiteLLM configuration")
    
    return config


def test_litellm_configuration():
    """Test LiteLLM configuration"""
    print("🧪 Testing LiteLLM Configuration")
    print("=" * 50)
    
    if not LITELLM_AVAILABLE:
        print("❌ LiteLLM not available")
        print("   Install with: pip install litellm")
        return False
    
    # Setup configuration
    config = setup_litellm_environment()
    
    # Test configuration
    model_info = config.get_model_info()
    print(f"Provider: {model_info['provider']}")
    print(f"Model: {model_info['model']}")
    print(f"Base URL: {model_info['base_url']}")
    print(f"Temperature: {model_info['temperature']}")
    print(f"Max Tokens: {model_info['max_tokens']}")
    
    return True


def get_litellm_completion_params(messages: list, tools: Optional[list] = None) -> Dict[str, Any]:
    """Get LiteLLM completion parameters"""
    config = setup_litellm_environment()
    return config.get_completion_params(messages, tools)


if __name__ == "__main__":
    # Test configuration
    test_litellm_configuration() 