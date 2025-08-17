#!/usr/bin/env python3
"""
Debug script to understand tool registration issues
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hardgate_agent.tools import (
    analyze_repository,
    evidence_collection_tool,
    llm_analysis_tool,
    validate_gates,
    analyze_security,
    scan_code,
    check_compliance,
    generate_report
)


def debug_tools():
    """Debug tool registration"""
    print("🔍 Debugging Tool Registration")
    print("=" * 40)
    
    # Check what tools we have
    tools = [
        analyze_repository,
        evidence_collection_tool,
        llm_analysis_tool,
        validate_gates,
        analyze_security,
        scan_code,
        check_compliance,
        generate_report
    ]
    
    print("📋 Available Tools:")
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {tool.__name__} - {type(tool)}")
        if hasattr(tool, '__doc__') and tool.__doc__:
            print(f"      Doc: {tool.__doc__.strip().split('.')[0]}")
        print()
    
    # Check if tools are callable
    print("🔧 Tool Callability:")
    for tool in tools:
        print(f"   {tool.__name__}: {callable(tool)}")
    
    # Check function signatures
    print("\n📝 Function Signatures:")
    import inspect
    for tool in tools:
        sig = inspect.signature(tool)
        print(f"   {tool.__name__}: {sig}")
    
    # Test basic functionality
    print("\n🧪 Basic Functionality Test:")
    try:
        # Test with a simple call
        result = analyze_repository(repository_path="/tmp/test")
        print(f"   analyze_repository: ✅ Works")
    except Exception as e:
        print(f"   analyze_repository: ❌ Error - {e}")
    
    try:
        result = validate_gates(repository_path="/tmp/test")
        print(f"   validate_gates: ✅ Works")
    except Exception as e:
        print(f"   validate_gates: ❌ Error - {e}")


if __name__ == "__main__":
    debug_tools() 