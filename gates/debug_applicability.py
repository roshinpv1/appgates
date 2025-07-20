#!/usr/bin/env python3
"""
Debug script to test gate applicability logic
"""

import sys
import os
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gate_applicability import gate_applicability_analyzer

def debug_applicability():
    """Debug the applicability logic"""
    
    # Mock metadata for a backend-only Java codebase
    metadata = {
        "language_stats": {
            "Java": {"files": 1000, "lines": 50000},
            "XML": {"files": 100, "lines": 5000},
            "Properties": {"files": 50, "lines": 1000}
        },
        "config": {
            "config_files": {
                "build_files": ["pom.xml", "build.gradle"],
                "config_files": ["application.properties", "application.yml"]
            }
        }
    }
    
    print("🔍 Debugging Gate Applicability Logic")
    print("=" * 50)
    
    # Analyze codebase characteristics
    characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
    print(f"\n📊 Codebase Characteristics:")
    print(f"   Languages: {characteristics['languages']}")
    print(f"   Is Frontend: {characteristics['is_frontend']}")
    print(f"   Is Backend: {characteristics['is_backend']}")
    print(f"   Is API: {characteristics['is_api']}")
    print(f"   Is Backend Only: {characteristics['is_backend_only']}")
    print(f"   Is Frontend Only: {characteristics['is_frontend_only']}")
    print(f"   Is Fullstack: {characteristics['is_fullstack']}")
    print(f"   Primary Technology: {characteristics['primary_technology']}")
    
    # Test specific gates
    test_gates = ["UI_ERRORS", "UI_ERROR_TOOLS", "HTTP_CODES", "LOG_API_CALLS", "AUTOMATED_TESTS"]
    
    print(f"\n🔍 Gate Applicability Test:")
    for gate_name in test_gates:
        applicability = gate_applicability_analyzer._check_gate_applicability(gate_name, characteristics)
        print(f"\n   {gate_name}:")
        print(f"      Is Applicable: {applicability['is_applicable']}")
        print(f"      Reason: {applicability['reason']}")
        print(f"      Required Technologies: {applicability['required_technologies']}")
        print(f"      Has Required: {applicability['has_required']}")
        print(f"      Is Excluded: {applicability['is_excluded']}")

if __name__ == "__main__":
    debug_applicability() 