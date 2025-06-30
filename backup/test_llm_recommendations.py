#!/usr/bin/env python3
"""
Test script for LLM-powered recommendations with enhanced metadata
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the current directory to Python path for imports
import sys
sys.path.append('.')

try:
    from codegates.core.gate_validator import GateValidator
    from codegates.core.llm_analyzer import LLMIntegrationManager, LLMConfig, LLMProvider
    from codegates.models import ScanConfig, Language
    from codegates.utils.env_loader import EnvironmentLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def create_test_files():
    """Create test files with various code patterns for analysis"""
    
    test_dir = Path("test_llm_data")
    test_dir.mkdir(exist_ok=True)
    
    # Python test file with various patterns
    python_file = test_dir / "test_app.py"
    python_code = '''
import logging
import json
import requests
from flask import Flask, request
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_user_data(user_id, email, password):
    """Process user data with various issues"""
    
    # Bad: Logging sensitive data
    logger.info(f"Processing user: {user_id}, email: {email}, password: {password}")
    
    # Bad: No structured logging
    print("User processing started")
    
    # Bad: No error handling
    response = requests.get(f"https://api.example.com/users/{user_id}")
    data = response.json()
    
    # Bad: No retry logic
    if response.status_code != 200:
        print("API call failed")
        return None
    
    return data

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create user endpoint with issues"""
    
    user_data = request.get_json()
    
    # Bad: Logging request data (might contain secrets)
    logger.info(f"Creating user with data: {user_data}")
    
    try:
        # Some processing
        result = process_user_data(
            user_data.get('id'),
            user_data.get('email'), 
            user_data.get('password')
        )
        
        # Bad: Basic logging without structure
        print(f"User created successfully: {result}")
        
        return {"status": "success", "data": result}
        
    except Exception as e:
        # Bad: Logging exception without proper context
        print(f"Error: {e}")
        return {"status": "error"}

def background_job():
    """Background job with issues"""
    
    # Bad: No structured logging for background jobs
    print("Background job started")
    
    for i in range(10):
        # Bad: No correlation ID
        logger.info(f"Processing item {i}")
        
        # Bad: No timeout handling
        response = requests.post("https://api.example.com/process", 
                               json={"item": i})
        
        # Bad: No retry logic
        if response.status_code != 200:
            print(f"Failed to process item {i}")
        
        time.sleep(1)

if __name__ == "__main__":
    app.run(debug=True)
'''
    
    python_file.write_text(python_code)
    
    # JavaScript test file
    js_file = test_dir / "test_app.js"
    js_code = '''
const express = require('express');
const axios = require('axios');
const app = express();

// Bad: No structured logging setup
console.log("Server starting...");

async function processUserData(userId, email, password) {
    // Bad: Logging sensitive data
    console.log(`Processing user: ${userId}, email: ${email}, password: ${password}`);
    
    try {
        // Bad: No timeout configuration
        const response = await axios.get(`https://api.example.com/users/${userId}`);
        
        // Bad: No structured logging
        console.log("API call successful");
        
        return response.data;
    } catch (error) {
        // Bad: Basic error logging
        console.log(`Error: ${error.message}`);
        throw error;
    }
}

app.post('/api/users', async (req, res) => {
    const userData = req.body;
    
    // Bad: Logging request data (potential secrets)
    console.log(`Creating user with data: ${JSON.stringify(userData)}`);
    
    try {
        const result = await processUserData(
            userData.id,
            userData.email,
            userData.password
        );
        
        // Bad: No correlation ID in logs
        console.log("User created successfully");
        
        res.json({ status: 'success', data: result });
    } catch (error) {
        // Bad: No structured error logging
        console.log(`Request failed: ${error.message}`);
        res.status(500).json({ status: 'error' });
    }
});

