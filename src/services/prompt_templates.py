#!/usr/bin/env python3
"""
Comprehensive Prompt Templates Management
Consolidates all prompt templates from JSON files into a structured Python class
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Prompt template structure"""
    use_case: str
    description: str
    prompt_template: str
    parameters: Dict[str, Any]


class PromptTemplates:
    """
    Comprehensive prompt templates management class
    Consolidates all prompts from JSON files into a structured Python interface
    """
    
    def __init__(self):
        """Initialize with all prompt templates"""
        # Use centralized gate definitions instead of local initialization
        from models.gate_definitions import gate_registry
        self.gates = gate_registry._gates
        self.templates = self._initialize_templates()
        
        print(f"📝 PromptTemplates initialized: {len(self.gates)} gates, {len(self.templates)} templates")
    
    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates"""
        templates = {}
        
        # LLM Pre-Analysis Template
        templates["llm_pre_analysis"] = PromptTemplate(
            use_case="LLM Pre-Analysis for Dynamic Pattern Generation",
            description="Template for LLM pre-analysis to generate dynamic patterns based on project structure",
            prompt_template="""
            
            STRICTLY PROVIDE THE RESPONSE AS A VALID JSON OBJECT AND IT SHOULD NOT INCLUDE ANY OTHER TEXT OR MARKDOWN FORMATTING.
            You are an expert code analysis assistant. Analyze the following project structure and generate dynamic patterns for security gates.

PROJECT STRUCTURE:
{project_structure}

BUILD CONFIGURATIONS:
{build_configs}

EXTRACTED CODE SNIPPETS:
{extracted_code}

AVAILABLE GATES:
{available_gates}

Based on the build configurations file contents and project structure, perform comprehensive analysis and generate dynamic patterns for ALL 16 security gates. Consider:

1. **Technology Stack Relevance**: Which gates are most relevant to the technologies used?
2. **Project Type**: What type of application is this and what gates apply?
3. **Architecture Patterns**: What architectural patterns suggest specific gate implementations?
4. **Dependencies**: What external dependencies are used in the project?
5. **Build Tools**: What build tools and configurations suggest specific implementations?

For each applicable gate, provide:
- gate_id: The gate identifier
- name: A descriptive name for the pattern
- description: What this pattern should detect
- applicable: true/false based on project relevance
- reason: Why this gate is applicable to this project
- pattern: Array of regex patterns to detect implementations
- expected_count: The expected number of implementations for this gate based on project structure
- expected_count_reasoning: Detailed reasoning for the expected count based on project structure, file count, architectural patterns, and technology stack

CRITICAL: The expected_count should be based on:
- Number of relevant file types (controllers, services, utilities, etc.)
- Project architecture patterns (MVC, microservices, etc.)
- Technology stack requirements (logging frameworks, security libraries, etc.)
- Build configuration indicators (dependencies, plugins, etc.)
- Industry best practices for the detected technology stack

Return the response as a valid JSON object with a "patterns" array containing the dynamic patterns.

IMPORTANT: Ensure the JSON is properly formatted with:
- All property names in double quotes
- All string values in double quotes
- No trailing commas
- Proper nesting of objects and arrays
- Valid JSON syntax that can be parsed by standard JSON parsers

Example format:
{
  "patterns": [
    {
      "gate_id": "1.2",
      "name": "Log Application Messages",
      "description": "Detects logging frameworks and application messages",
      "applicable": true,
      "reason": "Java project with web layer requires logging",
      "pattern": ["import org.slf4j.Logger", "logger.info", "logging.debug"],
      "expected_count": 3,
      "expected_count_reasoning": "Based on analysis of 2 controllers, 1 service layer, and logging configuration detected in the project structure"
    }
  ]
}""",
            parameters={
                "build_configs": "str", 
                "available_gates": "str",
                "extracted_code": "str",
                "project_structure": "str"
            }
        )
        
        # LLM Post-Analysis Template
        templates["llm_post_analysis"] = PromptTemplate(
            use_case="LLM Post-Analysis for Contextual Recommendations",
            description="Template for LLM post-analysis to generate contextual recommendations",
            prompt_template="""You are an expert code analysis assistant. Based on the gate evaluation results, provide contextual recommendations for improving the codebase.

GATE RESULTS:
{gate_results}

PROJECT SUMMARY:
{project_summary}

SCAN METADATA:
{scan_metadata}

Analyze the gate results and provide:

1. **Overall Assessment**: Summary of the codebase security posture
2. **Critical Issues**: High-priority security concerns that need immediate attention
3. **Improvement Areas**: Specific areas where security can be enhanced
4. **Best Practices**: Recommendations for implementing security best practices
5. **Compliance**: Suggestions for meeting enterprise compliance requirements

For each recommendation, provide:
- category: The type of recommendation (security, compliance, best_practice, etc.)
- priority: high/medium/low
- description: Detailed description of the recommendation
- rationale: Why this recommendation is important
- implementation: How to implement this recommendation

Return the response as a valid JSON object with a "recommendations" array.""",
            parameters={
                "gate_results": "str",
                "project_summary": "str",
                "scan_metadata": "str"
            }
        )
        
        # Project Summary Template
        templates["project_summary"] = PromptTemplate(
            use_case="LLM Project Summary Generation",
            description="Template for generating comprehensive project summaries",
            prompt_template="""You are an expert code analysis assistant. Generate a comprehensive project summary based on the repository analysis.

REPOSITORY URL: {repo_url}

METADATA:
{metadata}

