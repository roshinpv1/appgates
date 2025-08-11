"""
CodeGates Agent - Main Agent Implementation
Intelligent agent for enterprise gate validation using Google ADK with LiteLLM
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from google.adk.agents import Agent
    from google.adk.tools.base_tool import BaseTool
    from google.adk.tools.function_tool import FunctionTool
    from google.adk.tools.agent_tool import AgentTool
    from google.adk.runners import InMemoryRunner
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("⚠️ Google ADK not available. Install with: pip install google-adk")

# Import existing CodeGates functionality
try:
    from gates.utils.hard_gates import HARD_GATES, get_gate_number
    from gates.utils.git_operations import clone_repository, cleanup_repository
    from gates.utils.file_scanner import scan_directory
    from gates.criteria_evaluator import EnhancedGateEvaluator
    from gates.utils.splunk_integration import execute_splunk_query
    from gates.utils.appdynamics_integration import analyze_appdynamics_coverage
    from gates.utils.playwright_integration import collect_web_portal_evidence
    from gates.utils.llm_client import create_llm_client_from_env, LLMClient, LLMConfig
    CODEGATES_AVAILABLE = True
except ImportError as e:
    CODEGATES_AVAILABLE = False
    print(f"⚠️ CodeGates functionality not available: {e}")

# Import LiteLLM
try:
    import litellm
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    print("⚠️ LiteLLM not available. Install with: pip install litellm")


# Import local configuration
try:
    from .litellm_config import setup_litellm_environment, LiteLLMConfig
    LITELLM_CONFIG_AVAILABLE = True
except ImportError:
    LITELLM_CONFIG_AVAILABLE = False
    print("⚠️ LiteLLM configuration not available")


# =============================================================================
# AGENT INSTRUCTIONS
# =============================================================================

AGENT_INSTRUCTION = """
You are the CodeGates Validation Agent, an expert in enterprise application validation and gate compliance.

**YOUR ROLE:**
You are a specialized agent that helps users validate their codebases against enterprise standards and compliance requirements. You can analyze repositories, validate hard gates, collect evidence from external sources, and generate comprehensive reports.

**YOUR PROCESS:**
1. **Understand the user's request** - Analyze what validation they need
2. **Identify appropriate tools** - Choose the right tools for the task
3. **Execute validation** - Run the necessary validation steps
4. **Collect evidence** - Gather supporting evidence from external sources
5. **Generate reports** - Create comprehensive validation reports
6. **Provide recommendations** - Offer actionable improvement suggestions

**AVAILABLE GATES:**
- ALERTING_ACTIONABLE: Ensure all alerting integrations are present
- STRUCTURED_LOGS: Ensure logs are structured and searchable
- AVOID_LOGGING_SECRETS: Prevent sensitive data logging
- AUDIT_TRAIL: Ensure proper audit trails
- CORRELATION_ID: Ensure correlation IDs for tracing
- LOG_API_CALLS: Ensure API calls are logged
- CLIENT_UI_ERRORS: Ensure client-side error tracking
- RETRY_LOGIC: Ensure proper retry mechanisms
- TIMEOUT_IO: Ensure proper timeout handling
- THROTTLING: Ensure rate limiting implementation
- CIRCUIT_BREAKERS: Ensure circuit breaker patterns
- HTTP_ERROR_CODES: Ensure proper HTTP error handling
- URL_MONITORING: Ensure URL monitoring
- AUTOMATED_TESTS: Ensure comprehensive test coverage
- AUTO_SCALE: Ensure auto-scaling capabilities

**TOOLS AVAILABLE:**
1. **analyze_repository**: Clone and analyze repository structure
2. **validate_gates**: Validate specific gates against the codebase
3. **collect_evidence**: Collect evidence from external sources
4. **generate_report**: Generate comprehensive validation reports

**RESPONSE FORMAT:**
- Always be helpful, thorough, and provide clear explanations
- Use markdown formatting for better readability
- Provide actionable recommendations
- Include specific examples when possible
- Break down complex information into digestible sections

