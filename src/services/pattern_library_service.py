#!/usr/bin/env python3
"""
Pattern Library Service

This service integrates the static pattern library with the centralized gate definitions
to provide sophisticated pattern matching capabilities.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class PatternLibraryService:
    """Service for managing and using the enhanced pattern library"""
    
    def __init__(self, pattern_library_path: str = None):
        """Initialize the pattern library service"""
        if pattern_library_path is None:
            base_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            pattern_library_path = os.path.join(base_dir, "enhanced_pattern_library.json")
        
        self.pattern_library_path = pattern_library_path
        self.pattern_library = self._load_pattern_library()
        self.global_config = self.pattern_library.get("global_config", {})
        
        print(f"📚 PatternLibraryService initialized with {len(self.pattern_library.get('gates', {}))} gates")
    
    def _load_pattern_library(self) -> Dict[str, Any]:
        """Load the pattern library from JSON file"""
        try:
            with open(self.pattern_library_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading pattern library: {e}")
            return {"gates": {}, "global_config": {}}
    
    def get_gate_patterns(self, gate_name: str) -> Optional[Dict[str, Any]]:
        """Get patterns for a specific gate by name"""
        return self.pattern_library.get("gates", {}).get(gate_name)
    
    def get_all_gate_names(self) -> List[str]:
        """Get all gate names from the pattern library"""
        return list(self.pattern_library.get("gates", {}).keys())
    
    def map_gate_id_to_name(self, gate_id: str) -> Optional[str]:
        """Resolve a gate id to the pattern library key.
        Supports numeric internal ids (1..17), display ids (e.g., "1.1"), and exact library keys.
        """
        gates = self.pattern_library.get("gates", {})
        # Exact match
        if gate_id in gates:
            return gate_id
        # Try mapping via registry (numeric id -> display_id)
        try:
            from models.gate_definitions import gate_registry
            gd = gate_registry.get_gate(gate_id)
            if gd:
                # Try display id as key
                disp = gd.display_id
                if disp in gates:
                    return disp
                # Try by gate name
                # Normalize names
                lname = gd.gate_name.strip().lower()
                for key, cfg in gates.items():
                    disp_name = str(cfg.get("display_name", key)).strip().lower()
                    if lname == disp_name:
                        return key
        except Exception:
            pass
        return None
    
    def evaluate_gate(self, gate_id: str, file_content: str, file_path: str, 
                     technology: str = "any") -> Dict[str, Any]:
        """Evaluate a gate against file content using the library's criteria.
        Supports pattern and file_pattern conditions with AND/OR and NOT operators.
        Returns pass/fail, score, and threshold from library when present.
        """
        gate_key = self.map_gate_id_to_name(gate_id)
        if not gate_key:
            return {"gate_id": gate_id, "passed": False, "score": 0.0, "reason": f"Gate {gate_id} not mapped to pattern library"}
        gate = self.pattern_library.get("gates", {}).get(gate_key)
        if not gate:
            return {"gate_id": gate_id, "gate_name": gate_key, "passed": False, "score": 0.0, "reason": f"Gate {gate_key} not found in pattern library"}

        criteria = gate.get("criteria", {})
        operator = (criteria.get("operator") or "AND").upper()
        conditions = criteria.get("conditions", [])
        pass_threshold = gate.get("scoring", {}).get("pass_threshold", 50.0)

        def _file_context_allows(pattern_obj: Dict[str, Any]) -> bool:
            """If a pattern declares file_context, ensure file_path matches one of the context regexes"""
            ctx = pattern_obj.get("file_context")
            if not ctx:
                return True
            contexts = self.global_config.get("file_contexts", {})
            regexes = contexts.get(ctx, [])
            for rex in regexes:
                try:
                    if re.search(rex, file_path, flags=re.IGNORECASE):
                        return True
                except re.error:
                    continue
            return False

        def _technology_allows(pattern_obj: Dict[str, Any]) -> bool:
            req = (pattern_obj.get("technology") or "any").lower()
            if req in ("any", "all"):
                return True
            return req == (technology or "").lower()

        def eval_condition(cond: Dict[str, Any]) -> float:
            cond_type = (cond.get("type") or "pattern").lower()
            cond_op = (cond.get("operator") or "OR").upper()
            weight = float(cond.get("weight", 0.0))
            patterns = cond.get("patterns", [])
            file_patterns = cond.get("file_patterns", [])
            matches = 0
            total = 0
            try:
                if cond_type == "pattern":
                    total = max(1, len(patterns))
                    for p in patterns:
                        pat = p.get("pattern", "")
                        if not pat:
                            continue
                        if not (_technology_allows(p) and _file_context_allows(p)):
                            # pattern not applicable for this file
                            continue
                        try:
                            if re.search(pat, file_content, flags=re.IGNORECASE):
                                matches += 1
                        except re.error:
                            continue
                elif cond_type == "file_pattern":
                    total = max(1, len(file_patterns))
                    for p in file_patterns:
                        pat = p.get("pattern", "")
                        if not pat:
                            continue
                        if not (_technology_allows(p) and _file_context_allows(p)):
                            continue
                        try:
                            if re.search(pat, file_path, flags=re.IGNORECASE):
                                matches += 1
                        except re.error:
                            continue
                # operator semantics
                if cond_op == "NOT":
                    satisfied = (matches == 0)
                elif cond_op == "AND":
                    satisfied = (matches == total)
                else:  # OR
                    satisfied = (matches > 0)
                return weight if satisfied else 0.0
            except Exception:
                return 0.0

        import re
        scores = [eval_condition(c) for c in conditions]
        total_score = sum(scores)
        passed = total_score >= pass_threshold

        return {
            "gate_id": gate_id,
            "gate_name": gate.get("display_name", gate_key),
            "display_name": gate.get("display_name", gate_key),
            "passed": passed,
            "score": total_score,
            "max_score": sum(float(c.get("weight", 0.0)) for c in conditions) or 100.0,
            "threshold": pass_threshold,
            "category": gate.get("category", "Unknown"),
            "priority": gate.get("priority", "Unknown")
        }
    
    def get_patterns_for_gate(self, gate_id: str) -> List[str]:
        """Get all patterns for a gate as a list of strings"""
        gate_name = self.map_gate_id_to_name(gate_id)
        if not gate_name:
            return []
        
        gate_config = self.get_gate_patterns(gate_name)
        if not gate_config:
            return []
        
        patterns = []
        criteria = gate_config.get("criteria", {})
        conditions = criteria.get("conditions", [])
        
        for condition in conditions:
            if condition.get("type") == "pattern":
                for pattern_config in condition.get("patterns", []):
                    patterns.append(pattern_config.get("pattern", ""))
            elif condition.get("type") == "file_pattern":
                for pattern_config in condition.get("file_patterns", []):
                    patterns.append(pattern_config.get("pattern", ""))
        
        return patterns
    
    def get_technology_mapping(self) -> Dict[str, List[str]]:
        """Get technology to file extension mapping"""
        return self.global_config.get("technology_mapping", {})
    
    def detect_technology(self, file_path: str) -> str:
        """Detect technology based on file extension"""
        file_ext = Path(file_path).suffix.lower()
        technology_mapping = self.get_technology_mapping()
        
        for tech, extensions in technology_mapping.items():
            if file_ext in extensions:
                return tech
        
        return "unknown"
    
    def get_available_gates_text(self) -> str:
        """Get formatted text of all available gates"""
        gates = self.pattern_library.get("gates", {})
        if not gates:
            return "No gates defined in pattern library"
        
        gates_text = []
        for gate_name, gate_config in gates.items():
            gates_text.append(f"- {gate_name}: {gate_config.get('display_name', gate_name)}")
            gates_text.append(f"  Category: {gate_config.get('category', 'Unknown')}")
            gates_text.append(f"  Priority: {gate_config.get('priority', 'Unknown')}")
            gates_text.append(f"  Description: {gate_config.get('description', 'No description')}")
            gates_text.append("")
        
        return "\n".join(gates_text)


# Global instance for easy access
pattern_library_service = PatternLibraryService()


# Convenience functions
def get_gate_patterns(gate_id: str) -> Optional[Dict[str, Any]]:
    """Get patterns for a specific gate"""
    gate_name = pattern_library_service.map_gate_id_to_name(gate_id)
    if gate_name:
        return pattern_library_service.get_gate_patterns(gate_name)
    return None


def evaluate_gate(gate_id: str, file_content: str, file_path: str, 
                 technology: str = "any") -> Dict[str, Any]:
    """Evaluate a gate against file content"""
    return pattern_library_service.evaluate_gate(gate_id, file_content, file_path, technology)


def get_patterns_for_gate(gate_id: str) -> List[str]:
    """Get all patterns for a gate as a list of strings"""
    return pattern_library_service.get_patterns_for_gate(gate_id)


def get_available_gates_text() -> str:
    """Get formatted text of all available gates"""
    return pattern_library_service.get_available_gates_text()
