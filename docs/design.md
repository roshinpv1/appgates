# CodeGates Rewrite with PocketFlow - Design Document

## 1. Requirements

### Problem Statement
CodeGates is a comprehensive hard gate validation system that analyzes codebases for compliance with 15 enterprise security and reliability standards. The current implementation is complex with tightly coupled components. We need to rewrite it using PocketFlow for better maintainability, clarity, and AI-driven pattern generation.

### User Perspective
- **Repository Owners**: Want to validate their codebase against enterprise hard gates
- **Security Teams**: Need comprehensive reports on compliance status
- **DevOps Teams**: Require automated validation in CI/CD pipelines

### Success Criteria
- Single command execution for complete validation flow
- Dynamic LLM-powered pattern generation for better accuracy
- Clean, maintainable codebase using PocketFlow
- Identical report quality and features as current system

## 2. Flow Design

### High-Level Flow Pattern
This follows a **Linear Workflow** pattern with **Map-Reduce** elements for gate validation.

```text
flowchart LR
    start[Start] --> fetch[Fetch Repository]
    fetch --> process[Process Codebase]
    process --> extract[Extract Config & Build]
    extract --> prompt[Generate LLM Prompt]
    prompt --> llm[Call LLM for Patterns]
    llm --> validate[Validate Against Patterns]
    validate --> report[Generate Report]
    report --> cleanup[Cleanup]
    cleanup --> endNode[End]
    
    subgraph validate[Validate Against Patterns]
        map[Map: Split by Gates] --> parallel[Parallel Gate Validation]
        parallel --> reduce[Reduce: Combine Results]
    end
```

### Node Breakdown

1. **FetchRepositoryNode**: Clone/download repository to local directory
2. **ProcessCodebaseNode**: Extract file metadata, detect languages, count LOC
3. **ExtractConfigNode**: Extract configuration and build script contents
4. **GeneratePromptNode**: Create comprehensive LLM prompt with metadata and hard gate information
5. **CallLLMNode**: Send prompt to LLM and receive pattern suggestions
6. **ValidateGatesNode**: Apply patterns to codebase using Map-Reduce (map by gates, reduce results)
7. **GenerateReportNode**: Create comprehensive HTML/JSON reports
8. **CleanupNode**: Remove temporary files and directories

## 3. Utilities

### External Utility Functions

1. **Repository Management**
   - `utils/git_operations.py`: Clone repositories, checkout branches
   - `utils/github_api.py`: Download repositories via GitHub API

2. **File Operations**
   - `utils/file_scanner.py`: Recursively scan directories, extract metadata
   - `utils/config_extractor.py`: Extract content from build/config files

3. **LLM Integration**
   - `utils/llm_client.py`: Interface with LLM services (OpenAI, local models)
   - `utils/prompt_builder.py`: Construct structured prompts

4. **Pattern Validation**
   - `utils/pattern_matcher.py`: Apply regex patterns to source code
   - `utils/gate_validator.py`: Validate individual hard gates

5. **Report Generation**
   - `utils/report_builder.py`: Generate HTML/JSON reports
   - `utils/template_engine.py`: Apply report templates

## 4. Data Design

### Shared Store Schema

```python
shared = {
    "request": {
        "repository_url": "https://github.com/owner/repo",
        "branch": "main",
        "github_token": "optional_token",
        "threshold": 70
    },
    "repository": {
        "local_path": "/tmp/codegates_repo_xyz",
        "metadata": {
            "total_files": 150,
            "total_lines": 5000,
            "languages": ["Python", "JavaScript"],
            "file_list": [{"path": "src/main.py", "size": 1024, "language": "Python"}]
        }
    },
    "config": {
        "build_files": {
            "package.json": "content...",
            "requirements.txt": "content..."
        },
        "config_files": {
            "application.yml": "content..."
        },
        "dependencies": ["express", "flask", "spring-boot"]
    },
    "llm": {
        "prompt": "generated prompt text...",
        "response": "LLM response with patterns...",
        "patterns": {
            "STRUCTURED_LOGS": ["pattern1", "pattern2"],
            "RETRY_LOGIC": ["pattern3", "pattern4"]
        }
    },
    "validation": {
        "gate_results": [
            {
                "gate": "STRUCTURED_LOGS",
                "status": "PASS",
                "score": 85.0,
                "matches": [...],
                "details": [...],
                "recommendations": [...]
            }
        ],
        "overall_score": 78.5
    },
    "reports": {
        "html_path": "/tmp/reports/report.html",
        "json_path": "/tmp/reports/report.json"
    }
}
```

