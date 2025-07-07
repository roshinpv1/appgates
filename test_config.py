#!/usr/bin/env python3
"""
Test script to verify gate configuration loading
"""

import logging
from codegates.core.config_manager import get_config_manager
from codegates.core.pattern_loader import PatternLoader
from codegates.core.gate_config_validator import GateConfigValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config_loading():
    """Test gate configuration loading"""
    try:
        # Get config manager instance
        config_manager = get_config_manager()
        config = config_manager.config
        
        logger.info("Configuration loaded successfully")
        logger.info(f"Found {len(config.get('hard_gates', []))} gates")
        
        # Test pattern loader
        pattern_loader = PatternLoader()
        gates = pattern_loader.get_all_gates()
        logger.info(f"Pattern loader found {len(gates)} gates")
        
        # Test pattern statistics
        stats = pattern_loader.get_pattern_statistics()
        logger.info("Pattern statistics:")
        logger.info(f"- Total gates: {stats['total_gates']}")
        logger.info(f"- Total patterns: {stats['total_patterns']}")
        logger.info(f"- Languages supported: {', '.join(stats['languages_supported'])}")
        
        # Test validator
        validator = GateConfigValidator()
        validation_results = validator.validate_config()
        logger.info(f"\nValidation results for {len(validation_results)} gates:")
        
        for gate_key, result in validation_results.items():
            logger.info(f"\nGate: {result.gate_name}")
            logger.info(f"Overall Coverage: {result.overall_coverage:.1f}%")
            
            if result.issues:
                logger.info("Issues:")
                for issue in result.issues:
                    logger.info(f"- {issue}")
            
            if result.pattern_coverage:
                logger.info("Pattern Coverage:")
                for lang, coverage in result.pattern_coverage.items():
                    logger.info(f"  - {lang}: {coverage.coverage_percentage:.1f}% (Missing: {len(coverage.missing_patterns)})")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing configuration: {e}")
        return False

if __name__ == "__main__":
    success = test_config_loading()
    if success:
        logger.info("\nConfiguration test completed successfully")
    else:
        logger.error("\nConfiguration test failed") 