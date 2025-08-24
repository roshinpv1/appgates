#!/usr/bin/env python3
"""
Test script to verify title generation logic
"""

from services.html_report_service import HTMLReportService
from models.scan_models import ScanResult, GateResult, GateStatus
from datetime import datetime

def test_title_generation():
    """Test the title generation logic"""
    
    html_service = HTMLReportService()
    
    # Test cases
    test_cases = [
        {
            "name": "GitHub URL with app pattern",
            "repo_url": "https://github.com/company/app-myapp",
            "branch": "main",
            "expected_app_id": "myapp",
            "expected_project": "company/app-myapp"
        },
        {
            "name": "GitHub URL without app pattern",
            "repo_url": "https://github.com/octocat/Hello-World",
            "branch": "main",
            "expected_app_id": "APP ID",
            "expected_project": "octocat/Hello-World"
        },
        {
            "name": "GitHub URL with .git suffix",
            "repo_url": "https://github.com/company/app-test.git",
            "branch": "develop",
            "expected_app_id": "test",
            "expected_project": "company/app-test"
        },
        {
            "name": "Simple repository name",
            "repo_url": "https://github.com/user/repo",
            "branch": "master",
            "expected_app_id": "APP ID",
            "expected_project": "user/repo"
        }
    ]
    
    print("🧪 Testing Title Generation Logic")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   URL: {test_case['repo_url']}")
        print(f"   Branch: {test_case['branch']}")
        
        # Test App ID extraction
        app_id = html_service._extract_app_id(test_case['repo_url'])
        print(f"   Extracted App ID: '{app_id}' (Expected: '{test_case['expected_app_id']}')")
        
        # Test Project name extraction
        project_name = html_service._extract_project_name(test_case['repo_url'])
        print(f"   Extracted Project: '{project_name}' (Expected: '{test_case['expected_project']}')")
        
        # Test full display name
        display_name = f"{app_id} - {project_name} ({test_case['branch']})"
        print(f"   Full Display Name: '{display_name}'")
        
        # Check if results match expectations
        app_id_match = app_id == test_case['expected_app_id']
        project_match = project_name == test_case['expected_project']
        
        if app_id_match and project_match:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            if not app_id_match:
                print(f"      App ID mismatch: got '{app_id}', expected '{test_case['expected_app_id']}'")
            if not project_match:
                print(f"      Project mismatch: got '{project_name}', expected '{test_case['expected_project']}'")
    
    print("\n🎉 Title Generation Test Complete!")

def test_html_report_generation():
    """Test HTML report generation with mock data"""
    
    print("\n🧪 Testing HTML Report Generation")
    print("=" * 50)
    
    html_service = HTMLReportService()
    
    # Create mock scan result
    gate_results = [
        GateResult(
            gate_id="1.1",
            gate_name="Logs Searchable/Available",
            status=GateStatus.PASS,
            expected_count=5,
            actual_count=5,
            threshold=3,
            patterns_found=["logging.config", "log4j", "winston"],
            recommendations=["Good implementation of logging"],
            confidence_score=0.9,
            reasoning="Found 5 implementations, meeting expected 5"
        ),
        GateResult(
            gate_id="1.3",
            gate_name="Audit Trail",
            status=GateStatus.FAIL,
            expected_count=3,
            actual_count=1,
            threshold=2,
            patterns_found=["audit"],
            recommendations=["Implement audit trail"],
            confidence_score=0.3,
            reasoning="Found 1 implementations, below expected 3"
        )
    ]
    
    scan_result = ScanResult(
        scan_id="test_scan_123",
        repo_url="https://github.com/company/app-myapp",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=2,
        passed_gates=1,
        failed_gates=1,
        partial_gates=0,
        skipped_gates=0,
        gate_results=gate_results,
        recommendations=[],
        risk_score=0.5,
        scan_duration=10.5,
        metadata={}
    )
    
    # Generate HTML report
    html_report = html_service.generate_html_report(scan_result)
    
    print(f"✅ HTML Report Generated Successfully!")
    print(f"   Content Length: {len(html_report)} characters")
    
    # Check if title is correct
    if "myapp - company/app-myapp (main)" in html_report:
        print("   ✅ Title Generation: PASS")
    else:
        print("   ❌ Title Generation: FAIL")
        print("   Expected: 'myapp - company/app-myapp (main)'")
        print("   Actual title not found in HTML")
    
    # Check if gates are displayed
    if "Logs Searchable/Available" in html_report and "Audit Trail" in html_report:
        print("   ✅ Gate Display: PASS")
    else:
        print("   ❌ Gate Display: FAIL")
    
    # Save HTML report for inspection
    with open("test_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print("   📄 Report saved to: test_report.html")
    print("   🌐 Open in browser: file://$(pwd)/test_report.html")

if __name__ == "__main__":
    test_title_generation()
    test_html_report_generation()
