from pathlib import Path
import sys

# Add the current directory to Python path for imports
sys.path.append('.')

from codegates.models import ScanConfig, Language, ValidationResult, GateScore
from codegates.core.gate_validator import GateValidator

def run_validation() -> ValidationResult:
    """Run validation and return the result"""
    try:
        # Create scan config
        config = ScanConfig(
            target_path=str(Path.cwd()),  # Current directory
            languages=[Language.PYTHON],  # Start with Python
            exclude_patterns=[],
            include_patterns=[],
            max_file_size=1024*1024,  # 1MB
            follow_symlinks=False,
            min_coverage_threshold=70.0,
            min_quality_threshold=80.0
        )
        
        # Create validator
        validator = GateValidator(config)
        
        # Run validation
        result = validator.validate(Path.cwd())
        
        # Print results
        print(f"\nValidation Results:")
        print(f"Overall Score: {result.overall_score:.1f}%")
        print(f"Total Files: {result.total_files}")
        print(f"Total Lines: {result.total_lines}")
        print(f"\nGate Scores:")
        for gate_score in result.gate_scores:
            print(f"- {gate_score.gate.value}: {gate_score.final_score:.1f}% ({gate_score.status})")
            if gate_score.details:
                print(f"  Details: {gate_score.details[0]}")
        
        # Print critical issues
        if result.critical_issues:
            print("\nCritical Issues:")
            for issue in result.critical_issues:
                print(f"❌ {issue}")
        
        # Print recommendations
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"💡 {rec}")
        
        return result
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    run_validation() 