#!/usr/bin/env python3
"""
Test script to check applicability logic with Spring Framework metadata
"""

import sys
import os
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gate_applicability import gate_applicability_analyzer

def test_spring_framework_applicability():
    """Test applicability logic with Spring Framework metadata"""
    
    # Mock metadata for Spring Framework (core framework, mostly backend)
    metadata = {
        "language_stats": {
            "Java": {"files": 4000, "lines": 200000},
            "XML": {"files": 300, "lines": 15000},
            "Gradle": {"files": 50, "lines": 2000},
            "YAML": {"files": 20, "lines": 500},
            "HTML": {"files": 10, "lines": 200},  # Minimal HTML for documentation
            "JSON": {"files": 5, "lines": 100}
        },
        "config": {
            "config_files": {
                "build_files": ["build.gradle", "gradle.properties"],
                "config_files": []
            }
        }
    }
    
    print("🔍 Testing Applicability Logic with Spring Framework")
    print("=" * 60)
    
    # Test the exact same logic used in validation
    from utils.gate_applicability import gate_applicability_analyzer
    characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
    
    print(f"\n📊 Codebase Characteristics:")
    print(f"   Languages: {characteristics['languages']}")
    print(f"   Is Frontend: {characteristics['is_frontend']}")
    print(f"   Is Backend: {characteristics['is_backend']}")
    print(f"   Is API: {characteristics['is_api']}")
    print(f"   Is Backend Only: {characteristics['is_backend_only']}")
    print(f"   Primary Technology: {characteristics['primary_technology']}")
    
    # Test UI gates specifically
    ui_gates = ["UI_ERRORS", "UI_ERROR_TOOLS"]
    
    print(f"\n🔍 UI Gate Applicability Test:")
    for gate_name in ui_gates:
        applicability = gate_applicability_analyzer._check_gate_applicability(gate_name, characteristics)
        print(f"\n   {gate_name}:")
        print(f"      Is Applicable: {applicability['is_applicable']}")
        print(f"      Reason: {applicability['reason']}")
        
        # Check if this should be marked as NOT_APPLICABLE
        is_not_applicable = not applicability['is_applicable']
        print(f"      Is Not Applicable: {is_not_applicable}")
        
        if is_not_applicable:
            print(f"      ✅ Should be marked as NOT_APPLICABLE in validation")
        else:
            print(f"      ❌ Should NOT be marked as NOT_APPLICABLE in validation")

if __name__ == "__main__":
    test_spring_framework_applicability() 