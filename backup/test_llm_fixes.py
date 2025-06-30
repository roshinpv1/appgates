#!/usr/bin/env python3
"""
Test script to verify LLM fixes are working properly
"""

import os
import sys
import time
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append('.')

try:
    from codegates.core.gate_validator import GateValidator
    from codegates.core.llm_analyzer import LLMIntegrationManager, LLMConfig, LLMProvider
    from codegates.models import ScanConfig, Language, GateType
    from codegates.utils.env_loader import EnvironmentLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def create_test_project():
    """Create a test project with clear gate patterns"""
    
    test_dir = Path("test_llm_fixes")
    test_dir.mkdir(exist_ok=True)
    
    # Create a file with clear patterns for multiple gates
    test_file = test_dir / "app.py"
    test_file.write_text("""
import logging
import requests
from flask import Flask, jsonify

logger = logging.getLogger(__name__)
app = Flask(__name__)

def authenticate_user(username, password, api_key):
    \"\"\"Authenticate user with various patterns\"\"\"
    
    # BAD: Logging secrets (avoid_logging_secrets gate)
    logger.info(f"Login attempt: username={username}, password={password}")
    logger.debug(f"Using API key: {api_key}")
    
    # GOOD: Structured logging
    logger.info("User authentication started", extra={
        "username": username,
        "timestamp": "2024-01-01T10:00:00Z",
        "action": "authenticate"
    })
    
    try:
        # GOOD: HTTP status codes
        response = requests.get("https://api.example.com/auth", timeout=5)
        
        if response.status_code == 200:
            return {"status": "success", "user": username}
        elif response.status_code == 401:
            return {"status": "unauthorized", "message": "Invalid credentials"}
        elif response.status_code == 500:
            return {"status": "error", "message": "Server error"}
        else:
            return {"status": "unknown", "code": response.status_code}
            
    except requests.exceptions.Timeout:
        # GOOD: Error logging
        logger.error("Authentication timeout", extra={
            "username": username,
            "error_type": "timeout",
            "timestamp": "2024-01-01T10:00:00Z"
        })
        return {"status": "timeout"}
        
    except Exception as e:
        # GOOD: Error logging with context
        logger.error("Authentication failed", extra={
            "username": username,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return {"status": "error", "message": str(e)}

@app.route("/login", methods=["POST"])
def login():
    \"\"\"Login endpoint\"\"\"
    # This should trigger multiple gates
    return jsonify(authenticate_user("testuser", "secret123", "api_key_456"))

if __name__ == "__main__":
    app.run()
""")
    
    return test_dir


def test_llm_fixes():
    """Test that LLM fixes are working"""
    
    print("🔧 Testing LLM Fixes")
    print("=" * 60)
    
    # Create test project
    test_dir = create_test_project()
    print(f"✅ Created test project: {test_dir}")
    
    # Configure LLM
    llm_config = LLMConfig(
        provider=LLMProvider.LOCAL,
        model="meta-llama-3.1-8b-instruct",
        base_url="http://localhost:1234/v1",
        temperature=0.1
    )
    
    llm_manager = LLMIntegrationManager(llm_config)
    print(f"🤖 LLM Manager enabled: {llm_manager.is_enabled()}")
    
    # Configure scan
    config = ScanConfig(
        target_path=str(test_dir),
        languages=[Language.PYTHON],
        exclude_patterns=['.git', '__pycache__']
    )
    
    # Create validator
    validator = GateValidator(config)
    
    # Test specific gates that should now get LLM analysis
    test_gates = [
        GateType.AVOID_LOGGING_SECRETS,  # Should find secrets
        GateType.HTTP_CODES,            # Should find status codes  
        GateType.ERROR_LOGS,            # Should find error handling
        GateType.STRUCTURED_LOGS        # Should find structured logging
    ]
    
    print(f"\n🚪 Testing Individual Gates:")
    
    for gate_type in test_gates:
        print(f"\n  🔍 Testing {gate_type.value}:")
        
        try:
            # Run complete validation to see LLM calls
            start_time = time.time()
            result = validator.validate(test_dir, llm_manager)
            end_time = time.time()
            
            # Find this gate's score
            gate_score = next((g for g in result.gate_scores if g.gate == gate_type), None)
            
            if gate_score:
                print(f"    ✅ Gate processed:")
                print(f"      - Score: {gate_score.final_score:.1f}")
                print(f"      - Status: {gate_score.status}")
                print(f"      - Matches: {len(gate_score.matches) if gate_score.matches else 0}")
                print(f"      - Recommendations: {len(gate_score.recommendations)}")
                
                # Show first recommendation if available
                if gate_score.recommendations:
                    first_rec = gate_score.recommendations[0]
                    print(f"      - Sample rec: {first_rec[:80]}...")
            else:
                print(f"    ❌ Gate not found in results")
            
            break  # Only test once since all gates are processed together
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"\n📊 Overall Results:")
    print(f"  - Total gates: {len(result.gate_scores)}")
    print(f"  - Overall score: {result.overall_score:.1f}")
    print(f"  - Processing time: {end_time - start_time:.2f}s")
    
    # Count gates with matches
    gates_with_matches = [g for g in result.gate_scores if g.matches]
    print(f"  - Gates with matches: {len(gates_with_matches)}")
    
    for gate in gates_with_matches:
        print(f"    - {gate.gate.value}: {len(gate.matches)} matches")
    
    return result


def main():
    """Main test function"""
    
    print("🧪 LLM Fixes Verification")
    print("=" * 80)
    
    try:
        result = test_llm_fixes()
        
        print(f"\n✅ Test completed successfully!")
        print(f"Look for messages like:")
        print(f"  - '🔧 Extracted X code samples from Y matches'")
        print(f"  - '✅ LLM analysis approved for gate_name'")
        print(f"  - '🤖 LLM analyzing gate_name with X code samples'")
        print(f"  - '✅ LLM analysis completed for gate_name'")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        test_dir = Path("test_llm_fixes")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test project")


if __name__ == "__main__":
    main() 