VECTOR ANALYSIS:
{vector_analysis}

Generate a comprehensive project summary that includes:

1. **Project Overview**: High-level description of the project
2. **Technology Stack**: Primary languages, frameworks, and tools used
3. **Architecture**: Architectural patterns and design principles
4. **Application Type**: What type of application this is
5. **Key Features**: Main functionality and capabilities
6. **Development Practices**: Testing, logging, security, documentation practices
7. **Code Quality**: Organization, patterns, maintainability
8. **Infrastructure**: Deployment, monitoring, scalability considerations
9. **Dependencies**: External and internal dependencies
10. **Recommendations**: Suggestions for improvement

Provide the response as a structured JSON object with detailed information in each section.""",
            parameters={
                "repo_url": "str",
                "metadata": "str",
                "vector_analysis": "str"
            }
        )
        
        # Question Answering Template
        templates["question_answering"] = PromptTemplate(
            use_case="Code Analysis Question Answering",
            description="Template for answering questions about codebase using context",
            prompt_template="""You are a helpful code analysis assistant. Answer the following question about a codebase based on the provided context.

Question: {question}

Context from the codebase:
{context}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to answer the question, say so. Focus on providing accurate, helpful information about the codebase structure, patterns, and implementation details.

Answer:""",
            parameters={
                "question": "str",
                "context": "str"
            }
        )
        
        # Contextual Recommendations Template
        templates["contextual_recommendations"] = PromptTemplate(
            use_case="Contextual Recommendations for Gate Implementation",
            description="Template for generating contextual recommendations for specific gate implementations",
            prompt_template="""Generate specific, actionable recommendations for improving the implementation of gate: {gate_name}

Gate Details:
- Gate Name: {gate_name}
- Status: {gate_status}
- Expected Count: {expected_count}
- Actual Count: {actual_count}
- Category: {gate_category}
- Severity: {gate_severity}
- Current Reasoning: {current_reasoning}

Codebase Analysis:
{code_context}

Current Implementation Status:
- Found {actual_count} implementations out of {expected_count} expected

Generate 3-5 specific, actionable recommendations that:
1. Are specifically tailored to the {gate_name} gate and this codebase
2. Reference specific files, components, or patterns found in the codebase
3. Provide concrete implementation guidance based on the actual code structure
4. Address the specific gap (expected vs actual count) with codebase-specific solutions
5. Consider the technology stack and patterns used in this project
6. Suggest immediate fixes and long-term improvements based on the current implementation

IMPORTANT: 
- Make recommendations specific to {gate_name} and this codebase
- Reference specific files, classes, or methods when relevant
- Consider the technology stack and project structure
- Do not use markdown formatting (no **, ##, etc.)
- Use clear, actionable language with specific implementation details

Format as a numbered list of specific recommendations without any markdown formatting.""",
            parameters={
                "gate_name": "str",
                "gate_status": "str",
                "expected_count": "int",
                "actual_count": "int",
                "gate_category": "str",
                "gate_severity": "str",
                "current_reasoning": "str",
                "code_context": "str"
            }
        )
        
        return templates
    
    # Public Methods
    def get_gate(self, gate_id: str):
        """Get a specific gate definition"""
        return self.gates.get(gate_id)
    
    def get_gates_by_category(self, category) -> List:
        """Get all gates for a specific category"""
        from models.gate_definitions import GateCategory
        return [gate for gate in self.gates.values() if gate.category == category]
    
    def get_gates_by_severity(self, severity) -> List:
        """Get all gates for a specific severity level"""
        from models.gate_definitions import GateSeverity
        return [gate for gate in self.gates.values() if gate.severity == severity]
    
    def get_all_gates(self) -> List:
        """Get all gate definitions"""
        return list(self.gates.values())
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Get a specific prompt template"""
        return self.templates.get(template_name)
    
    def format_template(self, template_name: str, **kwargs) -> Optional[str]:
        """Format a template with provided parameters"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        try:
            return template.prompt_template.format(**kwargs)
        except KeyError as e:
            print(f"❌ Missing parameter for template {template_name}: {e}")
            return None
    
    def get_available_gates_text(self) -> str:
        """Get formatted text of all available gates"""
        if not self.gates:
            return "No gates defined"
        
        gates_text = []
        
        # Group by category
        categories = {}
        for gate in self.gates.values():
            if gate.category.value not in categories:
                categories[gate.category.value] = []
            categories[gate.category.value].append(gate)
        
        for category_name, category_gates in categories.items():
            gates_text.append(f"\n{category_name.upper()} GATES:")
            for gate in category_gates:
                gates_text.append(f"  {gate.gate_id}: {gate.gate_name} ({gate.severity.value.upper()})")
                gates_text.append(f"    {gate.prompt}")
        
        return "\n".join(gates_text)
    
    def get_gates_for_llm_analysis(self) -> str:
        """Get gates formatted for LLM analysis"""
        gates_text = []
        
        for gate in self.gates.values():
            # Required formatting: gate number, category, name, summary
            cat_disp = gate.category.value.replace("_", " ").title()
            gates_text.append(f"{gate.display_id} | {cat_disp} | {gate.gate_name} | {gate.prompt}")
        
        return "\n".join(gates_text)
    
    def get_gate_ids(self) -> List[str]:
        """Get list of all gate IDs"""
        return list(self.gates.keys())
    
    def get_template_names(self) -> List[str]:
        """Get list of all template names"""
        return list(self.templates.keys())


# Global instance for easy access
prompt_templates = PromptTemplates()
