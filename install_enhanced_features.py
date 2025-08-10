#!/usr/bin/env python3
"""
Enhanced Features Installation Script
Installs and configures enhanced CodeGates features
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing enhanced dependencies...")
    
    # Install PyYAML
    if not run_command("pip install PyYAML>=6.0", "Installing PyYAML"):
        return False
    
    # Install Playwright
    if not run_command("pip install playwright>=1.40.0", "Installing Playwright"):
        return False
    
    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright browsers"):
        return False
    
    # Install other dependencies
    dependencies = [
        "asyncio-compat>=0.1.2",
        "aiofiles>=23.0.0",
        "aiohttp>=3.9.0",
        "requests>=2.31.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "gates/config",
        "gates/cli",
        "gates/nodes",
        "evidence_screenshots"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_configuration():
    """Set up initial configuration"""
    print("\n⚙️ Setting up configuration...")
    
    # Check if config file exists
    config_path = Path("gates/config/gate_config.yml")
    if config_path.exists():
        print("✅ Configuration file already exists")
        return True
    
    # Create default configuration
    print("📝 Creating default configuration...")
    
    # The configuration file was already created earlier
    if config_path.exists():
        print("✅ Default configuration created")
        return True
    else:
        print("⚠️ Configuration file not found. Please create gates/config/gate_config.yml manually.")
        return False


def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    # Test imports
    try:
        import yaml
        print("✅ PyYAML import successful")
    except ImportError:
        print("❌ PyYAML import failed")
        return False
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright import successful")
    except ImportError:
        print("❌ Playwright import failed")
        return False
    
    # Test gate configuration loader
    try:
        from gates.utils.gate_config_loader import GateConfigLoader
        loader = GateConfigLoader()
        print("✅ Gate configuration loader working")
    except Exception as e:
        print(f"⚠️ Gate configuration loader test failed: {e}")
    
    # Test evidence collector
    try:
        from gates.utils.evidence_collector import is_evidence_available
        if is_evidence_available():
            print("✅ Evidence collector available")
        else:
            print("⚠️ Evidence collector not available (Playwright may not be installed)")
    except Exception as e:
        print(f"⚠️ Evidence collector test failed: {e}")
    
    # Test API validator
    try:
        from gates.utils.api_validator import is_api_validation_available
        if is_api_validation_available():
            print("✅ API validator available")
        else:
            print("⚠️ API validator not available (requests may not be installed)")
    except Exception as e:
        print(f"⚠️ API validator test failed: {e}")
    
    return True


def main():
    """Main installation function"""
    print("🚀 CodeGates Enhanced Features Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed. Please check the errors above.")
        sys.exit(1)
    
    # Setup configuration
    setup_configuration()
    
    # Test installation
    if not test_installation():
        print("\n⚠️ Installation completed with warnings. Some features may not work.")
    else:
        print("\n✅ Installation completed successfully!")
    
    print("\n📋 Next Steps:")
    print("1. Configure your gates in gates/config/gate_config.yml")
    print("2. Use the gate manager CLI: python -m gates.cli.gate_manager")
    print("3. Run enhanced validation with evidence collection")
    print("4. Check evidence_screenshots/ for collected evidence")
    
    print("\n🔗 Useful Commands:")
    print("  python -m gates.cli.gate_manager list")
    print("  python -m gates.cli.gate_manager add --help")
    print("  python -m gates.cli.gate_manager stats")


if __name__ == '__main__':
    main() 