#!/usr/bin/env python3
"""
Test script to verify LLM Pattern Manager initialization in validators
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from codegates.core.gate_validators.logging_validators import StructuredLogsValidator
from codegates.models import Language, GateType

def test_validator_llm_initialization():
    """Test LLM Pattern Manager initialization in validators"""
    
    print("🧪 Testing Validator LLM Initialization")
    print("=" * 50)
    
    try:
        # Create a validator
        print("🔧 Creating StructuredLogsValidator...")
        validator = StructuredLogsValidator(Language.JAVA, GateType.STRUCTURED_LOGS)
        
        print(f"✅ Validator created successfully")
        print(f"🔍 Language: {validator.language}")
        print(f"🔍 Gate Type: {validator.gate_type}")
        print(f"🔍 LLM Pattern Manager: {validator.llm_pattern_manager}")
        print(f"🔍 Pattern Loader: {validator.pattern_loader}")
        
        # Test pattern loading
        test_path = Path("test_codebase")
        test_path.mkdir(exist_ok=True)
        
        # Create a simple test file
        test_file = test_path / "TestApp.java"
        test_file.write_text("""
package com.example;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TestApp {
    private static final Logger logger = LoggerFactory.getLogger(TestApp.class);
    
    public static void main(String[] args) {
        logger.info("Application started");
        logger.debug("Debug message");
        logger.error("Error occurred", new Exception("Test error"));
    }
}
""")
        
        print(f"\n🔍 Testing pattern loading...")
        patterns = validator._get_patterns(test_path)
        print(f"🔍 Patterns received: {list(patterns.keys()) if patterns else 'empty'}")
        
        if 'llm_generated' in patterns:
            print(f"✅ LLM patterns found: {len(patterns['llm_generated'])} patterns")
        else:
            print(f"⚠️ No LLM patterns found, using fallback")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        if test_path.exists():
            shutil.rmtree(test_path)
        print("\n🧹 Cleaned up test directory")

if __name__ == "__main__":
    test_validator_llm_initialization() 