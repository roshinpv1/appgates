#!/usr/bin/env python3
"""
Simple test to verify report storage functionality
"""

import os
import json
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus
from services.html_report_service import HTMLReportService


def test_report_storage_simple():
    """Test report storage functionality with mock data"""
    
    print("🧪 Testing Report Storage Functionality (Simple)")
    print("=" * 50)
    
    # Create mock scan result
    scan_id = f"test_scan_{int(datetime.now().timestamp())}"
    
    # Create mock gate results
    gate_results = [
        GateResult(
            gate_id="security_auth",
            gate_name="Authentication Security",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["auth middleware found"],
            recommendations=["Implement JWT tokens"],
            confidence_score=0.9,
            reasoning="Authentication middleware is properly implemented"
        ),
        GateResult(
            gate_id="security_password",
            gate_name="Password Security",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement password hashing", "Add password validation"],
            confidence_score=0.8,
            reasoning="No password hashing implementation found"
        ),
        GateResult(
            gate_id="performance_cache",
            gate_name="Caching Implementation",
            status=GateStatus.PARTIAL,
            expected_count=2,
            actual_count=1,
            threshold=1,
            patterns_found=["redis cache found"],
            recommendations=["Implement database caching", "Add CDN caching"],
            confidence_score=0.7,
            reasoning="Basic caching implemented but could be enhanced"
        )
    ]
    
    # Create scan result
    scan_result = ScanResult(
        scan_id=scan_id,
        repo_url="https://github.com/example/test-repo",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=3,
        passed_gates=1,
        failed_gates=1,
        partial_gates=1,
        skipped_gates=0,
        gate_results=gate_results,
        recommendations=[
            "Implement comprehensive password security",
            "Add database caching layer",
            "Consider implementing CDN for static assets"
        ],
        risk_score=0.6,
        scan_duration=45.2,
        metadata={
            "main_repo": {
                "repo_url": "https://github.com/example/test-repo",
                "branch": "main",
                "total_files": 150,
                "total_lines": 5000,
                "languages": ["Python", "JavaScript"],
                "build_files": ["requirements.txt", "package.json"],
                "config_files": [".env", "config.py"]
            }
        }
    )
    
    # Generate HTML report
    print("📄 Generating HTML report...")
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
    
    report_paths = {}
    
    # Save HTML report
    html_filename = f"codegates_report_{scan_id}.html"
    html_path = os.path.join(scan_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    report_paths["html"] = html_path
    print(f"💾 HTML report saved: {html_path}")
    
    # Save JSON report
    json_filename = f"codegates_report_{scan_id}.json"
    json_path = os.path.join(scan_dir, json_filename)
    
    # Convert ScanResult to JSON-serializable dict
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
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    report_paths["json"] = json_path
    print(f"💾 JSON report saved: {json_path}")
    
    # Create a summary file
    summary_filename = f"report_summary_{scan_id}.txt"
    summary_path = os.path.join(scan_dir, summary_filename)
    
    summary_content = f"""
CodeGates Scan Report Summary
============================

Scan ID: {scan_id}
Repository: {scan_result.repo_url}
Branch: {scan_result.branch}
Scan Timestamp: {scan_result.scan_timestamp}

Results Summary:
- Total Gates: {scan_result.total_gates}
- Passed: {scan_result.passed_gates}
- Failed: {scan_result.failed_gates}
- Partial: {scan_result.partial_gates}
- Skipped: {scan_result.skipped_gates}
- Risk Score: {scan_result.risk_score:.2f}

Report Files:
- HTML Report: {html_filename}
- JSON Report: {json_filename}
- Summary: {summary_filename}

Report Directory: {scan_dir}

Generated on: {datetime.now().isoformat()}
"""
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    report_paths["summary"] = summary_path
    print(f"💾 Summary file saved: {summary_path}")
    
    # Verify files were created
    print("\n📋 Verifying created files...")
    
    for report_type, path in report_paths.items():
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"✅ {report_type.upper()}: {path} ({file_size} bytes)")
        else:
            print(f"❌ {report_type.upper()}: {path} (not found)")
    
    # Test file content
    print("\n📄 Testing file content...")
    
    # Test HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    html_checks = [
        ("DOCTYPE", "<!DOCTYPE html>" in html_content),
        ("Title", "CodeGates" in html_content),
        ("Scan ID", scan_id in html_content),
        ("CSS Styles", "style" in html_content),
        ("Table", "<table" in html_content)
    ]
    
    print("📋 HTML Content Verification:")
    for check_name, found in html_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Test JSON content
    with open(json_path, 'r', encoding='utf-8') as f:
        json_content = f.read()
    
    try:
        json_data_loaded = json.loads(json_content)
        json_checks = [
            ("scan_id", json_data_loaded.get("scan_id") == scan_id),
            ("repo_url", "repo_url" in json_data_loaded),
            ("gate_results", "gate_results" in json_data_loaded),
            ("risk_score", "risk_score" in json_data_loaded),
            ("total_gates", "total_gates" in json_data_loaded)
        ]
        
        print("📋 JSON Content Verification:")
        for check_name, found in json_checks:
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON is invalid: {e}")
    
    # Test summary content
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_content_loaded = f.read()
    
    summary_checks = [
        ("Scan ID", scan_id in summary_content_loaded),
        ("Repository", "Repository:" in summary_content_loaded),
        ("Results Summary", "Results Summary:" in summary_content_loaded),
        ("Report Files", "Report Files:" in summary_content_loaded),
        ("Report Directory", "Report Directory:" in summary_content_loaded)
    ]
    
    print("📋 Summary Content Verification:")
    for check_name, found in summary_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    print(f"\n🎉 Report Storage Test Complete!")
    print(f"\n📖 Report files are available at:")
    print(f"   📁 Directory: {scan_dir}")
    print(f"   🌐 HTML: file://{os.path.abspath(html_path)}")
    print(f"   📄 JSON: {json_path}")
    print(f"   📋 Summary: {summary_path}")
    
    return scan_id, report_paths


if __name__ == "__main__":
    test_report_storage_simple()
