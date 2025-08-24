#!/usr/bin/env python3
"""
Comprehensive test to verify full scan process works without JSON serialization errors
"""

import os
import json
import time
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus
from services.html_report_service import HTMLReportService
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService


def test_full_scan_fix():
    """Test full scan process with JSON serialization fix"""
    
    print("🧪 Testing Full Scan Process with JSON Serialization Fix")
    print("=" * 60)
    
    # Initialize services
    config = {
        "vector_size": 768,
        "distance_metric": "cosine",
        "use_qdrant": False,
        "provider": "local",
        "model": "text-embedding-nomic-embed-text-v1.5-embedding",
        "base_url": "http://localhost:1234"
    }
    
    vector_service = VectorService(config)
    embedding_service = EmbeddingService(config)
    html_service = HTMLReportService()
    
    # Create test scan ID
    scan_id = f"full_scan_test_{int(datetime.now().timestamp())}"
    
    # Create mock vector data
    print("📊 Creating mock vector data...")
    
    # Create collections
    main_collection = f"repo_{scan_id}"
    cd_collection = f"repo_{scan_id}_cd"
    
    vector_service.create_collection(main_collection)
    vector_service.create_collection(cd_collection)
    
    # Add sample files
    sample_files = [
        {
            "content": "import django from django.http import HttpResponse def index(request): return HttpResponse('Hello World')",
            "file_path": "views.py"
        },
        {
            "content": "const express = require('express'); const app = express(); app.get('/', (req, res) => { res.send('Hello World'); });",
            "file_path": "server.js"
        },
        {
            "content": "FROM python:3.9 WORKDIR /app COPY requirements.txt . RUN pip install -r requirements.txt",
            "file_path": "Dockerfile"
        }
    ]
    
    for i, file_data in enumerate(sample_files):
        embedding = embedding_service.embed_single(file_data["content"])
        if embedding:
            vector_service.upsert_vectors(
                collection_name=main_collection,
                vectors=[{
                    "id": f"file_{i}",
                    "vector": embedding,
                    "payload": {
                        "content": file_data["content"],
                        "file_path": file_data["file_path"]
                    }
                }]
            )
    
    # Add CD files
    cd_files = [
        {
            "content": "apiVersion: apps/v1 kind: Deployment metadata: name: my-app",
            "file_path": "k8s/deployment.yaml"
        }
    ]
    
    for i, file_data in enumerate(cd_files):
        embedding = embedding_service.embed_single(file_data["content"])
        if embedding:
            vector_service.upsert_vectors(
                collection_name=cd_collection,
                vectors=[{
                    "id": f"cd_file_{i}",
                    "vector": embedding,
                    "payload": {
                        "content": file_data["content"],
                        "file_path": file_data["file_path"]
                    }
                }]
            )
    
    print(f"✅ Added vectors to collections: {main_collection}, {cd_collection}")
    
    # Generate project summary
    print("\n🔍 Generating project summary...")
    project_info = vector_service.generate_project_summary(
        repo_url="https://github.com/example/full-scan-test",
        scan_id=scan_id
    )
    
    print(f"📋 Project Summary:")
    print(f"   Technologies: {project_info.get('technologies', [])}")
    print(f"   File Types: {project_info.get('file_types', [])}")
    print(f"   Dependencies: {project_info.get('dependencies', [])}")
    print(f"   Has CD Repo: {project_info.get('has_cd_repo', False)}")
    print(f"   Files Analyzed: {project_info.get('total_files_analyzed', 0)}")
    
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
        ),
        GateResult(
            gate_id="1.5",
            gate_name="Timeouts",
            status=GateStatus.PARTIAL,
            expected_count=1,
            actual_count=1,
            threshold=1,
            patterns_found=["timeout configuration found"],
            recommendations=["Enhance timeout handling"],
            confidence_score=0.7,
            reasoning="Basic timeout configuration exists but needs improvement"
        )
    ]
    
    # Create scan result
    scan_result = ScanResult(
        scan_id=scan_id,
        repo_url="https://github.com/example/full-scan-test",
        branch="main",
        scan_timestamp=datetime.now(),
        total_gates=len(gate_results),
        passed_gates=len([g for g in gate_results if g.status == GateStatus.PASS]),
        failed_gates=len([g for g in gate_results if g.status == GateStatus.FAIL]),
        partial_gates=len([g for g in gate_results if g.status == GateStatus.PARTIAL]),
        skipped_gates=len([g for g in gate_results if g.status == GateStatus.SKIPPED]),
        gate_results=gate_results,
        recommendations=[
            "Implement audit trail logging",
            "Enhance timeout handling",
            "Add centralized logging"
        ],
        risk_score=0.4,
        scan_duration=25.0,
        metadata={
            "main_repo": {
                "repo_url": "https://github.com/example/full-scan-test",
                "branch": "main",
                "total_files": len(sample_files),
                "total_lines": 500,
                "languages": ["Python", "JavaScript", "YAML"],
                "build_files": ["requirements.txt", "package.json"],
                "config_files": ["Dockerfile", "docker-compose.yml"]
            },
            "vector_config": config,
            "project_summary": project_info
        }
    )
    
    # Generate HTML report
    print("\n📄 Generating HTML report...")
    html_report = html_service.generate_html_report(scan_result)
    print(f"✅ HTML report generated: {len(html_report)} characters")
    
    # Test JSON serialization
    print("\n📋 Testing JSON serialization...")
    try:
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
        
        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
        print(f"✅ JSON serialization successful: {len(json_string)} characters")
        
        # Test deserialization
        parsed_data = json.loads(json_string)
        print("✅ JSON deserialization successful!")
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False
    
    # Save reports
    print("\n💾 Saving reports...")
    reports_dir = "reports"
    scan_dir = os.path.join(reports_dir, scan_id)
    os.makedirs(scan_dir, exist_ok=True)
    
    # Save HTML report
    html_filename = f"full_scan_test_{scan_id}.html"
    html_path = os.path.join(scan_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    # Save JSON report
    json_filename = f"full_scan_test_{scan_id}.json"
    json_path = os.path.join(scan_dir, json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Reports saved:")
    print(f"   📄 HTML: {html_path}")
    print(f"   📋 JSON: {json_path}")
    
    # Verify report content
    print("\n📋 Report Content Verification:")
    
    # Check HTML report
    html_checks = [
        ("Project Summary Section", "project-summary-section" in html_report),
        ("Hard Gates Notice", "Hard Gates Assessment" in html_report),
        ("Gate Results", "gate-results" in html_report),
        ("Technologies", any(tech in html_report for tech in ["python", "javascript", "docker"])),
        ("File Types", any(ft in html_report for ft in ["py", "js", "yaml"])),
        ("CD Repository", "CD repository" in html_report or "Continuous Deployment" in html_report)
    ]
    
    for check_name, found in html_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Check JSON report
    json_checks = [
        ("Scan ID", parsed_data.get("scan_id") == scan_id),
        ("Repo URL", parsed_data.get("repo_url") == scan_result.repo_url),
        ("Total Gates", parsed_data.get("total_gates") == len(gate_results)),
        ("Recommendations", len(parsed_data.get("recommendations", [])) == 3),
        ("Gate Results", len(parsed_data.get("gate_results", [])) == 3),
        ("Project Summary", "project_summary" in parsed_data.get("metadata", {}))
    ]
    
    for check_name, found in json_checks:
        status = "✅" if found else "❌"
        print(f"   {status} {check_name}: {'Found' if found else 'Not found'}")
    
    # Clean up
    try:
        vector_service.delete_collection(main_collection)
        vector_service.delete_collection(cd_collection)
        print(f"\n🧹 Cleaned up vector collections")
    except:
        pass
    
    print(f"\n🎉 Full Scan Test Complete!")
    print(f"\n📖 Full scan test reports are available at:")
    print(f"   🌐 HTML: file://{os.path.abspath(html_path)}")
    print(f"   📋 JSON: file://{os.path.abspath(json_path)}")
    print(f"   📁 Directory: {scan_dir}")
    
    return True


if __name__ == "__main__":
    test_full_scan_fix()
