#!/usr/bin/env python3
"""
CodeGates Agent Runner for ADK Web
Simple script to run the CodeGates validation agent
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Main function to run the agent"""
    
    print("🚀 CodeGates Validation Agent")
    print("=" * 50)
    print("Starting agent...")
    
    try:
        # Import agent components
        from agent import create_codegates_runner
        
        print("✅ Agent components loaded successfully")
        
        # Create runner
        runner = create_codegates_runner()
        print("✅ Runner created successfully")
        
        print("\n🎯 Agent is ready!")
        print("=" * 50)
        print("Available commands:")
        print("- Validate repository: 'Validate the repository at https://github.com/company/myapp'")
        print("- List gates: 'What gates are available for validation?'")
        print("- Get help: 'Help me understand the validation process'")
        print("- Collect evidence: 'Collect evidence from Splunk and AppDynamics'")
        print("=" * 50)
        
        # Example interaction
        print("\n📝 Example interaction:")
        user_message = {
            "parts": [{
                "text": "Hello! Can you help me understand what gates are available for validation?"
            }]
        }
        
        print("User: Hello! Can you help me understand what gates are available for validation?")
        print("Agent: Processing...")
        
        # Run the agent
        async def run_example():
            async for event in runner.run_async(
                user_id="user123",
                session_id="session456",
                new_message=user_message
            ):
                if hasattr(event, 'content') and event.content:
                    print(f"Agent: {event.content[:200]}...")
                    break
        
        # Run the example
        asyncio.run(run_example())
        
        print("\n✅ Agent is working correctly!")
        print("You can now use ADK web to interact with the agent:")
        print("  adk web .")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies:")
        print("  pip install google-adk litellm")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main() 