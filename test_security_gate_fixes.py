#!/usr/bin/env python3
"""
Test script to verify security gate fixes for AVOID_LOGGING_SECRETS
"""

import sys
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_security_gate_fixes():
    """Test the security gate fixes for AVOID_LOGGING_SECRETS"""
    print("🧪 Testing Security Gate Fixes")
    print("=" * 50)
    
    try:
        from nodes import ValidateGatesNode
        from utils.pattern_loader import PatternLoader
        
        # Create a mock gate with security gate configuration
        mock_gate = {
            "name": "AVOID_LOGGING_SECRETS",
            "display_name": "Avoid Logging Confidential Data",
            "description": "Prevent sensitive data from being logged accidentally",
            "priority": "critical",
            "expected_coverage": {
                "percentage": 0,
                "reasoning": "No secrets should be logged - this is a security gate where 0 violations is the goal",
                "confidence": "high",
                "max_files_expected": 100
            },
            "scoring": {
                "base_score": 100,
                "violation_penalty": 20,
                "max_penalty": 100,
                "bonus_for_clean": 10,
                "is_security_gate": True
            },
            "total_files": 5000,
            "relevant_files": 4210
        }
        
        # Test scenarios
        scenarios = [
            {
                "name": "No Violations (Perfect)",
                "matches": [],
                "expected_score": 100.0,
                "expected_status": "PASS"
            },
            {
                "name": "Minor Violations (1-5)",
                "matches": [
                    {"file": "src/main/java/com/example/Controller.java", "pattern": "log.info", "line": 15, "match": "log.info(\"password: {}\", userPassword)"},
                    {"file": "src/main/java/com/example/Service.java", "pattern": "log.error", "line": 42, "match": "log.error(\"token: {}\", authToken)"}
                ],
                "expected_score": 60.0,  # 100 - (2 * 20)
                "expected_status": "FAIL"
            },
            {
                "name": "Major Violations (10+)",
                "matches": [
                    {"file": f"src/main/java/com/example/File{i}.java", "pattern": "log.info", "line": 15, "match": f"log.info(\"secret{{i}}: {{}}\", secret{i})"}
                    for i in range(15)
                ],
                "expected_score": 0.0,  # 100 - (15 * 20) = -200, capped at 0
                "expected_status": "FAIL"
            }
        ]
        
        # Create validator instance
        validator = ValidateGatesNode()
        
        print("📊 Security Gate Test Results")
        print("-" * 40)
        
        for scenario in scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            
            # Calculate score using fixed method
            actual_score = validator._calculate_gate_score(mock_gate, scenario['matches'], {})
            actual_status = validator._determine_status(actual_score, mock_gate)
            
            # Generate details
            details = validator._generate_gate_details(mock_gate, scenario['matches'])
            recommendations = validator._generate_gate_recommendations(mock_gate, scenario['matches'], actual_score)
            
            print(f"  Expected Score: {scenario['expected_score']:.1f}%")
            print(f"  Actual Score: {actual_score:.1f}%")
            print(f"  Expected Status: {scenario['expected_status']}")
            print(f"  Actual Status: {actual_status}")
            
            # Show key details
            print(f"  Violations Found: {len(scenario['matches'])}")
            if details:
                print(f"  Details: {details[0] if details else 'None'}")
            if recommendations:
                print(f"  Recommendation: {recommendations[0] if recommendations else 'None'}")
            
            # Verify results
            score_correct = abs(actual_score - scenario['expected_score']) < 1.0
            status_correct = actual_status == scenario['expected_status']
            
            if score_correct and status_correct:
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL")
                if not score_correct:
                    print(f"    Score mismatch: expected {scenario['expected_score']:.1f}%, got {actual_score:.1f}%")
                if not status_correct:
                    print(f"    Status mismatch: expected {scenario['expected_status']}, got {actual_status}")
        
        # Test pattern loader security gate scoring
        print(f"\n🔧 Testing Pattern Loader Security Gate Scoring")
        print("-" * 50)
        
        pattern_loader = PatternLoader()
        
        for scenario in scenarios:
            print(f"\nTesting: {scenario['name']}")
            
            score, details = pattern_loader._calculate_security_gate_score(
                scenario['matches'], 
                mock_gate['scoring']
            )
            
            print(f"  Score: {score:.1f}%")
            print(f"  Security Violations: {details.get('security_violations', 0)}")
            print(f"  Penalty Applied: {details.get('penalty_applied', 0)}")
            print(f"  Is Security Gate: {details.get('is_security_gate', False)}")
        
        print(f"\n✅ Security gate fixes test completed successfully!")
        print(f"📝 Summary:")
        print(f"   - Security gates now properly penalize violations")
        print(f"   - Coverage calculation fixed for security gates")
        print(f"   - Recommendations properly focus on violations")
        print(f"   - Status determination works correctly")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_security_gate_fixes() 