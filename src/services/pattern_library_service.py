"""
Pattern Library Service for managing enhanced pattern library
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PatternInfo:
    """Information about a pattern"""
    gate_id: str
    display_name: str
    description: str
    category: str
    priority: str
    weight: float
    patterns: List[str]
    technology: Optional[str] = None


class PatternLibraryService:
    """
    Service for loading and managing the enhanced pattern library
    """
    
    def __init__(self, pattern_file_path: Optional[str] = None):
        """Initialize the pattern library service"""
        if pattern_file_path is None:
            # Default path relative to src directory
            src_dir = Path(__file__).parent.parent
            pattern_file_path = src_dir / "data" / "enhanced_pattern_library.json"
        
        self.pattern_file_path = Path(pattern_file_path)
        self.patterns: Dict[str, PatternInfo] = {}
        self.pattern_texts: List[str] = []
        self.global_config: Dict[str, Any] = {}
        
        # Load patterns on initialization
        self._load_patterns()
        
        print(f"📚 Pattern Library loaded: {len(self.patterns)} gates with {len(self.pattern_texts)} pattern texts")
    
    def _load_patterns(self):
        """Load patterns from the JSON file"""
        try:
            if not self.pattern_file_path.exists():
                print(f"⚠️ Pattern file not found: {self.pattern_file_path}")
                return
            
            with open(self.pattern_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load global configuration
            self.global_config = data.get("global_config", {})
            
            gates = data.get("gates", {})
            
            for gate_id, gate_data in gates.items():
                # Extract basic information
                display_name = gate_data.get("display_name", gate_id)
                description = gate_data.get("description", "")
                category = gate_data.get("category", "General")
                priority = gate_data.get("priority", "Medium")
                weight = gate_data.get("weight", 10.0)
                
                # Extract patterns from criteria
                patterns = self._extract_patterns_from_criteria(gate_data.get("criteria", {}))
                
                # Create pattern info
                pattern_info = PatternInfo(
                    gate_id=gate_id,
                    display_name=display_name,
                    description=description,
                    category=category,
                    priority=priority,
                    weight=weight,
                    patterns=patterns
                )
                
                self.patterns[gate_id] = pattern_info
                
                # Create text representation for embedding
                pattern_text = self._create_pattern_text(pattern_info)
                self.pattern_texts.append(pattern_text)
            
            print(f"✅ Loaded {len(self.patterns)} gates from pattern library")
            
        except Exception as e:
            print(f"❌ Failed to load pattern library: {e}")
    
    def _extract_patterns_from_criteria(self, criteria: Dict[str, Any]) -> List[str]:
        """Extract all patterns from criteria structure"""
        patterns = []
        
        if not criteria:
            return patterns
        
        conditions = criteria.get("conditions", [])
        
        for condition in conditions:
            if condition.get("type") == "pattern":
                # Extract patterns from pattern conditions
                pattern_list = condition.get("patterns", [])
                for pattern_item in pattern_list:
                    if isinstance(pattern_item, dict):
                        pattern = pattern_item.get("pattern", "")
                        if pattern:
                            patterns.append(pattern)
                    elif isinstance(pattern_item, str):
                        patterns.append(pattern_item)
            
            elif condition.get("type") == "file_pattern":
                # Extract patterns from file pattern conditions
                file_patterns = condition.get("file_patterns", [])
                for pattern_item in file_patterns:
                    if isinstance(pattern_item, dict):
                        pattern = pattern_item.get("pattern", "")
                        if pattern:
                            patterns.append(pattern)
                    elif isinstance(pattern_item, str):
                        patterns.append(pattern_item)
            
            elif condition.get("type") == "criteria":
                # Recursively extract patterns from nested criteria
                nested_patterns = self._extract_patterns_from_criteria(condition.get("criteria", {}))
                patterns.extend(nested_patterns)
        
        return patterns
    
    def _create_pattern_text(self, pattern_info: PatternInfo) -> str:
        """Create a text representation of a pattern for embedding"""
        text_parts = [
            f"Gate: {pattern_info.gate_id}",
            f"Name: {pattern_info.display_name}",
            f"Description: {pattern_info.description}",
            f"Category: {pattern_info.category}",
            f"Priority: {pattern_info.priority}",
            f"Weight: {pattern_info.weight}",
            f"Patterns: {', '.join(pattern_info.patterns)}"
        ]
        
        return " | ".join(text_parts)
    
    def get_pattern(self, gate_id: str) -> Optional[PatternInfo]:
        """Get a specific pattern by gate ID"""
        return self.patterns.get(gate_id)
    
    def get_patterns_by_category(self, category: str) -> List[PatternInfo]:
        """Get all patterns in a specific category"""
        return [pattern for pattern in self.patterns.values() if pattern.category == category]
    
    def get_patterns_by_priority(self, priority: str) -> List[PatternInfo]:
        """Get all patterns with a specific priority"""
        return [pattern for pattern in self.patterns.values() if pattern.priority == priority]
    
    def get_all_patterns(self) -> List[PatternInfo]:
        """Get all patterns"""
        return list(self.patterns.values())
    
    def get_pattern_texts(self) -> List[str]:
        """Get all pattern texts for embedding"""
        return self.pattern_texts.copy()
    
    def get_gate_ids(self) -> List[str]:
        """Get all gate IDs"""
        return list(self.patterns.keys())
    
    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        return list(set(pattern.category for pattern in self.patterns.values()))
    
    def get_priorities(self) -> List[str]:
        """Get all unique priorities"""
        return list(set(pattern.priority for pattern in self.patterns.values()))
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get the global configuration"""
        return self.global_config.copy()
    
    def get_scoring_config(self) -> Dict[str, Any]:
        """Get the scoring configuration"""
        return self.global_config.get("default_scoring", {})
    
    def get_gate_categories_config(self) -> Dict[str, Any]:
        """Get the gate categories configuration"""
        return self.global_config.get("gate_categories", {})
    
    def get_technology_mapping(self) -> Dict[str, List[str]]:
        """Get the technology mapping configuration"""
        return self.global_config.get("technology_mapping", {})
    
    def get_file_contexts(self) -> Dict[str, List[str]]:
        """Get the file contexts configuration"""
        return self.global_config.get("file_contexts", {})
    
    def reload_patterns(self):
        """Reload patterns from the file"""
        self.patterns.clear()
        self.pattern_texts.clear()
        self.global_config.clear()
        self._load_patterns()
    
    def search_patterns(self, query: str) -> List[PatternInfo]:
        """Search patterns by query string"""
        query_lower = query.lower()
        results = []
        
        for pattern in self.patterns.values():
            if (query_lower in pattern.gate_id.lower() or
                query_lower in pattern.display_name.lower() or
                query_lower in pattern.description.lower() or
                query_lower in pattern.category.lower()):
                results.append(pattern)
        
        return results
    
    def get_patterns_for_technology(self, technology: str) -> List[PatternInfo]:
        """Get patterns that are specific to a technology"""
        results = []
        
        for pattern in self.patterns.values():
            # Check if any pattern in this gate is specific to the technology
            for pattern_str in pattern.patterns:
                if f'"technology": "{technology}"' in pattern_str or f'"technology": "{technology.lower()}"' in pattern_str:
                    results.append(pattern)
                    break
        
        return results
