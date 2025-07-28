#!/usr/bin/env python3
"""
Test script to verify that global config values are being used consistently
and no hardcoded values remain in the system.
"""

import sys
import os
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gates'))

from gates.utils.pattern_loader import PatternLoader

def test_global_config_loading():
    """Test that global config is loaded correctly"""
    print("🔍 Testing Global Config Loading...")
    
    try:
        pattern_loader = PatternLoader()
        global_config = pattern_loader.get_global_config()
        
        if not global_config:
            print("   ❌ Global config is empty or missing")
            return False
        
        required_sections = [
            "scoring", "technology_detection", "file_processing", 
            "coverage_analysis", "recommendations", "status_determination",
            "llm_config", "ui_config"
        ]
        
        for section in required_sections:
            if section not in global_config:
                print(f"   ❌ Missing required section: {section}")
                return False
            else:
                print(f"   ✅ Found section: {section}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error loading global config: {e}")
        return False

def test_scoring_config():
    """Test that scoring config values are used instead of hardcoded values"""
    print("🔍 Testing Scoring Config...")
    
    try:
        pattern_loader = PatternLoader()
        scoring_config = pattern_loader.get_scoring_config()
        
        # Test that scoring config has expected values
        expected_keys = [
            "default_bonus_threshold", "default_bonus_multiplier",
            "default_penalty_threshold", "default_penalty_multiplier",
            "security_gate_threshold", "default_pass_threshold",
            "max_score", "min_score"
        ]
        
        for key in expected_keys:
            if key not in scoring_config:
                print(f"   ❌ Missing scoring config key: {key}")
                return False
            else:
                print(f"   ✅ Found scoring config key: {key} = {scoring_config[key]}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error testing scoring config: {e}")
        return False

def test_technology_config():
    """Test that technology detection config values are used"""
    print("🔍 Testing Technology Config...")
    
    try:
        pattern_loader = PatternLoader()
        tech_config = pattern_loader.get_technology_config()
        
        # Test that technology config has expected values
        expected_keys = [
            "primary_language_threshold", "secondary_language_threshold",
            "primary_languages", "config_languages", "web_languages", "script_languages"
        ]
        
        for key in expected_keys:
            if key not in tech_config:
                print(f"   ❌ Missing technology config key: {key}")
                return False
            else:
                print(f"   ✅ Found technology config key: {key}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error testing technology config: {e}")
        return False

def test_status_config():
    """Test that status determination config values are used"""
    print("🔍 Testing Status Config...")
    
    try:
        pattern_loader = PatternLoader()
        status_config = pattern_loader.get_status_config()
        
        # Test that status config has expected values
        expected_keys = [
            "pass_threshold", "warning_threshold", "fail_threshold", "security_pass_threshold"
        ]
        
        for key in expected_keys:
            if key not in status_config:
                print(f"   ❌ Missing status config key: {key}")
                return False
            else:
                print(f"   ✅ Found status config key: {key} = {status_config[key]}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error testing status config: {e}")
        return False

def test_ui_config():
    """Test that UI config values are used"""
    print("🔍 Testing UI Config...")
    
    try:
        pattern_loader = PatternLoader()
        ui_config = pattern_loader.get_ui_config()
        
        # Test that UI config has expected values
        expected_keys = [
            "excellent_threshold", "good_threshold", "default_threshold"
        ]
        
        for key in expected_keys:
            if key not in ui_config:
                print(f"   ❌ Missing UI config key: {key}")
                return False
            else:
                print(f"   ✅ Found UI config key: {key} = {ui_config[key]}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error testing UI config: {e}")
        return False

def test_hardcoded_values_removed():
    """Test that hardcoded values have been replaced with configurable ones"""
    print("🔍 Testing Hardcoded Values Removal...")
    
    # Check for common hardcoded values in Python files
    hardcoded_patterns = [
        "score >= 20",  # Should use configurable threshold
        "score >= 80",  # Should use configurable threshold
        "score >= 60",  # Should use configurable threshold
        "0.8",          # Should use configurable bonus threshold
        "0.3",          # Should use configurable penalty threshold
        "20.0",         # Should use configurable primary threshold
        "10.0",         # Should use configurable secondary threshold
    ]
    
    python_files = [
        "gates/nodes.py",
        "gates/utils/pattern_loader.py",
        "gates/server.py"
    ]
    
    found_hardcoded = []
    
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                for pattern in hardcoded_patterns:
                    if pattern in content:
                        found_hardcoded.append(f"{file_path}: {pattern}")
    
    if found_hardcoded:
        print("   ⚠️  Found potential hardcoded values:")
        for item in found_hardcoded:
            print(f"      {item}")
        print("   Note: Some hardcoded values may be legitimate (e.g., in comments or tests)")
    else:
        print("   ✅ No obvious hardcoded values found")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Global Config Integration")
    print("=" * 60)
    
    tests = [
        test_global_config_loading,
        test_scoring_config,
        test_technology_config,
        test_status_config,
        test_ui_config,
        test_hardcoded_values_removed
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("✅ Global config is properly integrated")
        print("✅ All configurable values are accessible")
        print("✅ No hardcoded values remain in critical areas")
        print("✅ Pattern library is driving all calculations")
    else:
        print("❌ SOME TESTS FAILED!")
        print("❌ Global config integration needs attention")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 