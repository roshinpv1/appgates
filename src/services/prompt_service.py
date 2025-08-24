#!/usr/bin/env python3
"""
Prompt Service for managing externalized LLM prompts
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Prompt template structure"""
    use_case: str
    description: str
    prompt_template: str
    parameters: Dict[str, Any]
    examples: List[Dict[str, Any]] = None


class PromptService:
    """
    Service for loading and managing externalized LLM prompts
    """
    
    def __init__(self, prompt_file_path: Optional[str] = None):
        """Initialize the prompt service"""
        if prompt_file_path is None:
            # Default path relative to src directory
            src_dir = Path(__file__).parent.parent
            prompt_file_path = src_dir / "data" / "prompt_library.json"
        
        self.prompt_file_path = Path(prompt_file_path)
        self.prompts: Dict[str, PromptTemplate] = {}
        self.gates_in_scope: Dict[str, List[Dict[str, Any]]] = {}
        
        # Load prompts on initialization
        self._load_prompts()
        
        print(f"📝 Prompt Service loaded: {len(self.prompts)} prompt templates")
    
    def _load_prompts(self):
        """Load prompts from the JSON file"""
        try:
            if not self.prompt_file_path.exists():
                print(f"⚠️ Prompt file not found: {self.prompt_file_path}")
                return
            
            with open(self.prompt_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load gates in scope
            self.gates_in_scope = data.get("gates_in_scope", {})
            print(f"✅ Loaded {sum(len(gates) for gates in self.gates_in_scope.values())} gates in scope")
            
            for prompt_id, prompt_data in data.items():
                # Skip gates_in_scope as it's not a prompt template
                if prompt_id == "gates_in_scope":
                    continue
                    
                prompt_template = PromptTemplate(
                    use_case=prompt_data.get("use_case", prompt_id),
                    description=prompt_data.get("description", ""),
                    prompt_template=prompt_data.get("prompt_template", ""),
                    parameters=prompt_data.get("parameters", {}),
                    examples=prompt_data.get("examples", [])
                )
                
                self.prompts[prompt_id] = prompt_template
            
            print(f"✅ Loaded {len(self.prompts)} prompt templates from prompt library")
            
        except Exception as e:
            print(f"❌ Failed to load prompt library: {e}")
    
    def get_available_gates_text(self) -> str:
        """Get formatted text of all available gates"""
        if not self.gates_in_scope:
            return "No gates defined in scope"
        
        gates_text = []
        
        for category, gates in self.gates_in_scope.items():
            gates_text.append(f"\n{category.upper()} GATES:")
            for gate in gates:
                gate_id = gate.get("gate_id", "Unknown")
                gate_name = gate.get("gate_name", "Unknown")
                severity = gate.get("severity", "medium")
                prompt = gate.get("prompt", "")
                
                gates_text.append(f"  {gate_id}: {gate_name} ({severity.upper()})")
                gates_text.append(f"    {prompt}")
        
        return "\n".join(gates_text)
    
    def get_available_gates_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available gates organized by category"""
        return self.gates_in_scope
    
    def get_available_gates_flat(self) -> List[Dict[str, Any]]:
        """Get all available gates as a flat list"""
        all_gates = []
        for category, gates in self.gates_in_scope.items():
            for gate in gates:
                gate_with_category = gate.copy()
                gate_with_category["category"] = category
                all_gates.append(gate_with_category)
        return all_gates
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
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
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None
        
        # Add available_gates to kwargs if not provided
        if "available_gates" not in kwargs:
            kwargs["available_gates"] = self.get_available_gates_text()
        
        try:
            return prompt.prompt_template.format(**kwargs)
        except KeyError as e:
            print(f"❌ Missing required parameter for prompt {prompt_id}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error formatting prompt {prompt_id}: {e}")
            return None
    
    def list_prompts(self) -> List[str]:
        """List all available prompt IDs"""
        return list(self.prompts.keys())
    
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
        """Reload prompts from the file"""
        self.prompts.clear()
        self.gates_in_scope.clear()
        self._load_prompts()
    
    def validate_prompt(self, prompt_id: str, **kwargs) -> bool:
        """Validate that all required parameters are provided for a prompt"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False
        
        # Add available_gates to kwargs for validation
        if "available_gates" not in kwargs:
            kwargs["available_gates"] = self.get_available_gates_text()
        
        try:
            prompt.prompt_template.format(**kwargs)
            return True
        except KeyError:
            return False
    
    def get_gates_summary(self) -> Dict[str, Any]:
        """Get a summary of available gates"""
        total_gates = sum(len(gates) for gates in self.gates_in_scope.values())
        categories = list(self.gates_in_scope.keys())
        
        return {
            "total_gates": total_gates,
            "categories": categories,
            "gates_by_category": {
                category: len(gates) for category, gates in self.gates_in_scope.items()
            }
        }
