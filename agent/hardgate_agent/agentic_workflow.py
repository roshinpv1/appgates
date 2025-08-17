"""
Agentic Workflow System
Replaces node-based framework with intelligent agent orchestration
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time
import re

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


class WorkflowState(Enum):
    """Workflow execution states"""
    INITIALIZED = "initialized"
    WORKFLOW_PLANNING = "workflow_planning"
    REPOSITORY_ANALYSIS = "repository_analysis"
    GATE_APPLICABILITY = "gate_applicability"
    LLM_PATTERN_GENERATION = "llm_pattern_generation"
    GATE_VALIDATION = "gate_validation"
    PARALLEL_ANALYSIS = "parallel_analysis"  # security + compliance together
    SECURITY_ANALYSIS = "security_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    EVIDENCE_COLLECTION = "evidence_collection"
    REPORT_GENERATION = "report_generation"
    INTEGRATION_UPLOAD = "integration_upload"
    COMPLETED = "completed"
    FAILED = "failed"


class DecisionType(Enum):
    """Types of decisions the agent can make"""
    CONTINUE = "continue"
    RETRY = "retry"
    SKIP = "skip"
    BRANCH = "branch"
    FAIL = "fail"
    OPTIMIZE = "optimize"


class SafetyMode(Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    LENIENT = "lenient"


class AutonomyLevel(Enum):
    LOW = "low"       # human approvals needed for sensitive actions
    MEDIUM = "medium" # proceed with caution; some approvals
    HIGH = "high"     # fully autonomous within safety policies


SENSITIVE_ACTIONS = {
    "jira_upload",
    "jira_create_issue",
    "splunk_query",
    "llm_generate_patterns",
}


@dataclass
class SafetyDecision:
    allow: bool
    needs_approval: bool = False
    reason: str = ""


class SafetyGuard:
    """Safety guard for action approval, limits, and redaction."""

    SECRET_REGEXES = [
        re.compile(r"(?i)(?:api[_-]?key|token|secret|passwd|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{6,}['\"]?"),
    ]

    def __init__(self,
                 safety_mode: SafetyMode = SafetyMode.BALANCED,
                 autonomy: AutonomyLevel = AutonomyLevel.MEDIUM,
                 allowed_domains: Optional[List[str]] = None,
                 rate_limits: Optional[Dict[str, int]] = None):
        self.safety_mode = safety_mode
        self.autonomy = autonomy
        self.allowed_domains = set(allowed_domains or [])
        self.rate_limits = rate_limits or {}
        self._action_counts: Dict[str, int] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def _within_rate_limit(self, action: str) -> bool:
        limit = self.rate_limits.get(action)
        if not limit:
            return True
        count = self._action_counts.get(action, 0)
        if count >= limit:
            return False
        self._action_counts[action] = count + 1
        return True

    def _domain_allowed(self, url: Optional[str]) -> bool:
        if not url or not self.allowed_domains:
            return True
        return any(domain in url for domain in self.allowed_domains)

    def sanitize_text(self, text: str) -> str:
        redacted = text
        for rx in self.SECRET_REGEXES:
            redacted = rx.sub("<REDACTED>", redacted)
        return redacted

    def decide(self, action: str, params: Optional[Dict[str, Any]] = None) -> SafetyDecision:
        params = params or {}
        if not self._within_rate_limit(action):
            return SafetyDecision(allow=False, needs_approval=False, reason=f"Rate limit exceeded for {action}")

        # Domain checks for external systems
        if action in {"jira_upload", "jira_create_issue"}:
            if not self._domain_allowed(os.getenv("JIRA_URL", "")):
                return SafetyDecision(allow=False, reason="JIRA domain not allowed")
        if action == "splunk_query":
            if not self._domain_allowed(os.getenv("SPLUNK_URL", "")):
                return SafetyDecision(allow=False, reason="Splunk domain not allowed")

        # Approval policy based on autonomy/safety
        if action in SENSITIVE_ACTIONS:
            if self.safety_mode == SafetyMode.STRICT and self.autonomy != AutonomyLevel.HIGH:
                return SafetyDecision(allow=False, needs_approval=True, reason=f"{action} requires approval in STRICT mode")
            if self.autonomy == AutonomyLevel.LOW:
                return SafetyDecision(allow=True, needs_approval=True, reason=f"{action} requires approval in LOW autonomy")
        return SafetyDecision(allow=True)


@dataclass
class WorkflowContext:
    """Context shared across the entire workflow"""
    request_id: str
    repository_url: Optional[str] = None
    repository_path: Optional[str] = None
    branch: str = "main"
    gates: List[str] = field(default_factory=list)
    app_id: Optional[str] = None
    time_range: str = "-24h"

    # Autonomy & safety
    autonomy: AutonomyLevel = AutonomyLevel.MEDIUM
    safety_mode: SafetyMode = SafetyMode.BALANCED
    allowed_domains: List[str] = field(default_factory=list)
    rate_limits: Dict[str, int] = field(default_factory=dict)

    # Analysis results
    repository_analysis: Optional[Dict[str, Any]] = None
    gate_applicability: Optional[Dict[str, Any]] = None
    llm_patterns: Optional[Dict[str, Any]] = None
    gate_validation: Optional[Dict[str, Any]] = None
    security_analysis: Optional[Dict[str, Any]] = None
    compliance_check: Optional[Dict[str, Any]] = None
    evidence_collection: Optional[Dict[str, Any]] = None
    report_data: Optional[Dict[str, Any]] = None

    # Workflow state
    current_state: WorkflowState = WorkflowState.INITIALIZED
    completed_states: List[WorkflowState] = field(default_factory=list)
    failed_states: List[WorkflowState] = field(default_factory=list)
    retry_count: Dict[WorkflowState, int] = field(default_factory=dict)

    # Configuration
    max_retries: int = 3
    enable_llm: bool = True
    enable_evidence: bool = True
    enable_integrations: bool = True
    llm_config: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    start_time: float = field(default_factory=time.time)
    step_timings: Dict[str, float] = field(default_factory=dict)

    # Planning
    planned_states: List[WorkflowState] = field(default_factory=list)


@dataclass
class AgentDecision:
    """Decision made by the agent"""
    decision_type: DecisionType
    next_state: Optional[WorkflowState] = None
    reason: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgenticWorkflowOrchestrator:
    """Intelligent agent that orchestrates the entire workflow"""

    def __init__(self, context: WorkflowContext):
        self.context = context
        self.guard = SafetyGuard(
            safety_mode=context.safety_mode,
            autonomy=context.autonomy,
            allowed_domains=context.allowed_domains,
            rate_limits=context.rate_limits,
        )
        self.state_handlers = {
            WorkflowState.INITIALIZED: self._handle_initialized,
            WorkflowState.WORKFLOW_PLANNING: self._handle_planning,
            WorkflowState.REPOSITORY_ANALYSIS: self._handle_repository_analysis,
            WorkflowState.GATE_APPLICABILITY: self._handle_gate_applicability,
            WorkflowState.LLM_PATTERN_GENERATION: self._handle_llm_pattern_generation,
            WorkflowState.GATE_VALIDATION: self._handle_gate_validation,
            WorkflowState.PARALLEL_ANALYSIS: self._handle_parallel_analysis,
            WorkflowState.SECURITY_ANALYSIS: self._handle_security_analysis,
            WorkflowState.COMPLIANCE_CHECK: self._handle_compliance_check,
            WorkflowState.EVIDENCE_COLLECTION: self._handle_evidence_collection,
            WorkflowState.REPORT_GENERATION: self._handle_report_generation,
            WorkflowState.INTEGRATION_UPLOAD: self._handle_integration_upload,
        }

    async def execute_workflow(self) -> Dict[str, Any]:
        """Execute the complete workflow with intelligent decision making"""
        print(f"🚀 Starting agentic workflow for request {self.context.request_id}")
        print(f"   Repository: {self.context.repository_url}")
        print(f"   Branch: {self.context.branch}")
        print(f"   Gates: {self.context.gates}")

        try:
            while self.context.current_state != WorkflowState.COMPLETED:
                handler = self.state_handlers.get(self.context.current_state)
                if not handler:
                    raise ValueError(f"No handler for state: {self.context.current_state}")

                decision = await handler()
                await self._process_decision(decision)

                if self.context.current_state == WorkflowState.FAILED:
                    break

            return self._generate_final_result()

        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            self.context.current_state = WorkflowState.FAILED
            return self._generate_final_result()

    async def _process_decision(self, decision: AgentDecision):
        """Process the agent's decision"""
        print(f"🤖 Agent decision: {decision.decision_type.value}")
        print(f"   Reason: {decision.reason}")
        print(f"   Confidence: {decision.confidence:.2f}")

        if decision.decision_type == DecisionType.CONTINUE:
            self.context.completed_states.append(self.context.current_state)
            self.context.current_state = decision.next_state or self._get_next_state()

        elif decision.decision_type == DecisionType.RETRY:
            retry_count = self.context.retry_count.get(self.context.current_state, 0)
            if retry_count < self.context.max_retries:
                self.context.retry_count[self.context.current_state] = retry_count + 1
                print(f"🔄 Retrying {self.context.current_state.value} (attempt {retry_count + 1})")
            else:
                print(f"❌ Max retries exceeded for {self.context.current_state.value}")
                self.context.failed_states.append(self.context.current_state)
                self.context.current_state = WorkflowState.FAILED

        elif decision.decision_type == DecisionType.SKIP:
            print(f"⏭️ Skipping {self.context.current_state.value}")
            self.context.current_state = decision.next_state or self._get_next_state()

        elif decision.decision_type == DecisionType.BRANCH:
            self.context.current_state = decision.next_state
            print(f"🔄 Branching to {decision.next_state.value}")

        elif decision.decision_type == DecisionType.FAIL:
            self.context.failed_states.append(self.context.current_state)
            self.context.current_state = WorkflowState.FAILED

        elif decision.decision_type == DecisionType.OPTIMIZE:
            await self._apply_optimization(decision.metadata)
            self.context.current_state = decision.next_state or self._get_next_state()

    def _get_next_state(self) -> WorkflowState:
        """Determine the next state based on current state and context"""
        # Prefer planned states if available
        if self.context.planned_states:
            try:
                idx = self.context.planned_states.index(self.context.current_state)
                return self.context.planned_states[idx + 1]
            except ValueError:
                pass
            except IndexError:
                return WorkflowState.COMPLETED

        # Fallback default sequence
        state_sequence = [
            WorkflowState.WORKFLOW_PLANNING,
            WorkflowState.REPOSITORY_ANALYSIS,
            WorkflowState.GATE_APPLICABILITY,
            WorkflowState.LLM_PATTERN_GENERATION,
            WorkflowState.GATE_VALIDATION,
            WorkflowState.PARALLEL_ANALYSIS,
            WorkflowState.EVIDENCE_COLLECTION,
            WorkflowState.REPORT_GENERATION,
            WorkflowState.INTEGRATION_UPLOAD,
            WorkflowState.COMPLETED
        ]
        try:
            current_index = state_sequence.index(self.context.current_state)
            return state_sequence[current_index + 1]
        except (ValueError, IndexError):
            return WorkflowState.COMPLETED

    async def _handle_initialized(self) -> AgentDecision:
        print(f"🔄 Starting workflow from INITIALIZED state.")
        return AgentDecision(
            decision_type=DecisionType.CONTINUE,
            next_state=WorkflowState.WORKFLOW_PLANNING,
            reason="Workflow initialized, proceeding to planning",
            confidence=1.0
        )

    async def _handle_planning(self) -> AgentDecision:
        """Create a plan based on autonomy/safety and repository hints."""
        plan = [
            WorkflowState.WORKFLOW_PLANNING,
            WorkflowState.REPOSITORY_ANALYSIS,
            WorkflowState.GATE_APPLICABILITY,
        ]
        if self.context.enable_llm:
            plan.append(WorkflowState.LLM_PATTERN_GENERATION)
        plan.extend([
            WorkflowState.GATE_VALIDATION,
            WorkflowState.PARALLEL_ANALYSIS,  # run security+compliance together
        ])
        if self.context.enable_evidence:
            plan.append(WorkflowState.EVIDENCE_COLLECTION)
        plan.extend([
            WorkflowState.REPORT_GENERATION,
        ])
        if self.context.enable_integrations:
            plan.append(WorkflowState.INTEGRATION_UPLOAD)
        plan.append(WorkflowState.COMPLETED)

        self.context.planned_states = plan
        return AgentDecision(
            decision_type=DecisionType.CONTINUE,
            next_state=WorkflowState.REPOSITORY_ANALYSIS,
            reason="Plan created",
            confidence=1.0
        )

    async def _handle_repository_analysis(self) -> AgentDecision:
        start_time = time.time()
        print(f"📊 Agentic repository analysis...")
        try:
            result = analyze_repository(
                repository_url=self.context.repository_url,
                branch=self.context.branch
            )
            if result.get("success"):
                self.context.repository_analysis = result
                self.context.repository_path = result.get("local_path")
                self.context.step_timings["repository_analysis"] = time.time() - start_time
                metadata = result.get("analysis", {})
                total_files = metadata.get("structure", {}).get("total_files", 0)
                if total_files == 0:
                    return AgentDecision(DecisionType.FAIL, reason="Repository is empty or inaccessible", confidence=1.0)
                elif total_files > 10000:
                    return AgentDecision(DecisionType.OPTIMIZE, next_state=WorkflowState.GATE_APPLICABILITY,
                                         reason="Large repository detected, optimizing analysis", confidence=0.9,
                                         metadata={"optimization": "large_repo", "file_count": total_files})
                else:
                    return AgentDecision(DecisionType.CONTINUE, reason="Repository analysis completed successfully", confidence=0.95)
            else:
                return AgentDecision(DecisionType.RETRY, reason=f"Repository analysis failed: {result.get('error', 'Unknown error')}", confidence=0.8)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Repository analysis exception: {str(e)}", confidence=0.7)

    async def _handle_gate_applicability(self) -> AgentDecision:
        start_time = time.time()
        print(f"🎯 Agentic gate applicability analysis...")
        try:
            if not self.context.repository_analysis:
                return AgentDecision(DecisionType.FAIL, reason="Repository analysis not completed", confidence=1.0)
            result = gate_applicability(
                repository_path=self.context.repository_path,
                metadata=self.context.repository_analysis.get("analysis", {})
            )
            if result.get("success"):
                self.context.gate_applicability = result
                self.context.step_timings["gate_applicability"] = time.time() - start_time
                applicable_gates = result.get("applicable_gates", [])
                if not applicable_gates:
                    return AgentDecision(DecisionType.SKIP, next_state=WorkflowState.REPORT_GENERATION,
                                         reason="No applicable gates found for this codebase", confidence=0.9)
                if not self.context.gates:
                    self.context.gates = [gate["gate_name"] for gate in applicable_gates]
                return AgentDecision(DecisionType.CONTINUE, reason=f"Found {len(applicable_gates)} applicable gates", confidence=0.95)
            else:
                return AgentDecision(DecisionType.RETRY, reason=f"Gate applicability failed: {result.get('error', 'Unknown error')}", confidence=0.8)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Gate applicability exception: {str(e)}", confidence=0.7)

    async def _handle_llm_pattern_generation(self) -> AgentDecision:
        start_time = time.time()
        print(f"🤖 Agentic LLM pattern generation...")
        if not self.context.enable_llm:
            return AgentDecision(DecisionType.SKIP, reason="LLM integration disabled", confidence=1.0)
        # Safety check
        decision = self.guard.decide("llm_generate_patterns")
        if not decision.allow:
            if decision.needs_approval:
                return AgentDecision(DecisionType.SKIP, reason=f"Awaiting approval for LLM pattern generation: {decision.reason}")
            return AgentDecision(DecisionType.SKIP, reason=f"LLM pattern generation blocked: {decision.reason}")
        try:
            if not self.context.gates:
                return AgentDecision(DecisionType.SKIP, reason="No gates to generate patterns for", confidence=1.0)
            patterns = {}
            for gate_name in self.context.gates:
                result = llm_integration(
                    repository_path=self.context.repository_path,
                    gate_name=gate_name,
                    llm_config=self.context.llm_config
                )
                if result.get("success"):
                    patterns[gate_name] = result.get("patterns", [])
                else:
                    print(f"⚠️ Failed to generate patterns for {gate_name}")
            self.context.llm_patterns = patterns
            self.context.step_timings["llm_pattern_generation"] = time.time() - start_time
            successful = len([p for p in patterns.values() if p])
            if successful == 0:
                return AgentDecision(DecisionType.SKIP, reason="No LLM patterns generated successfully, using static patterns", confidence=0.8)
            elif successful < len(self.context.gates):
                return AgentDecision(DecisionType.CONTINUE, reason=f"Generated patterns for {successful}/{len(self.context.gates)} gates", confidence=0.85)
            else:
                return AgentDecision(DecisionType.CONTINUE, reason="All LLM patterns generated successfully", confidence=0.95)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"LLM pattern generation exception: {str(e)}", confidence=0.7)

    async def _handle_gate_validation(self) -> AgentDecision:
        start_time = time.time()
        print(f"🔍 Agentic gate validation...")
        try:
            if not self.context.gates:
                return AgentDecision(DecisionType.FAIL, reason="No gates to validate", confidence=1.0)
            validation_params = {
                "repository_path": self.context.repository_path,
                "gates": self.context.gates,
                "metadata": self.context.repository_analysis.get("analysis", {})
            }
            if self.context.llm_patterns:
                validation_params["llm_patterns"] = self.context.llm_patterns
            result = validate_gates(**validation_params)
            if result.get("success"):
                self.context.gate_validation = result
                self.context.step_timings["gate_validation"] = time.time() - start_time
                results = result.get("validation_results", [])
                passed = len([r for r in results if r.get("status") == "PASS"])
                total = len(results)
                if passed == 0:
                    return AgentDecision(DecisionType.CONTINUE, reason="All gates failed validation - continuing for comprehensive analysis", confidence=0.9)
                elif passed < total * 0.5:
                    return AgentDecision(DecisionType.CONTINUE, reason=f"Low pass rate ({passed}/{total}) - detailed analysis needed", confidence=0.85)
                else:
                    return AgentDecision(DecisionType.CONTINUE, reason=f"Good pass rate ({passed}/{total})", confidence=0.95)
            else:
                return AgentDecision(DecisionType.RETRY, reason=f"Gate validation failed: {result.get('error', 'Unknown error')}", confidence=0.8)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Gate validation exception: {str(e)}", confidence=0.7)

    async def _handle_parallel_analysis(self) -> AgentDecision:
        """Run security analysis and compliance check in parallel for efficiency."""
        print("⚡ Running security and compliance analysis in parallel...")
        start = time.time()
        try:
            async def run_security():
                return analyze_security(
                    repository_path=self.context.repository_path,
                    analysis_data={
                        "repository_analysis": self.context.repository_analysis,
                        "gate_validation": self.context.gate_validation
                    }
                )

            async def run_compliance():
                return check_compliance(
                    analysis_data={
                        "repository_analysis": self.context.repository_analysis,
                        "gate_validation": self.context.gate_validation,
                        "security_analysis": self.context.security_analysis
                    },
                    frameworks=["SOC2", "ISO27001", "NIST"]
                )

            security_result, compliance_result = await asyncio.gather(run_security(), run_compliance())
            if security_result.get("success"):
                self.context.security_analysis = security_result
            if compliance_result.get("success"):
                self.context.compliance_check = compliance_result
            self.context.step_timings["parallel_analysis"] = time.time() - start
            return AgentDecision(DecisionType.CONTINUE, reason="Parallel analysis completed", confidence=0.95)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Parallel analysis exception: {e}")

    async def _handle_security_analysis(self) -> AgentDecision:
        start_time = time.time()
        print(f"🛡️ Agentic security analysis...")
        try:
            result = analyze_security(
                repository_path=self.context.repository_path,
                analysis_data={
                    "repository_analysis": self.context.repository_analysis,
                    "gate_validation": self.context.gate_validation
                }
            )
            if result.get("success"):
                self.context.security_analysis = result
                self.context.step_timings["security_analysis"] = time.time() - start_time
                vulns = result.get("scan_results", {}).get("vulnerabilities", {})
                total_vulns = vulns.get("total_vulnerabilities", 0)
                if total_vulns > 10:
                    return AgentDecision(DecisionType.CONTINUE, reason=f"High vulnerability count ({total_vulns}) - comprehensive analysis needed", confidence=0.9)
                else:
                    return AgentDecision(DecisionType.CONTINUE, reason=f"Security analysis completed ({total_vulns} vulnerabilities found)", confidence=0.95)
            else:
                return AgentDecision(DecisionType.RETRY, reason=f"Security analysis failed: {result.get('error', 'Unknown error')}", confidence=0.8)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Security analysis exception: {str(e)}", confidence=0.7)

    async def _handle_compliance_check(self) -> AgentDecision:
        start_time = time.time()
        print(f"📋 Agentic compliance check...")
        try:
            result = check_compliance(
                analysis_data={
                    "repository_analysis": self.context.repository_analysis,
                    "gate_validation": self.context.gate_validation,
                    "security_analysis": self.context.security_analysis
                },
                frameworks=["SOC2", "ISO27001", "NIST"]
            )
            if result.get("success"):
                self.context.compliance_check = result
                self.context.step_timings["compliance_check"] = time.time() - start_time
                return AgentDecision(DecisionType.CONTINUE, reason="Compliance check completed", confidence=0.95)
            else:
                return AgentDecision(DecisionType.RETRY, reason=f"Compliance check failed: {result.get('error', 'Unknown error')}", confidence=0.8)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Compliance check exception: {str(e)}", confidence=0.7)

    async def _handle_evidence_collection(self) -> AgentDecision:
        start_time = time.time()
        print(f"🔍 Agentic evidence collection...")
        if not self.context.enable_evidence:
            return AgentDecision(DecisionType.SKIP, reason="Evidence collection disabled", confidence=1.0)
        try:
            if not self.context.app_id:
                return AgentDecision(DecisionType.SKIP, reason="No app_id provided for evidence collection", confidence=1.0)
            # Safety: Splunk query approval
            decision = self.guard.decide("splunk_query")
            if not decision.allow:
                if decision.needs_approval:
                    return AgentDecision(DecisionType.SKIP, reason=f"Awaiting approval for Splunk query: {decision.reason}")
                return AgentDecision(DecisionType.SKIP, reason=f"Splunk query blocked: {decision.reason}")
            result = evidence_collection_tool(
                app_id=self.context.app_id,
                sources=["splunk", "appdynamics", "web_portal"],
                time_range=self.context.time_range
            )
            if result.get("success"):
                self.context.evidence_collection = result
                self.context.step_timings["evidence_collection"] = time.time() - start_time
                return AgentDecision(DecisionType.CONTINUE, reason="Evidence collection completed", confidence=0.95)
            else:
                return AgentDecision(DecisionType.RETRY, reason=f"Evidence collection failed: {result.get('error', 'Unknown error')}", confidence=0.8)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Evidence collection exception: {str(e)}", confidence=0.7)

    async def _handle_report_generation(self) -> AgentDecision:
        start_time = time.time()
        print(f"📊 Agentic report generation...")
        try:
            analysis_data = {
                "repository_analysis": self.context.repository_analysis,
                "gate_applicability": self.context.gate_applicability,
                "llm_patterns": self.context.llm_patterns,
                "gate_validation": self.context.gate_validation,
                "security_analysis": self.context.security_analysis,
                "compliance_check": self.context.compliance_check,
                "evidence_collection": self.context.evidence_collection,
                "workflow_metrics": {
                    "step_timings": self.context.step_timings,
                    "completed_states": [s.value for s in self.context.completed_states],
                    "failed_states": [s.value for s in self.context.failed_states],
                    "total_duration": time.time() - self.context.start_time
                }
            }
            html_result = html_report_generator(
                analysis_data=analysis_data,
                output_path=f"reports/{self.context.request_id}_report.html"
            )
            json_result = generate_report(
                analysis_data=analysis_data,
                output_format="json",
                output_path=f"reports/{self.context.request_id}_report.json"
            )
            self.context.report_data = {"html_report": html_result, "json_report": json_result}
            self.context.step_timings["report_generation"] = time.time() - start_time
            return AgentDecision(DecisionType.CONTINUE, reason="Report generation completed", confidence=0.95)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Report generation exception: {str(e)}", confidence=0.7)

    async def _handle_integration_upload(self) -> AgentDecision:
        start_time = time.time()
        print(f"📤 Agentic integration upload...")
        if not self.context.enable_integrations:
            return AgentDecision(DecisionType.SKIP, reason="Integrations disabled", confidence=1.0)
        try:
            if not self.context.app_id:
                return AgentDecision(DecisionType.SKIP, reason="No app_id provided for integration upload", confidence=1.0)
            decision = self.guard.decide("jira_upload")
            if not decision.allow:
                if decision.needs_approval:
                    return AgentDecision(DecisionType.SKIP, reason=f"Awaiting approval for JIRA upload: {decision.reason}")
                return AgentDecision(DecisionType.SKIP, reason=f"JIRA upload blocked: {decision.reason}")
            jira_integration(
                action="upload_report",
                app_id=self.context.app_id,
                report_path=f"reports/{self.context.request_id}_report.html",
                report_type="html",
                comment=f"Automated security analysis report for {self.context.app_id}"
            )
            self.context.step_timings["integration_upload"] = time.time() - start_time
            return AgentDecision(DecisionType.CONTINUE, reason="Integration upload completed", confidence=0.95)
        except Exception as e:
            return AgentDecision(DecisionType.RETRY, reason=f"Integration upload exception: {str(e)}", confidence=0.7)

    async def _apply_optimization(self, metadata: Dict[str, Any]):
        optimization_type = metadata.get("optimization")
        if optimization_type == "large_repo":
            print("🔧 Applying large repository optimizations...")
            # Placeholder: implement sampling, path filters, etc.
            pass

    def _generate_final_result(self) -> Dict[str, Any]:
        total_duration = time.time() - self.context.start_time
        return {
            "request_id": self.context.request_id,
            "status": "completed" if self.context.current_state == WorkflowState.COMPLETED else "failed",
            "current_state": self.context.current_state.value,
            "completed_states": [s.value for s in self.context.completed_states],
            "failed_states": [s.value for s in self.context.failed_states],
            "total_duration": total_duration,
            "step_timings": self.context.step_timings,
            "results": {
                "repository_analysis": self.context.repository_analysis,
                "gate_applicability": self.context.gate_applicability,
                "llm_patterns": self.context.llm_patterns,
                "gate_validation": self.context.gate_validation,
                "security_analysis": self.context.security_analysis,
                "compliance_check": self.context.compliance_check,
                "evidence_collection": self.context.evidence_collection,
                "report_data": self.context.report_data
            }
        }


