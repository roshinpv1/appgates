#!/usr/bin/env python3
"""
Test script to check applicability logic in validation process
"""

import sys
import os
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gate_applicability import gate_applicability_analyzer

def test_validation_applicability():
    """Test applicability logic as used in validation process"""
    
    # Mock metadata similar to what would be used in validation
    metadata = {
        "language_stats": {
            "Java": {"files": 2000, "lines": 100000},
            "XML": {"files": 200, "lines": 10000},
            "Properties": {"files": 100, "lines": 2000},
            "YAML": {"files": 50, "lines": 1000}
        },
        "config": {
            "config_files": {
                "build_files": ["pom.xml", "build.gradle"],
                "config_files": ["application.properties", "application.yml"]
            }
        }
    }
    
    print("🔍 Testing Applicability Logic in Validation Process")
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
    
    print(f"\n🔍 UI Gate Applicability Test (Validation Logic):")
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
    test_validation_applicability() 