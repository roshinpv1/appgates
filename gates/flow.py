"""
CodeGates Flow - PocketFlow Implementation
Defines the complete validation workflow using PocketFlow nodes
"""

try:
    from .base import Flow
except ImportError:
    from base import Flow

try:
    # Try relative imports first (when run as module)
    from .nodes import (
        FetchRepositoryNode,
        ProcessCodebaseNode, 
        ExtractConfigNode,
        ValidateGatesNode,
        GenerateReportNode,
        SplunkQueryNode,
        CleanupNode
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from nodes import (
        FetchRepositoryNode,
        ProcessCodebaseNode, 
        ExtractConfigNode,
        ValidateGatesNode,
        GenerateReportNode,
        SplunkQueryNode,
        CleanupNode
    )


def create_validation_flow() -> Flow:
    """
    Create and return the complete CodeGates validation flow.
    
    Flow sequence:
    1. Fetch Repository -> Clone/download repository
    2. Process Codebase -> Extract file metadata and statistics  
    3. Extract Config -> Extract build and config file contents
    4. Validate Gates -> Apply static patterns to codebase (Map-Reduce)
    5. Generate Report -> Create HTML/JSON reports
    6. Cleanup -> Remove temporary files
    
    Note: LLM steps have been removed for static-only operation
    """
    
    # Create all nodes
    fetch_repo = FetchRepositoryNode()
    process_codebase = ProcessCodebaseNode() 
    extract_config = ExtractConfigNode()
    validate_gates = ValidateGatesNode()
    generate_report = GenerateReportNode()
    splunk_query = SplunkQueryNode()
    cleanup = CleanupNode()
    
    # Connect nodes in sequence
    fetch_repo >> process_codebase
    process_codebase >> extract_config  
    extract_config >> validate_gates
    validate_gates >> generate_report
    generate_report >> splunk_query
    splunk_query >> cleanup
    
    # Create and return flow starting with fetch_repo
    return Flow(start=fetch_repo)


def create_static_only_flow() -> Flow:
    """
    Create and return a CodeGates validation flow that uses only static patterns.
    This is now the same as create_validation_flow() since LLM nodes have been removed.
    
    Flow sequence:
    1. Fetch Repository -> Clone/download repository
    2. Process Codebase -> Extract file metadata and statistics  
    3. Extract Config -> Extract build and config file contents
    4. Validate Gates -> Apply static patterns to codebase (Map-Reduce)
    5. Generate Report -> Create HTML/JSON reports
    6. Cleanup -> Remove temporary files
    """
    
    # Create all nodes
    fetch_repo = FetchRepositoryNode()
    process_codebase = ProcessCodebaseNode() 
    extract_config = ExtractConfigNode()
    validate_gates = ValidateGatesNode()
    generate_report = GenerateReportNode()
    splunk_query = SplunkQueryNode()
    cleanup = CleanupNode()
    
    # Connect nodes in sequence
    fetch_repo >> process_codebase
    process_codebase >> extract_config  
    extract_config >> validate_gates
    validate_gates >> generate_report
    generate_report >> splunk_query
    splunk_query >> cleanup
    
    # Create and return flow starting with fetch_repo
    return Flow(start=fetch_repo) 