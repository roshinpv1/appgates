#!/usr/bin/env python3
"""
Test script for Weighted Pattern System
Validates the externalized JSON patterns and weighted scoring system
"""

import sys
import json
import tempfile
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from gates.utils.pattern_loader import PatternLoader, get_pattern_loader
from gates.utils.hard_gates import HARD_GATES

def test_pattern_loader():
    """Test the pattern loader functionality"""
    print("🧪 Testing Weighted Pattern Loader")
    print("=" * 50)
    
    # Test pattern loader initialization
    loader = get_pattern_loader()
    
    # Test pattern statistics
    stats = loader.get_pattern_statistics()
    print(f"📊 Pattern Library Statistics:")
    print(f"   Total Gates: {stats['total_gates']}")
    print(f"   Total Patterns: {stats['total_patterns']}")
    print(f"   Total Weight: {stats['total_weight']:.1f}")
    print(f"   Supported Technologies: {', '.join(stats['supported_technologies'])}")
    print()
    
    # Test gate weights
    print("🏋️ Gate Weights:")
    for gate in HARD_GATES:
        gate_name = gate["name"]
        weight = loader.get_gate_weight(gate_name)
        print(f"   {gate_name}: {weight:.1f}")
    print()
    
    # Test pattern retrieval for different technologies
    test_cases = [
        (["Java"], "Java Project"),
        (["Python"], "Python Project"),
        (["JavaScript"], "JavaScript Project"),
        (["Java", "JavaScript"], "Full-Stack Project"),
        (["Python", "JavaScript"], "Python + JS Project")
    ]
    
    for technologies, description in test_cases:
        print(f"🔧 Testing {description}:")
        for gate in HARD_GATES[:3]:  # Test first 3 gates
            gate_name = gate["name"]
            patterns = loader.get_gate_patterns(gate_name, technologies)
            pattern_strings = loader.get_pattern_strings(gate_name, technologies)
            
            print(f"   {gate_name}: {len(patterns)} weighted patterns, {len(pattern_strings)} pattern strings")
            
            # Show some pattern details
            if patterns:
                for pattern in patterns[:2]:  # Show first 2 patterns
                    print(f"     - {pattern['pattern']} (weight: {pattern['weight']})")
        print()

def test_weighted_scoring():
    """Test the weighted scoring system"""
    print("📊 Testing Weighted Scoring System")
    print("=" * 50)
    
    loader = get_pattern_loader()
    
    # Create mock metadata
    metadata = {
        "language_stats": {
            "Java": {"files": 50, "lines": 5000},
            "Python": {"files": 30, "lines": 3000},
            "JavaScript": {"files": 20, "lines": 2000}
        },
        "total_files": 100,
        "total_lines": 10000
    }
    
    # Test scoring for different gates
    test_gates = ["STRUCTURED_LOGS", "AVOID_LOGGING_SECRETS", "AUTOMATED_TESTS"]
    
    for gate_name in test_gates:
        print(f"🎯 Testing {gate_name}:")
        
        # Get gate info
        gate_info = loader.get_gate_info(gate_name)
        if gate_info:
            weight = gate_info.get("weight", 0.0)
            expected_coverage = gate_info.get("expected_coverage", {})
            scoring_config = gate_info.get("scoring", {})
            
            print(f"   Weight: {weight:.1f}")
            print(f"   Expected Coverage: {expected_coverage.get('percentage', 0)}%")
            print(f"   Scoring Config: {scoring_config}")
            
            # Test with different match scenarios
            test_scenarios = [
                ([], "No matches"),
                ([{"file": "test1.java", "pattern": "logger.info", "match": "logger.info", "line": 1}], "One match"),
                ([{"file": "test1.java", "pattern": "logger.info", "match": "logger.info", "line": 1},
                  {"file": "test2.java", "pattern": "@Slf4j", "match": "@Slf4j", "line": 5}], "Multiple matches")
            ]
            
            for matches, scenario in test_scenarios:
                score, details = loader.calculate_weighted_score(gate_name, matches, metadata)
                print(f"     {scenario}: {score:.1f}%")
                if details:
                    print(f"       Details: {details}")
        print()

def test_overall_scoring():
    """Test overall weighted scoring"""
    print("📈 Testing Overall Weighted Scoring")
    print("=" * 50)
    
    # Create mock gate results
    mock_results = [
        {
            "gate": "STRUCTURED_LOGS",
            "score": 85.0,
            "status": "PASS"
        },
        {
            "gate": "AVOID_LOGGING_SECRETS",
            "score": 95.0,
            "status": "PASS"
        },
        {
            "gate": "AUTOMATED_TESTS",
            "score": 70.0,
            "status": "WARNING"
        },
        {
            "gate": "ERROR_LOGS",
            "score": 60.0,
            "status": "FAIL"
        }
    ]
    
    loader = get_pattern_loader()
    overall_score, scoring_summary = loader.calculate_overall_weighted_score(mock_results)
    
    print(f"Overall Weighted Score: {overall_score:.1f}%")
    print(f"Total Weight: {scoring_summary.get('total_weight', 0):.1f}")
    print(f"Applicable Gates: {scoring_summary.get('applicable_gates', 0)}")
    
    print("\nGate Scores:")
    for gate_name, gate_data in scoring_summary.get("gate_scores", {}).items():
        print(f"   {gate_name}: {gate_data['score']:.1f}% (weight: {gate_data['weight']:.1f}, weighted: {gate_data['weighted_score']:.1f})")

def test_json_pattern_file():
    """Test the JSON pattern file structure"""
    print("📄 Testing JSON Pattern File")
    print("=" * 50)
    
    # Load the JSON file directly
    pattern_file = Path("gates/patterns/pattern_library.json")
    
    if pattern_file.exists():
        with open(pattern_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ JSON file loaded successfully")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Total Gates: {data['metadata']['total_gates']}")
        print(f"   Total Patterns: {data['metadata']['total_patterns']}")
        
        # Test gate structure
        gates = data.get("gates", {})
        print(f"\n🏗️ Gate Structure Test:")
        for gate_name, gate_data in gates.items():
            required_fields = ["display_name", "description", "category", "priority", "weight", "patterns", "scoring"]
            missing_fields = [field for field in required_fields if field not in gate_data]
            
            if missing_fields:
                print(f"   ❌ {gate_name}: Missing fields: {missing_fields}")
            else:
                print(f"   ✅ {gate_name}: All required fields present")
                
                # Test pattern structure
                patterns = gate_data.get("patterns", {})
                for tech, tech_patterns in patterns.items():
                    if tech_patterns:
                        first_pattern = tech_patterns[0]
                        if isinstance(first_pattern, dict) and "pattern" in first_pattern and "weight" in first_pattern:
                            print(f"     ✅ {tech}: Proper pattern structure")
                        else:
                            print(f"     ❌ {tech}: Invalid pattern structure")
    else:
        print(f"❌ JSON file not found: {pattern_file}")

def main():
    """Run all tests"""
    print("🚀 Weighted Pattern System Test Suite")
    print("=" * 60)
    
    try:
        test_json_pattern_file()
        print()
        
        test_pattern_loader()
        print()
        
        test_weighted_scoring()
        print()
        
        test_overall_scoring()
        print()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 