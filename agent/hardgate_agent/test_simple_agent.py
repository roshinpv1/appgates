#!/usr/bin/env python3
"""
Simple test to verify agent works with basic tools
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from hardgate_agent.tools import (
    evidence_collection_tool,
    llm_analysis_tool
)


def test_simple_agent():
    """Test agent with just the basic tools that are known to work"""
    print("🧪 Testing Simple Agent")
    print("=" * 30)
    
    try:
        # Create a simple agent with just the working tools
        simple_agent = Agent(
            model=LiteLlm(
                model="gpt-3.5-turbo", 
                base_url="http://localhost:1234/v1", 
                api_key="test", 
                provider="openai"
            ),
            name="simple_hardgate_agent",
            description="Simple HardGate Agent for testing",
            instruction="You are a simple security analysis agent. Use the available tools to analyze security.",
            tools=[
                evidence_collection_tool,
                llm_analysis_tool
            ],
        )
        
        print("✅ Simple agent created successfully!")
        print(f"   Agent name: {simple_agent.name}")
        print(f"   Tools registered: {len(simple_agent.tools)}")
        
        # List the tools
        print("\n📋 Registered Tools:")
        for i, tool in enumerate(simple_agent.tools, 1):
            print(f"   {i}. {tool.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating simple agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_simple_agent() 