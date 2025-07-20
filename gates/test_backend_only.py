#!/usr/bin/env python3
"""
Test script to demonstrate NOT_APPLICABLE gates with a backend-only codebase
"""

import sys
import os
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import create_static_only_flow

def test_backend_only_applicability():
    """Test with a backend-only codebase to show NOT_APPLICABLE gates"""
    
    # Test with a backend-only repository (no frontend components)
    repository_url = "https://github.com/spring-projects/spring-framework"  # Core framework, mostly backend
    branch = "main"
    github_token = None
    threshold = 70
    
    print(f"🔍 Testing with Backend-Only Codebase: {repository_url}")
    print(f"   Branch: {branch}")
    print(f"   Threshold: {threshold}")
    
    # Initialize shared store
    shared = {
        "request": {
            "repository_url": repository_url,
            "branch": branch,
            "github_token": github_token,
            "threshold": threshold,
            "scan_id": str(uuid.uuid4())
        },
        "temp_dir": tempfile.mkdtemp(prefix="codegates_"),
        "repository": {},
        "metadata": {},
        "config": {},
        "llm": {},
        "validation": {},
        "reports": {},
        "errors": [],
        "hard_gates": []  # Will be populated by the flow
    }
    
    # Create flow
    flow = create_static_only_flow()
    
    try:
        # Execute flow
        result = flow.run(shared)
        
        if result.success:
            print("\n============================================================")
            print("🎯 VALIDATION COMPLETE")
            print("============================================================")
            print(f"📊 Overall Score: {shared['validation'].get('overall_score', 0):.1f}%")
            
            # Check for NOT_APPLICABLE gates
            gate_results = shared["validation"].get("gate_results", [])
            not_applicable_gates = [g for g in gate_results if g.get("status") == "NOT_APPLICABLE"]
            
            print(f"📋 Total Gates: {len(gate_results)}")
            print(f"❌ Not Applicable Gates: {len(not_applicable_gates)}")
            
            if not_applicable_gates:
                print("\n🔍 Not Applicable Gates:")
                for gate in not_applicable_gates:
                    print(f"   - {gate['display_name']}: {gate['details'][0]}")
            
            # Check applicability summary
            applicability_summary = shared["validation"].get("applicability_summary", {})
            if applicability_summary:
                print(f"\n📊 Applicability Summary:")
                print(f"   Total Gates: {applicability_summary.get('total_gates', 0)}")
                print(f"   Applicable Gates: {applicability_summary.get('applicable_gates', 0)}")
                print(f"   Non-Applicable Gates: {applicability_summary.get('non_applicable_gates', 0)}")
                
                # Show codebase characteristics
                characteristics = applicability_summary.get('codebase_characteristics', {})
                print(f"   Codebase Type: {characteristics.get('primary_technology', 'unknown')}")
                print(f"   Is Frontend: {characteristics.get('is_frontend', False)}")
                print(f"   Is Backend: {characteristics.get('is_backend', False)}")
                print(f"   Is Backend Only: {characteristics.get('is_backend_only', False)}")
            
        else:
            print(f"❌ Validation failed: {result.error}")
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backend_only_applicability() 