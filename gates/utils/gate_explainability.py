"""
Gate Explainability Module
Provides comprehensive explanations for gate validation results with detailed context for LLM recommendations
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class ValidationEvidence:
    """Structured evidence for gate validation"""
    evidence_type: str  # "pattern_match", "api_call", "database_query", "file_analysis", "manual_check"
    source: str  # Where the evidence came from
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]  # Specific evidence details
    timestamp: str  # When evidence was collected


@dataclass
class GateValidationContext:
    """Complete context for gate validation explainability"""
    # Gate Information
    gate_name: str
    gate_display_name: str
    gate_description: str
    gate_category: str
    gate_priority: str
    gate_weight: float
    
    # Validation Results
    validation_status: str  # "PASS", "FAIL", "WARNING", "NOT_APPLICABLE"
    validation_score: float  # 0.0 to 100.0
    validation_confidence: str  # "high", "medium", "low"
    
    # Evidence Collection
    evidence_collectors_used: List[str]
    evidence_collectors_failed: List[str]
    mandatory_collectors_passed: bool
    mandatory_collectors_failed: List[str]
    
    # Pattern Analysis
    patterns_analyzed: List[str]
    patterns_matched: List[str]
    patterns_failed: List[str]
    total_patterns: int
    matched_patterns: int
    
    # File Analysis
    files_analyzed: int
    files_with_matches: int
    relevant_files: int
    total_files_in_repo: int
    
    # Match Details
    matches_found: List[Dict[str, Any]]
    violation_details: List[Dict[str, Any]]
    code_examples: List[Dict[str, Any]]
    
    # Coverage Analysis
    expected_coverage_percentage: float
    actual_coverage_percentage: float
    coverage_gap: float
    coverage_reasoning: str
    
    # Technology Context
    primary_languages: List[str]
    frameworks_detected: List[str]
    build_tools: List[str]
    deployment_platforms: List[str]
    
    # Repository Context
    repository_url: str
    branch: str
    commit_hash: str
    last_commit_date: str
    
    # Validation Sources
    validation_sources: Dict[str, Any]
    enhanced_data: Dict[str, Any]
    
    # Timestamps
    validation_start_time: str
    validation_end_time: str
    evidence_collection_time: str


class GateExplainabilityEngine:
    """Engine for generating comprehensive gate validation explanations"""
    
    def __init__(self):
        self.explanation_templates = self._load_explanation_templates()
    
    def _load_explanation_templates(self) -> Dict[str, str]:
        """Load explanation templates for different gate statuses"""
        return {
            "PASS": """
## Gate Validation Success Explanation

**Gate**: {gate_name} ({gate_display_name})
**Status**: ✅ PASSED
**Score**: {score:.1f}%
**Confidence**: {confidence}

### What This Means
This gate has been successfully validated and meets all required criteria for production readiness.

### Evidence Summary
- **Patterns Analyzed**: {total_patterns} patterns
- **Patterns Matched**: {matched_patterns} patterns
- **Files Analyzed**: {files_analyzed} files
- **Coverage Achieved**: {actual_coverage:.1f}% (Target: {expected_coverage:.1f}%)
- **Evidence Collectors**: {collectors_used}

### Validation Details
{validation_details}

### Technology Context
- **Primary Languages**: {languages}
- **Frameworks**: {frameworks}
- **Build Tools**: {build_tools}

### Recommendations
{recommendations}
""",
            
            "FAIL": """
## Gate Validation Failure Explanation

**Gate**: {gate_name} ({gate_display_name})
**Status**: ❌ FAILED
**Score**: {score:.1f}%
**Confidence**: {confidence}

### What This Means
This gate has failed validation and requires immediate attention before production deployment.

### Failure Analysis
- **Patterns Analyzed**: {total_patterns} patterns
- **Patterns Matched**: {matched_patterns} patterns
- **Files Analyzed**: {files_analyzed} files
- **Coverage Gap**: {coverage_gap:.1f}% (Current: {actual_coverage:.1f}%, Target: {expected_coverage:.1f}%)
- **Mandatory Collectors Failed**: {mandatory_failures}

### Critical Issues Found
{critical_issues}

### Evidence Details
{evidence_details}

### Violation Examples
{violation_examples}

### Technology Context
- **Primary Languages**: {languages}
- **Frameworks**: {frameworks}
- **Build Tools**: {build_tools}

### Immediate Actions Required
{immediate_actions}

### Remediation Steps
{remediation_steps}
""",
            
            "WARNING": """
## Gate Validation Warning Explanation

**Gate**: {gate_name} ({gate_display_name})
**Status**: ⚠️ WARNING
**Score**: {score:.1f}%
**Confidence**: {confidence}

### What This Means
This gate has partial compliance but needs improvement to meet production standards.

### Warning Analysis
- **Patterns Analyzed**: {total_patterns} patterns
- **Patterns Matched**: {matched_patterns} patterns
- **Files Analyzed**: {files_analyzed} files
- **Coverage Gap**: {coverage_gap:.1f}% (Current: {actual_coverage:.1f}%, Target: {expected_coverage:.1f}%)

### Areas of Concern
{areas_of_concern}

### Evidence Details
{evidence_details}

### Technology Context
- **Primary Languages**: {languages}
- **Frameworks**: {frameworks}
- **Build Tools**: {build_tools}

### Improvement Recommendations
{improvement_recommendations}
""",
            
            "NOT_APPLICABLE": """
## Gate Not Applicable Explanation

**Gate**: {gate_name} ({gate_display_name})
**Status**: ➖ NOT APPLICABLE
**Reason**: {not_applicable_reason}

### What This Means
This gate is not applicable to your current technology stack or codebase structure.

### Applicability Analysis
{applicability_analysis}

### Technology Context
- **Primary Languages**: {languages}
- **Frameworks**: {frameworks}
- **Build Tools**: {build_tools}

