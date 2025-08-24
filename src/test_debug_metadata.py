#!/usr/bin/env python3
"""
Debug test to check scan result metadata
"""

import json
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus


def test_debug_metadata():
    """Debug scan result metadata"""
    
    print("🔍 Debugging Scan Result Metadata")
    print("=" * 40)
    
    # Create mock scan result with project summary
    scan_id = f"debug_metadata_{int(datetime.now().timestamp())}"
    
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
    
    # Create project summary
    project_summary = {
        "summary": "Project analysis reveals a technology stack primarily using python, javascript, docker. The codebase contains py, js, yaml files. Key dependencies include django, flask, react.",
        "technologies": ["python", "javascript", "docker"],
        "frameworks": [],
        "file_types": ["py", "js", "yaml"],
        "dependencies": ["django", "flask", "react"],
        "has_cd_repo": True,
        "total_files_analyzed": 10
    }
    
    # Create scan result
    scan_result = ScanResult(
        scan_id=scan_id,
        repo_url="https://github.com/example/debug-test",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=1,
        passed_gates=1,
        failed_gates=0,
        partial_gates=0,
        skipped_gates=0,
        gate_results=gate_results,
        recommendations=["test recommendation"],
        risk_score=0.1,
        scan_duration=10.0,
        metadata={
            "main_repo": {
                "repo_url": "https://github.com/example/debug-test",
                "branch": "main"
            },
            "vector_config": {
                "vector_size": 768,
                "distance_metric": "cosine",
                "use_qdrant": False
            },
            "project_summary": project_summary
        }
    )
    
    # Debug metadata
    print("📋 Scan Result Metadata:")
    print(f"   Scan ID: {scan_result.scan_id}")
    print(f"   Repo URL: {scan_result.repo_url}")
    print(f"   Metadata keys: {list(scan_result.metadata.keys())}")
    
    if "project_summary" in scan_result.metadata:
        print("   ✅ Project summary found in metadata")
        ps = scan_result.metadata["project_summary"]
        print(f"   Summary: {ps.get('summary', 'No summary')}")
        print(f"   Technologies: {ps.get('technologies', [])}")
        print(f"   File Types: {ps.get('file_types', [])}")
        print(f"   Dependencies: {ps.get('dependencies', [])}")
        print(f"   Has CD Repo: {ps.get('has_cd_repo', False)}")
        print(f"   Files Analyzed: {ps.get('total_files_analyzed', 0)}")
    else:
        print("   ❌ Project summary not found in metadata")
    
    # Test HTML report generation
    print("\n📄 Testing HTML report generation...")
    from services.html_report_service import HTMLReportService
    
    html_service = HTMLReportService()
    html_report = html_service.generate_html_report(scan_result)
    
    # Check if project summary content is in HTML
    print("\n📋 HTML Report Analysis:")
    
    checks = [
        ("Project Summary Heading", "Project Summary" in html_report),
        ("Project Summary Section", "project-summary-section" in html_report),
        ("Technologies in HTML", any(tech in html_report for tech in ["python", "javascript", "docker"])),
        ("File Types in HTML", any(ft in html_report for ft in ["py", "js", "yaml"])),
        ("Dependencies in HTML", any(dep in html_report for dep in ["django", "flask", "react"])),
        ("CD Repository in HTML", "CD repository" in html_report or "Continuous Deployment" in html_report),
        ("Files Analyzed in HTML", "10" in html_report)
    ]
    
    for check_name, found in checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Save report for inspection
    import os
    reports_dir = "reports"
    scan_dir = os.path.join(reports_dir, scan_id)
    os.makedirs(scan_dir, exist_ok=True)
    
    html_filename = f"debug_metadata_{scan_id}.html"
    html_path = os.path.join(scan_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"\n💾 Debug report saved: {html_path}")
    
    return scan_id, html_path


if __name__ == "__main__":
    test_debug_metadata()
