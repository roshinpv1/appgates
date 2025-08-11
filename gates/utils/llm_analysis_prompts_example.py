"""
Example usage of LLM Analysis Prompts for Success and Failure Gates
Demonstrates how to integrate the prompt generation into the existing gate evaluation system
"""

from typing import Dict, Any, List, Optional
from .llm_analysis_prompts import (
    LLMAnalysisPromptGenerator,
    generate_success_prompt,
    generate_failure_prompt,
    generate_enhanced_success_prompt,
    generate_enhanced_failure_prompt
)


def example_usage():
    """Example of how to use the LLM analysis prompts"""
    
    # Example data
    gate_name = "STRUCTURED_LOGS"
    success_condition_message = "Found 15 structured logging implementations across 12 files"
    failed_condition_message = "Missing structured logging in 8 critical files"
    evaluation_details = "Evaluated 45 files for structured logging patterns"
    pattern_data = "Patterns used: logger.info, structured.*log, json.*log"
    
    # Generate success prompt
    success_prompt = generate_success_prompt(
        gate_name=gate_name,
        success_condition_message=success_condition_message,
        evaluation_details=evaluation_details,
        pattern_data=pattern_data
    )
    
    print("=== SUCCESS PROMPT ===")
    print(success_prompt)
    print("\n" + "="*50 + "\n")
    
    # Generate failure prompt
    failure_prompt = generate_failure_prompt(
        gate_name=gate_name,
        failed_condition_message=failed_condition_message,
        evaluation_details=evaluation_details,
        pattern_data=pattern_data
    )
    
    print("=== FAILURE PROMPT ===")
    print(failure_prompt)
    print("\n" + "="*50 + "\n")
    
    # Example with ALERTING_ACTIONABLE gate
    alerting_success_prompt = generate_success_prompt(
        gate_name="ALERTING_ACTIONABLE",
        success_condition_message="All alerting integrations (Splunk, AppDynamics, ThousandEyes) are configured",
        evaluation_details="Database integration check completed successfully",
        pattern_data=None  # ALERTING_ACTIONABLE doesn't use pattern_data
    )
    
    print("=== ALERTING_ACTIONABLE SUCCESS PROMPT ===")
    print(alerting_success_prompt)
    print("\n" + "="*50 + "\n")
    
    # Example with enhanced context
    additional_context = {
        "Technology Stack": "Java Spring Boot",
        "Project Size": "Medium (500+ files)",
        "Critical Areas": "API endpoints, database operations"
    }
    
    enhanced_success_prompt = generate_enhanced_success_prompt(
        gate_name=gate_name,
        success_condition_message=success_condition_message,
        evaluation_details=evaluation_details,
        pattern_data=pattern_data,
        additional_context=additional_context
    )
    
    print("=== ENHANCED SUCCESS PROMPT ===")
    print(enhanced_success_prompt)


def integrate_with_gate_evaluation(gate_result: Dict[str, Any], pattern_data: Dict[str, Any]) -> str:
    """
    Example function showing how to integrate with existing gate evaluation
    
    Args:
        gate_result: Result from gate evaluation
        pattern_data: Pattern data for the gate
        
    Returns:
        Generated LLM analysis prompt
    """
    
    gate_name = gate_result.get("gate", "UNKNOWN")
    status = gate_result.get("status", "FAIL")
    score = gate_result.get("score", 0.0)
    details = gate_result.get("details", [])
    matches = gate_result.get("matches", [])
    
    # Prepare evaluation details
    evaluation_details = f"Gate: {gate_name}, Status: {status}, Score: {score:.1f}%"
    if details:
        evaluation_details += f"\nDetails: {'; '.join(details)}"
    
    # Prepare condition message
    if status == "PASS":
        condition_message = f"Gate passed with {len(matches)} matches found"
        pattern_data_str = None
        if gate_name in pattern_data:
            patterns = pattern_data[gate_name].get("patterns", [])
            pattern_data_str = f"Patterns used: {', '.join(patterns)}"
        
        return generate_success_prompt(
            gate_name=gate_name,
            success_condition_message=condition_message,
            evaluation_details=evaluation_details,
            pattern_data=pattern_data_str
        )
    else:
        condition_message = f"Gate failed with {len(matches)} matches found"
        pattern_data_str = None
        if gate_name in pattern_data:
            patterns = pattern_data[gate_name].get("patterns", [])
            pattern_data_str = f"Patterns used: {', '.join(patterns)}"
        
        return generate_failure_prompt(
            gate_name=gate_name,
            failed_condition_message=condition_message,
            evaluation_details=evaluation_details,
            pattern_data=pattern_data_str
        )


def batch_generate_prompts(gate_results: List[Dict[str, Any]], pattern_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate prompts for multiple gates
    
    Args:
        gate_results: List of gate evaluation results
        pattern_data: Pattern data for all gates
        
    Returns:
        Dictionary mapping gate names to their analysis prompts
    """
    
    prompts = {}
    
    for gate_result in gate_results:
        gate_name = gate_result.get("gate", "UNKNOWN")
        prompt = integrate_with_gate_evaluation(gate_result, pattern_data)
        prompts[gate_name] = prompt
    
    return prompts


if __name__ == "__main__":
    # Run the example
    example_usage() 