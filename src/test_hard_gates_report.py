#!/usr/bin/env python3
"""
Test script to verify hard gates are properly prioritized in the report
"""

import os
import json
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus
from services.html_report_service import HTMLReportService


def test_hard_gates_report():
    """Test hard gates prioritization in report generation"""
    
    print("🧪 Testing Hard Gates Report Prioritization")
    print("=" * 50)
    
    # Create mock scan result with hard gates
    scan_id = f"hard_gates_test_{int(datetime.now().timestamp())}"
    
    # Create mock gate results focusing on hard gates
    gate_results = [
        # Auditability Hard Gates
        GateResult(
            gate_id="1.1",
            gate_name="Logs Searchable/Available",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["logging configuration found", "centralized logging setup"],
            recommendations=["Ensure logs are sent to central system"],
            confidence_score=0.9,
            reasoning="Logging configuration is properly set up with centralized logging"
        ),
        GateResult(
            gate_id="1.3",
            gate_name="Audit Trail",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement audit trail logging", "Track user activities"],
            confidence_score=0.8,
            reasoning="No audit trail implementation found"
        ),
        GateResult(
            gate_id="1.5",
            gate_name="Implement tracking ID for log messages",
            status=GateStatus.PARTIAL,
            expected_count=2,
            actual_count=1,
            threshold=1,
            patterns_found=["request ID found"],
            recommendations=["Add correlation IDs", "Implement trace IDs"],
            confidence_score=0.7,
            reasoning="Basic request tracking found but needs enhancement"
        ),
        GateResult(
            gate_id="1.6",
            gate_name="Log API Calls",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["API logging middleware", "REST call logging"],
            recommendations=["Monitor API call volumes"],
            confidence_score=0.9,
            reasoning="API calls are properly logged"
        ),
        GateResult(
            gate_id="1.8",
            gate_name="Log Application Messages",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["standard logging library", "application logging"],
            recommendations=["Review log levels"],
            confidence_score=0.9,
            reasoning="Standard logging library is used"
        ),
        GateResult(
            gate_id="1.10",
            gate_name="Avoid Logging Sensitive Data",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement log masking", "Add sensitive data filtering"],
            confidence_score=0.9,
            reasoning="No sensitive data masking found in logs"
        ),
        GateResult(
            gate_id="2.7",
            gate_name="UI Error Handling",
            status=GateStatus.PARTIAL,
            expected_count=2,
            actual_count=1,
            threshold=1,
            patterns_found=["client error logging"],
            recommendations=["Enhance client error tracking", "Add error reporting"],
            confidence_score=0.6,
            reasoning="Basic client error handling found"
        ),
        # Error Handling Hard Gates
        GateResult(
            gate_id="1.1",
            gate_name="Log system errors",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["error logging", "exception handling"],
            recommendations=["Monitor error rates"],
            confidence_score=0.9,
            reasoning="System errors are properly logged"
        ),
        GateResult(
            gate_id="1.3",
            gate_name="Use HTTP standard error codes",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["HTTP status codes", "error response codes"],
            recommendations=["Document error codes"],
            confidence_score=0.9,
            reasoning="HTTP status codes are properly used"
        ),
        GateResult(
            gate_id="2.4",
            gate_name="Include Client error tracking",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement client error tracking", "Add error reporting system"],
            confidence_score=0.8,
            reasoning="No client error tracking implementation found"
        ),
        # Availability Hard Gates
        GateResult(
            gate_id="1.5",
            gate_name="Timeouts",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["timeout configuration", "connection timeout"],
            recommendations=["Review timeout values"],
            confidence_score=0.8,
            reasoning="Timeout configuration is present"
        ),
        GateResult(
            gate_id="1.12",
            gate_name="Retry Logic",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement retry logic", "Add retry policies"],
            confidence_score=0.8,
            reasoning="No retry logic implementation found"
        ),
        GateResult(
            gate_id="3.6",
            gate_name="Throttling, drop request",
            status=GateStatus.PARTIAL,
            expected_count=2,
            actual_count=1,
            threshold=1,
            patterns_found=["rate limiting"],
            recommendations=["Enhance throttling", "Add request dropping"],
            confidence_score=0.7,
            reasoning="Basic rate limiting found but needs enhancement"
        ),
        GateResult(
            gate_id="3.9",
            gate_name="Set circuit breakers on outgoing requests",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement circuit breakers", "Add failure detection"],
            confidence_score=0.8,
            reasoning="No circuit breaker implementation found"
        ),
        GateResult(
            gate_id="3.18",
            gate_name="Auto Scale",
            status=GateStatus.PARTIAL,
            expected_count=2,
            actual_count=1,
            threshold=1,
            patterns_found=["auto scaling configuration"],
            recommendations=["Enhance auto scaling", "Add monitoring"],
            confidence_score=0.6,
            reasoning="Basic auto scaling configuration found"
        ),
        # Testing Hard Gates
        GateResult(
            gate_id="2",
            gate_name="Automated Regression Testing",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["regression tests", "automated test suite"],
            recommendations=["Increase test coverage"],
            confidence_score=0.9,
            reasoning="Automated regression testing is implemented"
        ),
        # Additional non-hard gates for comparison
        GateResult(
            gate_id="security_001",
            gate_name="Security Check",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["security headers"],
            recommendations=["Review security headers"],
            confidence_score=0.8,
            reasoning="Security headers are present"
        )
    ]
    
    # Create scan result
    scan_result = ScanResult(
        scan_id=scan_id,
        repo_url="https://github.com/example/hard-gates-test",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=len(gate_results),
        passed_gates=len([g for g in gate_results if g.status == GateStatus.PASS]),
        failed_gates=len([g for g in gate_results if g.status == GateStatus.FAIL]),
        partial_gates=len([g for g in gate_results if g.status == GateStatus.PARTIAL]),
        skipped_gates=0,
        gate_results=gate_results,
        recommendations=[
            "Implement audit trail logging",
            "Add sensitive data masking",
            "Implement client error tracking",
            "Add retry logic",
            "Implement circuit breakers"
        ],
        risk_score=0.65,
        scan_duration=45.2,
        metadata={
            "main_repo": {
                "repo_url": "https://github.com/example/hard-gates-test",
                "branch": "main",
                "total_files": 200,
                "total_lines": 8000,
                "languages": ["Python", "JavaScript", "Java"],
                "build_files": ["requirements.txt", "package.json", "pom.xml"],
                "config_files": [".env", "config.py", "application.yml"]
            }
        }
    )
    
    # Generate HTML report
    print("📄 Generating HTML report with hard gates focus...")
    html_service = HTMLReportService()
    html_report = html_service.generate_html_report(scan_result)
    print(f"✅ HTML report generated: {len(html_report)} characters")
    
    # Test report storage
    print("\n💾 Testing report storage...")
    
    # Create reports directory structure
    reports_dir = "reports"
    scan_dir = os.path.join(reports_dir, scan_id)
    
    # Ensure directories exist
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(scan_dir, exist_ok=True)
    
    # Save HTML report
    html_filename = f"hard_gates_report_{scan_id}.html"
    html_path = os.path.join(scan_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"💾 Hard gates report saved: {html_path}")
    
    # Analyze the report content
    print("\n📋 Analyzing report content...")
    
    # Check for hard gates emphasis
    hard_gates_checks = [
        ("Hard Gates Notice", "Hard Gates Assessment - Primary Focus" in html_report),
        ("Hard Gate Badge", "HARD GATE" in html_report),
        ("Hard Gate Styling", "hard-gate-row" in html_report),
        ("Hard Gate Badge Styling", "hard-gate-badge" in html_report),
        ("16 Critical Hard Gates", "16 critical hard gates" in html_report),
        ("Primary Focus", "primary focus" in html_report.lower()),
        ("Auditability Category", "Auditability" in html_report),
        ("Error Handling Category", "Error Handling" in html_report),
        ("Availability Category", "Availability" in html_report),
        ("Testing Category", "Testing" in html_report)
    ]
    
    print("📋 Hard Gates Emphasis Verification:")
    for check_name, found in hard_gates_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Check for specific hard gates
    specific_gates_checks = [
        ("1.1 Logs Searchable/Available", "1.1" in html_report and "Logs Searchable/Available" in html_report),
        ("1.3 Audit Trail", "1.3" in html_report and "Audit Trail" in html_report),
        ("1.5 Tracking ID", "1.5" in html_report and "tracking ID" in html_report),
        ("1.6 Log API Calls", "1.6" in html_report and "Log API Calls" in html_report),
        ("1.8 Log Application Messages", "1.8" in html_report and "Log Application Messages" in html_report),
        ("1.10 Avoid Logging Sensitive Data", "1.10" in html_report and "Avoid Logging Sensitive Data" in html_report),
        ("2.7 UI Error Handling", "2.7" in html_report and "UI Error Handling" in html_report),
        ("1.1 Log system errors", "Log system errors" in html_report),
        ("1.3 HTTP standard error codes", "HTTP standard error codes" in html_report),
        ("2.4 Client error tracking", "2.4" in html_report and "Client error tracking" in html_report),
        ("1.5 Timeouts", "Timeouts" in html_report),
        ("1.12 Retry Logic", "1.12" in html_report and "Retry Logic" in html_report),
        ("3.6 Throttling", "3.6" in html_report and "Throttling" in html_report),
        ("3.9 Circuit breakers", "3.9" in html_report and "circuit breakers" in html_report),
        ("3.18 Auto Scale", "3.18" in html_report and "Auto Scale" in html_report),
        ("2 Automated Regression Testing", "2" in html_report and "Automated Regression Testing" in html_report)
    ]
    
    print("\n📋 Specific Hard Gates Verification:")
    for check_name, found in specific_gates_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Check gate ordering (hard gates should appear first)
    print("\n📋 Gate Ordering Analysis:")
    
    # Find positions of hard gates vs other gates
    hard_gate_positions = []
    other_gate_positions = []
    
    lines = html_report.split('\n')
    for i, line in enumerate(lines):
        if '1.1' in line or '1.3' in line or '1.5' in line or '1.6' in line or '1.8' in line or '1.10' in line or '2.7' in line or '2.4' in line or '1.12' in line or '3.6' in line or '3.9' in line or '3.18' in line or '2' in line:
            if 'security_001' not in line:  # Exclude non-hard gates
                hard_gate_positions.append(i)
        elif 'security_001' in line:
            other_gate_positions.append(i)
    
    if hard_gate_positions and other_gate_positions:
        avg_hard_gate_pos = sum(hard_gate_positions) / len(hard_gate_positions)
        avg_other_gate_pos = sum(other_gate_positions) / len(other_gate_positions)
        
        print(f"   📊 Average hard gate position: {avg_hard_gate_pos:.1f}")
        print(f"   📊 Average other gate position: {avg_other_gate_pos:.1f}")
        
        if avg_hard_gate_pos < avg_other_gate_pos:
            print("   ✅ Hard gates appear before other gates (prioritized)")
        else:
            print("   ⚠️ Other gates appear before hard gates")
    
    # Count hard gates vs other gates
    hard_gates_count = len([g for g in gate_results if g.gate_id in ['1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7', '2.4', '1.12', '3.6', '3.9', '3.18', '2']])
    other_gates_count = len([g for g in gate_results if g.gate_id not in ['1.1', '1.3', '1.5', '1.6', '1.8', '1.10', '2.7', '2.4', '1.12', '3.6', '3.9', '3.18', '2']])
    
    print(f"\n📊 Gate Distribution:")
    print(f"   🔴 Hard Gates: {hard_gates_count}")
    print(f"   🔵 Other Gates: {other_gates_count}")
    print(f"   📈 Hard Gates Percentage: {(hard_gates_count / len(gate_results)) * 100:.1f}%")
    
    print(f"\n🎉 Hard Gates Report Test Complete!")
    print(f"\n📖 Hard gates report is available at:")
    print(f"   🌐 HTML: file://{os.path.abspath(html_path)}")
    print(f"   📁 Directory: {scan_dir}")
    
    return scan_id, html_path


if __name__ == "__main__":
    test_hard_gates_report()
