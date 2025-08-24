#!/usr/bin/env python3
"""
Test JSON serialization with updated ScanResult model
"""

import json
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus


def test_json_serialization():
    """Test JSON serialization of ScanResult"""
    
    print("🧪 Testing JSON Serialization")
    print("=" * 30)
    
    # Create mock gate results
    gate_results = [
        GateResult(
            gate_id="1.1",
            gate_name="Test Gate",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["test pattern"],
            recommendations=["test recommendation"],
            confidence_score=0.9,
            reasoning="test reasoning"
        )
    ]
    
    # Create scan result with string recommendations
    scan_result = ScanResult(
        scan_id="test_scan_123",
        repo_url="https://github.com/example/test",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=1,
        passed_gates=1,
        failed_gates=0,
        partial_gates=0,
        skipped_gates=0,
        gate_results=gate_results,
        recommendations=[
            "Implement proper logging",
            "Add error handling",
            "Use secure authentication"
        ],
        risk_score=0.2,
        scan_duration=15.5,
        metadata={
            "main_repo": {
                "repo_url": "https://github.com/example/test",
                "branch": "main"
            },
            "project_summary": {
                "summary": "Test project with Python and JavaScript",
                "technologies": ["python", "javascript"],
                "file_types": ["py", "js"],
                "dependencies": ["django", "react"],
                "has_cd_repo": False,
                "total_files_analyzed": 5
            }
        }
    )
    
    # Test JSON serialization
    try:
        json_data = {
            "scan_id": scan_result.scan_id,
            "repo_url": scan_result.repo_url,
            "branch": scan_result.branch,
            "scan_timestamp": scan_result.scan_timestamp.isoformat(),
            "total_gates": scan_result.total_gates,
            "passed_gates": scan_result.passed_gates,
            "failed_gates": scan_result.failed_gates,
            "partial_gates": scan_result.partial_gates,
            "skipped_gates": scan_result.skipped_gates,
            "risk_score": scan_result.risk_score,
            "scan_duration": scan_result.scan_duration,
            "gate_results": [
                {
                    "gate_id": gate.gate_id,
                    "gate_name": gate.gate_name,
                    "status": gate.status.value,
                    "expected_count": gate.expected_count,
                    "actual_count": gate.actual_count,
                    "threshold": gate.threshold,
                    "patterns_found": gate.patterns_found,
                    "recommendations": gate.recommendations,
                    "confidence_score": gate.confidence_score,
                    "reasoning": gate.reasoning
                }
                for gate in scan_result.gate_results
            ],
            "recommendations": scan_result.recommendations,
            "metadata": scan_result.metadata
        }
        
        # Serialize to JSON
        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        print("✅ JSON serialization successful!")
        print(f"📄 JSON length: {len(json_string)} characters")
        
        # Test deserialization
        parsed_data = json.loads(json_string)
        print("✅ JSON deserialization successful!")
        
        # Verify key fields
        print(f"📋 Scan ID: {parsed_data['scan_id']}")
        print(f"📋 Repo URL: {parsed_data['repo_url']}")
        print(f"📋 Total Gates: {parsed_data['total_gates']}")
        print(f"📋 Recommendations count: {len(parsed_data['recommendations'])}")
        print(f"📋 Gate Results count: {len(parsed_data['gate_results'])}")
        
        # Check recommendations
        print("\n📋 Recommendations:")
        for i, rec in enumerate(parsed_data['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        # Check project summary in metadata
        if 'project_summary' in parsed_data['metadata']:
            ps = parsed_data['metadata']['project_summary']
            print(f"\n📋 Project Summary:")
            print(f"   Technologies: {ps.get('technologies', [])}")
            print(f"   File Types: {ps.get('file_types', [])}")
            print(f"   Dependencies: {ps.get('dependencies', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False


if __name__ == "__main__":
    test_json_serialization()
