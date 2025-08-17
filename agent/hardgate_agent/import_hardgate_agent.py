#!/usr/bin/env python3
"""
Dedicated import script for HardGate Agent
This script properly loads the HardGate Agent without conflicts with existing agent modules
"""

import sys
import os
from pathlib import Path

# Add the hardgate_agent directory to the path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def import_hardgate_agent():
    """Import and return the HardGate Agent"""
    try:
        from agent import HardGateAgent
        return HardGateAgent
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def create_hardgate_agent():
    """Create and return a HardGate Agent instance"""
    try:
        HardGateAgentClass = import_hardgate_agent()
        if HardGateAgentClass:
            agent = HardGateAgentClass()
            return agent
        else:
            return None
    except Exception as e:
        print(f"❌ Error creating HardGate Agent: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Loading HardGate Agent...")
    agent = create_hardgate_agent()
    
    if agent and agent.agent:
        print("✅ HardGate Agent loaded successfully!")
        print(f"📊 Agent has {len(agent.agent.tools)} tools configured")
        print("🎉 Ready for use!")
    else:
        print("❌ Failed to load HardGate Agent") 