**EXAMPLE INTERACTIONS:**
- "Validate the repository at https://github.com/company/myapp"
- "What gates are applicable for a Python web application?"
- "Generate a report for the validation results"
- "Collect evidence from Splunk and AppDynamics"
- "Explain the ALERTING_ACTIONABLE gate requirements"
"""


# =============================================================================
# TOOLS IMPLEMENTATION
# =============================================================================

class RepositoryAnalysisTool(BaseTool):
    """Tool for analyzing repository structure and codebase"""
    
    name = "analyze_repository"
    description = "Clone and analyze a repository to understand its structure, technologies, and patterns"
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Analyze repository structure and codebase"""
        try:
            repo_url = args["repository_url"]
            branch = args.get("branch", "main")
            github_token = args.get("github_token")
            
            print(f"🔍 Analyzing repository: {repo_url}")
            
            # Clone repository using existing functionality
            if CODEGATES_AVAILABLE:
                repo_path = clone_repository(
                    repo_url=repo_url,
                    branch=branch,
                    github_token=github_token
                )
                
                # Scan directory structure
                file_structure = scan_directory(repo_path)
                
                # Analyze technologies
                technologies = self._analyze_technologies(file_structure)
                
                # Determine applicable gates
                applicable_gates = self._determine_applicable_gates(technologies)
                
                return {
                    "status": "success",
                    "repository_path": repo_path,
                    "file_structure": file_structure,
                    "technologies": technologies,
                    "applicable_gates": applicable_gates,
                    "total_files": len(file_structure),
                    "message": f"Repository analyzed successfully. Found {len(file_structure)} files."
                }
            else:
                return {
                    "status": "error",
                    "message": "CodeGates functionality not available",
                    "data": None
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing repository: {str(e)}",
                "data": None
            }
    
    def _analyze_technologies(self, file_structure: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze technologies used in the codebase"""
        technologies = {
            "languages": set(),
            "frameworks": set(),
            "databases": set(),
            "cloud_platforms": set(),
            "monitoring_tools": set()
        }
        
        for file_info in file_structure:
            filename = file_info.get("name", "").lower()
            filepath = file_info.get("path", "").lower()
            
            # Detect programming languages
            if filename.endswith(('.py', '.pyc')):
                technologies["languages"].add("Python")
            elif filename.endswith(('.js', '.jsx', '.ts', '.tsx')):
                technologies["languages"].add("JavaScript/TypeScript")
            elif filename.endswith(('.java', '.class')):
                technologies["languages"].add("Java")
            elif filename.endswith(('.go')):
                technologies["languages"].add("Go")
            elif filename.endswith(('.rb')):
                technologies["languages"].add("Ruby")
            elif filename.endswith(('.php')):
                technologies["languages"].add("PHP")
            elif filename.endswith(('.cs')):
                technologies["languages"].add("C#")
            
            # Detect frameworks
            if any(framework in filepath for framework in ['django', 'flask', 'fastapi']):
                technologies["frameworks"].add("Django/Flask/FastAPI")
            if any(framework in filepath for framework in ['react', 'vue', 'angular']):
                technologies["frameworks"].add("React/Vue/Angular")
            if any(framework in filepath for framework in ['spring', 'hibernate']):
                technologies["frameworks"].add("Spring/Hibernate")
            
            # Detect databases
            if any(db in filepath for db in ['mysql', 'postgresql', 'mongodb', 'redis']):
                technologies["databases"].add("Database")
            
            # Detect cloud platforms
            if any(cloud in filepath for cloud in ['aws', 'azure', 'gcp', 'kubernetes']):
                technologies["cloud_platforms"].add("Cloud Platform")
            
            # Detect monitoring tools
            if any(tool in filepath for tool in ['splunk', 'appdynamics', 'newrelic', 'datadog']):
                technologies["monitoring_tools"].add("Monitoring Tool")
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in technologies.items()}
    
    def _determine_applicable_gates(self, technologies: Dict[str, Any]) -> List[str]:
        """Determine which gates are applicable based on technologies"""
        applicable_gates = []
        
        # All gates are generally applicable, but some are more relevant based on tech stack
        for gate in HARD_GATES:
            gate_name = gate["name"]
            
            # Always include critical gates
            if gate.get("priority") == "critical":
                applicable_gates.append(gate_name)
                continue
            
            # Include based on technology relevance
            if "Python" in technologies["languages"] and "STRUCTURED_LOGS" in gate_name:
                applicable_gates.append(gate_name)
            elif "JavaScript" in technologies["languages"] and "CLIENT_UI_ERRORS" in gate_name:
                applicable_gates.append(gate_name)
            elif "Database" in technologies["databases"] and "AUDIT_TRAIL" in gate_name:
                applicable_gates.append(gate_name)
            elif "Monitoring Tool" in technologies["monitoring_tools"] and "ALERTING_ACTIONABLE" in gate_name:
                applicable_gates.append(gate_name)
            else:
                # Include other gates by default
                applicable_gates.append(gate_name)
        
        return list(set(applicable_gates))  # Remove duplicates


class GateValidationTool(BaseTool):
    """Tool for validating specific gates against the codebase"""
    
    name = "validate_gates"
    description = "Validate hard gates against the codebase using pattern matching and analysis"
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Validate gates against the codebase"""
        try:
            gate_names = args.get("gate_names", [])
            repo_path = args["repository_path"]
            app_id = args.get("app_id", "unknown")
            
            print(f"🔍 Validating gates: {gate_names}")
            
            if not CODEGATES_AVAILABLE:
                return {
                    "status": "error",
                    "message": "CodeGates functionality not available",
                    "data": None
                }
            
            # Use existing EnhancedGateEvaluator
            evaluator = EnhancedGateEvaluator()
            results = []
            
            for gate_name in gate_names:
                try:
                    # Evaluate gate using existing logic
                    result = evaluator.evaluate_gate(gate_name, repo_path)
                    
                    # Add metadata
                    result["gate_name"] = gate_name
                    result["gate_number"] = get_gate_number(gate_name)
                    result["app_id"] = app_id
                    
                    results.append(result)
                    
                except Exception as e:
                    results.append({
                        "gate_name": gate_name,
                        "status": "error",
                        "message": f"Error validating gate {gate_name}: {str(e)}",
                        "app_id": app_id
                    })
            
            return {
                "status": "success",
                "validation_results": results,
                "total_gates": len(gate_names),
                "successful_validations": len([r for r in results if r.get("status") != "error"]),
                "message": f"Validated {len(gate_names)} gates successfully."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error validating gates: {str(e)}",
                "data": None
            }


class EvidenceCollectionTool(BaseTool):
    """Tool for collecting evidence from external sources"""
    
    name = "collect_evidence"
    description = "Collect evidence from Splunk, AppDynamics, and web portals"
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Collect evidence from external sources"""
        try:
            app_id = args["app_id"]
            evidence_sources = args.get("sources", ["splunk", "appdynamics", "web_portals"])
            
            print(f"🔍 Collecting evidence for app: {app_id}")
            
            evidence = {}
            
            # Collect from Splunk
            if "splunk" in evidence_sources and CODEGATES_AVAILABLE:
                try:
                    splunk_result = execute_splunk_query(
                        f"search index=* app_id={app_id} | head 100",
                        app_id
                    )
                    evidence["splunk"] = splunk_result
                except Exception as e:
                    evidence["splunk"] = {"status": "error", "message": str(e)}
            
            # Collect from AppDynamics
            if "appdynamics" in evidence_sources and CODEGATES_AVAILABLE:
                try:
                    appd_result = analyze_appdynamics_coverage(app_id)
                    evidence["appdynamics"] = appd_result
                except Exception as e:
                    evidence["appdynamics"] = {"status": "error", "message": str(e)}
            
            # Collect from web portals
            if "web_portals" in evidence_sources and CODEGATES_AVAILABLE:
                try:
                    web_result = collect_web_portal_evidence("custom", app_id)
                    evidence["web_portals"] = web_result
                except Exception as e:
                    evidence["web_portals"] = {"status": "error", "message": str(e)}
            
            return {
                "status": "success",
                "evidence": evidence,
                "sources_collected": list(evidence.keys()),
                "message": f"Collected evidence from {len(evidence)} sources."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error collecting evidence: {str(e)}",
                "data": None
            }


class ReportGenerationTool(BaseTool):
    """Tool for generating comprehensive validation reports"""
    
    name = "generate_report"
    description = "Generate comprehensive validation report with recommendations"
    
    async def run_async(self, args: dict, tool_context) -> dict:
        """Generate comprehensive report"""
        try:
            validation_results = args["validation_results"]
            evidence_data = args.get("evidence_data", {})
            repo_url = args.get("repository_url", "Unknown")
            
            print(f"📊 Generating report for validation results")
            
            # Generate summary
            summary = self._generate_summary(validation_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(validation_results, evidence_data)
            
            # Generate detailed report
            detailed_report = self._generate_detailed_report(validation_results, evidence_data)
            
            return {
                "status": "success",
                "report": {
                    "summary": summary,
                    "recommendations": recommendations,
                    "detailed_report": detailed_report,
                    "repository_url": repo_url,
                    "timestamp": self._get_timestamp()
                },
                "message": "Report generated successfully."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating report: {str(e)}",
                "data": None
            }
    
    def _generate_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate validation summary"""
        total_gates = len(validation_results)
        passed_gates = len([r for r in validation_results if r.get("status") == "passed"])
        failed_gates = len([r for r in validation_results if r.get("status") == "failed"])
        error_gates = len([r for r in validation_results if r.get("status") == "error"])
        
        return {
            "total_gates": total_gates,
            "passed": passed_gates,
            "failed": failed_gates,
            "errors": error_gates,
            "success_rate": (passed_gates / total_gates * 100) if total_gates > 0 else 0
        }
    
    def _generate_recommendations(self, validation_results: List[Dict[str, Any]], evidence_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for result in validation_results:
            if result.get("status") == "failed":
                gate_name = result.get("gate_name", "Unknown")
                gate_number = result.get("gate_number", "N/A")
                
                recommendations.append(
                    f"Gate {gate_number} ({gate_name}): Review and implement required patterns and practices."
                )
        
        # Add evidence-based recommendations
        if evidence_data.get("splunk", {}).get("status") == "error":
            recommendations.append("Splunk Integration: Configure Splunk monitoring and alerting.")
        
        if evidence_data.get("appdynamics", {}).get("status") == "error":
            recommendations.append("AppDynamics Integration: Set up AppDynamics application monitoring.")
        
        return recommendations
    
    def _generate_detailed_report(self, validation_results: List[Dict[str, Any]], evidence_data: Dict[str, Any]) -> str:
        """Generate detailed report text"""
        report_lines = ["# CodeGates Validation Report", ""]
        
        for result in validation_results:
            gate_name = result.get("gate_name", "Unknown")
            gate_number = result.get("gate_number", "N/A")
            status = result.get("status", "unknown")
            
            report_lines.append(f"## Gate {gate_number}: {gate_name}")
            report_lines.append(f"**Status**: {status.upper()}")
            
            if result.get("message"):
                report_lines.append(f"**Details**: {result['message']}")
            
            if result.get("patterns_found"):
                report_lines.append(f"**Patterns Found**: {len(result['patterns_found'])}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# =============================================================================
# LITELLM INTEGRATION
# =============================================================================

class LiteLLMIntegration:
    """Integration layer for LiteLLM with CodeGates configuration"""
    
    def __init__(self):
        self.llm_client = None
        self.llm_config = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client using CodeGates configuration"""
        try:
            if CODEGATES_AVAILABLE:
                # Use existing CodeGates LLM configuration
                self.llm_client = create_llm_client_from_env()
                self.llm_config = LLMConfig.from_env()
                
                # Configure LiteLLM with the same settings
                self._configure_litellm()
                
                print(f"✅ LiteLLM initialized with provider: {self.llm_config.provider}")
                print(f"   Model: {self.llm_config.model}")
                print(f"   Base URL: {self.llm_config.base_url}")
            else:
                print("⚠️ Using default LiteLLM configuration")
                
        except Exception as e:
            print(f"⚠️ Error initializing LLM: {e}")
            print("   Using default LiteLLM configuration")
    
    def _configure_litellm(self):
        """Configure LiteLLM with CodeGates settings"""
        if self.llm_config:
            # Set environment variables for LiteLLM
            if self.llm_config.api_key:
                os.environ["LITELLM_API_KEY"] = self.llm_config.api_key
            
            if self.llm_config.base_url:
                os.environ["LITELLM_BASE_URL"] = self.llm_config.base_url
            
            # Configure provider-specific settings
            if self.llm_config.provider == "ollama":
                os.environ["OLLAMA_BASE_URL"] = self.llm_config.base_url
            elif self.llm_config.provider == "openai":
                os.environ["OPENAI_API_KEY"] = self.llm_config.api_key
                if self.llm_config.base_url:
                    os.environ["OPENAI_API_BASE"] = self.llm_config.base_url
            elif self.llm_config.provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = self.llm_config.api_key
            elif self.llm_config.provider == "google":
                os.environ["GOOGLE_API_KEY"] = self.llm_config.api_key
    
    async def generate_response(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> Dict[str, Any]:
        """Generate LLM response using LiteLLM"""
        try:
            if not LITELLM_AVAILABLE:
                return {
                    "status": "error",
                    "message": "LiteLLM not available",
                    "content": None
                }
            
            # Prepare completion parameters
            params = {
                "model": self.llm_config.model if self.llm_config else "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            # Generate response
            response = await litellm.acompletion(**params)
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls if hasattr(response.choices[0].message, 'tool_calls') else None,
                "usage": response.usage
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating response: {str(e)}",
                "content": None
            }


# =============================================================================
# MAIN AGENT
# =============================================================================

def create_codegates_agent():
    """Create the main CodeGates agent"""
    
    # Setup LiteLLM environment if available
    if LITELLM_CONFIG_AVAILABLE:
        try:
            setup_litellm_environment()
        except Exception as e:
            print(f"⚠️ Error setting up LiteLLM environment: {e}")
    
    # Create tools
    tools = [
        RepositoryAnalysisTool(),
        GateValidationTool(),
        EvidenceCollectionTool(),
        ReportGenerationTool()
    ]
    
    # Create agent
    agent = Agent(
        model=os.getenv("CODEGATES_LLM_MODEL", "gpt-3.5-turbo"),
        name="codegates_validation_agent",
        description="Intelligent agent for enterprise gate validation and compliance",
        instruction=AGENT_INSTRUCTION,
        tools=tools,
        global_instruction="""
        You are the CodeGates Validation Agent, an expert in enterprise application validation.
        Always be helpful, thorough, and provide clear explanations.
        Use markdown formatting for better readability.
        Provide actionable recommendations with specific examples.
        """
    )
    
    return agent


# Create the root agent
root_agent = create_codegates_agent()


# =============================================================================
# RUNNER AND UTILITIES
# =============================================================================

def create_codegates_runner():
    """Create and configure the CodeGates runner"""
    if not ADK_AVAILABLE:
        raise ImportError("Google ADK is required for CodeGates Runner")
    
    # Create runner
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="CodeGates Validation Agent"
    )
    
    return runner


# Example usage
async def example_validation_workflow():
    """Example of how to use the CodeGates agent with LiteLLM"""
    
    # Create runner
    runner = create_codegates_runner()
    
    # Example user message
    user_message = {
        "parts": [{
            "text": "Please validate the repository at https://github.com/company/myapp for enterprise compliance"
        }]
    }
    
    # Run validation
    async for event in runner.run_async(
        user_id="user123",
        session_id="session456",
        new_message=user_message
    ):
        print(f"Event: {event.type}")
        if hasattr(event, 'content'):
            print(f"Content: {event.content}")


if __name__ == "__main__":
    # Test the agent
    if ADK_AVAILABLE and CODEGATES_AVAILABLE and LITELLM_AVAILABLE:
        asyncio.run(example_validation_workflow())
    else:
        print("❌ Required dependencies not available")
        print("Install with:")
        print("  pip install google-adk")
        print("  pip install litellm")
        print("Ensure CodeGates functionality is available") 