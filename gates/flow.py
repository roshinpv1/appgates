"""
CodeGates Flow - PocketFlow Implementation
Defines the complete validation workflow using PocketFlow nodes
"""

from pocketflow import Flow
try:
    # Try relative imports first (when run as module)
    from .nodes import (
        FetchRepositoryNode,
        ProcessCodebaseNode, 
        ExtractConfigNode,
        GeneratePromptNode,
        CallLLMNode,
        ValidateGatesNode,
        GenerateReportNode,
        CleanupNode
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from nodes import (
        FetchRepositoryNode,
        ProcessCodebaseNode, 
        ExtractConfigNode,
        GeneratePromptNode,
        CallLLMNode,
        ValidateGatesNode,
        GenerateReportNode,
        CleanupNode
    )


def create_validation_flow() -> Flow:
    """
    Create and return the complete CodeGates validation flow.
    
    Flow sequence:
    1. Fetch Repository -> Clone/download repository
    2. Process Codebase -> Extract file metadata and statistics  
    3. Extract Config -> Extract build and config file contents
    4. Generate Prompt -> Create comprehensive LLM prompt
    5. Call LLM -> Get AI-generated patterns for validation
    6. Validate Gates -> Apply patterns to codebase (Map-Reduce)
    7. Generate Report -> Create HTML/JSON reports
    8. Cleanup -> Remove temporary files
    """
    
    # Create all nodes
    fetch_repo = FetchRepositoryNode()
    process_codebase = ProcessCodebaseNode() 
    extract_config = ExtractConfigNode()
    generate_prompt = GeneratePromptNode()
    call_llm = CallLLMNode(max_retries=3, wait=2.0)
    validate_gates = ValidateGatesNode()
    generate_report = GenerateReportNode()
    cleanup = CleanupNode()
    
    # Connect nodes in sequence
    fetch_repo >> process_codebase
    process_codebase >> extract_config  
    extract_config >> generate_prompt
    generate_prompt >> call_llm
    call_llm >> validate_gates
    validate_gates >> generate_report
    generate_report >> cleanup
    
    # Create and return flow starting with fetch_repo
    return Flow(start=fetch_repo)


def create_static_only_flow() -> Flow:
    """
    Create and return a CodeGates validation flow that bypasses LLM steps.
    This flow uses only static patterns for validation while keeping all LLM code intact.
    
    Flow sequence:
    1. Fetch Repository -> Clone/download repository
    2. Process Codebase -> Extract file metadata and statistics  
    3. Extract Config -> Extract build and config file contents
    4. Validate Gates -> Apply static patterns to codebase (Map-Reduce)
    5. Generate Report -> Create HTML/JSON reports
    6. Cleanup -> Remove temporary files
    """
    
    # Create all nodes (keeping LLM nodes for future use)
    fetch_repo = FetchRepositoryNode()
    process_codebase = ProcessCodebaseNode() 
    extract_config = ExtractConfigNode()
    generate_prompt = GeneratePromptNode()
    call_llm = CallLLMNode(max_retries=3, wait=2.0)
    validate_gates = ValidateGatesNode()
    generate_report = GenerateReportNode()
    cleanup = CleanupNode()
    
    # Connect nodes in sequence, bypassing LLM steps
    fetch_repo >> process_codebase
    process_codebase >> extract_config  
    # Skip: extract_config >> generate_prompt
    # Skip: generate_prompt >> call_llm
    # Skip: call_llm >> validate_gates
    extract_config >> validate_gates  # Direct connection, bypassing LLM
    validate_gates >> generate_report
    generate_report >> cleanup
    
    # Create and return flow starting with fetch_repo
    return Flow(start=fetch_repo) 