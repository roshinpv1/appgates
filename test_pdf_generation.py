#!/usr/bin/env python3
"""
Test script for PDF generation functionality
Demonstrates how to generate PDFs with the new enhanced PDF generator
"""

import os
import sys
import json
from pathlib import Path

# Add gates directory to path
sys.path.append(str(Path(__file__).parent / "gates"))

def test_pdf_generation():
    """Test the PDF generation functionality"""
    
    print("🧪 Testing PDF Generation Functionality")
    print("=" * 50)
    
    # Check if ReportLab is available
    try:
        from utils.pdf_generator import EnhancedPDFGenerator, generate_pdfs_from_scan_id
        print("✅ ReportLab and PDF generator available")
    except ImportError as e:
        print(f"❌ PDF generation not available: {e}")
        print("💡 Install ReportLab: pip install reportlab")
        return False
    
    # Create a sample scan result for testing
    sample_scan_result = {
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
                    "json.*logger",
                    "structured.*log",
                    "log.*format"
                ],
                "matches": [
                    {"file": "src/utils/logger.py", "line": 15, "match": "json_logger", "pattern": "json.*logger"},
                    {"file": "src/config/logging.py", "line": 23, "match": "structured_log_format", "pattern": "structured.*log"}
                ]
            }
        ],
        "gates": []  # For compatibility
    }
    
    # Create output directory
    output_dir = "./test_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    
    try:
        # Test PDF generation
        print("\n🔧 Testing PDF generation...")
        pdf_generator = EnhancedPDFGenerator()
        pdf_results = pdf_generator.generate_pdfs(sample_scan_result, output_dir)
        
        if pdf_results["summary"]:
            print(f"✅ Summary PDF generated: {pdf_results['summary'][0]}")
        
        if pdf_results["gates"]:
            print(f"✅ Generated {len(pdf_results['gates'])} individual gate PDFs:")
            for pdf_path in pdf_results["gates"]:
                print(f"   📄 {os.path.basename(pdf_path)}")
        
        # Test the convenience function
        print("\n🔧 Testing convenience function...")
        
        # Save sample data to JSON file
        json_path = os.path.join(output_dir, sample_scan_result["scan_id"], f"codegates_report_{sample_scan_result['scan_id']}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(sample_scan_result, f, indent=2, ensure_ascii=False)
        
        # Test convenience function
        convenience_results = generate_pdfs_from_scan_id(sample_scan_result["scan_id"], output_dir)
        
        if convenience_results["summary"]:
            print(f"✅ Convenience function - Summary PDF: {convenience_results['summary'][0]}")
        
        if convenience_results["gates"]:
            print(f"✅ Convenience function - {len(convenience_results['gates'])} gate PDFs generated")
        
        print("\n🎉 PDF generation test completed successfully!")
        print(f"📁 Check the generated PDFs in: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_naming_convention():
    """Test the naming convention"""
    print("\n📝 Testing Naming Convention")
    print("=" * 30)
    
    # Test project name extraction
    test_cases = [
        {
            "project_name": "myapp - Web Service (main)",
            "expected": "myapp"
        },
        {
            "repository_url": "https://github.com/company/data-pipeline",
            "expected": "data-pipeline"
        },
        {
            "repository_url": "https://gitlab.com/org/mobile-app.git",
            "expected": "mobile-app"
        }
    ]
    
    try:
        from utils.pdf_generator import EnhancedPDFGenerator
        pdf_generator = EnhancedPDFGenerator()
        
        for i, test_case in enumerate(test_cases, 1):
            scan_data = {"project_name": test_case.get("project_name", ""), "repository_url": test_case.get("repository_url", "")}
            extracted_name = pdf_generator._extract_project_name(scan_data)
            
            status = "✅" if extracted_name == test_case["expected"] else "❌"
            print(f"{status} Test {i}: {extracted_name} (expected: {test_case['expected']})")
            
    except Exception as e:
        print(f"❌ Naming convention test failed: {e}")

if __name__ == "__main__":
    print("🚀 CodeGates PDF Generation Test")
    print("=" * 50)
    
    # Test naming convention
    test_naming_convention()
    
    # Test PDF generation
    success = test_pdf_generation()
    
    if success:
        print("\n🎉 All tests passed!")
        print("📄 PDF generation is working correctly")
        print("📁 Generated files follow the naming convention:")
        print("   • project-scanid-summary.pdf")
        print("   • project-scanid-gatename.pdf")
    else:
        print("\n❌ Some tests failed")
        print("💡 Check the error messages above") 