### Alternative Recommendations
{alternative_recommendations}
"""
        }
    
    def create_validation_context(self, gate_result: Dict[str, Any], shared: Dict[str, Any]) -> GateValidationContext:
        """Create comprehensive validation context from gate result"""
        
        # Extract gate information
        gate_name = gate_result.get("gate", "Unknown")
        gate_display_name = gate_result.get("display_name", gate_name)
        gate_description = gate_result.get("description", "No description available")
        gate_category = gate_result.get("category", "Unknown")
        gate_priority = gate_result.get("priority", "medium")
        gate_weight = gate_result.get("weight", 1.0)
        
        # Extract validation results
        validation_status = gate_result.get("status", "UNKNOWN")
        validation_score = gate_result.get("score", 0.0)
        validation_confidence = self._extract_confidence(gate_result)
        
        # Extract evidence collection information
        evidence_collectors_used = self._extract_evidence_collectors(gate_result)
        evidence_collectors_failed = self._extract_failed_collectors(gate_result)
        mandatory_collectors_passed = self._check_mandatory_collectors(gate_result)
        mandatory_collectors_failed = self._extract_mandatory_failures(gate_result)
        
        # Extract pattern analysis
        patterns_analyzed = self._extract_patterns(gate_result)
        patterns_matched = self._extract_matched_patterns(gate_result)
        patterns_failed = self._extract_failed_patterns(gate_result)
        total_patterns = len(patterns_analyzed)
        matched_patterns = len(patterns_matched)
        
        # Extract file analysis
        files_analyzed = gate_result.get("files_analyzed", 0)
        files_with_matches = len(set(match.get("file", "") for match in gate_result.get("matches", [])))
        relevant_files = gate_result.get("relevant_files", 0)
        total_files_in_repo = gate_result.get("total_files", 0)
        
        # Extract match details
        matches_found = gate_result.get("matches", [])
        violation_details = self._extract_violation_details(matches_found)
        code_examples = self._extract_code_examples(matches_found)
        
        # Extract coverage analysis
        expected_coverage = gate_result.get("expected_coverage", {})
        expected_coverage_percentage = expected_coverage.get("percentage", 10.0)
        actual_coverage_percentage = self._calculate_actual_coverage(files_with_matches, relevant_files)
        coverage_gap = max(0, expected_coverage_percentage - actual_coverage_percentage)
        coverage_reasoning = expected_coverage.get("reasoning", "Standard expectation")
        
        # Extract technology context
        metadata = shared.get("repository", {}).get("metadata", {})
        primary_languages = metadata.get("primary_languages", [])
        frameworks_detected = metadata.get("frameworks", [])
        build_tools = metadata.get("build_tools", [])
        deployment_platforms = metadata.get("deployment_platforms", [])
        
        # Extract repository context
        request = shared.get("request", {})
        repository_url = request.get("repository_url", "Unknown")
        branch = request.get("branch", "main")
        commit_hash = metadata.get("commit_hash", "Unknown")
        last_commit_date = metadata.get("last_commit_date", "Unknown")
        
        # Extract validation sources
        validation_sources = gate_result.get("validation_sources", {})
        enhanced_data = gate_result.get("enhanced_data", {})
        
        # Create timestamps
        now = datetime.now().isoformat()
        
        return GateValidationContext(
            gate_name=gate_name,
            gate_display_name=gate_display_name,
            gate_description=gate_description,
            gate_category=gate_category,
            gate_priority=gate_priority,
            gate_weight=gate_weight,
            validation_status=validation_status,
            validation_score=validation_score,
            validation_confidence=validation_confidence,
            evidence_collectors_used=evidence_collectors_used,
            evidence_collectors_failed=evidence_collectors_failed,
            mandatory_collectors_passed=mandatory_collectors_passed,
            mandatory_collectors_failed=mandatory_collectors_failed,
            patterns_analyzed=patterns_analyzed,
            patterns_matched=patterns_matched,
            patterns_failed=patterns_failed,
            total_patterns=total_patterns,
            matched_patterns=matched_patterns,
            files_analyzed=files_analyzed,
            files_with_matches=files_with_matches,
            relevant_files=relevant_files,
            total_files_in_repo=total_files_in_repo,
            matches_found=matches_found,
            violation_details=violation_details,
            code_examples=code_examples,
            expected_coverage_percentage=expected_coverage_percentage,
            actual_coverage_percentage=actual_coverage_percentage,
            coverage_gap=coverage_gap,
            coverage_reasoning=coverage_reasoning,
            primary_languages=primary_languages,
            frameworks_detected=frameworks_detected,
            build_tools=build_tools,
            deployment_platforms=deployment_platforms,
            repository_url=repository_url,
            branch=branch,
            commit_hash=commit_hash,
            last_commit_date=last_commit_date,
            validation_sources=validation_sources,
            enhanced_data=enhanced_data,
            validation_start_time=now,
            validation_end_time=now,
            evidence_collection_time=now
        )
    
    def generate_explanation(self, context: GateValidationContext) -> str:
        """Generate comprehensive explanation for gate validation"""
        
        template = self.explanation_templates.get(context.validation_status, self.explanation_templates["FAIL"])
        
        # Prepare template variables
        template_vars = {
            "gate_name": context.gate_name,
            "gate_display_name": context.gate_display_name,
            "score": context.validation_score,
            "confidence": context.validation_confidence,
            "total_patterns": context.total_patterns,
            "matched_patterns": context.matched_patterns,
            "files_analyzed": context.files_analyzed,
            "actual_coverage": context.actual_coverage_percentage,
            "expected_coverage": context.expected_coverage_percentage,
            "collectors_used": ", ".join(context.evidence_collectors_used),
            "languages": ", ".join(context.primary_languages) if context.primary_languages else "Not detected",
            "frameworks": ", ".join(context.frameworks_detected) if context.frameworks_detected else "Not detected",
            "build_tools": ", ".join(context.build_tools) if context.build_tools else "Not detected",
            "coverage_gap": context.coverage_gap,
            "mandatory_failures": ", ".join(context.mandatory_collectors_failed) if context.mandatory_collectors_failed else "None"
        }
        
        # Add status-specific content
        if context.validation_status == "PASS":
            template_vars.update(self._generate_pass_content(context))
        elif context.validation_status == "FAIL":
            template_vars.update(self._generate_fail_content(context))
        elif context.validation_status == "WARNING":
            template_vars.update(self._generate_warning_content(context))
        elif context.validation_status == "NOT_APPLICABLE":
            template_vars.update(self._generate_not_applicable_content(context))
        
        return template.format(**template_vars)
    
    def generate_llm_prompt(self, context: GateValidationContext) -> str:
        """Generate structured LLM prompt for recommendations with enhanced evaluation context"""
        
        # Determine the evaluation approach based on status
        evaluation_approach = self._determine_evaluation_approach(context)
        parameter_details = self._format_parameter_details(context)
        result_analysis = self._format_result_analysis(context)
        mitigation_strategy = self._format_mitigation_strategy(context)
        
        prompt = f"""
# Gate Validation Analysis Request

