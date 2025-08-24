#!/usr/bin/env python3
"""
Integration test for project summary functionality with actual scan data
"""

import os
import json
import time
from datetime import datetime
from models.scan_models import ScanResult, GateResult, GateStatus
from services.html_report_service import HTMLReportService
from services.vector_service import VectorService
from services.embedding_service import EmbeddingService


def test_project_summary_integration():
    """Test project summary with actual vector data"""
    
    print("🧪 Testing Project Summary Integration with Vector Data")
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
    
    # Create test scan ID
    scan_id = f"integration_test_{int(datetime.now().timestamp())}"
    
    # Create mock vector data for testing
    print("📊 Creating mock vector data...")
    
    # Sample project files with technology information
    project_files = [
        {
            "content": "import django from django.http import HttpResponse def index(request): return HttpResponse('Hello World')",
            "file_path": "views.py",
            "metadata": {"language": "python", "framework": "django"}
        },
        {
            "content": "import flask from flask import Flask app = Flask(__name__) @app.route('/') def hello(): return 'Hello World'",
            "file_path": "app.py",
            "metadata": {"language": "python", "framework": "flask"}
        },
        {
            "content": "const express = require('express'); const app = express(); app.get('/', (req, res) => { res.send('Hello World'); });",
            "file_path": "server.js",
            "metadata": {"language": "javascript", "framework": "express"}
        },
        {
            "content": "import React from 'react'; function App() { return <div>Hello World</div>; } export default App;",
            "file_path": "App.js",
            "metadata": {"language": "javascript", "framework": "react"}
        },
        {
            "content": "FROM python:3.9 WORKDIR /app COPY requirements.txt . RUN pip install -r requirements.txt",
            "file_path": "Dockerfile",
            "metadata": {"language": "docker", "framework": "docker"}
        },
        {
            "content": "django==4.2.0 flask==2.3.0 requests==2.31.0 pytest==7.4.0",
            "file_path": "requirements.txt",
            "metadata": {"language": "python", "dependencies": ["django", "flask", "requests", "pytest"]}
        },
        {
            "content": '{"name": "my-app", "dependencies": {"express": "^4.18.0", "react": "^18.0.0", "axios": "^1.4.0"}}',
            "file_path": "package.json",
            "metadata": {"language": "javascript", "dependencies": ["express", "react", "axios"]}
        }
    ]
    
    # Create collections and add vectors
    main_collection = f"repo_{scan_id}"
    cd_collection = f"repo_{scan_id}_cd"
    
    # Create collections
    vector_service.create_collection(main_collection)
    vector_service.create_collection(cd_collection)
    
    # Add vectors to main collection
    print(f"📁 Adding {len(project_files)} files to vector database...")
    
    for i, file_data in enumerate(project_files):
        # Generate embedding for file content
        embedding = embedding_service.embed_single(file_data["content"])
        
        if embedding:
            # Add to vector store
            vector_service.upsert_vectors(
                collection_name=main_collection,
                vectors=[{
                    "id": f"file_{i}",
                    "vector": embedding,
                    "payload": {
                        "content": file_data["content"],
                        "file_path": file_data["file_path"],
                        "metadata": file_data["metadata"]
                    }
                }]
            )
    
    # Add some CD repository files
    cd_files = [
        {
            "content": "apiVersion: apps/v1 kind: Deployment metadata: name: my-app spec: replicas: 3",
            "file_path": "k8s/deployment.yaml",
            "metadata": {"language": "yaml", "framework": "kubernetes"}
        },
        {
            "content": "version: '3.8' services: app: build: . ports: - '8000:8000'",
            "file_path": "docker-compose.yml",
            "metadata": {"language": "yaml", "framework": "docker-compose"}
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
                        "file_path": file_data["file_path"],
                        "metadata": file_data["metadata"]
                    }
                }]
            )
    
    print(f"✅ Added vectors to collections: {main_collection}, {cd_collection}")
    
    # Test project summary generation
    print("\n🔍 Testing project summary generation...")
    
    project_info = vector_service.generate_project_summary(
        repo_url="https://github.com/example/integration-test",
        scan_id=scan_id
    )
    
    print("📋 Generated Project Summary:")
    print(f"   Summary: {project_info.get('summary', 'No summary')}")
    print(f"   Technologies: {project_info.get('technologies', [])}")
    print(f"   File Types: {project_info.get('file_types', [])}")
    print(f"   Dependencies: {project_info.get('dependencies', [])}")
    print(f"   Has CD Repo: {project_info.get('has_cd_repo', False)}")
    print(f"   Files Analyzed: {project_info.get('total_files_analyzed', 0)}")
    
    # Create scan result with the project info
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
    
    scan_result = ScanResult(
        scan_id=scan_id,
        repo_url="https://github.com/example/integration-test",
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
                "repo_url": "https://github.com/example/integration-test",
                "branch": "main",
                "total_files": len(project_files),
                "total_lines": 1000,
                "languages": ["Python", "JavaScript", "YAML"],
                "build_files": ["requirements.txt", "package.json"],
                "config_files": ["Dockerfile", "docker-compose.yml"]
            },
            "vector_config": config
        }
    )
    
    # Generate HTML report
    print("\n📄 Generating HTML report with integrated project summary...")
    html_service = HTMLReportService()
    html_report = html_service.generate_html_report(scan_result)
    
    # Save report
    reports_dir = "reports"
    scan_dir = os.path.join(reports_dir, scan_id)
    os.makedirs(scan_dir, exist_ok=True)
    
    html_filename = f"integration_test_{scan_id}.html"
    html_path = os.path.join(scan_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"💾 Integration test report saved: {html_path}")
    
    # Analyze the report
    print("\n📋 Integration Test Results:")
    
    # Check if technologies were detected
    tech_detected = any(tech in html_report.lower() for tech in ["python", "javascript", "django", "flask", "react", "express"])
    print(f"   {'✅' if tech_detected else '❌'} Technologies detected in report")
    
    # Check if dependencies were detected
    deps_detected = any(dep in html_report.lower() for dep in ["django", "flask", "express", "react", "axios"])
    print(f"   {'✅' if deps_detected else '❌'} Dependencies detected in report")
    
    # Check if file types were detected
    file_types_detected = any(ext in html_report.lower() for ext in ["py", "js", "yaml", "json", "txt"])
    print(f"   {'✅' if file_types_detected else '❌'} File types detected in report")
    
    # Check if CD repository was mentioned
    cd_mentioned = "cd repository" in html_report.lower() or "continuous deployment" in html_report.lower()
    print(f"   {'✅' if cd_mentioned else '❌'} CD repository mentioned in report")
    
    # Check project summary section
    summary_section = "project-summary-section" in html_report
    print(f"   {'✅' if summary_section else '❌'} Project summary section present")
    
    # Check hard gates section
    hard_gates = "hard gates assessment" in html_report.lower()
    print(f"   {'✅' if hard_gates else '❌'} Hard gates section present")
    
    print(f"\n🎉 Integration Test Complete!")
    print(f"\n📖 Integration test report is available at:")
    print(f"   🌐 HTML: file://{os.path.abspath(html_path)}")
    print(f"   📁 Directory: {scan_dir}")
    
    # Clean up
    try:
        vector_service.delete_collection(main_collection)
        vector_service.delete_collection(cd_collection)
        print(f"🧹 Cleaned up vector collections")
    except:
        pass
    
    return scan_id, html_path


if __name__ == "__main__":
    test_project_summary_integration()