## 5. Node Design

### FetchRepositoryNode
- **Type**: Regular Node
- **Prep**: Read repository URL, branch, token from shared store
- **Exec**: Call git_operations.clone_repository() utility
- **Post**: Store local path in shared["repository"]["local_path"]

### ProcessCodebaseNode
- **Type**: Regular Node
- **Prep**: Read local repository path
- **Exec**: Call file_scanner.scan_directory() utility
- **Post**: Store metadata in shared["repository"]["metadata"]

### ExtractConfigNode
- **Type**: Regular Node
- **Prep**: Read repository path and file list
- **Exec**: Call config_extractor.extract_configs() utility
- **Post**: Store config content in shared["config"]

### GeneratePromptNode
- **Type**: Regular Node
- **Prep**: Read metadata, config, and hard gate definitions
- **Exec**: Call prompt_builder.build_comprehensive_prompt() utility
- **Post**: Store prompt in shared["llm"]["prompt"]

### CallLLMNode
- **Type**: Regular Node with retry
- **Prep**: Read generated prompt
- **Exec**: Call llm_client.call_llm() utility
- **Post**: Store response and parsed patterns in shared["llm"]

### ValidateGatesNode
- **Type**: Batch Node (Map-Reduce pattern)
- **Prep**: Read patterns and repository metadata
- **Exec**: For each gate, call gate_validator.validate_gate() utility
- **Post**: Store validation results in shared["validation"]

### GenerateReportNode
- **Type**: Regular Node
- **Prep**: Read validation results and metadata
- **Exec**: Call report_builder.generate_reports() utility
- **Post**: Store report paths in shared["reports"]

### CleanupNode
- **Type**: Regular Node
- **Prep**: Read temporary paths
- **Exec**: Remove temporary directories and files
- **Post**: Mark cleanup complete

## 6. Hard Gates Definition

The system validates 15 enterprise hard gates:

1. **STRUCTURED_LOGS**: Logs Searchable/Available
2. **AVOID_LOGGING_SECRETS**: Avoid Logging Confidential Data
3. **AUDIT_TRAIL**: Create Audit Trail Logs
4. **CORRELATION_ID**: Tracking ID for Logs
5. **LOG_API_CALLS**: Log REST API Calls
6. **LOG_APPLICATION_MESSAGES**: Log Application Messages
7. **UI_ERRORS**: Client UI Errors Logged
8. **RETRY_LOGIC**: Retry Logic
9. **TIMEOUTS**: Timeouts in IO Ops
10. **THROTTLING**: Throttling & Drop Request
11. **CIRCUIT_BREAKERS**: Circuit Breakers
12. **ERROR_LOGS**: Log System Errors
13. **HTTP_CODES**: HTTP Error Codes
14. **UI_ERROR_TOOLS**: Client Error Tracking
15. **AUTOMATED_TESTS**: Automated Tests

## 7. Implementation Strategy

### Phase 1: Core Infrastructure
1. Set up PocketFlow project structure
2. Implement basic utilities (git operations, file scanning)
3. Create simple linear flow with mock LLM

### Phase 2: LLM Integration
1. Implement LLM client and prompt builder
2. Add pattern parsing and validation
3. Test with real LLM responses

### Phase 3: Gate Validation
1. Implement pattern matching utilities
2. Create batch validation for all gates
3. Add fallback patterns for offline mode

### Phase 4: Reporting & Polish
1. Port existing report generation logic
2. Add CLI and server interfaces
3. Optimize performance and add error handling

## 8. Success Metrics

- **Functional**: All 15 hard gates validated correctly
- **Performance**: Complete analysis in under 5 minutes for typical repositories
- **Reliability**: 99% success rate with proper error handling
- **Maintainability**: Clear separation of concerns, easy to modify/extend
- **User Experience**: Single command execution, clear progress indicators 