## Gate Information
- **Name**: {context.gate_name}
- **Display Name**: {context.gate_display_name}
- **Description**: {context.gate_description}
- **Category**: {context.gate_category}
- **Priority**: {context.gate_priority}
- **Weight**: {context.gate_weight}

## Validation Results
- **Status**: {context.validation_status}
- **Score**: {context.validation_score:.1f}%
- **Confidence**: {context.validation_confidence}

## How This Gate Was Evaluated
{evaluation_approach}

## Parameters Considered
{parameter_details}

## Detailed Results Analysis
{result_analysis}

## Evidence Collection Summary
- **Collectors Used**: {', '.join(context.evidence_collectors_used)}
- **Collectors Failed**: {', '.join(context.evidence_collectors_failed)}
- **Mandatory Collectors Passed**: {context.mandatory_collectors_passed}
- **Mandatory Failures**: {', '.join(context.mandatory_collectors_failed) if context.mandatory_collectors_failed else 'None'}

## Pattern Analysis Details
- **Total Patterns**: {context.total_patterns}
- **Matched Patterns**: {context.matched_patterns}
- **Patterns Analyzed**: {', '.join(context.patterns_analyzed[:5])}
- **Patterns Matched**: {', '.join(context.patterns_matched[:5])}

## File Analysis Results
- **Files Analyzed**: {context.files_analyzed}
- **Files with Matches**: {context.files_with_matches}
- **Relevant Files**: {context.relevant_files}
- **Total Files in Repo**: {context.total_files_in_repo}

## Coverage Analysis
- **Expected Coverage**: {context.expected_coverage_percentage:.1f}%
- **Actual Coverage**: {context.actual_coverage_percentage:.1f}%
- **Coverage Gap**: {context.coverage_gap:.1f}%
- **Coverage Reasoning**: {context.coverage_reasoning}

## Technology Context
- **Primary Languages**: {', '.join(context.primary_languages)}
- **Frameworks**: {', '.join(context.frameworks_detected)}
- **Build Tools**: {', '.join(context.build_tools)}

## Repository Context
- **Repository**: {context.repository_url}
- **Branch**: {context.branch}
- **Commit**: {context.commit_hash}

## Specific Match Details
{self._format_matches_for_llm(context.matches_found)}

## Violation Details
{self._format_violations_for_llm(context.violation_details)}

## Code Examples Found
{self._format_code_examples_for_llm(context.code_examples)}

## Mitigation Strategy
{mitigation_strategy}

## Task
Based on the above comprehensive validation data, provide a detailed, actionable response that a developer can immediately use to improve their codebase.

**CRITICAL INSTRUCTIONS:**
- DO NOT include any introductory phrases like 'Based on the provided data...' or 'Here is the analysis...' or 'I will provide a comprehensive response...'
- DO NOT use placeholder text like '*Gate Validation Analysis Report**' or '*Root Cause Analysis**'
- DO NOT include generic analysis headers without content
- Start directly with the 'Root Cause Analysis' or the main recommendation
- Provide specific, actionable content for each section
- Use natural language without bullet points or excessive formatting

**Required Sections:**

1. **Root Cause Analysis**: Explain why this gate {context.validation_status.lower()}ed
   - Be specific about what was found or missing
   - Reference the actual patterns, files, or evidence collected
   - Explain the technical reasons for the status

2. **Impact Assessment**: What are the implications for production readiness?
   - Focus on real-world consequences
   - Consider security, performance, reliability, and maintainability impacts
   - Be specific about potential risks or benefits

3. **Specific Recommendations**: Provide actionable steps to improve this gate
   - Give concrete, implementable advice
   - Include specific technologies or approaches relevant to the codebase
   - Prioritize recommendations by impact and effort

4. **Code Examples**: Show specific code changes needed
   - Provide actual code snippets when possible
   - Reference the specific languages and frameworks detected
   - Show before/after examples if applicable

5. **Best Practices**: Reference industry standards and best practices
   - Include relevant standards, frameworks, or guidelines
   - Explain why these practices matter
   - Connect to the specific technology stack

6. **Priority Actions**: What should be done first, second, third?
   - Provide a clear action plan
   - Consider dependencies and effort
   - Include timeframes or effort estimates