// Background job
setInterval(() => {
    // Bad: No structured logging for background jobs
    console.log("Running background job");
    
    for (let i = 0; i < 5; i++) {
        // Bad: No correlation ID
        console.log(`Processing batch item ${i}`);
        
        // Bad: No error handling or retry logic
        axios.post('https://api.example.com/batch', { item: i })
            .then(() => console.log(`Item ${i} processed`))
            .catch(err => console.log(`Item ${i} failed: ${err.message}`));
    }
}, 60000);

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
'''
    
    js_file.write_text(js_code)
    
    print(f"✅ Created test files in {test_dir}")
    return test_dir


def setup_llm_manager():
    """Setup LLM manager with available configuration"""
    
    # Load environment
    env_loader = EnvironmentLoader()
    env_loader.load_environment(force_reload=True)
    
    # Get preferred provider
    preferred_provider = env_loader.get_preferred_llm_provider()
    
    if not preferred_provider:
        print("⚠️ No LLM provider configured. Using mock mode.")
        return None
    
    print(f"🤖 Using LLM provider: {preferred_provider}")
    
    # Get provider configuration
    provider_config = env_loader.get_llm_config(preferred_provider)
    
    if not provider_config:
        print("⚠️ LLM provider configuration not found. Using mock mode.")
        return None
    
    # Create LLM configuration
    if preferred_provider == 'local':
        llm_config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model=provider_config['model'],
            api_key=provider_config['api_key'],
            base_url=provider_config['base_url'],
            temperature=provider_config['temperature'],
            max_tokens=provider_config['max_tokens']
        )
    elif preferred_provider == 'openai':
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=provider_config['model'],
            api_key=provider_config['api_key'],
            base_url=provider_config.get('base_url'),
            temperature=provider_config['temperature'],
            max_tokens=provider_config['max_tokens']
        )
    elif preferred_provider == 'anthropic':
        llm_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model=provider_config['model'],
            api_key=provider_config['api_key'],
            temperature=provider_config['temperature'],
            max_tokens=provider_config['max_tokens']
        )
    else:
        print(f"⚠️ Provider {preferred_provider} not supported in this test")
        return None
    
    # Create LLM manager
    llm_manager = LLMIntegrationManager(llm_config)
    
    if llm_manager.is_enabled():
        print(f"✅ LLM manager initialized successfully")
        return llm_manager
    else:
        print("⚠️ LLM manager not available. Using mock mode.")
        return None


def run_enhanced_analysis():
    """Run enhanced analysis with LLM-powered recommendations"""
    
    print("\n🚀 Testing Enhanced LLM-Powered Recommendations")
    print("=" * 60)
    
    # Create test files
    test_dir = create_test_files()
    
    # Setup LLM manager
    llm_manager = setup_llm_manager()
    
    # Configure gate validator
    config = ScanConfig(
        target_path=str(test_dir),
        languages=[Language.PYTHON, Language.JAVASCRIPT],
        exclude_patterns=['.git', '__pycache__', 'node_modules']
    )
    
    validator = GateValidator(config)
    
    print(f"\n📊 Analyzing test directory: {test_dir}")
    
    # Run validation with LLM enhancement
    result = validator.validate(test_dir, llm_manager=llm_manager)
    
    print(f"\n📈 Analysis Results:")
    print(f"Overall Score: {result.overall_score:.1f}")
    print(f"Passed Gates: {result.passed_gates}")
    print(f"Warning Gates: {result.warning_gates}")
    print(f"Failed Gates: {result.failed_gates}")
    
    # Display detailed results for each gate
    for gate_score in result.gate_scores:
        print(f"\n🔍 Gate: {gate_score.gate.value}")
        print(f"   Status: {gate_score.status}")
        print(f"   Score: {gate_score.final_score:.1f}")
        print(f"   Found: {gate_score.found}/{gate_score.expected}")
        print(f"   Matches: {len(gate_score.matches)} enhanced metadata entries")
        
        # Show enhanced metadata sample
        if gate_score.matches:
            sample_match = gate_score.matches[0]
            print(f"   📝 Sample Enhanced Metadata:")
            print(f"      File: {sample_match.get('file_name', 'unknown')}")
            print(f"      Line: {sample_match.get('line_number', 0)}")
            print(f"      Severity: {sample_match.get('severity', 'UNKNOWN')}")
            print(f"      Priority: {sample_match.get('priority', 0)}")
            print(f"      Category: {sample_match.get('category', 'unknown')}")
            print(f"      Pattern Type: {sample_match.get('pattern_type', 'unknown')}")
            
            func_context = sample_match.get('function_context', {})
            if func_context.get('function_name'):
                print(f"      Function: {func_context['function_name']}")
            
            if sample_match.get('suggested_fix'):
                print(f"      Suggested Fix: {sample_match['suggested_fix'][:100]}...")
        
        # Show LLM-enhanced recommendations
        print(f"   🤖 {'LLM-Enhanced' if llm_manager else 'Static'} Recommendations:")
        for i, rec in enumerate(gate_score.recommendations[:3], 1):
            print(f"      {i}. {rec}")
        
        if len(gate_score.recommendations) > 3:
            print(f"      ... and {len(gate_score.recommendations) - 3} more")
    
    # Save detailed results
    results_file = "llm_enhanced_results.json"
    detailed_results = {
        "overall_score": result.overall_score,
        "gate_scores": [],
        "llm_enabled": llm_manager is not None and llm_manager.is_enabled()
    }
    
    for gate_score in result.gate_scores:
        gate_data = {
            "gate": gate_score.gate.value,
            "status": gate_score.status,
            "score": gate_score.final_score,
            "found": gate_score.found,
            "expected": gate_score.expected,
            "recommendations": gate_score.recommendations,
            "enhanced_metadata_count": len(gate_score.matches),
            "sample_metadata": gate_score.matches[0] if gate_score.matches else None
        }
        detailed_results["gate_scores"].append(gate_data)
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    print(f"🧹 Cleaned up test directory: {test_dir}")
    
    return result


def compare_recommendations():
    """Compare static vs LLM-enhanced recommendations"""
    
    print("\n🔄 Comparing Static vs LLM-Enhanced Recommendations")
    print("=" * 60)
    
    # Test without LLM
    print("\n📊 Running analysis WITHOUT LLM enhancement...")
    test_dir = create_test_files()
    
    config = ScanConfig(
        target_path=str(test_dir),
        languages=[Language.PYTHON],
        exclude_patterns=['.git', '__pycache__']
    )
    
    validator = GateValidator(config)
    result_static = validator.validate(test_dir, llm_manager=None)
    
    # Test with LLM
    print("\n🤖 Running analysis WITH LLM enhancement...")
    llm_manager = setup_llm_manager()
    result_llm = validator.validate(test_dir, llm_manager=llm_manager)
    
    # Compare results
    print(f"\n📈 Comparison Results:")
    print(f"{'Metric':<25} {'Static':<15} {'LLM-Enhanced':<15} {'Improvement'}")
    print("-" * 70)
    
    print(f"{'Overall Score':<25} {result_static.overall_score:<15.1f} {result_llm.overall_score:<15.1f} {result_llm.overall_score - result_static.overall_score:+.1f}")
    
    # Compare gate-by-gate
    for static_gate, llm_gate in zip(result_static.gate_scores, result_llm.gate_scores):
        if static_gate.gate == llm_gate.gate:
            gate_name = static_gate.gate.value
            print(f"{gate_name:<25} {static_gate.final_score:<15.1f} {llm_gate.final_score:<15.1f} {llm_gate.final_score - static_gate.final_score:+.1f}")
            
            print(f"\n🔍 {gate_name} Recommendations Comparison:")
            print(f"   📝 Static Recommendations ({len(static_gate.recommendations)}):")
            for i, rec in enumerate(static_gate.recommendations[:2], 1):
                print(f"      {i}. {rec}")
            
            print(f"   🤖 LLM-Enhanced Recommendations ({len(llm_gate.recommendations)}):")
            for i, rec in enumerate(llm_gate.recommendations[:2], 1):
                print(f"      {i}. {rec}")
            print()
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    return result_static, result_llm


if __name__ == "__main__":
    print("🎯 LLM-Enhanced Recommendations Test Suite")
    print("=" * 60)
    
    try:
        # Run enhanced analysis
        result = run_enhanced_analysis()
        
        # Compare static vs LLM recommendations
        if input("\n❓ Would you like to compare static vs LLM recommendations? (y/n): ").lower() == 'y':
            compare_recommendations()
        
        print("\n✅ LLM-Enhanced Recommendations test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 