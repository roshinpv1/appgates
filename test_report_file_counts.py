#!/usr/bin/env python3
"""
Test script to check file counts in report generation
"""

import sys
import json
from pathlib import Path

# Add the gates directory to the path
sys.path.insert(0, 'gates')

def test_report_file_counts():
    """Test file counts in report generation"""
    print("🔍 Testing Report File Counts")
    print("=" * 50)
    
    try:
        from utils.file_scanner import scan_directory
        from nodes import GenerateReportNode
        
        # Test with a sample repository path
        test_repo_path = "/Users/roshinpv/Downloads/spring-petclinic-main"  # Adjust this path
        
        if not Path(test_repo_path).exists():
            print(f"❌ Test repository not found: {test_repo_path}")
            print("Please update the test_repo_path variable to point to a valid repository")
            return False
        
        print(f"📁 Scanning repository: {test_repo_path}")
        
        # Scan the repository
        metadata = scan_directory(test_repo_path, max_files=5000)
        
        print(f"\n📊 Original Metadata:")
        print(f"   Total Files: {metadata.get('total_files', 0)}")
        print(f"   Total Lines: {metadata.get('total_lines', 0)}")
        print(f"   File List Length: {len(metadata.get('file_list', []))}")
        
        # Create mock validation results
        mock_validation = {
            "gate_results": [
                {
                    "gate": "STRUCTURED_LOGS",
                    "display_name": "Structured Logs",
                    "status": "PASS",
                    "score": 85.0,
                    "details": ["Test details"],
                    "category": "Auditability",
                    "priority": "high",
                    "description": "Test description",
                    "patterns_used": 5,
                    "matches_found": 10,
                    "recommendations": ["Test recommendation"],
                    "pattern_description": "Test pattern description",
                    "pattern_significance": "Test significance",
                    "expected_coverage": {
                        "percentage": 25,
                        "reasoning": "Test reasoning",
                        "confidence": "high"
                    },
                    "total_files": metadata.get("total_files", 1),
                    "relevant_files": 25,
                    "validation_sources": {
                        "llm_patterns": {"count": 3, "matches": 5, "source": "llm_generated"},
                        "static_patterns": {"count": 2, "matches": 5, "source": "static_library"},
                        "combined_confidence": "high",
                        "unique_matches": 10,
                        "overlap_matches": 0
                    }
                }
            ],
            "overall_score": 85.0,
            "hybrid_stats": {
                "total_llm_patterns": 3,
                "total_static_patterns": 2,
                "total_llm_matches": 5,
                "total_static_matches": 5,
                "total_unique_matches": 10,
                "total_overlap_matches": 0,
                "coverage_improvement": 0.0,
                "confidence_distribution": {"high": 1, "medium": 0, "low": 0}
            }
        }
        
        # Create mock request
        mock_request = {
            "repository_url": "https://github.com/test/repo",
            "branch": "main",
            "scan_id": "test-scan-123",
            "output_dir": "./test_reports",
            "report_format": "json"
        }
        
        # Create mock LLM info
        mock_llm_info = {
            "source": "test",
            "model": "test-model"
        }
        
        # Create params for report generation
        params = {
            "validation_results": mock_validation,
            "metadata": metadata,
            "request": mock_request,
            "llm_info": mock_llm_info,
            "scan_id": "test-scan-123"
        }
        
        # Create GenerateReportNode and test JSON report generation
        report_node = GenerateReportNode()
        json_report = report_node._generate_json_report(params)
        
        print(f"\n📋 JSON Report File Counts:")
        print(f"   Scan Metadata Total Files: {json_report['scan_metadata']['total_files']}")
        print(f"   Scan Metadata Total Lines: {json_report['scan_metadata']['total_lines']}")
        
        # Check gate results
        for gate in json_report['gates']:
            print(f"\n   Gate: {gate['name']}")
            print(f"     Total Files: {gate['actual_coverage']['total_files']}")
            print(f"     Relevant Files: {gate['actual_coverage']['relevant_files']}")
            print(f"     Files with Matches: {gate['actual_coverage']['files_with_matches']}")
            print(f"     Technology Filtered: {gate['actual_coverage']['technology_filtered']}")
        
        # Check for discrepancies
        original_total = metadata.get("total_files", 0)
        scan_metadata_total = json_report['scan_metadata']['total_files']
        
        print(f"\n🔍 File Count Verification:")
        print(f"   Original Metadata: {original_total}")
        print(f"   Scan Metadata: {scan_metadata_total}")
        
        if original_total != scan_metadata_total:
            print(f"   ⚠️ DISCREPANCY FOUND: {original_total} vs {scan_metadata_total}")
        else:
            print(f"   ✅ File counts match")
        
        # Check if any gate shows different file counts
        for gate in json_report['gates']:
            gate_total = gate['actual_coverage']['total_files']
            if gate_total != original_total:
                print(f"   ⚠️ Gate {gate['name']} shows different total: {gate_total} vs {original_total}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_report_file_counts()
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed") 