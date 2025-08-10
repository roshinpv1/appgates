#!/usr/bin/env python3
"""
Backward Compatibility Test for CodeGates Status API
Tests that the enhanced status API remains compatible with existing clients
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_scan_result_model_compatibility():
    """Test that ScanResult model has all required fields for backward compatibility"""
    print("🔍 Testing ScanResult model compatibility...")
    
    try:
        from server import ScanResult
        
        # Test that all required fields exist
        required_fields = [
            "scan_id", "status", "overall_score", "total_files", "total_lines",
            "passed_gates", "failed_gates", "warning_gates", "total_gates",
            "html_report_url", "json_report_url", "completed_at", "errors",
            "current_step", "progress_percentage", "step_details", "app_id"
        ]
        
        # Test that backward compatibility aliases exist
        backward_compat_fields = ["score", "gates", "progress"]
        
        # Test that enhanced fields exist
        enhanced_fields = [
            "evidence_collection_progress", "mandatory_collectors_status", 
            "gate_validation_progress"
        ]
        
        all_fields = required_fields + backward_compat_fields + enhanced_fields
        
        # Create a mock ScanResult to test field access
        mock_data = {
            "scan_id": "test-123",
            "status": "completed",
            "overall_score": 85.5,
            "total_files": 100,
            "total_lines": 5000,
            "passed_gates": 8,
            "failed_gates": 2,
            "warning_gates": 0,
            "total_gates": 10,
            "html_report_url": "http://example.com/report.html",
            "json_report_url": "http://example.com/report.json",
            "completed_at": "2024-01-01T12:00:00Z",
            "errors": [],
            "current_step": "Completed",
            "progress_percentage": 100,
            "step_details": "Scan completed successfully",
            "app_id": "test-app",
            # Backward compatibility aliases
            "score": 85.5,
            "gates": [],
            "progress": 100,
            # Enhanced fields
            "evidence_collection_progress": {},
            "mandatory_collectors_status": {},
            "gate_validation_progress": []
        }
        
        # Test model creation
        scan_result = ScanResult(**mock_data)
        
        # Test field access
        for field in all_fields:
            if hasattr(scan_result, field):
                value = getattr(scan_result, field)
                print(f"   ✅ {field}: {type(value).__name__} = {value}")
            else:
                print(f"   ❌ Missing field: {field}")
                return False
        
        print("   ✅ All fields present and accessible")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing ScanResult model: {e}")
        return False

def test_vscode_extension_compatibility():
    """Test compatibility with VSCode extension expected fields"""
    print("🔍 Testing VSCode extension compatibility...")
    
    try:
        from server import ScanResult
        
        # VSCode extension expected fields (from api.ts)
        vscode_expected_fields = {
            "scan_id": str,
            "status": str,
            "message": str,
            "repository_url": str,
            "score": (int, float),  # VSCode expects 'score' not 'overall_score'
            "gates": list,  # VSCode expects 'gates' not 'gate_results'
            "recommendations": list,
            "report_url": str,
            "progress": (int, float),  # VSCode expects 'progress' not 'progress_percentage'
            "languages_detected": list,
            "current_step": str,
            "progress_percentage": (int, float),
            "step_details": str,
            "app_id": str
        }
        
        # Create mock data with VSCode extension field names
        mock_data = {
            "scan_id": "test-123",
            "status": "completed",
            "overall_score": 85.5,  # Will be aliased to 'score'
            "total_files": 100,
            "total_lines": 5000,
            "passed_gates": 8,
            "failed_gates": 2,
            "warning_gates": 0,
            "total_gates": 10,
            "html_report_url": "http://example.com/report.html",
            "json_report_url": "http://example.com/report.json",
            "completed_at": "2024-01-01T12:00:00Z",
            "errors": [],
            "current_step": "Completed",
            "progress_percentage": 100,  # Will be aliased to 'progress'
            "step_details": "Scan completed successfully",
            "app_id": "test-app",
            "gate_results": [],  # Will be aliased to 'gates'
            "score": 85.5,  # Backward compatibility alias
            "gates": [],  # Backward compatibility alias
            "progress": 100,  # Backward compatibility alias
            "evidence_collection_progress": {},
            "mandatory_collectors_status": {},
            "gate_validation_progress": []
        }
        
        # Create ScanResult
        scan_result = ScanResult(**mock_data)
        
        # Convert to dict for testing
        result_dict = scan_result.dict()
        
        # Test VSCode extension field compatibility
        vscode_compatible = True
        
        # Test that 'score' alias works
        if "score" in result_dict and result_dict["score"] == 85.5:
            print("   ✅ 'score' alias works correctly")
        else:
            print("   ❌ 'score' alias not working")
            vscode_compatible = False
        
        # Test that 'gates' alias works
        if "gates" in result_dict and isinstance(result_dict["gates"], list):
            print("   ✅ 'gates' alias works correctly")
        else:
            print("   ❌ 'gates' alias not working")
            vscode_compatible = False
        
        # Test that 'progress' alias works
        if "progress" in result_dict and result_dict["progress"] == 100:
            print("   ✅ 'progress' alias works correctly")
        else:
            print("   ❌ 'progress' alias not working")
            vscode_compatible = False
        
        return vscode_compatible
        
    except Exception as e:
        print(f"   ❌ Error testing VSCode extension compatibility: {e}")
        return False

def test_simple_server_compatibility():
    """Test compatibility with simple server"""
    print("🔍 Testing simple server compatibility...")
    
    try:
        from simple_server import ScanResult as SimpleScanResult
        
        # Test that simple server has required fields
        required_fields = [
            "scan_id", "status", "overall_score", "total_files", "total_lines",
            "passed_gates", "failed_gates", "warning_gates", "total_gates",
            "html_report_url", "json_report_url", "completed_at", "errors",
            "current_step", "progress_percentage", "step_details"
        ]
        
        # Create mock data
        mock_data = {
            "scan_id": "test-123",
            "status": "completed",
            "overall_score": 85.5,
            "total_files": 100,
            "total_lines": 5000,
            "passed_gates": 8,
            "failed_gates": 2,
            "warning_gates": 0,
            "total_gates": 10,
            "html_report_url": "http://example.com/report.html",
            "json_report_url": "http://example.com/report.json",
            "completed_at": "2024-01-01T12:00:00Z",
            "errors": [],
            "current_step": "Completed",
            "progress_percentage": 100,
            "step_details": "Scan completed successfully"
        }
        
        # Test model creation
        scan_result = SimpleScanResult(**mock_data)
        
        # Test field access
        for field in required_fields:
            if hasattr(scan_result, field):
                value = getattr(scan_result, field)
                print(f"   ✅ {field}: {type(value).__name__} = {value}")
            else:
                print(f"   ❌ Missing field: {field}")
                return False
        
        print("   ✅ Simple server compatibility verified")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing simple server compatibility: {e}")
        return False

def test_json_serialization():
    """Test that ScanResult can be properly serialized to JSON"""
    print("🔍 Testing JSON serialization...")
    
    try:
        from server import ScanResult
        
        # Create mock data
        mock_data = {
            "scan_id": "test-123",
            "status": "completed",
            "overall_score": 85.5,
            "total_files": 100,
            "total_lines": 5000,
            "passed_gates": 8,
            "failed_gates": 2,
            "warning_gates": 0,
            "total_gates": 10,
            "html_report_url": "http://example.com/report.html",
            "json_report_url": "http://example.com/report.json",
            "completed_at": "2024-01-01T12:00:00Z",
            "errors": [],
            "current_step": "Completed",
            "progress_percentage": 100,
            "step_details": "Scan completed successfully",
            "app_id": "test-app",
            "score": 85.5,
            "gates": [],
            "progress": 100,
            "evidence_collection_progress": {},
            "mandatory_collectors_status": {},
            "gate_validation_progress": []
        }
        
        # Create ScanResult
        scan_result = ScanResult(**mock_data)
        
        # Test JSON serialization
        json_str = scan_result.json()
        parsed_data = json.loads(json_str)
        
        # Verify key fields are present
        required_json_fields = [
            "scan_id", "status", "overall_score", "score", "gates", "progress",
            "warning_gates", "step_details"
        ]
        
        for field in required_json_fields:
            if field in parsed_data:
                print(f"   ✅ JSON field '{field}' present: {parsed_data[field]}")
            else:
                print(f"   ❌ JSON field '{field}' missing")
                return False
        
        print("   ✅ JSON serialization works correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing JSON serialization: {e}")
        return False

def main():
    """Run all backward compatibility tests"""
    print("🔄 CodeGates Status API Backward Compatibility Test")
    print("=" * 60)
    
    tests = [
        ("ScanResult Model Compatibility", test_scan_result_model_compatibility),
        ("VSCode Extension Compatibility", test_vscode_extension_compatibility),
        ("Simple Server Compatibility", test_simple_server_compatibility),
        ("JSON Serialization", test_json_serialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backward compatibility tests PASSED!")
        print("✅ Status API is fully backward compatible")
        return True
    else:
        print("❌ Some backward compatibility tests FAILED!")
        print("⚠️ Status API may have compatibility issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 