#!/usr/bin/env python3
"""
Test script to demonstrate gate applicability functionality
"""

import sys
import os
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gate_applicability import gate_applicability_analyzer


def test_applicability_analysis():
    """Test gate applicability analysis with different codebase types"""
    
    print("🔍 Testing Gate Applicability Analysis")
    print("=" * 50)
    
    # Test 1: Backend-only Java codebase
    print("\n📋 Test 1: Backend-only Java codebase")
    print("-" * 40)
    
    backend_java_metadata = {
        "language_stats": {
            "Java": {"files": 1000, "lines": 50000},
            "XML": {"files": 50, "lines": 2000},
            "YAML": {"files": 20, "lines": 800}
        },
        "config": {
            "config_files": {
                "api": ["src/main/java/com/example/controller/UserController.java"],
                "rest": ["src/main/java/com/example/controller/UserController.java"]
            }
        }
    }
    
    applicability_summary = gate_applicability_analyzer.get_applicability_summary(backend_java_metadata)
    
    print(f"Codebase Type: {applicability_summary['codebase_characteristics']['primary_technology']}")
    print(f"Languages: {', '.join(applicability_summary['codebase_characteristics']['languages'])}")
    print(f"Applicable Gates: {applicability_summary['applicable_gates']}/{applicability_summary['total_gates']}")
    print(f"Non-Applicable Gates: {applicability_summary['non_applicable_gates']}")
    
    if applicability_summary['non_applicable_details']:
        print("\nExcluded Gates:")
        for gate in applicability_summary['non_applicable_details']:
            print(f"  - {gate['name']} ({gate['category']}): {gate['reason']}")
    
    # Test 2: Frontend-only JavaScript codebase
    print("\n📋 Test 2: Frontend-only JavaScript codebase")
    print("-" * 40)
    
    frontend_js_metadata = {
        "language_stats": {
            "JavaScript": {"files": 500, "lines": 25000},
            "TypeScript": {"files": 200, "lines": 12000},
            "HTML": {"files": 50, "lines": 2000},
            "CSS": {"files": 100, "lines": 5000}
        },
        "config": {
            "config_files": {}
        }
    }
    
    applicability_summary = gate_applicability_analyzer.get_applicability_summary(frontend_js_metadata)
    
    print(f"Codebase Type: {applicability_summary['codebase_characteristics']['primary_technology']}")
    print(f"Languages: {', '.join(applicability_summary['codebase_characteristics']['languages'])}")
    print(f"Applicable Gates: {applicability_summary['applicable_gates']}/{applicability_summary['total_gates']}")
    print(f"Non-Applicable Gates: {applicability_summary['non_applicable_gates']}")
    
    if applicability_summary['non_applicable_details']:
        print("\nExcluded Gates:")
        for gate in applicability_summary['non_applicable_details']:
            print(f"  - {gate['name']} ({gate['category']}): {gate['reason']}")
    
    # Test 3: Fullstack codebase
    print("\n📋 Test 3: Fullstack codebase")
    print("-" * 40)
    
    fullstack_metadata = {
        "language_stats": {
            "Java": {"files": 800, "lines": 40000},
            "JavaScript": {"files": 300, "lines": 15000},
            "TypeScript": {"files": 150, "lines": 8000},
            "HTML": {"files": 50, "lines": 2000},
            "CSS": {"files": 100, "lines": 5000}
        },
        "config": {
            "config_files": {
                "api": ["src/main/java/com/example/controller/UserController.java"],
                "rest": ["src/main/java/com/example/controller/UserController.java"]
            }
        }
    }
    
    applicability_summary = gate_applicability_analyzer.get_applicability_summary(fullstack_metadata)
    
    print(f"Codebase Type: {applicability_summary['codebase_characteristics']['primary_technology']}")
    print(f"Languages: {', '.join(applicability_summary['codebase_characteristics']['languages'])}")
    print(f"Applicable Gates: {applicability_summary['applicable_gates']}/{applicability_summary['total_gates']}")
    print(f"Non-Applicable Gates: {applicability_summary['non_applicable_gates']}")
    
    if applicability_summary['non_applicable_details']:
        print("\nExcluded Gates:")
        for gate in applicability_summary['non_applicable_details']:
            print(f"  - {gate['name']} ({gate['category']}): {gate['reason']}")
    
    print("\n✅ Applicability analysis tests completed!")


if __name__ == "__main__":
    test_applicability_analysis() 