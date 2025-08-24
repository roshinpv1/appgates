#!/usr/bin/env python3
"""
Test script to verify project summary functionality
"""

import os
import json
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus
from services.html_report_service import HTMLReportService


def test_project_summary():
    """Test project summary generation"""
    
    print("🧪 Testing Project Summary Functionality")
    print("=" * 50)
    
    # Create mock scan result with vector configuration
    scan_id = f"project_summary_test_{int(datetime.now().timestamp())}"
    
    # Create mock gate results
    gate_results = [
        GateResult(
            gate_id="1.1",
            gate_name="Logs Searchable/Available",
            status=GateStatus.PASS,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["logging configuration found"],
            recommendations=["Ensure logs are sent to central system"],
            confidence_score=0.9,
            reasoning="Logging configuration is properly set up"
        ),
        GateResult(
            gate_id="1.3",
            gate_name="Audit Trail",
            status=GateStatus.FAIL,
            expected_count=1,
            actual_count=0,
            threshold=1,
            patterns_found=[],
            recommendations=["Implement audit trail logging"],
            confidence_score=0.8,
            reasoning="No audit trail implementation found"
        )
    ]
    
    # Create scan result with vector configuration
    scan_result = ScanResult(
        scan_id=scan_id,
        repo_url="https://github.com/example/project-summary-test",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=2,
        passed_gates=1,
        failed_gates=1,
        partial_gates=0,
        skipped_gates=0,
        gate_results=gate_results,
        recommendations=[
            "Implement audit trail logging",
            "Add centralized logging"
        ],
        risk_score=0.5,
        scan_duration=30.0,
        metadata={
            "main_repo": {
                "repo_url": "https://github.com/example/project-summary-test",
                "branch": "main",
                "total_files": 100,
                "total_lines": 3000,
                "languages": ["Python", "JavaScript"],
                "build_files": ["requirements.txt", "package.json"],
                "config_files": [".env", "config.py"]
            },
            "vector_config": {
                "vector_size": 768,
                "distance_metric": "cosine",
                "use_qdrant": False
            }
        }
    )
    
    # Generate HTML report
    print("📄 Generating HTML report with project summary...")
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
    html_filename = f"project_summary_test_{scan_id}.html"
    html_path = os.path.join(scan_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"💾 Project summary report saved: {html_path}")
    
    # Analyze the report content
    print("\n📋 Analyzing report content...")
    
    # Check for project summary section
    project_summary_checks = [
        ("Project Summary Heading", "Project Summary" in html_report),
        ("Project Summary Section", "project-summary-section" in html_report),
        ("Project Description", "project-description" in html_report),
        ("Project Details Grid", "project-details-grid" in html_report),
        ("Technologies Section", "Technologies" in html_report),
        ("File Types Section", "File Types" in html_report),
        ("Key Dependencies Section", "Key Dependencies" in html_report),
        ("Analysis Stats Section", "Analysis Stats" in html_report),
        ("Tech Tags", "tech-tags" in html_report),
        ("File Type Tags", "file-type-tags" in html_report),
        ("Dependency Tags", "dependency-tags" in html_report),
        ("Stats Info", "stats-info" in html_report)
    ]
    
    print("📋 Project Summary Section Verification:")
    for check_name, found in project_summary_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Check for hard gates section
    hard_gates_checks = [
        ("Hard Gates Notice", "Hard Gates Assessment - Primary Focus" in html_report),
        ("Hard Gate Badge", "HARD GATE" in html_report),
        ("Executive Summary", "Executive Summary" in html_report),
        ("Gate Categories", "Auditability" in html_report or "Error Handling" in html_report)
    ]
    
    print("\n📋 Hard Gates Section Verification:")
    for check_name, found in hard_gates_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Check section ordering
    print("\n📋 Section Ordering Analysis:")
    
    # Find positions of key sections
    lines = html_report.split('\n')
    executive_summary_pos = -1
    project_summary_pos = -1
    hard_gates_pos = -1
    
    for i, line in enumerate(lines):
        if "Executive Summary" in line:
            executive_summary_pos = i
        elif "Project Summary" in line:
            project_summary_pos = i
        elif "Hard Gates Assessment - Primary Focus" in line:
            hard_gates_pos = i
    
    print(f"   📊 Executive Summary position: {executive_summary_pos}")
    print(f"   📊 Project Summary position: {project_summary_pos}")
    print(f"   📊 Hard Gates Notice position: {hard_gates_pos}")
    
    if executive_summary_pos >= 0 and project_summary_pos >= 0:
        if project_summary_pos > executive_summary_pos:
            print("   ✅ Project Summary appears after Executive Summary")
        else:
            print("   ⚠️ Project Summary appears before Executive Summary")
    
    # Check for CSS styles
    css_checks = [
        ("Project Summary CSS", ".project-summary-section" in html_report),
        ("Tech Tags CSS", ".tech-tag" in html_report),
        ("File Type Tags CSS", ".file-type-tag" in html_report),
        ("Dependency Tags CSS", ".dependency-tag" in html_report),
        ("Detail Cards CSS", ".detail-card" in html_report),
        ("Stats Info CSS", ".stats-info" in html_report)
    ]
    
    print("\n📋 CSS Styling Verification:")
    for check_name, found in css_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Check for fallback content
    fallback_checks = [
        ("No Data Messages", "No technologies detected" in html_report or "No file types detected" in html_report or "No dependencies detected" in html_report),
        ("Fallback Summary", "Project analysis for" in html_report),
        ("Hard Gates Reference", "hard gates" in html_report.lower()),
        ("Compliance Reference", "compliance" in html_report.lower())
    ]
    
    print("\n📋 Fallback Content Verification:")
    for check_name, found in fallback_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    print(f"\n🎉 Project Summary Test Complete!")
    print(f"\n📖 Project summary report is available at:")
    print(f"   🌐 HTML: file://{os.path.abspath(html_path)}")
    print(f"   📁 Directory: {scan_dir}")
    
    return scan_id, html_path


if __name__ == "__main__":
    test_project_summary()
