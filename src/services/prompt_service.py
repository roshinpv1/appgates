#!/usr/bin/env python3
"""
Prompt Service for managing externalized LLM prompts
"""

from typing import Dict, Any, Optional, List
from .prompt_templates import PromptTemplates, prompt_templates


class PromptService:
    """
    Service for loading and managing externalized LLM prompts
    """
    
    def __init__(self, prompt_file_path: Optional[str] = None):
        """Initialize the prompt service"""
        # Use the centralized prompt templates
        self.prompt_templates = prompt_templates
        self.prompts = self.prompt_templates.templates
        self.gates_in_scope = self._convert_gates_to_dict()
        
        print(f"📝 Prompt Service loaded: {len(self.prompts)} prompt templates")
    
    def _convert_gates_to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert gate definitions to the expected dictionary format"""
        gates_dict = {}
        
        for gate in self.prompt_templates.get_all_gates():
            category = gate.category.value
            if category not in gates_dict:
                gates_dict[category] = []
            
            gates_dict[category].append({
                "gate_id": gate.gate_id,
                "gate_name": gate.gate_name,
                "prompt": gate.prompt,
                "category": gate.category.value,
                "severity": gate.severity.value
            })
        
        return gates_dict
    

    
    def get_available_gates_text(self) -> str:
        """Get formatted text of all available gates"""
        return self.prompt_templates.get_available_gates_text()
    
    def get_available_gates_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available gates organized by category"""
        return self.gates_in_scope
    
    def get_available_gates_flat(self) -> List[Dict[str, Any]]:
        """Get all available gates as a flat list"""
        all_gates = []
        for gate in self.prompt_templates.get_all_gates():
            all_gates.append({
                "gate_id": gate.gate_id,
                "gate_name": gate.gate_name,
                "prompt": gate.prompt,
                "category": gate.category.value,
                "severity": gate.severity.value
            })
        return all_gates
    
    def get_prompt(self, prompt_id: str) -> Optional[Any]:
        """Get a specific prompt template"""
        return self.prompts.get(prompt_id)
    
    def get_prompt_template(self, prompt_id: str) -> Optional[str]:
        """Get the raw prompt template string"""
        prompt = self.get_prompt(prompt_id)
        return prompt.prompt_template if prompt else None
    
    def get_prompt_parameters(self, prompt_id: str) -> Dict[str, Any]:
        """Get the parameters for a specific prompt"""
        prompt = self.get_prompt(prompt_id)
        return prompt.parameters if prompt else {}
    
    def format_prompt(self, prompt_id: str, **kwargs) -> Optional[str]:
        """Format a prompt template with provided parameters"""
        # Add available_gates to kwargs if not provided
        if "available_gates" not in kwargs:
            kwargs["available_gates"] = self.get_available_gates_text()
        
        return self.prompt_templates.format_template(prompt_id, **kwargs)
    
    def list_prompts(self) -> List[str]:
        """List all available prompt IDs"""
        return self.prompt_templates.get_template_names()
    
    def get_prompt_info(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a prompt"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None
        
        return {
            "id": prompt_id,
            "use_case": prompt.use_case,
            "description": prompt.description,
            "parameters": prompt.parameters,
            "examples_count": len(prompt.examples) if prompt.examples else 0
        }
    
    def reload_prompts(self):
        """Reload prompts from the centralized templates"""
        # Reinitialize the prompt templates
        self.prompt_templates = PromptTemplates()
        self.prompts = self.prompt_templates.templates
        self.gates_in_scope = self._convert_gates_to_dict()
    
    def validate_prompt(self, prompt_id: str, **kwargs) -> bool:
        """Validate that all required parameters are provided for a prompt"""
        # Add available_gates to kwargs for validation
        if "available_gates" not in kwargs:
            kwargs["available_gates"] = self.get_available_gates_text()
        
        try:
            self.prompt_templates.format_template(prompt_id, **kwargs)
            return True
        except (KeyError, TypeError):
            return False
    
    def get_gates_summary(self) -> Dict[str, Any]:
        """Get a summary of available gates"""
        all_gates = self.prompt_templates.get_all_gates()
        categories = {}
        
        for gate in all_gates:
            category = gate.category.value
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            "total_gates": len(all_gates),
            "categories": list(categories.keys()),
            "gates_by_category": categories
        }
