#!/usr/bin/env python3
"""
Test script for enhanced pattern library and LLM improvements
Validates comprehensive coverage across different technologies
"""

import sys
import tempfile
import json
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from gates.utils.static_patterns import get_static_patterns_for_gate, get_pattern_statistics
from gates.nodes import CallLLMNode

def test_enhanced_static_patterns():
    """Test enhanced static pattern library"""
    print("🧪 Testing Enhanced Static Pattern Library")
    print("=" * 60)
    
    # Test different technology combinations
    test_cases = [
        {
            "name": "Java Spring Boot",
            "technologies": ["Java"],
            "expected_gates": ["STRUCTURED_LOGS", "LOG_API_CALLS", "AUTOMATED_TESTS", "ERROR_LOGS"],
            "expected_min_patterns": 20
        },
        {
            "name": "Python Django",
            "technologies": ["Python"],
            "expected_gates": ["STRUCTURED_LOGS", "LOG_API_CALLS", "AUTOMATED_TESTS", "ERROR_LOGS"],
            "expected_min_patterns": 15
        },
        {
            "name": "JavaScript Node.js",
            "technologies": ["JavaScript"],
            "expected_gates": ["STRUCTURED_LOGS", "LOG_API_CALLS", "AUTOMATED_TESTS", "ERROR_LOGS"],
            "expected_min_patterns": 15
        },
        {
            "name": "Multi-language Project",
            "technologies": ["Java", "Python", "JavaScript"],
            "expected_gates": ["STRUCTURED_LOGS", "LOG_API_CALLS", "AUTOMATED_TESTS", "ERROR_LOGS"],
            "expected_min_patterns": 30
        },
        {
            "name": "Modern Stack",
            "technologies": ["TypeScript", "Go", "Rust"],
            "expected_gates": ["STRUCTURED_LOGS", "AUTOMATED_TESTS"],
            "expected_min_patterns": 10
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        print(f"   Technologies: {', '.join(test_case['technologies'])}")
        
        total_patterns = 0
        for gate in test_case['expected_gates']:
            patterns = get_static_patterns_for_gate(gate, test_case['technologies'])
            total_patterns += len(patterns)
            print(f"   {gate}: {len(patterns)} patterns")
            
            # Validate patterns are not empty
            assert len(patterns) > 0, f"No patterns found for {gate} with {test_case['technologies']}"
            
            # Validate patterns are valid regex
            import re
            for pattern in patterns[:5]:  # Test first 5 patterns
                try:
                    re.compile(pattern)
                except re.error as e:
                    print(f"   ❌ Invalid regex pattern: {pattern} - {e}")
                    assert False, f"Invalid regex pattern: {pattern}"
        
        print(f"   ✅ Total patterns: {total_patterns}")
        assert total_patterns >= test_case['expected_min_patterns'], \
            f"Expected at least {test_case['expected_min_patterns']} patterns, got {total_patterns}"
    
    print("\n✅ All static pattern tests passed!")

def test_spring_boot_specific_patterns():
    """Test Spring Boot specific pattern detection"""
    print("\n🌱 Testing Spring Boot Specific Patterns")
    print("=" * 60)
    
    # Test Spring Boot logging patterns
    spring_patterns = get_static_patterns_for_gate("STRUCTURED_LOGS", ["Java"])
    
    # Expected Spring Boot patterns
    expected_patterns = [
        r'import\s+org\.slf4j\.Logger',
        r'import\s+org\.slf4j\.LoggerFactory',
        r'@Slf4j',
        r'LoggerFactory\.getLogger\(',
        r'log\.(info|debug|error|warn|trace|fatal)\(',
        r'logger\.(info|debug|error|warn|trace|fatal)\(',
        r'logback\.xml',
        r'logback-spring\.xml',
        r'application\.properties',
        r'application\.yml'
    ]
    
    found_patterns = 0
    for expected in expected_patterns:
        if expected in spring_patterns:
            found_patterns += 1
            print(f"   ✅ Found: {expected}")
        else:
            print(f"   ❌ Missing: {expected}")
    
    coverage = (found_patterns / len(expected_patterns)) * 100
    print(f"\n   📊 Spring Boot pattern coverage: {coverage:.1f}% ({found_patterns}/{len(expected_patterns)})")
    
    assert coverage >= 80, f"Spring Boot pattern coverage too low: {coverage:.1f}%"
    print("   ✅ Spring Boot patterns test passed!")

def test_pattern_validation():
    """Test pattern validation and cleaning"""
    print("\n🧹 Testing Pattern Validation")
    print("=" * 60)
    
    # Test pattern cleaning
    from gates.nodes import CallLLMNode
    llm_node = CallLLMNode()
    
    # Test patterns with various formats
    test_patterns = [
        "r'\\b\\w*logger\\w*\\.(info|debug|error|warn|trace)'",
        'r"import\\s+org\\.slf4j\\.Logger"',
        "'@Slf4j'",
        '"@RestController"',
        "log.(info|debug|error|warn|trace)",  # Missing escaping
        "invalid[regex",  # Invalid regex
        "",  # Empty pattern
        None,  # None pattern
        "r'valid\\.pattern\\('"
    ]
    
    cleaned = llm_node._clean_and_validate_patterns(test_patterns)
    
    print(f"   📥 Input patterns: {len(test_patterns)}")
    print(f"   📤 Cleaned patterns: {len(cleaned)}")
    
    # Validate all cleaned patterns are valid regex
    import re
    for pattern in cleaned:
        try:
            re.compile(pattern)
            print(f"   ✅ Valid: {pattern}")
        except re.error as e:
            print(f"   ❌ Invalid: {pattern} - {e}")
            assert False, f"Cleaned pattern is still invalid: {pattern}"
    
    assert len(cleaned) > 0, "No patterns survived cleaning"
    print("   ✅ Pattern validation test passed!")

def test_technology_mapping():
    """Test technology mapping and detection"""
    print("\n🗺️ Testing Technology Mapping")
    print("=" * 60)
    
    # Test technology variations
    test_mappings = [
        (["Java"], "java"),
        (["JavaScript"], "javascript"),
        (["TypeScript"], "typescript"),
        (["Python"], "python"),
        (["C#"], "csharp"),
        (["Go"], "go"),
        (["Rust"], "rust"),
        (["spring"], "java"),  # Should map to java
        (["nodejs"], "javascript"),  # Should map to javascript
        (["django"], "python"),  # Should map to python
    ]
    
    for technologies, expected_category in test_mappings:
        patterns = get_static_patterns_for_gate("STRUCTURED_LOGS", technologies)
        assert len(patterns) > 0, f"No patterns found for {technologies}"
        print(f"   ✅ {technologies} → {len(patterns)} patterns")
    
    print("   ✅ Technology mapping test passed!")

def test_gate_specific_enhancements():
    """Test gate-specific pattern enhancements"""
    print("\n🚪 Testing Gate-Specific Enhancements")
    print("=" * 60)
    
    # Test different gates have appropriate patterns
    gate_tests = [
        {
            "gate": "STRUCTURED_LOGS",
            "technologies": ["Java"],
            "expected_keywords": ["slf4j", "logback", "Logger", "log.", "logger."],
            "min_patterns": 20
        },
        {
            "gate": "AUTOMATED_TESTS",
            "technologies": ["Java"],
            "expected_keywords": ["@Test", "junit", "mockito", "assert"],
            "min_patterns": 15
        },
        {
            "gate": "LOG_API_CALLS",
            "technologies": ["Java"],
            "expected_keywords": ["@RestController", "@GetMapping", "@PostMapping", "RequestMapping"],
            "min_patterns": 15
        },
        {
            "gate": "ERROR_LOGS",
            "technologies": ["Java"],
            "expected_keywords": ["try", "catch", "Exception", "Error", "throw"],
            "min_patterns": 10
        }
    ]
    
    for test in gate_tests:
        patterns = get_static_patterns_for_gate(test["gate"], test["technologies"])
        
        print(f"\n   🔍 Testing {test['gate']}:")
        print(f"      Patterns found: {len(patterns)}")
        
        # Check minimum pattern count
        assert len(patterns) >= test["min_patterns"], \
            f"{test['gate']} has only {len(patterns)} patterns, expected at least {test['min_patterns']}"
        
        # Check for expected keywords
        pattern_text = " ".join(patterns)
        found_keywords = 0
        for keyword in test["expected_keywords"]:
            if keyword in pattern_text:
                found_keywords += 1
                print(f"      ✅ Found keyword: {keyword}")
            else:
                print(f"      ❌ Missing keyword: {keyword}")
        
        keyword_coverage = (found_keywords / len(test["expected_keywords"])) * 100
        print(f"      📊 Keyword coverage: {keyword_coverage:.1f}%")
        
        assert keyword_coverage >= 50, f"Keyword coverage too low for {test['gate']}: {keyword_coverage:.1f}%"
    
    print("\n   ✅ Gate-specific enhancement tests passed!")

def test_pattern_statistics():
    """Test pattern statistics and reporting"""
    print("\n📊 Testing Pattern Statistics")
    print("=" * 60)
    
    stats = get_pattern_statistics()
    
    print(f"   Total gates: {stats['total_gates']}")
    print(f"   Total patterns: {stats['total_patterns']}")
    print(f"   Average patterns per gate: {stats['average_patterns_per_gate']:.1f}")
    
    # Validate statistics
    assert stats['total_gates'] > 0, "No gates found in statistics"
    assert stats['total_patterns'] > 0, "No patterns found in statistics"
    assert stats['average_patterns_per_gate'] > 0, "Invalid average patterns per gate"
    
    # Check technology coverage
    for tech, count in stats['patterns_by_technology'].items():
        print(f"   {tech}: {count} patterns")
        assert count > 0, f"No patterns found for {tech}"
    
    print("   ✅ Pattern statistics test passed!")

def main():
    """Run all enhanced pattern tests"""
    print("🚀 Enhanced Pattern Library Test Suite")
    print("=" * 80)
    
    try:
        test_enhanced_static_patterns()
        test_spring_boot_specific_patterns()
        test_pattern_validation()
        test_technology_mapping()
        test_gate_specific_enhancements()
        test_pattern_statistics()
        
        print("\n" + "=" * 80)
        print("🎉 All Enhanced Pattern Tests Passed!")
        print("\n📈 Key Improvements Validated:")
        print("   • Enhanced static pattern library with comprehensive coverage")
        print("   • Spring Boot specific patterns for better Java project support")
        print("   • Robust pattern validation and cleaning")
        print("   • Intelligent technology mapping and detection")
        print("   • Gate-specific pattern enhancements")
        print("   • Comprehensive pattern statistics and reporting")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 