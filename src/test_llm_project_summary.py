#!/usr/bin/env python3
"""
Test script for LLM-based Project Summary Service

This script tests the new LLM-based project summary generation
that provides intelligent, contextual analysis of codebases.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.vector_service import VectorService
from services.llm_service import LLMService
from services.embedding_service import EmbeddingService
from services.project_summary_service import ProjectSummaryService


async def test_llm_project_summary():
    """Test the LLM-based project summary service"""
    print("🧪 Testing LLM-based Project Summary Service")
    print("=" * 60)
    
    try:
        # Initialize services
        print("📡 Initializing services...")
        
        # Vector service config
        vector_config = {
            "vector_size": 768,
            "distance_metric": "cosine",
            "use_qdrant": False,
            "qdrant_path": "./qdrant_data"
        }
        
        # LLM service config
        llm_config = {
            "provider": "local",
            "model": "llama3.2:3b",
            "timeout": 300,
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        # Initialize services
        vector_service = VectorService(vector_config)
        llm_service = LLMService(llm_config)
        embedding_service = EmbeddingService(vector_config)
        
        # Initialize project summary service
        project_summary_service = ProjectSummaryService(
            vector_service, llm_service, embedding_service
        )
        
        print("✅ Services initialized successfully")
        
        # Test parameters
        repo_url = "https://github.com/spring-projects/spring-petclinic"
        scan_id = f"test_llm_summary_{int(datetime.now().timestamp())}"
        
        # Mock metadata (similar to what would be available during scan)
        metadata = {
            "main_repo": {
                "repo_url": repo_url,
                "branch": "main",
                "total_files": 108,
                "total_lines": 19526,
                "languages": ["java"],
                "commit_hash": "test_commit_hash"
            },
            "cd_repo": {
                "repo_url": f"{repo_url}-cd",
                "branch": "main",
                "total_files": 15,
                "total_lines": 1200,
                "languages": ["yaml", "dockerfile"],
                "commit_hash": "test_cd_commit_hash"
            }
        }
        
        print(f"🔍 Testing project summary generation for: {repo_url}")
        print(f"📊 Scan ID: {scan_id}")
        
        # Generate LLM-based project summary
        print("\n🤖 Generating LLM-based project summary...")
        start_time = datetime.now()
        
        project_summary = await project_summary_service.generate_llm_project_summary(
            repo_url=repo_url,
            scan_id=scan_id,
            metadata=metadata
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Project summary generated in {duration:.2f} seconds")
        
        # Display results
        print("\n📋 Project Summary Results:")
        print("-" * 40)
        
        # Summary
        print(f"📝 Summary: {project_summary.get('summary', 'No summary available')[:200]}...")
        
        # Technology Stack
        tech_stack = project_summary.get('technology_stack', {})
        print(f"\n🔧 Technology Stack:")
        print(f"  • Primary Language: {tech_stack.get('primary_language', 'Unknown')}")
        print(f"  • Frameworks: {', '.join(tech_stack.get('frameworks', []))}")
        print(f"  • Build Tools: {', '.join(tech_stack.get('build_tools', []))}")
        print(f"  • Databases: {', '.join(tech_stack.get('databases', []))}")
        
        # Architecture
        architecture = project_summary.get('architecture', {})
        print(f"\n🏗️ Architecture:")
        print(f"  • Pattern: {architecture.get('pattern', 'Unknown')}")
        print(f"  • Layers: {', '.join(architecture.get('layers', []))}")
        print(f"  • Application Type: {project_summary.get('application_type', 'Unknown')}")
        
        # Key Features
        key_features = project_summary.get('key_features', [])
        print(f"\n✨ Key Features:")
        for feature in key_features[:3]:
            print(f"  • {feature}")
        
        # Development Practices
        practices = project_summary.get('development_practices', {})
        print(f"\n🛠️ Development Practices:")
        print(f"  • Testing: {practices.get('testing', 'Unknown')}")
        print(f"  • Logging: {practices.get('logging', 'Unknown')}")
        print(f"  • Security: {practices.get('security', 'Unknown')}")
        
        # Infrastructure
        infrastructure = project_summary.get('infrastructure', {})
        print(f"\n🏢 Infrastructure:")
        print(f"  • Deployment: {infrastructure.get('deployment', 'Unknown')}")
        print(f"  • Monitoring: {infrastructure.get('monitoring', 'Unknown')}")
        print(f"  • Scalability: {infrastructure.get('scalability', 'Unknown')}")
        
        # Vector Analysis Stats
        vector_analysis = project_summary.get('vector_analysis', {})
        print(f"\n📊 Vector Analysis Stats:")
        print(f"  • Total Files Analyzed: {vector_analysis.get('total_files_analyzed', 0)}")
        print(f"  • Java Files: {vector_analysis.get('java_files_analyzed', 0)}")
        print(f"  • Config Files: {vector_analysis.get('config_files_analyzed', 0)}")
        
        # Recommendations
        recommendations = project_summary.get('recommendations', [])
        print(f"\n💡 Recommendations:")
        for rec in recommendations[:3]:
            print(f"  • {rec}")
        
        # Analysis timestamp
        print(f"\n⏰ Analysis Timestamp: {project_summary.get('analysis_timestamp', 'Unknown')}")
        
        # Save detailed results to file
        output_file = f"test_llm_project_summary_{scan_id}.json"
        with open(output_file, 'w') as f:
            json.dump(project_summary, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Validation checks
        print("\n🔍 Validation Checks:")
        print("-" * 20)
        
        validation_checks = [
            ("Summary generated", bool(project_summary.get('summary'))),
            ("Technology stack detected", bool(tech_stack.get('primary_language') != 'Unknown')),
            ("Architecture pattern identified", bool(architecture.get('pattern') != 'Unknown')),
            ("Key features found", len(key_features) > 0),
            ("Recommendations provided", len(recommendations) > 0),
            ("Vector analysis stats available", vector_analysis.get('total_files_analyzed', 0) > 0),
            ("Analysis timestamp present", bool(project_summary.get('analysis_timestamp')))
        ]
        
        all_passed = True
        for check_name, passed in validation_checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 Starting LLM Project Summary Service Test")
    print("=" * 60)
    
    success = await test_llm_project_summary()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("💥 Some tests failed. Check the output above for details.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
