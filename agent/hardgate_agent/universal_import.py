#!/usr/bin/env python3
"""
Universal Import Script for HardGate Agent
Works from any location and bypasses existing module conflicts
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any

def find_hardgate_agent_path() -> Optional[Path]:
    """Find the hardgate_agent directory from any location"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Check if we're already in the hardgate_agent directory
    if (script_dir / "agent.py").exists() and (script_dir / "prompt.py").exists():
        return script_dir
    
    # Check common relative paths
    possible_paths = [
        script_dir,
        script_dir.parent / "hardgate_agent",
        script_dir.parent.parent / "agent" / "hardgate_agent",
        Path.cwd() / "agent" / "hardgate_agent",
        Path.cwd() / "hardgate_agent",
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "agent.py").exists() and (path / "prompt.py").exists():
            return path
    
    return None

def setup_import_path() -> bool:
    """Setup the import path for HardGate Agent"""
    hardgate_path = find_hardgate_agent_path()
    
    if not hardgate_path:
        print("❌ Could not find HardGate Agent directory")
        return False
    
    # Add to Python path if not already there
    if str(hardgate_path) not in sys.path:
        sys.path.insert(0, str(hardgate_path))
        print(f"✅ Added HardGate Agent path: {hardgate_path}")
    
    return True

def import_hardgate_agent() -> Optional[Any]:
    """Import the HardGate Agent class"""
    if not setup_import_path():
        return None
    
    try:
        # Import directly from the hardgate_agent directory
        import agent
        return agent.HardGateAgent
    except ImportError as e:
        print(f"❌ Failed to import HardGate Agent: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error importing HardGate Agent: {e}")
        return None

def create_hardgate_agent() -> Optional[Any]:
    """Create and return a HardGate Agent instance"""
    HardGateAgentClass = import_hardgate_agent()
    
    if not HardGateAgentClass:
        return None
    
    try:
        agent = HardGateAgentClass()
        return agent
    except Exception as e:
        print(f"❌ Error creating HardGate Agent: {e}")
        return None

def verify_imports() -> bool:
    """Verify that all required modules can be imported"""
    print("🔍 Verifying HardGate Agent imports...")
    
    if not setup_import_path():
        return False
    
    try:
        # Test import prompt module
        import prompt
        print("✅ Prompt module imported successfully")
        
        # Test import tools
        from tools import (
            RepositoryAnalysisTool,
            GateValidationTool,
            EvidenceCollectionTool,
            ReportGenerationTool,
            CodeScanningTool,
            SecurityAnalysisTool,
            ComplianceCheckTool,
            LLMAnalysisTool
        )
        print("✅ Tools imported successfully")
        
        # Test import agent
        import agent
        print("✅ Agent module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import verification failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during verification: {e}")
        return False

def test_agent_creation() -> bool:
    """Test creating a HardGate Agent instance"""
    print("🔍 Testing agent creation...")
    
    agent = create_hardgate_agent()
    
    if agent and agent.agent:
        print("✅ HardGate Agent created successfully!")
        print(f"📊 Agent has {len(agent.agent.tools)} tools configured")
        return True
    else:
        print("❌ Failed to create HardGate Agent")
        return False

if __name__ == "__main__":
    print("🚀 Universal HardGate Agent Import Test")
    print("=" * 50)
    
    # Test imports
    if verify_imports():
        print("\n✅ All imports verified successfully!")
        
        # Test agent creation
        if test_agent_creation():
            print("\n🎉 HardGate Agent is ready for use!")
            print("📍 You can now import it from any location using:")
            print("   from agent.hardgate_agent.universal_import import create_hardgate_agent")
        else:
            print("\n❌ Agent creation failed")
    else:
        print("\n❌ Import verification failed") 