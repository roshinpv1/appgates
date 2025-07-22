#!/usr/bin/env python3
"""
Test script to verify LLM pattern generation integration
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from codegates.core.llm_pattern_manager import LLMPatternManager
from codegates.models import Language, GateType

def test_llm_pattern_generation():
    """Test LLM pattern generation for a simple codebase"""
    
    print("🧪 Testing LLM Pattern Generation")
    print("=" * 50)
    
    # Create a simple test directory with some code
    test_dir = Path("test_codebase")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple Java file
    java_file = test_dir / "TestApp.java"
    java_file.write_text("""
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TestApp {
    private static final Logger logger = LoggerFactory.getLogger(TestApp.class);
    
    public static void main(String[] args) {
        logger.info("Application started");
        logger.debug("Debug message");
        logger.error("Error occurred", new Exception("Test error"));
        
        // Some structured logging
        logger.info("User action: {}", "login");
        logger.error("API call failed: {}", "GET /api/users");
    }
}
""")
    
    # Create a simple Python file
    python_file = test_dir / "app.py"
    python_file.write_text("""
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Application started")
    logger.debug("Debug message")
    logger.error("Error occurred")
    
    # Structured logging
    logger.info("User action: %s", "login")
    logger.error("API call failed: %s", "GET /api/users")
    
    # JSON logging
    log_data = {"user": "john", "action": "login", "timestamp": "2024-01-01"}
    logger.info("Structured log: %s", json.dumps(log_data))

if __name__ == "__main__":
    main()
""")
    
    try:
        # Initialize LLM Pattern Manager
        print("🤖 Initializing LLM Pattern Manager...")
        llm_manager = LLMPatternManager()
        
        if not llm_manager.is_llm_available():
            print("⚠️ LLM not available, testing fallback patterns...")
            return
        
        print("✅ LLM Pattern Manager initialized successfully")
        
        # Generate patterns for the test codebase
        print(f"📁 Analyzing test codebase: {test_dir}")
        result = llm_manager.generate_patterns_for_codebase(
            test_dir, 
            [Language.JAVA, Language.PYTHON]
        )
        
        if result.get('success', False):
            print("✅ LLM pattern generation successful!")
            
            # Show some patterns
            llm_response = result.get('llm_response', {})
            hard_gates_analysis = llm_response.get('hard_gates_analysis_short', {})
            
            print(f"\n📊 Generated patterns for {len(hard_gates_analysis)} gates:")
            for gate_name, gate_data in hard_gates_analysis.items():
                patterns = gate_data.get('patterns', [])
                print(f"   {gate_name}: {len(patterns)} patterns")
                if patterns:
                    print(f"      Sample: {patterns[0]}")
            
            # Show technology summary
            tech_summary = llm_response.get('tech_summary', {})
            print(f"\n🏗️ Detected technologies:")
            for tech_type, tech_list in tech_summary.items():
                if tech_list:
                    print(f"   {tech_type}: {', '.join(tech_list)}")
        
        else:
            print("❌ LLM pattern generation failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("\n🧹 Cleaned up test directory")

if __name__ == "__main__":
    test_llm_pattern_generation() 