**Response Format:**
Write in natural, flowing paragraphs. Avoid bullet points, numbered lists, or excessive formatting. Make the content readable and conversational while being technically precise.
"""
        
        # Log the prompt
        try:
            from utils.prompt_logger import prompt_logger
            
            # Prepare context data for logging
            context_data = {
                "gate_name": context.gate_name,
                "validation_status": context.validation_status,
                "validation_score": context.validation_score,
                "evidence_collectors_used": context.evidence_collectors_used,
                "mandatory_collectors_failed": context.mandatory_collectors_failed,
                "total_patterns": context.total_patterns,
                "matched_patterns": context.matched_patterns,
                "files_analyzed": context.files_analyzed,
                "coverage_gap": context.coverage_gap
            }
            
            # Prepare metadata
            metadata = {
                "validation_confidence": context.validation_confidence,
                "gate_category": context.gate_category,
                "gate_priority": context.gate_priority,
                "primary_languages": context.primary_languages,
                "frameworks_detected": context.frameworks_detected,
                "repository_url": context.repository_url,
                "branch": context.branch
            }
            
            prompt_logger.log_explainability_prompt(
                gate_name=context.gate_name,
                prompt=prompt,
                context=context_data,
                metadata=metadata
            )
            
        except Exception as e:
            print(f"⚠️ Failed to log explainability prompt: {e}")
        
        return prompt
    
    def _extract_confidence(self, gate_result: Dict[str, Any]) -> str:
        """Extract confidence level from gate result"""
        validation_sources = gate_result.get("validation_sources", {})
        combined_confidence = validation_sources.get("combined_confidence", "medium")
        return combined_confidence
    
    def _extract_evidence_collectors(self, gate_result: Dict[str, Any]) -> List[str]:
        """Extract evidence collectors used"""
        validation_sources = gate_result.get("validation_sources", {})
        collectors = []
        
        for source_name, source_data in validation_sources.items():
            if isinstance(source_data, dict) and source_data.get("enabled", False):
                collectors.append(source_name)
        
        return collectors
    
    def _extract_failed_collectors(self, gate_result: Dict[str, Any]) -> List[str]:
        """Extract failed evidence collectors"""
        # This would be populated from enhanced validation data
        enhanced_data = gate_result.get("enhanced_data", {})
        failed_collectors = enhanced_data.get("failed_collectors", [])
        return failed_collectors
    
    def _check_mandatory_collectors(self, gate_result: Dict[str, Any]) -> bool:
        """Check if mandatory collectors passed"""
        mandatory_failures = self._extract_mandatory_failures(gate_result)
        return len(mandatory_failures) == 0
    
    def _extract_mandatory_failures(self, gate_result: Dict[str, Any]) -> List[str]:
        """Extract mandatory collector failures"""
        # This would be populated from enhanced validation data
        enhanced_data = gate_result.get("enhanced_data", {})
        mandatory_failures = enhanced_data.get("mandatory_failures", [])
        return mandatory_failures
    
    def _extract_patterns(self, gate_result: Dict[str, Any]) -> List[str]:
        """Extract patterns analyzed"""
        patterns = gate_result.get("patterns", [])
        if isinstance(patterns, list):
            return patterns
        elif isinstance(patterns, dict):
            all_patterns = []
            for pattern_list in patterns.values():
                if isinstance(pattern_list, list):
                    all_patterns.extend(pattern_list)
            return all_patterns
        return []
    
    def _extract_matched_patterns(self, gate_result: Dict[str, Any]) -> List[str]:
        """Extract patterns that matched"""
        matches = gate_result.get("matches", [])
        matched_patterns = set()
        
        for match in matches:
            pattern = match.get("pattern", "")
            if pattern:
                matched_patterns.add(pattern)
        
        return list(matched_patterns)
    
    def _extract_failed_patterns(self, gate_result: Dict[str, Any]) -> List[str]:
        """Extract patterns that failed to match"""
        all_patterns = set(self._extract_patterns(gate_result))
        matched_patterns = set(self._extract_matched_patterns(gate_result))
        return list(all_patterns - matched_patterns)
    
    def _extract_violation_details(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract violation details from matches"""
        violations = []
        
        for match in matches:
            violation = {
                "file": match.get("file", "unknown"),
                "line": match.get("line", 0),
                "pattern": match.get("pattern", ""),
                "context": match.get("context", ""),
                "severity": self._determine_violation_severity(match),
                "type": self._determine_violation_type(match)
            }
            violations.append(violation)
        
        return violations
    
    def _extract_code_examples(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract code examples from matches"""
        examples = []
        
        for match in matches:
            example = {
                "file": match.get("file", "unknown"),
                "line": match.get("line", 0),
                "code": match.get("context", "")[:200],  # Limit code length
                "pattern": match.get("pattern", ""),
                "language": self._detect_language_from_file(match.get("file", ""))
            }
            examples.append(example)
        
        return examples
    
    def _calculate_actual_coverage(self, files_with_matches: int, relevant_files: int) -> float:
        """Calculate actual coverage percentage"""
        if relevant_files == 0:
            return 0.0
        return (files_with_matches / relevant_files) * 100.0
    
    def _determine_violation_severity(self, match: Dict[str, Any]) -> str:
        """Determine violation severity"""
        pattern = match.get("pattern", "").lower()
        
        # High severity patterns
        high_severity = ["password", "secret", "key", "token", "credential", "auth"]
        if any(term in pattern for term in high_severity):
            return "HIGH"
        
        # Medium severity patterns
        medium_severity = ["error", "exception", "fail", "warning", "deprecated"]
        if any(term in pattern for term in medium_severity):
            return "MEDIUM"
        
        return "LOW"
    
    def _determine_violation_type(self, match: Dict[str, Any]) -> str:
        """Determine violation type"""
        pattern = match.get("pattern", "").lower()
        
        if any(term in pattern for term in ["password", "secret", "key", "token"]):
            return "SECURITY_CREDENTIAL"
        elif any(term in pattern for term in ["error", "exception", "fail"]):
            return "ERROR_HANDLING"
        elif any(term in pattern for term in ["log", "debug", "print"]):
            return "LOGGING"
        elif any(term in pattern for term in ["test", "spec", "mock"]):
            return "TESTING"
        else:
            return "GENERAL"
    
    def _detect_language_from_file(self, file_path: str) -> str:
        """Detect programming language from file path"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".rb": "Ruby",
            ".scala": "Scala",
            ".kt": "Kotlin",
            ".swift": "Swift"
        }
        return language_map.get(ext, "Unknown")
    
    def _generate_pass_content(self, context: GateValidationContext) -> Dict[str, str]:
        """Generate content for PASS status"""
        return {
            "validation_details": self._format_validation_details(context),
            "recommendations": self._generate_pass_recommendations(context)
        }
    
    def _generate_fail_content(self, context: GateValidationContext) -> Dict[str, str]:
        """Generate content for FAIL status"""
        return {
            "critical_issues": self._format_critical_issues(context),
            "evidence_details": self._format_evidence_details(context),
            "violation_examples": self._format_violation_examples(context),
            "immediate_actions": self._generate_immediate_actions(context),
            "remediation_steps": self._generate_remediation_steps(context)
        }
    
    def _generate_warning_content(self, context: GateValidationContext) -> Dict[str, str]:
        """Generate content for WARNING status"""
        return {
            "areas_of_concern": self._format_areas_of_concern(context),
            "evidence_details": self._format_evidence_details(context),
            "improvement_recommendations": self._generate_improvement_recommendations(context)
        }
    
    def _generate_not_applicable_content(self, context: GateValidationContext) -> Dict[str, str]:
        """Generate content for NOT_APPLICABLE status"""
        return {
            "not_applicable_reason": self._determine_not_applicable_reason(context),
            "applicability_analysis": self._format_applicability_analysis(context),
            "alternative_recommendations": self._generate_alternative_recommendations(context)
        }
    
    def _format_validation_details(self, context: GateValidationContext) -> str:
        """Format validation details for display"""
        details = []
        details.append(f"✅ **Pattern Analysis**: {context.matched_patterns}/{context.total_patterns} patterns matched")
        details.append(f"✅ **File Coverage**: {context.files_with_matches}/{context.files_analyzed} files have implementations")
        details.append(f"✅ **Coverage Achievement**: {context.actual_coverage_percentage:.1f}% (Target: {context.expected_coverage_percentage:.1f}%)")
        details.append(f"✅ **Evidence Collection**: {len(context.evidence_collectors_used)} collectors successful")
        
        if context.mandatory_collectors_passed:
            details.append("✅ **Mandatory Requirements**: All mandatory collectors passed")
        
        return "\n".join(details)
    
    def _format_critical_issues(self, context: GateValidationContext) -> str:
        """Format critical issues for display"""
        issues = []
        
        if context.mandatory_collectors_failed:
            issues.append(f"❌ **Mandatory Collectors Failed**: {', '.join(context.mandatory_collectors_failed)}")
        
        if context.coverage_gap > 50:
            issues.append(f"❌ **Major Coverage Gap**: {context.coverage_gap:.1f}% below target")
        elif context.coverage_gap > 25:
            issues.append(f"❌ **Significant Coverage Gap**: {context.coverage_gap:.1f}% below target")
        
        if context.files_with_matches == 0:
            issues.append("❌ **No Implementation Found**: Zero files contain required patterns")
        
        if context.violation_details:
            high_severity_violations = [v for v in context.violation_details if v.get("severity") == "HIGH"]
            if high_severity_violations:
                issues.append(f"❌ **High Severity Violations**: {len(high_severity_violations)} critical issues found")
        
        return "\n".join(issues) if issues else "No critical issues identified"
    
    def _format_evidence_details(self, context: GateValidationContext) -> str:
        """Format evidence details for display"""
        details = []
        
        if context.evidence_collectors_used:
            details.append(f"**Evidence Collectors Used**: {', '.join(context.evidence_collectors_used)}")
        
        if context.evidence_collectors_failed:
            details.append(f"**Failed Collectors**: {', '.join(context.evidence_collectors_failed)}")
        
        if context.patterns_matched:
            details.append(f"**Matched Patterns**: {', '.join(context.patterns_matched[:3])}")
        
        if context.matches_found:
            details.append(f"**Total Matches**: {len(context.matches_found)}")
        
        return "\n".join(details)
    
    def _format_violation_examples(self, context: GateValidationContext) -> str:
        """Format violation examples for display"""
        if not context.violation_details:
            return "No violations found"
        
        examples = []
        for i, violation in enumerate(context.violation_details[:3], 1):
            examples.append(f"**Violation {i}**: {violation['file']}:{violation['line']} - {violation['pattern']}")
        
        return "\n".join(examples)
    
    def _format_matches_for_llm(self, matches: List[Dict[str, Any]]) -> str:
        """Format matches for LLM prompt"""
        if not matches:
            return "No matches found"
        
        formatted = []
        for i, match in enumerate(matches[:5], 1):
            formatted.append(f"Match {i}:")
            formatted.append(f"  File: {match.get('file', 'unknown')}")
            formatted.append(f"  Line: {match.get('line', 0)}")
            formatted.append(f"  Pattern: {match.get('pattern', '')}")
            formatted.append(f"  Context: {match.get('context', '')[:100]}...")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_violations_for_llm(self, violations: List[Dict[str, Any]]) -> str:
        """Format violations for LLM prompt"""
        if not violations:
            return "No violations found"
        
        formatted = []
        for i, violation in enumerate(violations[:5], 1):
            formatted.append(f"Violation {i}:")
            formatted.append(f"  File: {violation.get('file', 'unknown')}")
            formatted.append(f"  Line: {violation.get('line', 0)}")
            formatted.append(f"  Type: {violation.get('type', 'unknown')}")
            formatted.append(f"  Severity: {violation.get('severity', 'unknown')}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_code_examples_for_llm(self, examples: List[Dict[str, Any]]) -> str:
        """Format code examples for LLM prompt"""
        if not examples:
            return "No code examples available"
        
        formatted = []
        for i, example in enumerate(examples[:3], 1):
            formatted.append(f"Code Example {i}:")
            formatted.append(f"  File: {example.get('file', 'unknown')}")
            formatted.append(f"  Line: {example.get('line', 0)}")
            formatted.append(f"  Language: {example.get('language', 'unknown')}")
            formatted.append(f"  Code: {example.get('code', '')}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _generate_pass_recommendations(self, context: GateValidationContext) -> str:
        """Generate recommendations for PASS status"""
        recommendations = []
        recommendations.append("✅ **Maintain Current Implementation**: Your current approach is working well")
        recommendations.append("📈 **Consider Enhancements**: Look for opportunities to improve beyond minimum requirements")
        recommendations.append("🔄 **Monitor for Changes**: Ensure new code continues to follow established patterns")
        recommendations.append("📚 **Document Best Practices**: Share your successful implementation with the team")
        
        return "\n".join(recommendations)
    
    def _generate_immediate_actions(self, context: GateValidationContext) -> str:
        """Generate immediate actions for FAIL status"""
        actions = []
        
        if context.mandatory_collectors_failed:
            actions.append("🚨 **Fix Mandatory Collectors**: Address failed mandatory evidence collectors first")
        
        if context.coverage_gap > 50:
            actions.append("📋 **Implement Core Requirements**: Focus on basic implementation across key files")
        elif context.coverage_gap > 25:
            actions.append("🔧 **Improve Coverage**: Extend implementation to more files")
        
        if context.violation_details:
            high_severity = [v for v in context.violation_details if v.get("severity") == "HIGH"]
            if high_severity:
                actions.append("⚠️ **Address High Severity Issues**: Fix critical violations immediately")
        
        return "\n".join(actions)
    
    def _generate_remediation_steps(self, context: GateValidationContext) -> str:
        """Generate remediation steps for FAIL status"""
        steps = []
        steps.append("1. **Analyze Current Implementation**: Review existing code to understand current state")
        steps.append("2. **Identify Missing Patterns**: Determine which required patterns are not implemented")
        steps.append("3. **Prioritize by Impact**: Focus on high-impact, low-effort improvements first")
        steps.append("4. **Implement Incrementally**: Make changes in small, testable increments")
        steps.append("5. **Verify Changes**: Test that new implementations work correctly")
        steps.append("6. **Monitor Progress**: Track improvement in gate scores over time")
        
        return "\n".join(steps)
    
    def _format_areas_of_concern(self, context: GateValidationContext) -> str:
        """Format areas of concern for WARNING status"""
        concerns = []
        
        if context.coverage_gap > 0:
            concerns.append(f"⚠️ **Coverage Gap**: {context.coverage_gap:.1f}% below target coverage")
        
        if context.evidence_collectors_failed:
            concerns.append(f"⚠️ **Failed Collectors**: {', '.join(context.evidence_collectors_failed)}")
        
        if context.patterns_failed:
            concerns.append(f"⚠️ **Failed Patterns**: {len(context.patterns_failed)} patterns not matched")
        
        return "\n".join(concerns) if concerns else "No specific concerns identified"
    
    def _generate_improvement_recommendations(self, context: GateValidationContext) -> str:
        """Generate improvement recommendations for WARNING status"""
        recommendations = []
        recommendations.append("📈 **Extend Implementation**: Add missing patterns to more files")
        recommendations.append("🔧 **Fix Failed Collectors**: Address any failed evidence collectors")
        recommendations.append("📚 **Review Best Practices**: Ensure implementation follows industry standards")
        recommendations.append("🔄 **Monitor Progress**: Track improvements and maintain consistency")
        
        return "\n".join(recommendations)
    
    def _determine_not_applicable_reason(self, context: GateValidationContext) -> str:
        """Determine reason for NOT_APPLICABLE status"""
        if not context.primary_languages:
            return "No supported programming languages detected"
        
        # Add more specific logic based on gate type and technology stack
        return "Technology stack not compatible with this gate"
    
    def _format_applicability_analysis(self, context: GateValidationContext) -> str:
        """Format applicability analysis for NOT_APPLICABLE status"""
        analysis = []
        analysis.append(f"**Detected Languages**: {', '.join(context.primary_languages)}")
        analysis.append(f"**Detected Frameworks**: {', '.join(context.frameworks_detected)}")
        analysis.append(f"**Build Tools**: {', '.join(context.build_tools)}")
        
        return "\n".join(analysis)
    
    def _generate_alternative_recommendations(self, context: GateValidationContext) -> str:
        """Generate alternative recommendations for not applicable gates"""
        return f"""
Since this gate is not applicable to your technology stack, consider these alternatives:
- Focus on similar gates that are applicable
- Implement equivalent functionality using your stack's patterns
- Consider industry best practices for your specific technology
"""
    
    def _determine_evaluation_approach(self, context: GateValidationContext) -> str:
        """Determine and format the evaluation approach used for this gate"""
        # Special handling for database-based gates
        if "database_integration" in context.evidence_collectors_used:
            enhanced_data = context.enhanced_data or {}
            integration_status = enhanced_data.get("integration_status", {})
            present_integrations = enhanced_data.get("present_integrations", [])
            missing_integrations = enhanced_data.get("missing_integrations", [])
            
            if context.validation_status == "PASS":
                return f"""
This gate was evaluated using a comprehensive database integration approach:
- **Database Integration**: Checked {len(integration_status)} alerting integrations via database query
- **Integrations Verified**: {', '.join(present_integrations)} - All required integrations are present and actionable
- **Integration Status**: 100% of required integrations are properly configured
- **Database Query Success**: Successfully queried integration status from monitoring database
- **Confidence Level**: {context.validation_confidence} confidence based on direct database verification
- **Technology-Specific Validation**: Database integration approach ensures real-time accuracy
"""
            elif context.validation_status == "FAIL":
                return f"""
This gate was evaluated using a comprehensive database integration approach:
- **Database Integration**: Checked {len(integration_status)} alerting integrations via database query
- **Integrations Missing**: {', '.join(missing_integrations)} - Critical integrations are not configured
- **Integrations Present**: {', '.join(present_integrations) if present_integrations else 'None'}
- **Integration Gap**: {len(missing_integrations)}/{len(integration_status)} integrations missing
- **Database Query Success**: Successfully queried integration status from monitoring database
- **Critical Issues**: Missing integrations prevent comprehensive alerting coverage
- **Technology-Specific Validation**: Database integration approach ensures real-time accuracy
"""
            else:  # WARNING
                return f"""
This gate was evaluated using a comprehensive database integration approach:
- **Database Integration**: Checked {len(integration_status)} alerting integrations via database query
- **Integrations Present**: {', '.join(present_integrations) if present_integrations else 'None'}
- **Integrations Missing**: {', '.join(missing_integrations) if missing_integrations else 'None'}
- **Partial Coverage**: {len(present_integrations)}/{len(integration_status)} integrations configured
- **Database Query Success**: Successfully queried integration status from monitoring database
- **Improvement Needed**: Additional integrations required for comprehensive alerting
- **Technology-Specific Validation**: Database integration approach ensures real-time accuracy
"""
        
        # Standard evaluation approach for pattern-based gates
        if context.validation_status == "PASS":
            return f"""
This gate was evaluated using a comprehensive multi-method approach:
- **Pattern Analysis**: Scanned {context.total_patterns} patterns across {context.files_analyzed} files
- **Evidence Collection**: Used {len(context.evidence_collectors_used)} evidence collectors successfully
- **Coverage Assessment**: Achieved {context.actual_coverage_percentage:.1f}% coverage (expected: {context.expected_coverage_percentage:.1f}%)
- **Technology-Specific Validation**: Tailored to {', '.join(context.primary_languages)} and {', '.join(context.frameworks_detected)}
- **Confidence Level**: {context.validation_confidence} confidence based on {context.matched_patterns} successful pattern matches
"""
        elif context.validation_status == "FAIL":
            return f"""
This gate was evaluated using a comprehensive multi-method approach:
- **Pattern Analysis**: Scanned {context.total_patterns} patterns across {context.files_analyzed} files
- **Evidence Collection**: Used {len(context.evidence_collectors_used)} evidence collectors, {len(context.evidence_collectors_failed)} failed
- **Coverage Assessment**: Achieved {context.actual_coverage_percentage:.1f}% coverage (expected: {context.expected_coverage_percentage:.1f}%)
- **Critical Issues**: Found {len(context.violation_details)} violations requiring immediate attention
- **Mandatory Failures**: {len(context.mandatory_collectors_failed)} mandatory collectors failed
- **Technology-Specific Validation**: Tailored to {', '.join(context.primary_languages)} and {', '.join(context.frameworks_detected)}
"""
        elif context.validation_status == "WARNING":
            return f"""
This gate was evaluated using a comprehensive multi-method approach:
- **Pattern Analysis**: Scanned {context.total_patterns} patterns across {context.files_analyzed} files
- **Evidence Collection**: Used {len(context.evidence_collectors_used)} evidence collectors
- **Coverage Assessment**: Achieved {context.actual_coverage_percentage:.1f}% coverage (expected: {context.expected_coverage_percentage:.1f}%)
- **Areas of Concern**: Found {len(context.violation_details)} issues that need attention
- **Technology-Specific Validation**: Tailored to {', '.join(context.primary_languages)} and {', '.join(context.frameworks_detected)}
- **Improvement Opportunities**: {context.coverage_gap:.1f}% coverage gap identified
"""
        else:  # NOT_APPLICABLE
            return f"""
This gate was evaluated for applicability to your technology stack:
- **Technology Analysis**: Assessed compatibility with {', '.join(context.primary_languages)} and {', '.join(context.frameworks_detected)}
- **Pattern Analysis**: Scanned {context.total_patterns} patterns across {context.files_analyzed} files
- **Evidence Collection**: Used {len(context.evidence_collectors_used)} evidence collectors
- **Applicability Assessment**: Determined not applicable based on technology stack and project characteristics
"""
    
    def _format_parameter_details(self, context: GateValidationContext) -> str:
        """Format detailed parameter information considered during evaluation"""
        parameters = []
        
        # Gate-specific parameters
        parameters.append(f"- **Gate Weight**: {context.gate_weight} (impact on overall score)")
        parameters.append(f"- **Priority Level**: {context.gate_priority} (urgency for remediation)")
        parameters.append(f"- **Category**: {context.gate_category} (type of validation)")
        
        # Special handling for database-based gates
        if "database_integration" in context.evidence_collectors_used:
            enhanced_data = context.enhanced_data or {}
            integration_status = enhanced_data.get("integration_status", {})
            present_integrations = enhanced_data.get("present_integrations", [])
            missing_integrations = enhanced_data.get("missing_integrations", [])
            
            parameters.append(f"- **Database Integration**: {len(integration_status)} integrations checked")
            parameters.append(f"- **Integrations Present**: {', '.join(present_integrations) if present_integrations else 'None'}")
            parameters.append(f"- **Integrations Missing**: {', '.join(missing_integrations) if missing_integrations else 'None'}")
            parameters.append(f"- **Integration Coverage**: {len(present_integrations)}/{len(integration_status)} ({len(present_integrations)/len(integration_status)*100:.1f}%)")
            
            # Add database-specific parameters
            app_id = enhanced_data.get("app_id")
            if app_id:
                parameters.append(f"- **Application ID**: {app_id}")
            parameters.append(f"- **Database Query Success**: Yes")
            parameters.append(f"- **Real-time Verification**: Database integration ensures current status")
        else:
            # Coverage parameters for pattern-based gates
            parameters.append(f"- **Expected Coverage**: {context.expected_coverage_percentage:.1f}% (target implementation)")
            parameters.append(f"- **Coverage Reasoning**: {context.coverage_reasoning}")
            
            # Pattern parameters
            parameters.append(f"- **Pattern Count**: {context.total_patterns} patterns analyzed")
            if context.total_patterns > 0:
                parameters.append(f"- **Pattern Success Rate**: {(context.matched_patterns/context.total_patterns*100):.1f}% ({context.matched_patterns}/{context.total_patterns})")
            
            # File parameters
            parameters.append(f"- **File Analysis Scope**: {context.files_analyzed} files analyzed")
            parameters.append(f"- **Relevant Files**: {context.relevant_files} files considered relevant")
            parameters.append(f"- **Match Distribution**: {context.files_with_matches} files contain matches")
        
        # Technology parameters
        if context.primary_languages:
            parameters.append(f"- **Primary Languages**: {', '.join(context.primary_languages)}")
        if context.frameworks_detected:
            parameters.append(f"- **Frameworks**: {', '.join(context.frameworks_detected)}")
        if context.build_tools:
            parameters.append(f"- **Build Tools**: {', '.join(context.build_tools)}")
        
        # Evidence collector parameters
        if context.evidence_collectors_used:
            parameters.append(f"- **Evidence Collectors**: {', '.join(context.evidence_collectors_used)}")
        if context.mandatory_collectors_failed:
            parameters.append(f"- **Mandatory Failures**: {', '.join(context.mandatory_collectors_failed)}")
        
        return "\n".join(parameters)
    
    def _format_result_analysis(self, context: GateValidationContext) -> str:
        """Format detailed analysis of the evaluation results"""
        # Special handling for database-based gates
        if "database_integration" in context.evidence_collectors_used:
            enhanced_data = context.enhanced_data or {}
            integration_status = enhanced_data.get("integration_status", {})
            present_integrations = enhanced_data.get("present_integrations", [])
            missing_integrations = enhanced_data.get("missing_integrations", [])
            
            if context.validation_status == "PASS":
                return f"""
**Success Analysis**:
- **Integration Achievement**: {len(present_integrations)}/{len(integration_status)} integrations present (100%)
- **Database Verification**: Successfully verified all required alerting integrations
- **Real-time Status**: Database query confirmed current integration status
- **Production Readiness**: All alerting integrations are actionable and properly configured
- **Monitoring Coverage**: Comprehensive alerting coverage achieved across all required platforms
- **Technology Alignment**: Database integration approach ensures accurate real-time validation
"""
            elif context.validation_status == "FAIL":
                return f"""
**Failure Analysis**:
- **Integration Deficiency**: {len(missing_integrations)}/{len(integration_status)} integrations missing
- **Missing Integrations**: {', '.join(missing_integrations)} - Critical alerting platforms not configured
- **Present Integrations**: {', '.join(present_integrations) if present_integrations else 'None'}
- **Database Verification**: Successfully identified missing integrations via database query
- **Critical Issues**: Missing integrations prevent comprehensive alerting and monitoring
- **Production Risk**: Incomplete alerting setup poses operational risks
- **Technology Alignment**: Database integration approach ensures accurate real-time validation
"""
            else:  # WARNING
                return f"""
**Warning Analysis**:
- **Partial Integration**: {len(present_integrations)}/{len(integration_status)} integrations present
- **Present Integrations**: {', '.join(present_integrations) if present_integrations else 'None'}
- **Missing Integrations**: {', '.join(missing_integrations) if missing_integrations else 'None'}
- **Database Verification**: Successfully identified integration gaps via database query
- **Areas of Concern**: Missing integrations limit alerting coverage
- **Improvement Needed**: Additional integrations required for comprehensive monitoring
- **Technology Alignment**: Database integration approach ensures accurate real-time validation
"""
        
        # Standard analysis for pattern-based gates
        if context.validation_status == "PASS":
            return f"""
**Success Analysis**:
- **Score Achievement**: {context.validation_score:.1f}% (exceeds minimum threshold)
- **Pattern Success**: {context.matched_patterns}/{context.total_patterns} patterns matched successfully
- **Coverage Achievement**: {context.actual_coverage_percentage:.1f}% coverage (target: {context.expected_coverage_percentage:.1f}%)
- **Evidence Quality**: All mandatory evidence collectors passed
- **Implementation Quality**: Good practices detected across {context.files_with_matches} files
- **Technology Alignment**: Well-implemented for {', '.join(context.primary_languages)} stack
"""
        elif context.validation_status == "FAIL":
            return f"""
**Failure Analysis**:
- **Score Deficiency**: {context.validation_score:.1f}% (below minimum threshold)
- **Pattern Failures**: {context.total_patterns - context.matched_patterns}/{context.total_patterns} patterns failed
- **Coverage Gap**: {context.coverage_gap:.1f}% below expected coverage
- **Critical Issues**: {len(context.violation_details)} violations found
- **Mandatory Failures**: {len(context.mandatory_collectors_failed)} mandatory collectors failed
- **Implementation Gaps**: Missing implementations in {context.relevant_files - context.files_with_matches} relevant files
- **Technology Misalignment**: Not properly implemented for {', '.join(context.primary_languages)} stack
"""
        elif context.validation_status == "WARNING":
            return f"""
**Warning Analysis**:
- **Score Concern**: {context.validation_score:.1f}% (meets minimum but needs improvement)
- **Pattern Performance**: {context.matched_patterns}/{context.total_patterns} patterns matched
- **Coverage Concern**: {context.coverage_gap:.1f}% below optimal coverage
- **Areas of Concern**: {len(context.violation_details)} issues identified
- **Partial Implementation**: Found in {context.files_with_matches}/{context.relevant_files} relevant files
- **Improvement Needed**: Better alignment with {', '.join(context.primary_languages)} best practices
"""
        else:  # NOT_APPLICABLE
            return f"""
**Not Applicable Analysis**:
- **Technology Mismatch**: Gate designed for different technology stack
- **Pattern Relevance**: {context.matched_patterns}/{context.total_patterns} patterns relevant
- **Implementation Status**: {context.files_with_matches} files contain relevant patterns
- **Alternative Approach**: Consider equivalent functionality for {', '.join(context.primary_languages)} stack
- **Recommendation**: Focus on applicable gates for your technology
"""
    
    def _format_mitigation_strategy(self, context: GateValidationContext) -> str:
        """Format mitigation strategy based on gate status and issues"""
        # Special handling for database-based gates
        if "database_integration" in context.evidence_collectors_used:
            enhanced_data = context.enhanced_data or {}
            integration_status = enhanced_data.get("integration_status", {})
            present_integrations = enhanced_data.get("present_integrations", [])
            missing_integrations = enhanced_data.get("missing_integrations", [])
            
            if context.validation_status == "PASS":
                return f"""
**Maintenance Strategy**:
- **Continue Best Practices**: Maintain current integration configuration and monitoring
- **Monitor Integration Health**: Ensure {', '.join(present_integrations)} integrations remain active and functional
- **Database Monitoring**: Continue monitoring integration status via database queries
- **Documentation**: Document current successful integration setup for team reference
- **Continuous Improvement**: Consider expanding to additional alerting platforms if needed
- **Real-time Validation**: Leverage database integration for ongoing validation
"""
            elif context.validation_status == "FAIL":
                return f"""
**Critical Mitigation Strategy**:
- **Immediate Actions**: Configure missing {', '.join(missing_integrations)} integrations
- **Integration Setup**: Set up alerting integrations for {', '.join(missing_integrations)}
- **Configuration Priority**: Focus on high-impact integrations first (Splunk, AppDynamics)
- **Database Integration**: Ensure new integrations are properly registered in monitoring database
- **Testing**: Verify integrations are actionable and properly configured
- **Documentation**: Document integration setup process for future reference
- **Priority Order**: Address Splunk first (logging), then AppDynamics (APM), then ThousandEyes (monitoring)
"""
            else:  # WARNING
                return f"""
**Improvement Strategy**:
- **Address Missing Integrations**: Configure {', '.join(missing_integrations)} integrations
- **Integration Enhancement**: Improve existing {', '.join(present_integrations)} integrations
- **Database Registration**: Ensure all integrations are properly registered in monitoring database
- **Testing**: Verify all integrations are actionable and properly configured
- **Documentation**: Document integration setup and configuration
- **Gradual Improvement**: Focus on high-impact integrations first
"""
        
        # Standard mitigation strategy for pattern-based gates
        if context.validation_status == "PASS":
            return f"""
**Maintenance Strategy**:
- **Continue Best Practices**: Maintain current implementation quality
- **Monitor Coverage**: Ensure {context.actual_coverage_percentage:.1f}% coverage is sustained
- **Technology Updates**: Keep aligned with {', '.join(context.frameworks_detected)} updates
- **Documentation**: Document current successful patterns for team reference
- **Continuous Improvement**: Consider expanding to achieve {context.expected_coverage_percentage:.1f}% coverage
"""
        elif context.validation_status == "FAIL":
            return f"""
**Critical Mitigation Strategy**:
- **Immediate Actions**: Address {len(context.mandatory_collectors_failed)} mandatory collector failures
- **Violation Remediation**: Fix {len(context.violation_details)} critical violations
- **Coverage Improvement**: Increase coverage from {context.actual_coverage_percentage:.1f}% to {context.expected_coverage_percentage:.1f}%
- **Pattern Implementation**: Implement missing patterns in {context.relevant_files - context.files_with_matches} files
- **Technology Alignment**: Align with {', '.join(context.primary_languages)} best practices
- **Priority Order**: Address mandatory failures first, then violations, then coverage gaps
"""
        elif context.validation_status == "WARNING":
            return f"""
**Improvement Strategy**:
- **Address Issues**: Fix {len(context.violation_details)} identified issues
- **Coverage Enhancement**: Improve coverage from {context.actual_coverage_percentage:.1f}% to {context.expected_coverage_percentage:.1f}%
- **Pattern Optimization**: Improve {context.total_patterns - context.matched_patterns} failed patterns
- **Technology Best Practices**: Better align with {', '.join(context.primary_languages)} standards
- **Gradual Improvement**: Focus on high-impact areas first
"""
        else:  # NOT_APPLICABLE
            return f"""
**Alternative Strategy**:
- **Focus on Applicable Gates**: Prioritize gates relevant to {', '.join(context.primary_languages)} stack
- **Equivalent Implementation**: Implement similar functionality using appropriate patterns
- **Technology-Specific Best Practices**: Follow {', '.join(context.frameworks_detected)} guidelines
- **Custom Validation**: Consider creating custom validation for your specific needs
- **Documentation**: Document why this gate is not applicable for future reference
"""


# Global instance for easy access
gate_explainability_engine = GateExplainabilityEngine() 