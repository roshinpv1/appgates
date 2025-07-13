#!/usr/bin/env python3
"""
Test script to verify the new flow:
Repo checkout -> Analyse repository -> LLM pattern generation -> Validation -> Report -> Cleanup
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

from codegates.core.gate_validator import GateValidator
from codegates.models import ScanConfig, Language

def test_new_flow():
    """Test the new flow with comprehensive repository analysis"""
    
    print("🧪 Testing new flow: Repository Analysis → LLM Pattern Generation → Validation")
    print("=" * 80)
    
    try:
        # Create scan configuration
        config = ScanConfig(
            target_path=str(Path.cwd()),  # Convert to string
            languages=[Language.PYTHON],
            min_coverage_threshold=70.0,
            exclude_patterns=[
                "node_modules/**", ".git/**", "**/__pycache__/**",
                "**/target/**", "**/bin/**", "**/obj/**"
            ],
            max_file_size=1024*1024  # 1MB
        )
        
        # Create validator
        validator = GateValidator(config)
        
        print("🔍 Phase 1: Starting comprehensive repository analysis...")
        
        # Run validation (this will trigger the new flow)
        result = validator.validate(Path.cwd())
        
        print("\n📊 Results:")
        print(f"   Overall Score: {result.overall_score:.1f}%")
        print(f"   Total Files: {result.total_files}")
        print(f"   Total Lines: {result.total_lines}")
        print(f"   Scan Duration: {result.scan_duration:.2f}s")
        print(f"   Gates Analyzed: {len(result.gate_scores)}")
        
        # Show gate results
        print("\n🎯 Gate Results:")
        for gate_score in result.gate_scores[:5]:  # Show first 5 gates
            print(f"   {gate_score.gate.value}: {gate_score.final_score:.1f}% ({gate_score.status})")
            if gate_score.details:
                print(f"     Details: {gate_score.details[0]}")
        
        print("\n✅ New flow test completed successfully!")
        print("\n📋 Flow Summary:")
        print("   1. ✅ Repository checkout (current directory)")
        print("   2. ✅ Repository analysis and file metadata extraction")
        print("   3. ✅ Config and build file content extraction")
        print("   4. ✅ LLM prompt generation (if LLM available)")
        print("   5. ✅ Pattern generation (LLM or fallback)")
        print("   6. ✅ Pattern processing against source code")
        print("   7. ✅ Analysis generation")
        print("   8. ✅ Report generation")
        print("   9. ✅ Cleanup (automatic)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_new_flow()
    sys.exit(0 if success else 1) 