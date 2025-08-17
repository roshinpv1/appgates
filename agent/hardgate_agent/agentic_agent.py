"""
Agentic HardGate Agent
Enhanced agent with intelligent workflow orchestration and decision making
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from . import prompt
from .agentic_workflow import (
    AgenticWorkflowManager,
    run_agentic_workflow,
    create_agentic_workflow,
    WorkflowContext,
    WorkflowState
)
from .tools import (
    analyze_repository,
    validate_gates,
    evidence_collection_tool,
    llm_analysis_tool,
    analyze_security,
    scan_code,
    check_compliance,
    generate_report,
    llm_integration,
    splunk_integration,
    jira_integration,
    gate_applicability,
    html_report_generator
)


class AgenticHardGateAgent:
    """Enhanced agentic agent with intelligent workflow orchestration"""
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """Initialize the agentic agent"""
        self.model_config = model_config or {
            "model": "gpt-3.5-turbo",
            "base_url": "http://localhost:1234/v1",
            "api_key": "sdsd",
            "provider": "openai"
        }
        
        # Create the underlying ADK agent
        self.agent = Agent(
            model=LiteLlm(**self.model_config),
            name="agentic_hardgate_agent",
            description="Intelligent agentic code security analysis with workflow orchestration",
            instruction=prompt.AGENTIC_AGENT_INSTR,
            tools=[
                # Core analysis tools
                analyze_repository,
                validate_gates,
                evidence_collection_tool,
                llm_analysis_tool,
                
                # Security and compliance tools
                analyze_security,
                scan_code,
                check_compliance,
                
                # Reporting and integration tools
                generate_report,
                html_report_generator,
                llm_integration,
                splunk_integration,
                jira_integration,
                
                # Advanced analysis tools
                gate_applicability
            ],
        )
        
        # Workflow management
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.workflow_history: List[Dict[str, Any]] = []
    
    async def execute_comprehensive_analysis(
        self,
        repository_url: Optional[str] = None,
        repository_path: Optional[str] = None,
        branch: str = "main",
        gates: Optional[List[str]] = None,
        app_id: Optional[str] = None,
        time_range: str = "-24h",
        enable_llm: bool = True,
        enable_evidence: bool = True,
        enable_integrations: bool = True,
        llm_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a comprehensive agentic analysis workflow
        
        This method orchestrates the entire analysis process using intelligent
        decision making and adaptive workflow execution.
        """
        request_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        print(f"🤖 Starting agentic comprehensive analysis")
        print(f"   Request ID: {request_id}")
        print(f"   Repository: {repository_url or repository_path}")
        print(f"   Branch: {branch}")
        print(f"   Gates: {gates or 'Auto-detect'}")
        print(f"   App ID: {app_id}")
        
        try:
            # Execute the agentic workflow
            result = await run_agentic_workflow(
                request_id=request_id,
                repository_url=repository_url,
                repository_path=repository_path,
                branch=branch,
                gates=gates,
                app_id=app_id,
                time_range=time_range,
                enable_llm=enable_llm,
                enable_evidence=enable_evidence,
                enable_integrations=enable_integrations,
                llm_config=llm_config,
                max_retries=max_retries
            )
            
            # Store in history
            self.workflow_history.append({
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            return result
        
        except Exception as e:
            error_result = {
                "request_id": request_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            self.workflow_history.append({
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "result": error_result
            })
            
            return error_result
    
    async def execute_targeted_analysis(
        self,
        analysis_type: str,
        repository_url: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a targeted analysis for specific use cases
        
        Args:
            analysis_type: Type of analysis ("security", "compliance", "gates", "evidence")
            repository_url: Repository URL
            repository_path: Local repository path
            **kwargs: Additional parameters
        """
        request_id = f"{analysis_type}_{uuid.uuid4().hex[:8]}"
        
        print(f"🎯 Starting targeted {analysis_type} analysis")
        print(f"   Request ID: {request_id}")
        
        try:
            if analysis_type == "security":
                return await self._execute_security_analysis(request_id, repository_url, repository_path, **kwargs)
            elif analysis_type == "compliance":
                return await self._execute_compliance_analysis(request_id, repository_url, repository_path, **kwargs)
            elif analysis_type == "gates":
                return await self._execute_gate_analysis(request_id, repository_url, repository_path, **kwargs)
            elif analysis_type == "evidence":
                return await self._execute_evidence_analysis(request_id, repository_url, repository_path, **kwargs)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        except Exception as e:
            return {
                "request_id": request_id,
                "status": "failed",
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    async def _execute_security_analysis(
        self, request_id: str, repository_url: Optional[str], repository_path: Optional[str], **kwargs
    ) -> Dict[str, Any]:
        """Execute focused security analysis"""
        print(f"🛡️ Executing security analysis for {request_id}")
        
        # First, analyze repository if needed
        if not repository_path:
            repo_result = analyze_repository(
                repository_url=repository_url,
                branch=kwargs.get("branch", "main")
            )
            if not repo_result.get("success"):
                return {"request_id": request_id, "status": "failed", "error": "Repository analysis failed"}
            repository_path = repo_result.get("local_path")
        
        # Execute security analysis
        security_result = analyze_security(
            repository_path=repository_path,
            analysis_data=kwargs.get("analysis_data", {})
        )
        
        # Execute code scanning
        scan_result = scan_code(
            repository_path=repository_path,
            scan_type=kwargs.get("scan_type", "comprehensive")
        )
        
        return {
            "request_id": request_id,
            "status": "completed",
            "analysis_type": "security",
            "results": {
                "security_analysis": security_result,
                "code_scan": scan_result
            }
        }
    
    async def _execute_compliance_analysis(
        self, request_id: str, repository_url: Optional[str], repository_path: Optional[str], **kwargs
    ) -> Dict[str, Any]:
        """Execute focused compliance analysis"""
        print(f"📋 Executing compliance analysis for {request_id}")
        
        # First, analyze repository if needed
        if not repository_path:
            repo_result = analyze_repository(
                repository_url=repository_url,
                branch=kwargs.get("branch", "main")
            )
            if not repo_result.get("success"):
                return {"request_id": request_id, "status": "failed", "error": "Repository analysis failed"}
            repository_path = repo_result.get("local_path")
        
        # Execute compliance check
        compliance_result = check_compliance(
            analysis_data=kwargs.get("analysis_data", {}),
            frameworks=kwargs.get("frameworks", ["SOC2", "ISO27001", "NIST"])
        )
        
        return {
            "request_id": request_id,
            "status": "completed",
            "analysis_type": "compliance",
            "results": {
                "compliance_check": compliance_result
            }
        }
    
    async def _execute_gate_analysis(
        self, request_id: str, repository_url: Optional[str], repository_path: Optional[str], **kwargs
    ) -> Dict[str, Any]:
        """Execute focused gate analysis"""
        print(f"🎯 Executing gate analysis for {request_id}")
        
        # First, analyze repository if needed
        if not repository_path:
            repo_result = analyze_repository(
                repository_url=repository_url,
                branch=kwargs.get("branch", "main")
            )
            if not repo_result.get("success"):
                return {"request_id": request_id, "status": "failed", "error": "Repository analysis failed"}
            repository_path = repo_result.get("local_path")
        
        # Check gate applicability
        applicability_result = gate_applicability(
            repository_path=repository_path,
            metadata=kwargs.get("metadata", {})
        )
        
        # Execute gate validation
        gates = kwargs.get("gates", [])
        if not gates and applicability_result.get("success"):
            gates = [gate["gate_name"] for gate in applicability_result.get("applicable_gates", [])]
        
        validation_result = validate_gates(
            repository_path=repository_path,
            gates=gates,
            metadata=kwargs.get("metadata", {})
        )
        
        return {
            "request_id": request_id,
            "status": "completed",
            "analysis_type": "gates",
            "results": {
                "gate_applicability": applicability_result,
                "gate_validation": validation_result
            }
        }
    
    async def _execute_evidence_analysis(
        self, request_id: str, repository_url: Optional[str], repository_path: Optional[str], **kwargs
    ) -> Dict[str, Any]:
        """Execute focused evidence analysis"""
        print(f"🔍 Executing evidence analysis for {request_id}")
        
        app_id = kwargs.get("app_id")
        if not app_id:
            return {"request_id": request_id, "status": "failed", "error": "App ID required for evidence analysis"}
        
        # Execute evidence collection
        evidence_result = evidence_collection_tool(
            app_id=app_id,
            sources=kwargs.get("sources", ["splunk", "appdynamics", "web_portal"]),
            time_range=kwargs.get("time_range", "-24h")
        )
        
        # Execute Splunk queries if configured
        splunk_result = None
        if kwargs.get("enable_splunk", True):
            splunk_result = splunk_integration(
                app_id=app_id,
                gate_name=kwargs.get("gate_name"),
                time_range=kwargs.get("time_range", "-24h")
            )
        
        return {
            "request_id": request_id,
            "status": "completed",
            "analysis_type": "evidence",
            "results": {
                "evidence_collection": evidence_result,
                "splunk_analysis": splunk_result
            }
        }
    
    async def get_workflow_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow"""
        # Check active workflows
        if request_id in self.active_workflows:
            context = self.active_workflows[request_id]
            return {
                "request_id": request_id,
                "status": "active",
                "current_state": context.current_state.value,
                "completed_states": [s.value for s in context.completed_states],
                "failed_states": [s.value for s in context.failed_states],
                "progress": len(context.completed_states) / 10.0  # Assuming 10 total states
            }
        
        # Check history
        for workflow in self.workflow_history:
            if workflow["request_id"] == request_id:
                return {
                    "request_id": request_id,
                    "status": "completed",
                    "result": workflow["result"]
                }
        
        return {
            "request_id": request_id,
            "status": "not_found"
        }
    
    async def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow history"""
        return self.workflow_history[-limit:] if self.workflow_history else []
    
    async def cancel_workflow(self, request_id: str) -> Dict[str, Any]:
        """Cancel an active workflow"""
        if request_id in self.active_workflows:
            context = self.active_workflows[request_id]
            context.current_state = WorkflowState.FAILED
            del self.active_workflows[request_id]
            
            return {
                "request_id": request_id,
                "status": "cancelled",
                "message": "Workflow cancelled successfully"
            }
        
        return {
            "request_id": request_id,
            "status": "not_found",
            "message": "Workflow not found or already completed"
        }
    
    async def optimize_workflow(self, request_id: str, optimization_type: str) -> Dict[str, Any]:
        """Apply optimizations to a workflow"""
        if request_id not in self.active_workflows:
            return {
                "request_id": request_id,
                "status": "not_found",
                "message": "Workflow not found or already completed"
            }
        
        context = self.active_workflows[request_id]
        
        if optimization_type == "performance":
            # Apply performance optimizations
            context.max_retries = min(context.max_retries, 2)
            print(f"🔧 Applied performance optimizations to {request_id}")
        
        elif optimization_type == "accuracy":
            # Apply accuracy optimizations
            context.max_retries = max(context.max_retries, 5)
            print(f"🔧 Applied accuracy optimizations to {request_id}")
        
        return {
            "request_id": request_id,
            "status": "optimized",
            "optimization_type": optimization_type,
            "message": f"Applied {optimization_type} optimizations"
        }
    
    async def generate_report(self, request_id: str, report_type: str = "html") -> Dict[str, Any]:
        """Generate a report for a completed workflow"""
        # Find the workflow in history
        workflow_data = None
        for workflow in self.workflow_history:
            if workflow["request_id"] == request_id:
                workflow_data = workflow["result"]
                break
        
        if not workflow_data:
            return {
                "request_id": request_id,
                "status": "not_found",
                "message": "Workflow not found"
            }
        
        try:
            if report_type == "html":
                result = html_report_generator(
                    analysis_data=workflow_data.get("results", {}),
                    output_path=f"reports/{request_id}_report.html"
                )
            else:
                result = generate_report(
                    analysis_data=workflow_data.get("results", {}),
                    output_format=report_type,
                    output_path=f"reports/{request_id}_report.{report_type}"
                )
            
            return {
                "request_id": request_id,
                "status": "completed",
                "report_type": report_type,
                "result": result
            }
        
        except Exception as e:
            return {
                "request_id": request_id,
                "status": "failed",
                "error": str(e),
                "report_type": report_type
            }


# Create the main agentic agent instance
agentic_agent = AgenticHardGateAgent()


# Convenience functions for easy usage
async def run_comprehensive_analysis(
    repository_url: Optional[str] = None,
    repository_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Run a comprehensive agentic analysis"""
    return await agentic_agent.execute_comprehensive_analysis(
        repository_url=repository_url,
        repository_path=repository_path,
        **kwargs
    )


async def run_targeted_analysis(
    analysis_type: str,
    repository_url: Optional[str] = None,
    repository_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Run a targeted analysis"""
    return await agentic_agent.execute_targeted_analysis(
        analysis_type=analysis_type,
        repository_url=repository_url,
        repository_path=repository_path,
        **kwargs
    )


def create_agentic_agent(model_config: Optional[Dict[str, Any]] = None) -> AgenticHardGateAgent:
    """Create a new agentic agent instance"""
    return AgenticHardGateAgent(model_config=model_config) 