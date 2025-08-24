#!/usr/bin/env python3
"""
Test script to demonstrate LLM logging functionality
"""

import asyncio
from services.llm_logger import LLMLogger
from services.llm_service import LLMService


async def test_llm_logging():
    """Test LLM logging functionality"""
    
    print("🧪 Testing LLM Logging Functionality")
    print("=" * 50)
    
    # Initialize services
    llm_logger = LLMLogger()
    llm_service = LLMService({
        "provider": "local",
        "model": "llama-3.2-3b-instruct",
        "base_url": "http://localhost:1234"
    })
    
    # Test scan ID
    scan_id = "test_scan_123"
    
    # Test 1: LLM Pre-Analysis Node
    print("\n📝 Test 1: LLM Pre-Analysis Node")
    print("-" * 30)
    
    pre_analysis_prompt = """
Analyze the following project and generate applicable security, performance, and quality patterns:

Project Information:
- Repository: https://github.com/example/test-repo
- Branch: main
- Total Files: 150
- Total Lines: 5000
- Languages: Python, JavaScript
- Dependencies: {'python': ['requests', 'flask'], 'javascript': ['react', 'axios']}

Build Configuration:
- Build files: package.json, requirements.txt, Dockerfile
- Config files: .env, config.py

Available Gates:
- Security: Authentication, Authorization, Input Validation
- Performance: Caching, Database Optimization
- Code Quality: Logging, Error Handling

Generate patterns in JSON format.
"""
    
    try:
        response = await llm_service.generate(
            pre_analysis_prompt,
            scan_id=scan_id,
            node_name="LLMPreAnalysisNode",
            metadata={
                "project_type": "web_application",
                "languages": ["Python", "JavaScript"],
                "framework": "Flask + React"
            }
        )
        print(f"✅ Pre-analysis response: {len(response)} characters")
    except Exception as e:
        print(f"❌ Pre-analysis failed: {e}")
    
    # Test 2: LLM Post-Analysis Node
    print("\n📝 Test 2: LLM Post-Analysis Node")
    print("-" * 30)
    
    post_analysis_prompt = """
Analyze the following gate evaluation results and provide comprehensive recommendations:

Gate Results:
- Authentication Check: PASS (95% compliance)
- Authorization Check: FAIL (30% compliance)
- Input Validation: PARTIAL (60% compliance)
- Caching Implementation: PASS (85% compliance)
- Logging Implementation: FAIL (20% compliance)

Project Metadata:
- Repository: https://github.com/example/test-repo
- Total Gates: 5
- Passed Gates: 2
- Failed Gates: 2
- Partial Gates: 1

Provide analysis and recommendations.
"""
    
    try:
        response = await llm_service.generate(
            post_analysis_prompt,
            scan_id=scan_id,
            node_name="LLMPostAnalysisNode",
            metadata={
                "total_gates": 5,
                "passed_gates": 2,
                "failed_gates": 2,
                "partial_gates": 1,
                "compliance_score": 0.6
            }
        )
        print(f"✅ Post-analysis response: {len(response)} characters")
    except Exception as e:
        print(f"❌ Post-analysis failed: {e}")
    
    # Test 3: Check Logs
    print("\n📊 Test 3: Check Generated Logs")
    print("-" * 30)
    
    try:
        # Get scan logs
        logs = llm_logger.get_scan_logs(scan_id)
        print(f"✅ Found {len(logs)} log entries")
        
        # Get scan summary
        summary = llm_logger.get_scan_summary(scan_id)
        print(f"📈 Scan Summary:")
        print(f"   - Total Interactions: {summary['total_interactions']}")
        print(f"   - Total Prompt Tokens: {summary['total_prompt_tokens']}")
        print(f"   - Total Response Tokens: {summary['total_response_tokens']}")
        print(f"   - Total Duration: {summary['total_duration']:.2f}s")
        print(f"   - Average Duration: {summary['average_duration']:.2f}s")
        print(f"   - Errors: {summary['errors']}")
        print(f"   - Nodes: {', '.join(summary['nodes'])}")
        print(f"   - Log File: {summary['log_file']}")
        
        # Show log entries
        print(f"\n📋 Log Entries:")
        for i, log in enumerate(logs, 1):
            print(f"   {i}. {log['node_name']} - {log['timestamp']}")
            print(f"      Duration: {log['duration']:.2f}s")
            print(f"      Prompt Length: {log['prompt_length']} chars")
            print(f"      Response Length: {log['response_length']} chars")
            if log.get('error'):
                print(f"      Error: {log['error']}")
            print()
        
    except Exception as e:
        print(f"❌ Log retrieval failed: {e}")
    
    # Test 4: List All Log Files
    print("\n📁 Test 4: List All Log Files")
    print("-" * 30)
    
    try:
        import os
        from pathlib import Path
        
        log_dir = Path("logs/llm")
        if log_dir.exists():
            log_files = list(log_dir.glob("scan_*_llm_log.jsonl"))
            print(f"✅ Found {len(log_files)} log files:")
            for log_file in log_files:
                size = log_file.stat().st_size
                print(f"   - {log_file.name} ({size} bytes)")
        else:
            print("❌ Log directory not found")
            
    except Exception as e:
        print(f"❌ Log file listing failed: {e}")
    
    print("\n🎉 LLM Logging Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_llm_logging())
