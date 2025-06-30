#!/usr/bin/env python3
"""
Comprehensive test to trace the complete hard gate validation workflow
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add the current directory to Python path for imports
sys.path.append('.')

try:
    from codegates.core.gate_validator import GateValidator
    from codegates.core.llm_analyzer import LLMIntegrationManager, LLMConfig, LLMProvider
    from codegates.core.gate_validators.factory import GateValidatorFactory
    from codegates.models import ScanConfig, Language, GateType
    from codegates.utils.env_loader import EnvironmentLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def create_comprehensive_test_project():
    """Create a comprehensive test project with multiple gate patterns"""
    
    test_dir = Path("test_workflow_project")
    test_dir.mkdir(exist_ok=True)
    
    # Create main.py with multiple patterns
    main_file = test_dir / "main.py"
    main_file.write_text("""
import logging
import json
import requests
import time
from datetime import datetime
from flask import Flask, request, jsonify

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def process_user_data(user_id, password, api_key):
    \"\"\"Process user data with various gate patterns\"\"\"
    
    correlation_id = request.headers.get('X-Correlation-ID', 'unknown')
    
    # GOOD: Structured logging
    logger.info("Processing user request", extra={
        "user_id": user_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.now().isoformat(),
        "action": "process_user_data"
    })
    
    # BAD: Logging secrets (should trigger avoid_logging_secrets gate)
    logger.info(f"User credentials: password={password}, api_key={api_key}")
    
    try:
        # Simulate API call with timeout
        response = requests.get(
            f"https://api.example.com/users/{user_id}",
            timeout=30,  # GOOD: Timeout configuration
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            # GOOD: HTTP status code handling
            return {"status": "success", "data": response.json()}
        elif response.status_code == 404:
            return {"status": "not_found", "message": "User not found"}
        else:
            return {"status": "error", "code": response.status_code}
            
    except requests.exceptions.Timeout:
        # GOOD: Error logging with context
        logger.error("API timeout occurred", extra={
            "user_id": user_id,
            "correlation_id": correlation_id,
            "error_type": "timeout",
            "timestamp": datetime.now().isoformat()
        })
        return {"status": "timeout", "message": "Request timed out"}
        
    except Exception as e:
        # GOOD: Exception handling with audit trail
        logger.error("Unexpected error processing user data", extra={
            "user_id": user_id,
            "correlation_id": correlation_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        })
        return {"status": "error", "message": "Internal server error"}

@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    \"\"\"API endpoint with logging\"\"\"
    
    # GOOD: API call logging
    logger.info("API call received", extra={
        "endpoint": "/api/users",
        "method": "GET",
        "user_id": user_id,
        "ip": request.remote_addr,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        result = process_user_data(user_id, "secret123", "api_key_12345")
        
        # GOOD: API response logging
        logger.info("API call completed", extra={
            "endpoint": "/api/users",
            "user_id": user_id,
            "status": result.get("status"),
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify(result)
        
    except Exception as e:
        # GOOD: Error response with proper HTTP codes
        logger.error("API error", extra={
            "endpoint": "/api/users",
            "user_id": user_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
""")
    
    # Create test file
    test_file = test_dir / "test_main.py"
    test_file.write_text("""
import unittest
from unittest.mock import patch, MagicMock
from main import process_user_data

class TestUserProcessing(unittest.TestCase):
    \"\"\"Test cases for user processing\"\"\"
    
    def test_successful_processing(self):
        \"\"\"Test successful user data processing\"\"\"
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"name": "John Doe"}
            mock_get.return_value = mock_response
            
            result = process_user_data("123", "password", "api_key")
            self.assertEqual(result["status"], "success")
    
    def test_user_not_found(self):
        \"\"\"Test user not found scenario\"\"\"
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = process_user_data("456", "password", "api_key")
            self.assertEqual(result["status"], "not_found")

if __name__ == '__main__':
    unittest.main()
""")
    
    return test_dir


def trace_workflow_execution():
    """Trace the complete workflow execution with detailed logging"""
    
    print("🔍 Tracing Hard Gate Validation Workflow")
    print("=" * 80)
    
    # Create test project
    test_dir = create_comprehensive_test_project()
    print(f"✅ Created comprehensive test project at: {test_dir}")
    
    # Configure environment
    env_loader = EnvironmentLoader()
    
    # Create LLM configuration
    llm_config = LLMConfig(
        provider=LLMProvider.LOCAL,
        model="meta-llama-3.1-8b-instruct",
        base_url="http://localhost:1234/v1",
        temperature=0.1,
        max_tokens=4000
    )
    
    # Create LLM manager
    llm_manager = LLMIntegrationManager(llm_config)
    print(f"🤖 LLM Manager created - Enabled: {llm_manager.is_enabled()}")
    
    # Configure scan
    config = ScanConfig(
        target_path=str(test_dir),
        languages=[Language.PYTHON],
        exclude_patterns=['.git', '__pycache__'],
        max_file_size=1024*1024  # 1MB
    )
    
    print(f"\n📋 Scan Configuration:")
    print(f"  - Target path: {config.target_path}")
    print(f"  - Languages: {config.languages}")
    print(f"  - Exclude patterns: {config.exclude_patterns}")
    
    # Create gate validator
    validator = GateValidator(config)
    print(f"✅ Gate validator created")
    
    # Step 1: Language Detection
    print(f"\n🔍 Step 1: Language Detection")
    detected_languages = validator.language_detector.detect_languages(test_dir)
    print(f"  - Detected languages: {detected_languages}")
    
    # Step 2: File Analysis
    print(f"\n📁 Step 2: File Analysis")
    file_analyses = validator._scan_files(test_dir)
    print(f"  - Files analyzed: {len(file_analyses)}")
    for analysis in file_analyses:
        print(f"    - {analysis.file_path}: {analysis.lines_of_code} lines ({analysis.language.value})")
    
    # Step 3: Individual Gate Validation
    print(f"\n🚪 Step 3: Individual Gate Validation")
    
    # Test specific gates
    test_gates = [
        GateType.STRUCTURED_LOGS,
        GateType.AVOID_LOGGING_SECRETS,
        GateType.ERROR_LOGS,
        GateType.HTTP_CODES,
        GateType.AUTOMATED_TESTS
    ]
    
    gate_results = {}
    
    for gate_type in test_gates:
        print(f"\n  🔍 Testing Gate: {gate_type.value}")
        
        # Get validator for this gate
        validator_factory = GateValidatorFactory()
        gate_validator = validator_factory.get_validator(gate_type, Language.PYTHON)
        
        if gate_validator:
            print(f"    ✅ Gate validator found: {type(gate_validator).__name__}")
            
            # Run validation
            try:
                result = gate_validator.validate(test_dir, file_analyses)
                print(f"    📊 Validation result:")
                print(f"      - Expected: {result.expected}")
                print(f"      - Found: {result.found}")
                print(f"      - Quality Score: {result.quality_score:.1f}")
                print(f"      - Details: {len(result.details)} items")
                print(f"      - Recommendations: {len(result.recommendations)} items")
                
                if hasattr(result, 'matches') and result.matches:
                    print(f"      - Matches: {len(result.matches)} pattern matches")
                    for i, match in enumerate(result.matches[:3]):  # Show first 3
                        print(f"        {i+1}. {match.get('file', 'unknown')}:{match.get('line', '?')} - {match.get('matched_text', 'N/A')[:50]}...")
                
                gate_results[gate_type] = result
                
            except Exception as e:
                print(f"    ❌ Validation failed: {e}")
                gate_results[gate_type] = None
        else:
            print(f"    ❌ No validator found for {gate_type.value}")
    
    # Step 4: LLM Enhancement Testing
    print(f"\n🤖 Step 4: LLM Enhancement Testing")
    
    if llm_manager.is_enabled():
        print(f"  ✅ LLM is enabled and available")
        
        for gate_type, result in gate_results.items():
            if result and hasattr(result, 'matches') and result.matches:
                print(f"\n  🔍 Testing LLM enhancement for {gate_type.value}")
                
                try:
                    # Prepare matches for LLM
                    matches = result.matches[:5]  # Limit to 5 matches
                    print(f"    📋 Sending {len(matches)} matches to LLM")
                    
                    # Test LLM enhancement
                    enhancement = llm_manager.enhance_gate_validation(
                        gate_type.value,
                        matches,
                        Language.PYTHON,
                        {"python": ["flask", "requests", "unittest"]},
                        result.recommendations
                    )
                    
                    if enhancement:
                        print(f"    ✅ LLM enhancement received:")
                        print(f"      - Enhanced quality score: {enhancement.get('enhanced_quality_score')}")
                        print(f"      - LLM recommendations: {len(enhancement.get('llm_recommendations', []))}")
                        print(f"      - Security insights: {len(enhancement.get('security_insights', []))}")
                        print(f"      - Code examples: {len(enhancement.get('code_examples', []))}")
                        
                        # Show sample recommendations
                        if enhancement.get('llm_recommendations'):
                            print(f"      - Sample recommendation: {enhancement['llm_recommendations'][0][:100]}...")
                    else:
                        print(f"    ⚠️ LLM returned empty enhancement")
                        
                except Exception as e:
                    print(f"    ❌ LLM enhancement failed: {e}")
            else:
                print(f"  ⚠️ No matches to send to LLM for {gate_type.value}")
    else:
        print(f"  ❌ LLM is not enabled or available")
        print(f"    - Check LLM service at: {llm_config.base_url}")
        print(f"    - Model: {llm_config.model}")
    
    # Step 5: Complete Validation
    print(f"\n🎯 Step 5: Complete Validation Run")
    
    start_time = time.time()
    complete_result = validator.validate(test_dir, llm_manager)
    end_time = time.time()
    
    print(f"  ✅ Complete validation finished in {end_time - start_time:.2f} seconds")
    print(f"  📊 Results:")
    print(f"    - Project: {complete_result.project_name}")
    print(f"    - Language: {complete_result.language.value}")
    print(f"    - Total files: {complete_result.total_files}")
    print(f"    - Total lines: {complete_result.total_lines}")
    print(f"    - Gates analyzed: {len(complete_result.gate_scores)}")
    print(f"    - Overall score: {complete_result.overall_score:.1f}")
    print(f"    - Passed gates: {complete_result.passed_gates}")
    print(f"    - Warning gates: {complete_result.warning_gates}")
    print(f"    - Failed gates: {complete_result.failed_gates}")
    
    # Analyze gate scores
    print(f"\n  📋 Gate Score Details:")
    for gate_score in complete_result.gate_scores:
        print(f"    - {gate_score.gate.value}: {gate_score.final_score:.1f} ({gate_score.status})")
        if gate_score.matches:
            print(f"      Matches: {len(gate_score.matches)}")
    
    return complete_result


def analyze_llm_call_points():
    """Analyze where LLM calls should be made in the workflow"""
    
    print(f"\n🔬 Analyzing LLM Call Points")
    print("=" * 60)
    
    print(f"📍 LLM calls should be made at these points:")
    print(f"")
    print(f"1. **Gate Validator Level** (codegates/core/gate_validator.py)")
    print(f"   - Method: _validate_single_gate()")
    print(f"   - Line ~350: llm_manager.enhance_gate_validation()")
    print(f"   - Purpose: Enhance individual gate analysis")
    print(f"")
    print(f"2. **Individual Validator Level** (codegates/core/gate_validators/base.py)")
    print(f"   - Method: _generate_llm_recommendations()")
    print(f"   - Line ~563: llm_manager.enhance_gate_validation()")
    print(f"   - Purpose: Generate intelligent recommendations")
    print(f"")
    print(f"3. **LLM Integration Manager** (codegates/core/llm_analyzer.py)")
    print(f"   - Method: enhance_gate_validation()")
    print(f"   - Line ~1000+: analyzer.analyze_gate_with_enhanced_metadata()")
    print(f"   - Purpose: Actual LLM API call")
    print(f"")
    print(f"4. **LLM Optimizer** (codegates/core/llm_optimizer.py)")
    print(f"   - Method: optimize_gate_analysis()")
    print(f"   - Line ~45: _should_skip_llm_analysis() - MAY SKIP LLM!")
    print(f"   - Purpose: Performance optimization (may skip low-priority gates)")
    print(f"")
    
    print(f"⚠️ **Common reasons LLM calls are skipped:**")
    print(f"   1. LLM service not available (connection issues)")
    print(f"   2. Gate classified as low-priority (http_codes, ui_error_tools, log_background_jobs)")
    print(f"   3. Insufficient code samples (< 2 samples for low-priority gates)")
    print(f"   4. LLM timeout or error during processing")
    print(f"   5. LLM integration not properly configured")


def main():
    """Main test function"""
    
    print("🧪 Hard Gate Workflow Analysis")
    print("=" * 100)
    
    try:
        # Trace workflow execution
        result = trace_workflow_execution()
        
        # Analyze LLM call points
        analyze_llm_call_points()
        
        print(f"\n📋 Summary:")
        print(f"  - Workflow completed successfully")
        print(f"  - Total gates analyzed: {len(result.gate_scores)}")
        print(f"  - Overall score: {result.overall_score:.1f}")
        print(f"  - LLM calls should be visible in the output above")
        
    except Exception as e:
        print(f"❌ Error during workflow analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        test_dir = Path("test_workflow_project")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test project")


if __name__ == "__main__":
    main() 