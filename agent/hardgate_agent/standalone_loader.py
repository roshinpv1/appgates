#!/usr/bin/env python3
"""
Standalone HardGate Agent Loader
Completely bypasses existing agent module conflicts and provides clean access to root_agent
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any

class StandaloneHardGateLoader:
    """Standalone loader for HardGate Agent that bypasses all conflicts"""
    
    def __init__(self):
        self.hardgate_path = None
        self.root_agent = None
        self._setup_path()
    
    def _setup_path(self):
        """Setup the path for HardGate Agent"""
        # Find the hardgate_agent directory
        possible_paths = [
            Path(__file__).parent,  # Current directory
            Path.cwd() / "agent" / "hardgate_agent",
            Path.cwd() / "hardgate_agent",
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "agent.py").exists():
                self.hardgate_path = path
                break
        
        if self.hardgate_path:
            # Add to Python path
            if str(self.hardgate_path) not in sys.path:
                sys.path.insert(0, str(self.hardgate_path))
                print(f"✅ Found HardGate Agent at: {self.hardgate_path}")
        else:
            print("❌ Could not find HardGate Agent directory")
    
    def load_root_agent(self):
        """Load the HardGate Agent root_agent"""
        if not self.hardgate_path:
            print("❌ HardGate Agent path not set")
            return None
        
        try:
            # Import the HardGate Agent directly
            import agent
            from agent import HardGateAgent
            
            # Create the root agent
            self.root_agent = HardGateAgent()
            
            if self.root_agent and self.root_agent.agent:
                print("✅ HardGate Agent root_agent loaded successfully")
                print(f"📊 Agent has {len(self.root_agent.agent.tools)} tools configured")
                return self.root_agent
            else:
                print("❌ Failed to create HardGate Agent root_agent")
                return None
                
        except Exception as e:
            print(f"❌ Error loading root_agent: {e}")
            return None
    
    def create_codegates_runner(self):
        """Create and return a runner for the HardGate Agent"""
        if not self.root_agent:
            self.root_agent = self.load_root_agent()
        
        if self.root_agent and self.root_agent.agent:
            return self.root_agent.runner
        else:
            raise Exception("HardGate Agent not properly initialized")

# Global loader instance
_loader = None

def get_loader():
    """Get the global loader instance"""
    global _loader
    if _loader is None:
        _loader = StandaloneHardGateLoader()
    return _loader

def load_root_agent():
    """Load the HardGate Agent root_agent"""
    loader = get_loader()
    return loader.load_root_agent()

def create_codegates_runner():
    """Create and return a runner for the HardGate Agent"""
    loader = get_loader()
    return loader.create_codegates_runner()

# Load the root_agent when this module is imported
root_agent = load_root_agent()

if __name__ == "__main__":
    print("🚀 Standalone HardGate Agent Loader")
    print("=" * 50)
    
    agent = load_root_agent()
    
    if agent and agent.agent:
        print("🎉 HardGate Agent root_agent is ready!")
        print("📍 You can now import it using:")
        print("   from agent.hardgate_agent.standalone_loader import root_agent")
        
        # Test the runner
        try:
            runner = create_codegates_runner()
            print("✅ Runner created successfully")
        except Exception as e:
            print(f"❌ Runner creation failed: {e}")
    else:
        print("❌ Failed to load HardGate Agent root_agent") 