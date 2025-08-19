#!/usr/bin/env python3
"""
Comprehensive Import Resolver for HardGate Agent
Handles all import issues and provides robust module loading from any location
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

class HardGateImportResolver:
    """Resolves all import issues for HardGate Agent"""
    
    def __init__(self):
        self.hardgate_agent_path = None
        self.prompt_module = None
        self.tools_module = None
        self.agent_module = None
        self._setup_paths()
    
    def _setup_paths(self):
        """Setup import paths for HardGate Agent"""
        # Find the hardgate_agent directory
        possible_paths = [
            # Current directory
            Path.cwd() / "agent" / "hardgate_agent",
            # Script directory
            Path(__file__).parent,
            # Parent directory
            Path(__file__).parent.parent / "hardgate_agent",
            # Project root
            Path(__file__).parent.parent.parent / "agent" / "hardgate_agent",
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "agent.py").exists():
                self.hardgate_agent_path = path
                break
        
        if self.hardgate_agent_path:
            # Add to Python path
            if str(self.hardgate_agent_path) not in sys.path:
                sys.path.insert(0, str(self.hardgate_agent_path))
            print(f"✅ Found HardGate Agent at: {self.hardgate_agent_path}")
        else:
            print("❌ Could not find HardGate Agent directory")
    
    def import_prompt_module(self) -> Optional[Any]:
        """Import the prompt module"""
        if self.prompt_module is not None:
            return self.prompt_module
        
        try:
            import prompt
            self.prompt_module = prompt
            print("✅ Prompt module imported successfully")
            return prompt
        except ImportError:
            print("❌ Failed to import prompt module")
            return None
    
    def import_tools_module(self) -> Optional[Dict[str, Any]]:
        """Import all tools from the tools module"""
        if self.tools_module is not None:
            return self.tools_module
        
        try:
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
            
            self.tools_module = {
                "RepositoryAnalysisTool": RepositoryAnalysisTool,
                "GateValidationTool": GateValidationTool,
                "EvidenceCollectionTool": EvidenceCollectionTool,
                "ReportGenerationTool": ReportGenerationTool,
                "CodeScanningTool": CodeScanningTool,
                "SecurityAnalysisTool": SecurityAnalysisTool,
                "ComplianceCheckTool": ComplianceCheckTool,
                "LLMAnalysisTool": LLMAnalysisTool
            }
            print("✅ Tools module imported successfully")
            return self.tools_module
        except ImportError as e:
            print(f"❌ Failed to import tools module: {e}")
            return None
    
    def import_agent_module(self) -> Optional[Any]:
        """Import the HardGate Agent"""
        if self.agent_module is not None:
            return self.agent_module
        
        try:
            from agent import HardGateAgent
            self.agent_module = HardGateAgent
            print("✅ HardGate Agent imported successfully")
            return HardGateAgent
        except ImportError as e:
            print(f"❌ Failed to import HardGate Agent: {e}")
            return None
    
    def create_agent(self) -> Optional[Any]:
        """Create and return a HardGate Agent instance"""
        try:
            HardGateAgentClass = self.import_agent_module()
            if HardGateAgentClass:
                agent = HardGateAgentClass()
                return agent
            else:
                return None
        except Exception as e:
            print(f"❌ Error creating HardGate Agent: {e}")
            return None
    
    def verify_all_imports(self) -> bool:
        """Verify that all required modules can be imported"""
        print("🔍 Verifying all imports...")
        
        # Check prompt module
        prompt = self.import_prompt_module()
        if not prompt:
            print("❌ Prompt module verification failed")
            return False
        
        # Check tools module
        tools = self.import_tools_module()
        if not tools:
            print("❌ Tools module verification failed")
            return False
        
        # Check agent module
        agent_class = self.import_agent_module()
        if not agent_class:
            print("❌ Agent module verification failed")
            return False
        
        print("✅ All imports verified successfully")
        return True

# Global resolver instance
_resolver = None

def get_resolver() -> HardGateImportResolver:
    """Get the global resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = HardGateImportResolver()
    return _resolver

def import_hardgate_agent() -> Optional[Any]:
    """Import and return the HardGate Agent class"""
    resolver = get_resolver()
    return resolver.import_agent_module()

def create_hardgate_agent() -> Optional[Any]:
    """Create and return a HardGate Agent instance"""
    resolver = get_resolver()
    return resolver.create_agent()

def verify_imports() -> bool:
    """Verify that all imports are working"""
    resolver = get_resolver()
    return resolver.verify_all_imports()

if __name__ == "__main__":
    print("🔧 HardGate Agent Import Resolver")
    print("=" * 50)
    
    # Test the resolver
    resolver = get_resolver()
    
    if resolver.verify_all_imports():
        print("\n🎉 All imports working correctly!")
        
        # Try to create an agent
        agent = resolver.create_agent()
        if agent and agent.agent:
            print("✅ HardGate Agent created successfully!")
            print(f"📊 Agent has {len(agent.agent.tools)} tools configured")
        else:
            print("❌ Failed to create HardGate Agent")
    else:
        print("\n❌ Import verification failed") 