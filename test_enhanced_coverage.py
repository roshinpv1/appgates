#!/usr/bin/env python3
"""
Test script to demonstrate enhanced coverage calculation with maximum files expected
"""

import sys
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_enhanced_coverage_calculation():
    """Test the enhanced coverage calculation with maximum files expected"""
    print("🧪 Testing Enhanced Coverage Calculation")
    print("=" * 60)
    
    try:
        from nodes import ValidateGatesNode
        
        # Create a mock gate with enhanced expected coverage data
        mock_gate = {
            "name": "STRUCTURED_LOGS",
            "display_name": "Structured Logging",
            "description": "Implement structured logging throughout the application",
            "priority": "high",
            "expected_coverage": {
                "percentage": 10,
                "reasoning": "Standard expectation for logging implementation",
                "confidence": "medium",
                "max_files_expected": 160  # LLM-determined maximum files
            },
            "total_files": 540,
            "relevant_files": 155
        }
        
        # Mock matches (6 files with logging patterns)
        mock_matches = [
            {"file": "src/main/java/com/example/Controller.java", "pattern": "log.info", "line": 15, "match": "log.info(\"Request received\")"},
            {"file": "src/main/java/com/example/Service.java", "pattern": "log.error", "line": 42, "match": "log.error(\"Service error occurred\")"},
            {"file": "src/main/java/com/example/Repository.java", "pattern": "log.debug", "line": 28, "match": "log.debug(\"Database query executed\")"},
            {"file": "src/main/java/com/example/Config.java", "pattern": "log.warn", "line": 33, "match": "log.warn(\"Configuration warning\")"},
            {"file": "src/main/java/com/example/Utils.java", "pattern": "log.trace", "line": 19, "match": "log.trace(\"Utility function called\")"},
            {"file": "src/main/java/com/example/Helper.java", "pattern": "log.info", "line": 55, "match": "log.info(\"Helper method completed\")"}
        ]
        
        # Mock metadata
        mock_metadata = {
            "total_files": 540,
            "language_stats": {
                "Java": {"files": 120, "percentage": 80.0},
                "XML": {"files": 15, "percentage": 10.0},
                "Properties": {"files": 10, "percentage": 6.7},
                "YAML": {"files": 5, "percentage": 3.3}
            }
        }
        
        # Create validator instance
        validator = ValidateGatesNode()
        
        print("📊 Coverage Analysis Comparison")
        print("-" * 40)
        
        # Calculate score using enhanced method
        enhanced_score = validator._calculate_gate_score(mock_gate, mock_matches, mock_metadata)
        
        # Calculate traditional coverage
        files_with_matches = len(set(m['file'] for m in mock_matches))
        traditional_coverage = (files_with_matches / mock_gate["relevant_files"]) * 100
        enhanced_coverage = (files_with_matches / mock_gate["expected_coverage"]["max_files_expected"]) * 100
        
        print(f"Gate: {mock_gate['display_name']}")
        print(f"Files with matches: {files_with_matches}")
        print(f"Total files in repo: {mock_metadata['total_files']}")
        print(f"Relevant files (filtered): {mock_gate['relevant_files']}")
        print(f"Maximum files expected (LLM): {mock_gate['expected_coverage']['max_files_expected']}")
        print()
        
        print("📈 Coverage Calculations:")
        print(f"Traditional Coverage: {traditional_coverage:.1f}% ({files_with_matches}/{mock_gate['relevant_files']} relevant files)")
        print(f"Enhanced Coverage: {enhanced_coverage:.1f}% ({files_with_matches}/{mock_gate['expected_coverage']['max_files_expected']} expected files)")
        print(f"Enhanced Score: {enhanced_score:.1f}%")
        print()
        
        # Generate details and recommendations
        details = validator._generate_gate_details(mock_gate, mock_matches)
        recommendations = validator._generate_gate_recommendations(mock_gate, mock_matches, enhanced_score)
        
        print("📋 Analysis Details:")
        for detail in details:
            print(f"  {detail}")
        print()
        
        print("💡 Recommendations:")
        for rec in recommendations:
            print(f"  {rec}")
        print()
        
        # Test different scenarios
        print("🔄 Testing Different Scenarios")
        print("-" * 40)
        
        scenarios = [
            {
                "name": "High Coverage (80%)",
                "max_files_expected": 160,
                "files_with_matches": 128,
                "expected_percentage": 80
            },
            {
                "name": "Medium Coverage (40%)",
                "max_files_expected": 160,
                "files_with_matches": 64,
                "expected_percentage": 40
            },
            {
                "name": "Low Coverage (15%)",
                "max_files_expected": 160,
                "files_with_matches": 24,
                "expected_percentage": 15
            },
            {
                "name": "Infrastructure Pattern (100%)",
                "max_files_expected": 160,
                "files_with_matches": 120,
                "expected_percentage": 100
            }
        ]
        
        for scenario in scenarios:
            test_gate = mock_gate.copy()
            test_gate["expected_coverage"]["max_files_expected"] = scenario["max_files_expected"]
            test_gate["expected_coverage"]["percentage"] = scenario["expected_percentage"]
            
            # Create mock matches for this scenario
            test_matches = [{"file": f"file_{i}.java", "pattern": "log.info", "line": 1, "match": "log.info(\"Test message\")"} 
                           for i in range(scenario["files_with_matches"])]
            
            test_score = validator._calculate_gate_score(test_gate, test_matches, mock_metadata)
            test_coverage = (scenario["files_with_matches"] / scenario["max_files_expected"]) * 100
            
            print(f"{scenario['name']}:")
            print(f"  Coverage: {test_coverage:.1f}% ({scenario['files_with_matches']}/{scenario['max_files_expected']} files)")
            print(f"  Score: {test_score:.1f}%")
            print()
        
        print("✅ Enhanced coverage calculation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_coverage_calculation() 