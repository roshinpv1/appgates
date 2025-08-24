#!/usr/bin/env python3
"""
Debug script to test GateResult object creation and method calls
"""

from models.scan_models import GateResult, GateStatus
from services.html_report_service import HTMLReportService

def debug_gate_result():
    """Debug GateResult object creation and method calls"""
    
    print("🧪 Debugging GateResult Object")
    print("=" * 50)
    
    # Create a GateResult object with the same data as the scan
    gate_result = GateResult(
        gate_id="security_auth",
        gate_name="Authentication Check",
        status=GateStatus.PASS,
        expected_count=10,
        actual_count=190,
        threshold=5,
        patterns_found=["auth", "auth", "auth", "auth", "auth"],
        recommendations=["Good implementation of Authentication Check"],
        confidence_score=1.0,
        reasoning="Found 190 implementations, meeting expected 10"
    )
    
    print(f"✅ GateResult created successfully")
    print(f"   Gate ID: {gate_result.gate_id}")
    print(f"   Gate Name: {gate_result.gate_name}")
    print(f"   Status: {gate_result.status}")
    print(f"   Recommendations: {gate_result.recommendations}")
    print(f"   Recommendations type: {type(gate_result.recommendations)}")
    
    # Test HTML report service methods
    html_service = HTMLReportService()
    
    print("\n🧪 Testing HTML Report Service Methods")
    print("=" * 50)
    
    try:
        # Test _format_evidence
        evidence = html_service._format_evidence(gate_result)
        print(f"✅ _format_evidence: {evidence}")
    except Exception as e:
        print(f"❌ _format_evidence failed: {e}")
    
    try:
        # Test _get_recommendation
        recommendation = html_service._get_recommendation(gate_result)
        print(f"✅ _get_recommendation: {recommendation}")
    except Exception as e:
        print(f"❌ _get_recommendation failed: {e}")
    
    try:
        # Test _generate_patterns_html
        patterns_html = html_service._generate_patterns_html(gate_result.patterns_found)
        print(f"✅ _generate_patterns_html: {len(patterns_html)} characters")
    except Exception as e:
        print(f"❌ _generate_patterns_html failed: {e}")
    
    try:
        # Test _generate_gate_recommendations_html
        rec_html = html_service._generate_gate_recommendations_html(gate_result.recommendations)
        print(f"✅ _generate_gate_recommendations_html: {len(rec_html)} characters")
    except Exception as e:
        print(f"❌ _generate_gate_recommendations_html failed: {e}")
    
    try:
        # Test _generate_recommendations_html (this might be the issue)
        rec_html2 = html_service._generate_recommendations_html(gate_result.recommendations)
        print(f"✅ _generate_recommendations_html: {len(rec_html2)} characters")
    except Exception as e:
        print(f"❌ _generate_recommendations_html failed: {e}")
    
    print("\n🎉 Debug Complete!")

if __name__ == "__main__":
    debug_gate_result()
