#!/usr/bin/env python3
"""
Root Agent Loader for HardGate Agent
Provides a clean way to load the HardGate Agent root_agent without conflicts
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any

def setup_hardgate_agent_path():
    """Setup the path for HardGate Agent"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Add to Python path if not already there
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
        print(f"✅ Added HardGate Agent path: {script_dir}")
    
    return True

def load_root_agent():
    """Load the HardGate Agent root_agent"""
    setup_hardgate_agent_path()
    
    try:
        # Import the HardGate Agent
        from agent import HardGateAgent
        
        # Create the root agent
        root_agent = HardGateAgent()
        
        if root_agent and root_agent.agent:
            print("✅ HardGate Agent root_agent loaded successfully")
            print(f"📊 Agent has {len(root_agent.agent.tools)} tools configured")
            return root_agent
        else:
            print("❌ Failed to create HardGate Agent root_agent")
            return None
            
    except Exception as e:
        print(f"❌ Error loading root_agent: {e}")
        return None

def create_codegates_runner():
    """Create and return a runner for the HardGate Agent"""
    root_agent = load_root_agent()
    
    if root_agent and root_agent.agent:
        return root_agent.runner
    else:
        raise Exception("HardGate Agent not properly initialized")

# Load the root_agent when this module is imported
root_agent = load_root_agent()

if __name__ == "__main__":
    print("🚀 HardGate Agent Root Agent Loader")
    print("=" * 50)
    
    agent = load_root_agent()
    
    if agent and agent.agent:
        print("🎉 HardGate Agent root_agent is ready!")
        print("📍 You can now import it using:")
        print("   from agent.hardgate_agent.root_agent_loader import root_agent")
    else:
        print("❌ Failed to load HardGate Agent root_agent") 