#!/usr/bin/env python3
"""
Test script to check UI gate applicability for backend codebase
"""

import sys
import os
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gate_applicability import gate_applicability_analyzer

def test_ui_applicability():
    """Test UI gate applicability for backend codebase"""
    
    # Mock metadata for a backend-only Java codebase (like Spring Boot)
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
    
    print("🔍 Testing UI Gate Applicability for Backend Codebase")
    print("=" * 60)
    
    # Analyze codebase characteristics
    characteristics = gate_applicability_analyzer.analyze_codebase_type(metadata)
    print(f"\n📊 Codebase Characteristics:")
    print(f"   Languages: {characteristics['languages']}")
    print(f"   Is Frontend: {characteristics['is_frontend']}")
    print(f"   Is Backend: {characteristics['is_backend']}")
    print(f"   Is API: {characteristics['is_api']}")
    print(f"   Is Backend Only: {characteristics['is_backend_only']}")
    print(f"   Primary Technology: {characteristics['primary_technology']}")
    
    # Test UI-specific gates
    ui_gates = ["UI_ERRORS", "UI_ERROR_TOOLS"]
    
    print(f"\n🔍 UI Gate Applicability Test:")
    for gate_name in ui_gates:
        applicability = gate_applicability_analyzer._check_gate_applicability(gate_name, characteristics)
        print(f"\n   {gate_name}:")
        print(f"      Is Applicable: {applicability['is_applicable']}")
        print(f"      Reason: {applicability['reason']}")
        if 'required_technologies' in applicability:
            print(f"      Required Technologies: {applicability['required_technologies']}")
            print(f"      Has Required: {applicability['has_required']}")
            print(f"      Is Excluded: {applicability['is_excluded']}")
        
        # Check if this should be marked as NOT_APPLICABLE
        if not applicability['is_applicable']:
            print(f"      ✅ Should be marked as NOT_APPLICABLE")
        else:
            print(f"      ❌ Should NOT be marked as NOT_APPLICABLE")

if __name__ == "__main__":
    test_ui_applicability() 