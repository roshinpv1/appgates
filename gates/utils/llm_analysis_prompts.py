"""
LLM Analysis Prompts for Success and Failure Gates
Handles prompt generation for gate analysis with different logic for ALERTING_ACTIONABLE vs other gates
"""

from typing import Dict, Any, List, Optional


class LLMAnalysisPromptGenerator:
    """Generates LLM analysis prompts for success and failure gate conditions"""
    
    @staticmethod
    def generate_success_prompt(
        gate_name: str,
        success_condition_message: str,
        evaluation_details: str,
        pattern_data: Optional[str] = None
    ) -> str:
        """
        Generate LLM analysis prompt for success gates
        
        Args:
            gate_name: Name of the gate being analyzed
            success_condition_message: Message describing successful conditions
            evaluation_details: Details of the evaluation
            pattern_data: Pattern data if available
            
        Returns:
            Formatted prompt string for LLM analysis
        """
        
        if gate_name == "ALERTING_ACTIONABLE":
            # Special prompt for ALERTING_ACTIONABLE gate
            prompt = (
                "Analyze the logs below and provide:\n"
                "- A descriptive summary (max 200 words) Strictly Do not include any percentage or Score in report\n"
                "Strictly Do not include any percentage or Score in report, like passed with this percentage or such\n"
                "\nLogs:\n"
                f"{success_condition_message}\n"
                "\nEvaluation Details:\n"
                f"{evaluation_details}\n"
            )
        else:
            # Standard prompt for other gates
            prompt = (
                "Analyze the logs below and provide:\n"
                "- Key insights for each condition Strictly Do not include any percentage in report, referencing relevant names and patterns\n"
                "- Actionable recommendations for improvement\n"
                "\nLogs:\n"
                f"{success_condition_message}\n"
                "\nEvaluation Details:\n"
                f"{evaluation_details}\n"
            )
            
            # Add pattern data if available
            if pattern_data:
                prompt += f"\nPatterns Used:\n{pattern_data}\n"
            
            prompt += (
                "- A descriptive summary (max 200 words) Strictly Do not include any percentage or Score in report\n"
                "Strictly Do not include any percentage or Score in report, like passed with this percentage or such\n"
            )
        
        return prompt
    
    @staticmethod
    def generate_failure_prompt(
        gate_name: str,
        failed_condition_message: str,
        evaluation_details: str,
        pattern_data: Optional[str] = None
    ) -> str:
        """
        Generate LLM analysis prompt for failure gates
        
        Args:
            gate_name: Name of the gate being analyzed
            failed_condition_message: Message describing failed conditions
            evaluation_details: Details of the evaluation
            pattern_data: Pattern data if available
            
        Returns:
            Formatted prompt string for LLM analysis
        """
        
        if gate_name == "ALERTING_ACTIONABLE":
            # Special prompt for ALERTING_ACTIONABLE gate failures
            prompt = (
                "Analyze the logs below and provide for each failed condition:\n"
                "- Brief descriptive summary (max 200 words) Strictly Do not include any percentage or Score in report\n"
                "Strictly Do not include any percentage or Score in report, like passed with this percentage or such\n"
                "- recommendation for Failures: Setup actionable Alerts (max 100 words)\n"
                "\nLogs:\n"
                f"{failed_condition_message}\n"
                "\nEvaluation Details:\n"
                f"{evaluation_details}\n"
            )
        else:
            # Standard prompt for other gate failures
            prompt = (
                "Analyze the logs below and provide for each failed condition:\n"
                "- Brief descriptive summary (max 200 words) Strictly Do not include any percentage or Score in report\n"
                "Strictly Do not include any percentage or Score in report, like passed with this percentage or such\n"
                "- Insights on the scanning pattern (max 100 words) Strictly Do not include any percentage\n"
                "- recommendation for Failures: (max 100 words)\n"
                "Reference the names and patterns from the patterns file for each condition.\n"
                "\nLogs:\n"
                f"{failed_condition_message}\n"
                "\nEvaluation Details:\n"
                f"{evaluation_details}\n"
            )
            
            # Add pattern data if available
            if pattern_data:
                prompt += f"\nPatterns Used:\n{pattern_data}\n"
        
        return prompt
    
    @staticmethod
    def generate_enhanced_success_prompt(
        gate_name: str,
        success_condition_message: str,
        evaluation_details: str,
        pattern_data: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate enhanced LLM analysis prompt for success gates with additional context
        
        Args:
            gate_name: Name of the gate being analyzed
            success_condition_message: Message describing successful conditions
            evaluation_details: Details of the evaluation
            pattern_data: Pattern data if available
            additional_context: Additional context data for enhanced analysis
            
        Returns:
            Formatted prompt string for LLM analysis
        """
        
        base_prompt = LLMAnalysisPromptGenerator.generate_success_prompt(
            gate_name, success_condition_message, evaluation_details, pattern_data
        )
        
        # Add enhanced context if available
        if additional_context:
            context_section = "\nAdditional Context:\n"
            for key, value in additional_context.items():
                context_section += f"- {key}: {value}\n"
            base_prompt += context_section
        
        return base_prompt
    
    @staticmethod
    def generate_enhanced_failure_prompt(
        gate_name: str,
        failed_condition_message: str,
        evaluation_details: str,
        pattern_data: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate enhanced LLM analysis prompt for failure gates with additional context
        
        Args:
            gate_name: Name of the gate being analyzed
            failed_condition_message: Message describing failed conditions
            evaluation_details: Details of the evaluation
            pattern_data: Pattern data if available
            additional_context: Additional context data for enhanced analysis
            
        Returns:
            Formatted prompt string for LLM analysis
        """
        
        base_prompt = LLMAnalysisPromptGenerator.generate_failure_prompt(
            gate_name, failed_condition_message, evaluation_details, pattern_data
        )
        
        # Add enhanced context if available
        if additional_context:
            context_section = "\nAdditional Context:\n"
            for key, value in additional_context.items():
                context_section += f"- {key}: {value}\n"
            base_prompt += context_section
        
        return base_prompt


# Convenience functions for easy access
def generate_success_prompt(
    gate_name: str,
    success_condition_message: str,
    evaluation_details: str,
    pattern_data: Optional[str] = None
) -> str:
    """Convenience function to generate success prompt"""
    return LLMAnalysisPromptGenerator.generate_success_prompt(
        gate_name, success_condition_message, evaluation_details, pattern_data
    )


def generate_failure_prompt(
    gate_name: str,
    failed_condition_message: str,
    evaluation_details: str,
    pattern_data: Optional[str] = None
) -> str:
    """Convenience function to generate failure prompt"""
    return LLMAnalysisPromptGenerator.generate_failure_prompt(
        gate_name, failed_condition_message, evaluation_details, pattern_data
    )


def generate_enhanced_success_prompt(
    gate_name: str,
    success_condition_message: str,
    evaluation_details: str,
    pattern_data: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience function to generate enhanced success prompt"""
    return LLMAnalysisPromptGenerator.generate_enhanced_success_prompt(
        gate_name, success_condition_message, evaluation_details, pattern_data, additional_context
    )


def generate_enhanced_failure_prompt(
    gate_name: str,
    failed_condition_message: str,
    evaluation_details: str,
    pattern_data: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience function to generate enhanced failure prompt"""
    return LLMAnalysisPromptGenerator.generate_enhanced_failure_prompt(
        gate_name, failed_condition_message, evaluation_details, pattern_data, additional_context
    ) 