class AgenticWorkflowManager:
    """Manager for creating and executing agentic workflows"""

    @staticmethod
    def create_workflow(
        request_id: str,
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
        max_retries: int = 3,
        autonomy: AutonomyLevel = AutonomyLevel.MEDIUM,
        safety_mode: SafetyMode = SafetyMode.BALANCED,
        allowed_domains: Optional[List[str]] = None,
        rate_limits: Optional[Dict[str, int]] = None,
    ) -> AgenticWorkflowOrchestrator:
        """Create a new agentic workflow"""
        context = WorkflowContext(
            request_id=request_id,
            repository_url=repository_url,
            repository_path=repository_path,
            branch=branch,
            gates=gates or [],
            app_id=app_id,
            time_range=time_range,
            enable_llm=enable_llm,
            enable_evidence=enable_evidence,
            enable_integrations=enable_integrations,
            llm_config=llm_config or {},
            max_retries=max_retries,
            autonomy=autonomy,
            safety_mode=safety_mode,
            allowed_domains=allowed_domains or [],
            rate_limits=rate_limits or {},
        )
        return AgenticWorkflowOrchestrator(context)

    @staticmethod
    async def execute_workflow(
        request_id: str,
        repository_url: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        orchestrator = AgenticWorkflowManager.create_workflow(
            request_id=request_id,
            repository_url=repository_url,
            repository_path=repository_path,
            **kwargs
        )
        return await orchestrator.execute_workflow()


# Convenience functions for easy usage
async def run_agentic_workflow(
    request_id: str,
    repository_url: Optional[str] = None,
    repository_path: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    return await AgenticWorkflowManager.execute_workflow(
        request_id=request_id,
        repository_url=repository_url,
        repository_path=repository_path,
        **kwargs
    )


def create_agentic_workflow(
    request_id: str,
    repository_url: Optional[str] = None,
    repository_path: Optional[str] = None,
    **kwargs
) -> AgenticWorkflowOrchestrator:
    return AgenticWorkflowManager.create_workflow(
        request_id=request_id,
        repository_url=repository_url,
        repository_path=repository_path,
        **kwargs
    ) 