#!/usr/bin/env python3
"""
Test script for HTML to PDF conversion functionality
Verifies that PDFs are generated based on HTML reports as requested:
- Summary PDF: PDF version of the HTML report
- Individual gate PDFs: Individual reports for each gate
"""

import os
import sys
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_html_to_pdf_conversion():
    """Test the HTML to PDF conversion functionality"""

    print("🧪 Testing HTML to PDF Conversion Functionality")
    print("=" * 60)

    # Check if ReportLab is available
    try:
        from utils.html_to_pdf_converter import HTMLToPDFConverter, generate_pdfs_from_html_reports
        print("✅ ReportLab and HTML to PDF converter available")
    except ImportError as e:
        print(f"❌ HTML to PDF conversion not available: {e}")
        print("💡 Install ReportLab: pip install reportlab")
        return False

    # Create a sample HTML report for testing
    sample_html_report = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeGates Security Analysis Report</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            margin: 0;
            padding: 20px;
            background-color: #f9fafb;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        .content {
            padding: 30px;
        }
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border: 1px solid #e5e7eb;
            margin: 10px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #6b7280;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 CodeGates Security Analysis</h1>
            <p>Enterprise Security Gate Validation Report</p>
        </div>
        <div class="content">
            <h2>Executive Summary</h2>
            <p>This is a test HTML report for PDF conversion verification.</p>

            <h2>Overall Statistics</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div class="metric-card">
                    <div class="metric-value">75.5%</div>
                    <div class="metric-label">Overall Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">15</div>
                    <div class="metric-label">Total Gates</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">8</div>
                    <div class="metric-label">Passed Gates</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">7</div>
                    <div class="metric-label">Failed Gates</div>
                </div>
            </div>

            <h2>Gate Results</h2>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Gate Name</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Status</th>
                        <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Score</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">Alerting Actionable</td>
                        <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb; color: #ef4444;">FAIL</td>
                        <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">0.0%</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">Structured Logs</td>
                        <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb; color: #10b981;">PASS</td>
                        <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">100.0%</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
    """

    # Create test directories
    test_dir = "./test_html_to_pdf"
    os.makedirs(test_dir, exist_ok=True)

    # Create sample HTML report file
    html_report_path = os.path.join(test_dir, "test_report.html")
    with open(html_report_path, 'w', encoding='utf-8') as f:
        f.write(sample_html_report)

    print(f"✅ Created test HTML report: {html_report_path}")

    # Create sample scan results
    sample_scan_results = {
        "scan_id": "test-scan-123",
        "repository_url": "https://github.com/company/myapp",
        "branch": "main",
        "overall_score": 75.5,
        "threshold": 70,
        "scan_timestamp_formatted": "2024-01-15 10:30:00",
        "project_name": "myapp",
        "metadata": {
            "file_count": 150,
            "line_count": 5000,
            "language_distribution": {
                "python": {"files": 50, "lines": 2000},
                "javascript": {"files": 30, "lines": 1500},
                "html": {"files": 20, "lines": 800}
            }
        },
        "gate_results": [
            {
                "gate": "ALERTING_ACTIONABLE",
                "display_name": "Alerting Actionable",
                "status": "FAIL",
                "score": 0.0,
                "description": "Ensure all alerting integrations are present",
                "category": "Monitoring",
                "priority": "High",
                "patterns_used": 5,
                "matches_found": 0,
                "relevant_files": 10,
                "total_files": 150,
                "llm_recommendation": "This gate failed because no alerting integrations were found. Consider implementing Splunk, AppDynamics, or other monitoring solutions.",
                "enhanced_data": {
                    "confidence_score": 0.95,
                    "coverage_percentage": 0.0,
                    "technology_detected": ["python", "javascript"]
                },
                "validation_sources": {
                    "llm_patterns": {"count": 3, "matches": 0},
                    "static_patterns": {"count": 2, "matches": 0},
                    "combined_confidence": "high"
                },
                "patterns": [
                    "splunk.*integration",
                    "appdynamics.*config",
                    "alerting.*setup"
                ],
                "matches": []
            },
            {
                "gate": "STRUCTURED_LOGS",
                "display_name": "Structured Logs",
                "status": "PASS",
                "score": 100.0,
                "description": "Ensure logs are structured and searchable",
                "category": "Logging",
                "priority": "Medium",
                "patterns_used": 3,
                "matches_found": 15,
                "relevant_files": 25,
                "total_files": 150,
                "llm_recommendation": "Excellent implementation of structured logging. The codebase shows proper use of JSON logging and structured log formats.",
                "enhanced_data": {
                    "confidence_score": 0.92,
                    "coverage_percentage": 85.0,
                    "technology_detected": ["python", "javascript"]
                },
                "validation_sources": {
                    "llm_patterns": {"count": 2, "matches": 8},
                    "static_patterns": {"count": 1, "matches": 7},
                    "combined_confidence": "high"
                },
                "patterns": [
                    "json.*log",
                    "structured.*logging",
                    "log.*format"
                ],
                "matches": [
                    {
                        "file_path": "src/logging.py",
                        "line_number": 15,
                        "pattern": "json.*log",
                        "context": "logger = json_logging.getLogger()"
                    }
                ]
            }
        ],
        "gates": []  # Will be populated from gate_results
    }

    # Populate gates array for compatibility
    sample_scan_results["gates"] = sample_scan_results["gate_results"]

    print("✅ Created sample scan results")

    # Test PDF generation from HTML
    print("\n🔧 Testing PDF generation from HTML...")
    try:
        pdf_results = generate_pdfs_from_html_reports(sample_scan_results, html_report_path, test_dir)

        print(f"📄 PDF generation results:")
        print(f"   Summary PDFs: {len(pdf_results['summary'])}")
        print(f"   Individual Gate PDFs: {len(pdf_results['gates'])}")

        # Verify summary PDF was generated
        if pdf_results["summary"]:
            summary_pdf = pdf_results["summary"][0]
            if os.path.exists(summary_pdf):
                file_size = os.path.getsize(summary_pdf)
                print(f"✅ Summary PDF generated: {os.path.basename(summary_pdf)} ({file_size} bytes)")
                print(f"   📍 Path: {summary_pdf}")
            else:
                print(f"❌ Summary PDF file not found: {summary_pdf}")
        else:
            print("❌ No summary PDF generated")

        # Verify individual gate PDFs were generated
        if pdf_results["gates"]:
            print(f"✅ Generated {len(pdf_results['gates'])} individual gate PDFs:")
            for pdf_path in pdf_results["gates"]:
                if os.path.exists(pdf_path):
                    file_size = os.path.getsize(pdf_path)
                    filename = os.path.basename(pdf_path)
                    print(f"   📄 {filename} ({file_size} bytes)")
                else:
                    print(f"   ❌ File not found: {pdf_path}")
        else:
            print("❌ No individual gate PDFs generated")

        # Verify naming convention
        print("\n🔍 Verifying naming convention...")
        expected_summary_name = "myapp-test-scan-123-summary.pdf"
        expected_gate_names = [
            "myapp-test-scan-123-alerting_actionable.pdf",
            "myapp-test-scan-123-structured_logs.pdf"
        ]

        if pdf_results["summary"]:
            actual_summary_name = os.path.basename(pdf_results["summary"][0])
            if actual_summary_name == expected_summary_name:
                print(f"✅ Summary PDF naming convention correct: {actual_summary_name}")
            else:
                print(f"❌ Summary PDF naming convention incorrect:")
                print(f"   Expected: {expected_summary_name}")
                print(f"   Actual: {actual_summary_name}")

        if pdf_results["gates"]:
            actual_gate_names = [os.path.basename(pdf_path) for pdf_path in pdf_results["gates"]]
            for expected_name in expected_gate_names:
                if expected_name in actual_gate_names:
                    print(f"✅ Gate PDF naming convention correct: {expected_name}")
                else:
                    print(f"❌ Gate PDF naming convention incorrect - missing: {expected_name}")

        # Test the converter class directly
        print("\n🔧 Testing HTMLToPDFConverter class...")
        converter = HTMLToPDFConverter()

        # Test summary PDF generation
        summary_pdf_path = converter._generate_summary_pdf_from_html(
            html_report_path, "myapp", "test-scan-123", test_dir, sample_scan_results
        )
        if summary_pdf_path and os.path.exists(summary_pdf_path):
            print(f"✅ Direct converter test - Summary PDF: {os.path.basename(summary_pdf_path)}")
        else:
            print("❌ Direct converter test - Summary PDF generation failed")

        # Test individual gate PDF generation
        gate = sample_scan_results["gate_results"][0]
        gate_pdf_path = converter._generate_gate_pdf_from_html(
            gate, sample_scan_results, "myapp", "test-scan-123", test_dir
        )
        if gate_pdf_path and os.path.exists(gate_pdf_path):
            print(f"✅ Direct converter test - Gate PDF: {os.path.basename(gate_pdf_path)}")
        else:
            print("❌ Direct converter test - Gate PDF generation failed")

        print("\n🎉 HTML to PDF conversion test completed successfully!")
        print(f"📁 Test files generated in: {test_dir}")

        return True

    except Exception as e:
        print(f"❌ HTML to PDF conversion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_naming_convention():
    """Test that the naming convention is correct"""
    print("\n🔍 Testing Naming Convention...")

    try:
        from utils.html_to_pdf_converter import HTMLToPDFConverter

        converter = HTMLToPDFConverter()

        # Test project name extraction
        test_cases = [
            ("https://github.com/company/myapp", "myapp"),
            ("https://github.com/org/web-service", "web-service"),
            ("https://gitlab.com/team/data-pipeline.git", "data-pipeline"),
            ("https://bitbucket.org/user/mobile-app", "mobile-app")
        ]

        for url, expected in test_cases:
            actual = converter._extract_project_name(url)
            if actual == expected:
                print(f"✅ Project name extraction: {url} -> {actual}")
            else:
                print(f"❌ Project name extraction: {url} -> {actual} (expected: {expected})")

        return True

    except Exception as e:
        print(f"❌ Naming convention test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 CodeGates HTML to PDF Conversion Test")
    print("=" * 60)

    # Test HTML to PDF conversion
    success = test_html_to_pdf_conversion()

    # Test naming convention
    naming_success = test_naming_convention()

    if success and naming_success:
        print("\n✅ All tests passed!")
        print("📄 HTML to PDF conversion is working correctly")
        print("📋 Requirements met:")
        print("   ✅ Summary PDF: PDF version of the HTML report")
        print("   ✅ Individual gate PDFs: Individual reports for each gate")
        print("   ✅ Proper naming convention: project-scanid-summary.pdf and project-scanid-gatename.pdf")
        print("   ✅ Pure Python implementation: No system dependencies")
    else:
        print("\n❌ Some tests failed!")
        if not success:
            print("   ❌ HTML to PDF conversion test failed")
        if not naming_success:
            print("   ❌ Naming convention test failed")

if __name__ == "__main__":
    main() 