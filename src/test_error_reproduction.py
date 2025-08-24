#!/usr/bin/env python3
"""
Test script to reproduce the exact error
"""

import json
from datetime import datetime
from services.html_report_service import HTMLReportService
from models.scan_models import ScanResult, GateResult, GateStatus

def test_error_reproduction():
    """Test to reproduce the exact error"""
    
    print("🧪 Testing Error Reproduction")
    print("=" * 50)
    
    # Get actual scan data from the server
    import requests
    
    try:
        # Get the scan data that's causing the error
        response = requests.get("http://localhost:8000/api/v1/scan/scan_1756012469")
        if response.status_code != 200:
            print(f"❌ Failed to get scan data: {response.status_code}")
            return
        
        scan_data = response.json()
        print(f"✅ Got scan data: {scan_data.get('scan_id')}")
        
        # Get the actual scan result data
        result_data = scan_data.get("result", scan_data)
        
        if not result_data:
            print("❌ No result data found")
            return
        
        print(f"✅ Got result data with {len(result_data.get('gate_results', []))} gates")
        
        # Convert scan data to ScanResult object (same as in server.py)
        gate_results = []
        for gate_data in result_data.get("gate_results", []):
            print(f"   Processing gate: {gate_data.get('gate_id')} - {gate_data.get('gate_name')}")
            print(f"   Recommendations: {gate_data.get('recommendations', [])}")
            print(f"   Recommendations type: {type(gate_data.get('recommendations', []))}")
            
            gate_result = GateResult(
                gate_id=gate_data.get("gate_id", ""),
                gate_name=gate_data.get("gate_name", ""),
                status=GateStatus(gate_data.get("status", "unknown")),
                expected_count=gate_data.get("expected_count", 0),
                actual_count=gate_data.get("actual_count", 0),
                threshold=gate_data.get("threshold", 0),
                patterns_found=gate_data.get("patterns_found", []),
                recommendations=gate_data.get("recommendations", []),
                confidence_score=gate_data.get("confidence_score", 0.0),
                reasoning=gate_data.get("reasoning", "")
            )
            gate_results.append(gate_result)
            print(f"   ✅ Created GateResult object")
        
        scan_result = ScanResult(
            scan_id="scan_1756012469",
            repo_url=result_data.get("repo_url", "Unknown"),
            branch=result_data.get("branch", "Unknown"),
            scan_timestamp=datetime.fromisoformat(result_data.get("scan_timestamp", datetime.now().isoformat())),
            total_gates=result_data.get("total_gates", 0),
            passed_gates=result_data.get("passed_gates", 0),
            failed_gates=result_data.get("failed_gates", 0),
            partial_gates=result_data.get("partial_gates", 0),
            skipped_gates=result_data.get("skipped_gates", 0),
            gate_results=gate_results,
            recommendations=result_data.get("recommendations", []),
            risk_score=result_data.get("risk_score", 0.0),
            scan_duration=result_data.get("scan_duration", 0.0),
            metadata=result_data.get("metadata", {})
        )
        
        print(f"✅ Created ScanResult object with {len(scan_result.gate_results)} gates")
        
        # Generate HTML report (this should trigger the error)
        html_service = HTMLReportService()
        print("🔧 Generating HTML report...")
        
        try:
            html_report = html_service.generate_html_report(scan_result)
            print(f"✅ HTML report generated successfully! ({len(html_report)} characters)")
        except Exception as e:
            print(f"❌ HTML report generation failed: {e}")
            print(f"   Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_error_reproduction()
