#!/usr/bin/env python3
"""
Load HardGate Agent for Google ADK Agent Development Kit
This script provides direct access to the root_agent without conflicts
"""

import sys
import os
from pathlib import Path

def setup_hardgate_agent():
    """Setup the HardGate Agent for Google ADK"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Add to Python path if not already there
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    try:
        # Import the root_agent directly
        from agent import root_agent
        
        print("✅ HardGate Agent loaded successfully for Google ADK")
        print(f"📊 Agent name: {root_agent.name}")
        print(f"📊 Agent has {len(root_agent.tools)} tools")
        print(f"📊 Agent model: {root_agent.model}")
        
        return root_agent
        
    except Exception as e:
        print(f"❌ Error loading HardGate Agent: {e}")
        return None

def get_root_agent():
    """Get the root_agent for Google ADK"""
    return setup_hardgate_agent()

# Load the root_agent when this module is imported
root_agent = get_root_agent()

if __name__ == "__main__":
    print("🚀 HardGate Agent Loader for Google ADK")
    print("=" * 50)
    
    agent = get_root_agent()
    
    if agent:
        print("\n🎉 HardGate Agent is ready for Google ADK!")
        print("📍 You can now use this agent in the Google ADK Agent Development Kit")
        print("\n📋 Available tools:")
        for i, tool in enumerate(agent.tools, 1):
            print(f"   {i}. {tool.name}: {tool.description}")
    else:
        print("\n❌ Failed to load HardGate Agent") 