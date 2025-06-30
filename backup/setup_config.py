#!/usr/bin/env python3
"""
CodeGates Configuration Setup Script

Interactive script to help users set up their CodeGates environment configuration.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def get_user_input(prompt: str, default: Optional[str] = None, required: bool = False) -> str:
    """Get user input with optional default value"""
    if default:
        prompt = f"{prompt} [{default}]"
    
    while True:
        response = input(f"{prompt}: ").strip()
        
        if response:
            return response
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please enter a value.")

def get_boolean_input(prompt: str, default: bool = False) -> bool:
    """Get boolean input from user"""
    default_str = "y" if default else "n"
    response = input(f"{prompt} [y/n, default: {default_str}]: ").strip().lower()
    
    if response in ('y', 'yes', 'true', '1'):
        return True
    elif response in ('n', 'no', 'false', '0'):
        return False
    else:
        return default

def get_int_input(prompt: str, default: int, min_val: int = 1, max_val: int = 65535) -> int:
    """Get integer input with validation"""
    while True:
        response = input(f"{prompt} [{default}]: ").strip()
        
        if not response:
            return default
        
        try:
            value = int(response)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"Value must be between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid integer")

def setup_api_config() -> Dict[str, Any]:
    """Setup API server configuration"""
    print("\n🌐 API Server Configuration")
    print("=" * 40)
    
    config = {}
    
    # Basic API settings
    config['CODEGATES_API_HOST'] = get_user_input(
        "API Host (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)", 
        "0.0.0.0"
    )
    
    config['CODEGATES_API_PORT'] = str(get_int_input(
        "API Port", 
        8000, 
        1024, 
        65535
    ))
    
    # Generate base URL
    host_for_url = "localhost" if config['CODEGATES_API_HOST'] == "127.0.0.1" else config['CODEGATES_API_HOST']
    default_base_url = f"http://{host_for_url}:{config['CODEGATES_API_PORT']}"
    
    config['CODEGATES_API_BASE_URL'] = get_user_input(
        "API Base URL (for generating report links)", 
        default_base_url
    )
    
    config['CODEGATES_API_TITLE'] = get_user_input(
        "API Title", 
        "MyGates API"
    )
    
    config['CODEGATES_API_DOCS_ENABLED'] = str(get_boolean_input(
        "Enable API Documentation (/docs endpoint)", 
        True
    )).lower()
    
    return config

def setup_llm_config() -> Dict[str, Any]:
    """Setup LLM configuration"""
    print("\n🤖 LLM Configuration")
    print("=" * 40)
    
    config = {}
    
    enable_llm = get_boolean_input("Enable LLM-enhanced analysis", False)
    config['CODEGATES_LLM_ENABLED'] = str(enable_llm).lower()
    
    if enable_llm:
        providers = {
            '1': 'local',
            '2': 'openai', 
            '3': 'anthropic',
            '4': 'gemini'
        }
        
        print("\nAvailable LLM providers:")
        print("1. Local (LM Studio, Ollama, etc.)")
        print("2. OpenAI")
        print("3. Anthropic")
        print("4. Google Gemini")
        
        while True:
            choice = input("Select LLM provider [1-4, default: 1]: ").strip()
            if not choice:
                choice = '1'
            if choice in providers:
                config['CODEGATES_LLM_PROVIDER'] = providers[choice]
                break
            print("Invalid choice. Please select 1-4.")
        
        provider = config['CODEGATES_LLM_PROVIDER']
        
        if provider == 'local':
            config['LOCAL_LLM_URL'] = get_user_input(
                "Local LLM URL", 
                "http://localhost:1234/v1"
            )
            config['LOCAL_LLM_MODEL'] = get_user_input(
                "Local LLM Model", 
                "meta-llama-3.1-8b-instruct"
            )
        
        elif provider == 'openai':
            config['OPENAI_API_KEY'] = get_user_input(
                "OpenAI API Key", 
                required=True
            )
            config['OPENAI_MODEL'] = get_user_input(
                "OpenAI Model", 
                "gpt-4"
            )
        
        elif provider == 'anthropic':
            config['ANTHROPIC_API_KEY'] = get_user_input(
                "Anthropic API Key", 
                required=True
            )
            config['ANTHROPIC_MODEL'] = get_user_input(
                "Anthropic Model", 
                "claude-3-sonnet-20240229"
            )
        
        elif provider == 'gemini':
            config['GOOGLE_API_KEY'] = get_user_input(
                "Google API Key", 
                required=True
            )
            config['GEMINI_MODEL'] = get_user_input(
                "Gemini Model", 
                "gemini-pro"
            )
    
    return config

def setup_github_config() -> Dict[str, Any]:
    """Setup GitHub integration"""
    print("\n🐙 GitHub Integration")
    print("=" * 40)
    
    config = {}
    
    config['GITHUB_TOKEN'] = get_user_input(
        "GitHub Personal Access Token (for private repos, optional)"
    )
    
    if get_boolean_input("Using GitHub Enterprise", False):
        config['GITHUB_API_BASE_URL'] = get_user_input(
            "GitHub Enterprise API Base URL",
            "https://github.company.com/api/v3"
        )
    
    return config

def setup_jira_config() -> Dict[str, Any]:
    """Setup JIRA integration"""
    print("\n📋 JIRA Integration")
    print("=" * 40)
    
    config = {}
    
    if get_boolean_input("Enable JIRA integration", False):
        config['JIRA_URL'] = get_user_input(
            "JIRA Instance URL",
            "https://company.atlassian.net",
            required=True
        )
        
        config['JIRA_USERNAME'] = get_user_input(
            "JIRA Username/Email",
            required=True
        )
        
        config['JIRA_API_TOKEN'] = get_user_input(
            "JIRA API Token",
            required=True
        )
    
    return config

def setup_cors_config() -> Dict[str, Any]:
    """Setup CORS configuration"""
    print("\n🌍 CORS Configuration")
    print("=" * 40)
    
    config = {}
    
    print("Current CORS origins: vscode-webview://* and localhost variants")
    
    if get_boolean_input("Add custom CORS origins", False):
        custom_origins = get_user_input(
            "Additional CORS origins (comma-separated)",
            "https://mydomain.com,https://app.mydomain.com"
        )
        
        default_origins = "vscode-webview://*,http://localhost:*,http://127.0.0.1:*,https://localhost:*,https://127.0.0.1:*"
        if custom_origins:
            config['CODEGATES_CORS_ORIGINS'] = f"{default_origins},{custom_origins}"
        else:
            config['CODEGATES_CORS_ORIGINS'] = default_origins
    
    return config

def write_env_file(config: Dict[str, Any], file_path: str):
    """Write configuration to .env file"""
    
    # Load template
    template_path = Path("codegates/config/environment.template")
    if not template_path.exists():
        print(f"⚠️ Template file not found: {template_path}")
        print("Creating basic .env file...")
        
        with open(file_path, 'w') as f:
            f.write("# CodeGates Environment Configuration\n")
            f.write("# Generated by setup_config.py\n\n")
            for key, value in config.items():
                f.write(f"{key}={value}\n")
    else:
        # Use template and replace values
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Replace values in template
        for key, value in config.items():
            # Find the line with this key and replace its value
            lines = template_content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    break
            template_content = '\n'.join(lines)
        
        # Write updated template
        with open(file_path, 'w') as f:
            f.write(template_content)
    
    print(f"✅ Configuration written to: {file_path}")

def main():
    """Main setup function"""
    print("🛡️  CodeGates Configuration Setup")
    print("=" * 50)
    print("This script will help you configure CodeGates for your environment.")
    print()
    
    # Collect all configuration
    all_config = {}
    
    # API Configuration
    all_config.update(setup_api_config())
    
    # LLM Configuration
    all_config.update(setup_llm_config())
    
    # GitHub Configuration
    all_config.update(setup_github_config())
    
    # JIRA Configuration
    all_config.update(setup_jira_config())
    
    # CORS Configuration
    all_config.update(setup_cors_config())
    
    # Remove empty values
    all_config = {k: v for k, v in all_config.items() if v}
    
    print("\n📄 Configuration Summary")
    print("=" * 40)
    for key, value in all_config.items():
        # Mask sensitive values
        if 'key' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
            display_value = '*' * 8 if value else ''
        else:
            display_value = value
        print(f"{key}: {display_value}")
    
    print()
    
    # Choose output file
    env_files = ['.env', 'config/.env', 'codegates/.env']
    print("Available .env file locations:")
    for i, env_file in enumerate(env_files, 1):
        print(f"{i}. {env_file}")
    
    while True:
        choice = input(f"Choose location [1-{len(env_files)}, default: 1]: ").strip()
        if not choice:
            choice = '1'
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(env_files):
                env_file = env_files[choice_idx]
                break
        except ValueError:
            pass
        print("Invalid choice.")
    
    # Create directory if needed
    env_path = Path(env_file)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing file
    if env_path.exists():
        backup_path = f"{env_file}.backup"
        print(f"📁 Backing up existing file to: {backup_path}")
        import shutil
        shutil.copy2(env_path, backup_path)
    
    # Write configuration
    write_env_file(all_config, env_file)
    
    print()
    print("🎉 Configuration setup complete!")
    print()
    print("Next steps:")
    print("1. Review and edit the generated .env file if needed")
    print("2. Start the CodeGates API server:")
    print("   python start_server.py")
    print("3. Test the configuration:")
    print("   python test_local_llm.py")
    print()
    print("For VS Code extension setup:")
    print("1. Install the CodeGates extension")
    print("2. Configure the API URL in VS Code settings")
    print(f"3. Set API URL to: {all_config.get('CODEGATES_API_BASE_URL', 'http://localhost:8000')}/api/v1")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1) 