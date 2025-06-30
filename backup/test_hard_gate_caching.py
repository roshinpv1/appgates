#!/usr/bin/env python3
"""
Test script to investigate hard gate analysis caching
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the current directory to Python path for imports
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


def create_test_project():
    """Create a test project to analyze"""
    
    test_dir = Path("test_cache_project")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple Python file with patterns
    test_file = test_dir / "main.py"
    test_file.write_text("""
import logging
import json
from datetime import datetime

# Structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_user_data(user_id, password):
    \"\"\"Process user data with logging\"\"\"
    
    # Avoid logging secrets - GOOD
    logger.info(f"Processing user data for user_id: {user_id}")
    
    # This would be BAD - logging secrets
    # logger.info(f"User password: {password}")
    
    try:
        # Some processing logic
        result = {"user_id": user_id, "processed": True}
        
        # Structured logging - GOOD
        logger.info("User data processed", extra={
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        # Error logging - GOOD
        logger.error(f"Failed to process user data: {str(e)}", extra={
            "user_id": user_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise

if __name__ == "__main__":
    process_user_data("user123", "secret_password")
""")
    
    return test_dir


def test_caching_behavior():
    """Test if hard gate analysis has caching behavior"""
    
    print("🔍 Testing Hard Gate Caching Behavior")
    print("=" * 60)
    
    # Create test project
    test_dir = create_test_project()
    print(f"✅ Created test project at: {test_dir}")
    
    # Configure environment
    env_loader = EnvironmentLoader()
    
    # Check cache configuration
    cache_enabled = env_loader.get_config_value("CODEGATES_CACHE_ENABLED", "true").lower() == "true"
    cache_ttl = int(env_loader.get_config_value("CODEGATES_CACHE_TTL", "3600"))
    cache_dir = env_loader.get_config_value("CODEGATES_CACHE_DIR", ".cache")
    
    print(f"📊 Cache Configuration:")
    print(f"  - Enabled: {cache_enabled}")
    print(f"  - TTL: {cache_ttl} seconds")
    print(f"  - Directory: {cache_dir}")
    
    # Check if cache directory exists
    cache_path = Path(cache_dir)
    if cache_path.exists():
        print(f"  - Cache directory exists: {cache_path.absolute()}")
        cache_files = list(cache_path.rglob("*"))
        print(f"  - Cache files found: {len(cache_files)}")
        for cache_file in cache_files[:5]:  # Show first 5
            print(f"    - {cache_file}")
    else:
        print(f"  - Cache directory does not exist: {cache_path.absolute()}")
    
    # Configure scan
    config = ScanConfig(
        target_path=str(test_dir),
        languages=[Language.PYTHON],
        exclude_patterns=['.git', '__pycache__']
    )
    
    # Create LLM manager
    llm_config = LLMConfig(
        provider=LLMProvider.LOCAL,
        model="meta-llama-3.1-8b-instruct",
        base_url="http://localhost:1234/v1",
        temperature=0.1
    )
    llm_manager = LLMIntegrationManager(llm_config)
    
    # Create gate validator
    validator = GateValidator(config)
    
    print(f"\n🚀 Running First Hard Gate Analysis...")
    start_time = time.time()
    
    # First analysis
    result1 = validator.validate(test_dir, llm_manager)
    
    first_duration = time.time() - start_time
    print(f"✅ First analysis completed in {first_duration:.2f} seconds")
    print(f"  - Gates analyzed: {len(result1.gate_scores)}")
    print(f"  - Overall score: {result1.overall_score:.1f}")
    
    # Check if any cache files were created
    if cache_path.exists():
        cache_files_after_first = list(cache_path.rglob("*"))
        print(f"  - Cache files after first run: {len(cache_files_after_first)}")
    
    print(f"\n🔄 Running Second Hard Gate Analysis (to test caching)...")
    start_time = time.time()
    
    # Second analysis (should use cache if available)
    result2 = validator.validate(test_dir, llm_manager)
    
    second_duration = time.time() - start_time
    print(f"✅ Second analysis completed in {second_duration:.2f} seconds")
    print(f"  - Gates analyzed: {len(result2.gate_scores)}")
    print(f"  - Overall score: {result2.overall_score:.1f}")
    
    # Check if any cache files were created
    if cache_path.exists():
        cache_files_after_second = list(cache_path.rglob("*"))
        print(f"  - Cache files after second run: {len(cache_files_after_second)}")
    
    # Compare results
    print(f"\n📊 Caching Analysis:")
    print(f"  - First run duration: {first_duration:.2f}s")
    print(f"  - Second run duration: {second_duration:.2f}s")
    
    if second_duration < first_duration * 0.8:  # 20% faster
        print(f"  - ✅ Second run was significantly faster - likely using cache")
        print(f"  - Speed improvement: {((first_duration - second_duration) / first_duration * 100):.1f}%")
    else:
        print(f"  - ❓ No significant speed improvement - cache may not be implemented")
    
    # Compare gate scores
    print(f"\n🔍 Gate Score Comparison:")
    for i, (gate1, gate2) in enumerate(zip(result1.gate_scores, result2.gate_scores)):
        if gate1.gate == gate2.gate:
            scores_match = abs(gate1.final_score - gate2.final_score) < 0.01
            print(f"  - {gate1.gate.value}: {gate1.final_score:.1f} vs {gate2.final_score:.1f} {'✅' if scores_match else '❌'}")
    
    # Check specific cache locations
    print(f"\n📁 Checking Specific Cache Locations:")
    
    # Check for gate-specific cache files
    possible_cache_locations = [
        ".cache",
        "cache",
        "codegates_cache",
        ".codegates_cache",
        f"{test_dir}/.cache",
        "intake/cache"
    ]
    
    for cache_loc in possible_cache_locations:
        cache_path = Path(cache_loc)
        if cache_path.exists():
            print(f"  - Found cache directory: {cache_path.absolute()}")
            cache_files = list(cache_path.rglob("*"))
            print(f"    - Files: {len(cache_files)}")
            for cache_file in cache_files[:3]:  # Show first 3
                if cache_file.is_file():
                    print(f"      - {cache_file.name} ({cache_file.stat().st_size} bytes)")
    
    # Check for in-memory caching indicators
    print(f"\n🧠 Checking In-Memory Cache Indicators:")
    
    # Check LLM availability cache
    if hasattr(llm_manager, '_availability_cache'):
        print(f"  - LLM availability cache: {llm_manager._availability_cache}")
        print(f"  - Last availability check: {llm_manager._last_availability_check}")
    
    # Check if validator has any cache attributes
    validator_attrs = [attr for attr in dir(validator) if 'cache' in attr.lower()]
    if validator_attrs:
        print(f"  - Validator cache attributes: {validator_attrs}")
    else:
        print(f"  - No cache attributes found in validator")
    
    return {
        'first_duration': first_duration,
        'second_duration': second_duration,
        'cache_enabled': cache_enabled,
        'cache_dir': cache_dir,
        'results_match': result1.overall_score == result2.overall_score
    }


def investigate_cache_implementation():
    """Investigate the cache implementation in the codebase"""
    
    print(f"\n🔬 Investigating Cache Implementation:")
    print("=" * 60)
    
    # Check if there's a cache manager class
    cache_related_files = []
    
    # Search for cache-related files
    for root, dirs, files in os.walk("codegates"):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'cache' in content.lower() and ('class' in content or 'def' in content):
                            cache_related_files.append(file_path)
                except:
                    pass
    
    print(f"📁 Files with cache-related code:")
    for file_path in cache_related_files:
        print(f"  - {file_path}")
    
    # Check environment loader for cache configuration
    env_loader = EnvironmentLoader()
    cache_config = {}
    
    cache_vars = [
        "CODEGATES_CACHE_ENABLED",
        "CODEGATES_CACHE_TTL", 
        "CODEGATES_CACHE_DIR",
        "CODEGATES_CLEAR_CACHE_ON_START"
    ]
    
    for var in cache_vars:
        value = env_loader.get_config_value(var, "NOT_SET")
        cache_config[var] = value
    
    print(f"\n⚙️ Cache Configuration from Environment:")
    for key, value in cache_config.items():
        print(f"  - {key}: {value}")
    
    return cache_config


def main():
    """Main test function"""
    
    print("🧪 Hard Gate Caching Investigation")
    print("=" * 80)
    
    try:
        # Test caching behavior
        cache_results = test_caching_behavior()
        
        # Investigate cache implementation
        cache_config = investigate_cache_implementation()
        
        # Summary
        print(f"\n📋 Summary:")
        print(f"  - Cache configuration enabled: {cache_config.get('CODEGATES_CACHE_ENABLED', 'NOT_SET')}")
        print(f"  - First analysis time: {cache_results['first_duration']:.2f}s")
        print(f"  - Second analysis time: {cache_results['second_duration']:.2f}s")
        print(f"  - Results consistent: {cache_results['results_match']}")
        
        if cache_results['second_duration'] < cache_results['first_duration'] * 0.8:
            print(f"  - ✅ Caching appears to be working")
        else:
            print(f"  - ❓ No clear evidence of caching for hard gate analysis")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        test_dir = Path("test_cache_project")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test project")


if __name__ == "__main__":
    main() 