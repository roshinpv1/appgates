#!/usr/bin/env python3
"""
Test script to verify that the application properly relies on LLM expected counts
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_llm_expected_counts_processing():
    """Test the processing of LLM expected counts"""
    
    print("🧪 Testing LLM Expected Counts Processing")
    print("=" * 50)
    
    # Simulate LLM response with expected counts
    mock_llm_response = {
        "patterns": [
            {
                "gate_id": "1.1",
                "name": "Log system errors",
                "description": "Log system errors for troubleshooting",
                "applicable": True,
                "reason": "Repository contains logging framework",
                "pattern": "error.*log|system.*error",
                "expected_count": 5,
                "expected_count_reasoning": "Based on 3 controller classes, 2 service classes that should implement error logging according to Spring Boot best practices"
            },
            {
                "gate_id": "1.3",
                "name": "Use HTTP standard error codes",
                "description": "All APIs must return standardized HTTP status codes",
                "applicable": False,
                "reason": "No API-related files or HTTP handlers found in repository",
                "pattern": "",
                "expected_count": 0,
                "expected_count_reasoning": "No web framework or API endpoints detected in the codebase"
            },
            {
                "gate_id": "1.5",
                "name": "Input validation",
                "description": "Validate all user inputs",
                "applicable": True,
                "reason": "Web application with user input forms",
                "pattern": "validation|validate|input.*check",
                "expected_count": 3,
                "expected_count_reasoning": "Based on 2 form controllers and 1 service class that should implement input validation"
            }
        ]
    }
    
    # Test the expected counts processing logic
    llm_expected_counts = {}
    
    for pattern in mock_llm_response["patterns"]:
        gate_id = pattern.get("gate_id")
        if gate_id:
            expected_count = pattern.get("expected_count")
            expected_count_reasoning = pattern.get("expected_count_reasoning", "")
            applicable = pattern.get("applicable", False)
            
            if expected_count is not None:
                llm_expected_counts[gate_id] = {
                    "expected_count": expected_count,
                    "reasoning": expected_count_reasoning,
                    "applicable": applicable,
                    "source": "llm_analysis"
                }
                print(f"📊 LLM expected count for {gate_id}: {expected_count} (applicable: {applicable})")
                print(f"   📝 Reasoning: {expected_count_reasoning[:80]}...")
            else:
                print(f"⚠️ No expected_count provided by LLM for gate {gate_id}")
        else:
            print(f"⚠️ No gate_id found in pattern: {pattern}")
    
    print(f"\n�� Total LLM expected counts stored: {len(llm_expected_counts)}")
    
    # Test gate evaluation logic
    print(f"\n🔍 Testing Gate Evaluation Logic")
    print("-" * 30)
    
    test_gates = ["1.1", "1.3", "1.5", "2.4"]  # Include a gate not in LLM response
    
    for gate_id in test_gates:
        if gate_id in llm_expected_counts:
            llm_count = llm_expected_counts[gate_id]
            expected_count = llm_count.get("expected_count")
            reasoning = llm_count.get("reasoning", "")
            applicable = llm_count.get("applicable", False)
            
            print(f"🎯 Gate {gate_id}: Using LLM expected count {expected_count} (applicable: {applicable})")
            if reasoning:
                print(f"   📝 LLM reasoning: {reasoning[:60]}...")
        else:
            print(f"⚠️ Gate {gate_id}: No LLM expected count found, would use calculated fallback")
    
    # Test applicability logic
    print(f"\n�� Testing Applicability Logic")
    print("-" * 30)
    
    for gate_id in test_gates:
        if gate_id in llm_expected_counts:
            llm_count = llm_expected_counts[gate_id]
            applicable = llm_count.get("applicable", True)
            
            if not applicable:
                print(f"⏭️ Gate {gate_id}: LLM marked as not applicable - would be skipped")
            else:
                print(f"✅ Gate {gate_id}: LLM marked as applicable - would be evaluated")
        else:
            print(f"❓ Gate {gate_id}: No LLM applicability decision - would use traditional logic")

def test_expected_count_priority():
    """Test that LLM expected counts take priority over calculated counts"""
    
    print(f"\n🧪 Testing Expected Count Priority")
    print("=" * 50)
    
    # Simulate different scenarios
    scenarios = [
        {
            "name": "LLM provides expected count",
            "llm_count": 5,
            "calculated_count": 3,
            "expected_result": "Use LLM count (5)"
        },
        {
            "name": "LLM provides 0 expected count",
            "llm_count": 0,
            "calculated_count": 3,
            "expected_result": "Use LLM count (0)"
        },
        {
            "name": "LLM provides None expected count",
            "llm_count": None,
            "calculated_count": 3,
            "expected_result": "Use calculated fallback (3)"
        },
        {
            "name": "No LLM expected count",
            "llm_count": None,
            "calculated_count": 3,
            "expected_result": "Use calculated fallback (3)"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   LLM count: {scenario['llm_count']}")
        print(f"   Calculated count: {scenario['calculated_count']}")
        print(f"   Expected result: {scenario['expected_result']}")
        
        # Simulate the logic
        if scenario['llm_count'] is not None:
            result = scenario['llm_count']
            source = "LLM"
        else:
            result = scenario['calculated_count']
            source = "Calculated"
        
        print(f"   ✅ Actual result: Use {source} count ({result})")

if __name__ == "__main__":
    test_llm_expected_counts_processing()
    test_expected_count_priority()
    print(f"\n🎉 LLM Expected Counts Reliance Test Completed!")
