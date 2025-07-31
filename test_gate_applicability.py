#!/usr/bin/env python3
"""
Test script to verify gate applicability logic
"""

import sys
import os
sys.path.append('gates')

from utils.gate_applicability import gate_applicability_analyzer

def test_gate_applicability():
    """Test gate applicability logic"""
    
    # Test case 1: Backend-only codebase (should NOT have UI_ERRORS applicable)
    backend_metadata = {
        "language_stats": {
            "Java": {"files": 50, "lines": 5000},
            "Python": {"files": 30, "lines": 3000},
            "HTML": {"files": 2, "lines": 100}  # Just documentation
        }
    }
    
    print("=== Test Case 1: Backend-only codebase ===")
    characteristics = gate_applicability_analyzer.analyze_codebase_type(backend_metadata)
    print(f"Characteristics: {characteristics}")
    
    ui_errors_applicability = gate_applicability_analyzer._check_gate_applicability("UI_ERRORS", characteristics)
    print(f"UI_ERRORS applicability: {ui_errors_applicability}")
    
    http_codes_applicability = gate_applicability_analyzer._check_gate_applicability("HTTP_CODES", characteristics)
    print(f"HTTP_CODES applicability: {http_codes_applicability}")
    
    # Test case 2: Frontend-heavy codebase (should have UI_ERRORS applicable)
    frontend_metadata = {
        "language_stats": {
            "JavaScript": {"files": 40, "lines": 4000},
            "TypeScript": {"files": 30, "lines": 3000},
            "HTML": {"files": 20, "lines": 2000},
            "CSS": {"files": 15, "lines": 1500},
            "Java": {"files": 5, "lines": 500}  # Minimal backend
        }
    }
    
    print("\n=== Test Case 2: Frontend-heavy codebase ===")
    characteristics = gate_applicability_analyzer.analyze_codebase_type(frontend_metadata)
    print(f"Characteristics: {characteristics}")
    
    ui_errors_applicability = gate_applicability_analyzer._check_gate_applicability("UI_ERRORS", characteristics)
    print(f"UI_ERRORS applicability: {ui_errors_applicability}")
    
    http_codes_applicability = gate_applicability_analyzer._check_gate_applicability("HTTP_CODES", characteristics)
    print(f"HTTP_CODES applicability: {http_codes_applicability}")
    
    # Test case 3: Documentation-heavy codebase (should NOT have UI_ERRORS applicable)
    docs_metadata = {
        "language_stats": {
            "HTML": {"files": 100, "lines": 10000},  # Documentation
            "CSS": {"files": 10, "lines": 1000},     # Documentation styling
            "Java": {"files": 5, "lines": 500}        # Minimal backend
        }
    }
    
    print("\n=== Test Case 3: Documentation-heavy codebase ===")
    characteristics = gate_applicability_analyzer.analyze_codebase_type(docs_metadata)
    print(f"Characteristics: {characteristics}")
    
    ui_errors_applicability = gate_applicability_analyzer._check_gate_applicability("UI_ERRORS", characteristics)
    print(f"UI_ERRORS applicability: {ui_errors_applicability}")
    
    # Test case 4: Pure frontend codebase (should have UI_ERRORS applicable, but NOT HTTP_CODES)
    pure_frontend_metadata = {
        "language_stats": {
            "JavaScript": {"files": 50, "lines": 5000},
            "TypeScript": {"files": 30, "lines": 3000},
            "HTML": {"files": 20, "lines": 2000},
            "CSS": {"files": 15, "lines": 1500}
        }
    }
    
    print("\n=== Test Case 4: Pure frontend codebase ===")
    characteristics = gate_applicability_analyzer.analyze_codebase_type(pure_frontend_metadata)
    print(f"Characteristics: {characteristics}")
    
    ui_errors_applicability = gate_applicability_analyzer._check_gate_applicability("UI_ERRORS", characteristics)
    print(f"UI_ERRORS applicability: {ui_errors_applicability}")
    
    http_codes_applicability = gate_applicability_analyzer._check_gate_applicability("HTTP_CODES", characteristics)
    print(f"HTTP_CODES applicability: {http_codes_applicability}")
    
    # Test case 5: API-heavy backend codebase (should have HTTP_CODES applicable)
    api_backend_metadata = {
        "language_stats": {
            "Java": {"files": 60, "lines": 6000},
            "Python": {"files": 40, "lines": 4000},
            "YAML": {"files": 10, "lines": 1000},  # API config files
            "JSON": {"files": 5, "lines": 500}      # API config files
        },
        "config": {
            "config_files": {
                "api_files": ["swagger.yaml", "openapi.json", "api-docs.yml"]
            }
        }
    }
    
    print("\n=== Test Case 5: API-heavy backend codebase ===")
    characteristics = gate_applicability_analyzer.analyze_codebase_type(api_backend_metadata)
    print(f"Characteristics: {characteristics}")
    
    http_codes_applicability = gate_applicability_analyzer._check_gate_applicability("HTTP_CODES", characteristics)
    print(f"HTTP_CODES applicability: {http_codes_applicability}")
    
    ui_errors_applicability = gate_applicability_analyzer._check_gate_applicability("UI_ERRORS", characteristics)
    print(f"UI_ERRORS applicability: {ui_errors_applicability}")

if __name__ == "__main__":
    test_gate_applicability() 