"""
Integration Example: Using LLM Analysis Prompts with Existing Gate Evaluation
Shows how to integrate the new prompt generation with the current gate evaluation workflow
"""

from typing import Dict, Any, List
from .llm_analysis_prompts import (
    generate_success_prompt,
    generate_failure_prompt,
    LLMAnalysisPromptGenerator
)


def integrate_with_gate_evaluation(gate_result: Dict[str, Any], pattern_data: Dict[str, Any]) -> str:
    """
    Generate LLM analysis prompt from gate evaluation result
    
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


def integrate_with_validate_gates_node(gate_results: List[Dict[str, Any]], pattern_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Example integration with ValidateGatesNode results
    
    This function shows how to integrate the LLM analysis prompts with the existing
    gate validation workflow in ValidateGatesNode.
    
    Args:
        gate_results: Results from ValidateGatesNode.exec()
        pattern_data: Pattern data from LLM pattern generation
        
    Returns:
        Dictionary mapping gate names to their analysis prompts
    """
    
    print("🔍 Generating LLM analysis prompts for gate results...")
    
    # Generate prompts for all gates
    prompts = batch_generate_prompts(gate_results, pattern_data)
    
    # Log the generated prompts
    for gate_name, prompt in prompts.items():
        print(f"   📝 Generated prompt for {gate_name} ({len(prompt)} characters)")
    
    return prompts


def process_gate_with_llm_analysis(gate_result: Dict[str, Any], pattern_data: Dict[str, Any], llm_client=None):
    """
    Example of processing a single gate with LLM analysis
    
    Args:
        gate_result: Single gate evaluation result
        pattern_data: Pattern data for the gate
        llm_client: LLM client instance (optional)
        
    Returns:
        LLM analysis result (if llm_client provided) or just the prompt
    """
    
    gate_name = gate_result.get("gate", "UNKNOWN")
    status = gate_result.get("status", "FAIL")
    
    print(f"🤖 Processing {gate_name} ({status}) with LLM analysis...")
    
    # Generate the analysis prompt
    prompt = integrate_with_gate_evaluation(gate_result, pattern_data)
    
    print(f"   📋 Generated prompt ({len(prompt)} characters)")
    
    # If LLM client is provided, make the call
    if llm_client:
        try:
            print(f"   🔗 Calling LLM for analysis...")
            response = llm_client.call_llm(
                prompt,
                gate_name=gate_name,
                conversation_type="gate_analysis",
                context={"gate_status": status},
                metadata={"analysis_type": "gate_evaluation"}
            )
            
            print(f"   ✅ LLM analysis completed ({len(response)} characters)")
            return {
                "gate_name": gate_name,
                "status": status,
                "prompt": prompt,
                "analysis": response
            }
            
        except Exception as e:
            print(f"   ❌ LLM analysis failed: {e}")
            return {
                "gate_name": gate_name,
                "status": status,
                "prompt": prompt,
                "error": str(e)
            }
    else:
        return {
            "gate_name": gate_name,
            "status": status,
            "prompt": prompt
        }


def example_integration_workflow():
    """
    Example of a complete integration workflow
    """
    
    # Simulate gate evaluation results (similar to what ValidateGatesNode produces)
    gate_results = [
        {
            "gate": "STRUCTURED_LOGS",
            "status": "PASS",
            "score": 85.0,
            "details": ["Found structured logging in 12 files", "All critical files have proper logging"],
            "matches": [
                {"file": "src/main/java/com/app/Controller.java", "pattern": "logger.info"},
                {"file": "src/main/java/com/app/Service.java", "pattern": "structured.*log"}
            ],
            "patterns_used": 3,
            "matches_found": 15
        },
        {
            "gate": "ALERTING_ACTIONABLE",
            "status": "FAIL",
            "score": 30.0,
            "details": ["Missing Splunk integration", "AppDynamics not configured"],
            "matches": [],
            "patterns_used": 0,
            "matches_found": 0
        },
        {
            "gate": "AVOID_LOGGING_SECRETS",
            "status": "PASS",
            "score": 95.0,
            "details": ["No secrets found in logging statements"],
            "matches": [],
            "patterns_used": 5,
            "matches_found": 0
        }
    ]
    
    # Simulate pattern data (similar to what LLM pattern generation produces)
    pattern_data = {
        "STRUCTURED_LOGS": {
            "patterns": ["logger.info", "structured.*log", "json.*log"],
            "description": "Structured logging patterns for Java applications",
            "significance": "Critical for monitoring and debugging"
        },
        "ALERTING_ACTIONABLE": {
            "patterns": [],
            "description": "Database integration check",
            "significance": "Ensures alerting is actionable"
        },
        "AVOID_LOGGING_SECRETS": {
            "patterns": ["password.*log", "secret.*log", "token.*log"],
            "description": "Security patterns to prevent secret logging",
            "significance": "Critical for security compliance"
        }
    }
    
    print("🚀 Starting integration workflow example...")
    print(f"   📊 Processing {len(gate_results)} gate results")
    
    # Generate all prompts
    prompts = integrate_with_validate_gates_node(gate_results, pattern_data)
    
    print(f"\n📋 Generated {len(prompts)} analysis prompts")
    
    # Show example prompts
    for gate_name, prompt in prompts.items():
        print(f"\n=== {gate_name} PROMPT ===")
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
        print("=" * 50)
    
    # Process individual gates
    print(f"\n🔍 Processing individual gates...")
    
    for gate_result in gate_results:
        result = process_gate_with_llm_analysis(gate_result, pattern_data)
        print(f"   ✅ {result['gate_name']}: {result['status']} - Prompt generated")
    
    print(f"\n🎉 Integration workflow completed successfully!")


if __name__ == "__main__":
    example_integration_workflow() 