"""
Pattern Library Service
Loads and manages the enhanced pattern library for embedding and context retrieval
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
            # Default path relative to gates directory
            gates_dir = Path(__file__).parent.parent
            pattern_file_path = gates_dir / "patterns" / "enhanced_pattern_library.json"
        
        self.pattern_file_path = Path(pattern_file_path)
        self.patterns: Dict[str, PatternInfo] = {}
        self.pattern_texts: List[str] = []
        
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
        """Extract patterns from criteria structure"""
        patterns = []
        
        def extract_from_conditions(conditions):
            for condition in conditions:
                if isinstance(condition, dict):
                    if condition.get("type") == "pattern":
                        # Extract patterns from this condition
                        condition_patterns = condition.get("patterns", [])
                        for pattern_data in condition_patterns:
                            if isinstance(pattern_data, dict):
                                pattern = pattern_data.get("pattern", "")
                                if pattern:
                                    patterns.append(pattern)
                    
                    # Recursively check nested conditions
                    nested_conditions = condition.get("conditions", [])
                    if nested_conditions:
                        extract_from_conditions(nested_conditions)
        
        conditions = criteria.get("conditions", [])
        extract_from_conditions(conditions)
        
        return patterns
    
    def _create_pattern_text(self, pattern_info: PatternInfo) -> str:
        """Create a text representation of a pattern for embedding"""
        text_parts = [
            f"Gate: {pattern_info.display_name}",
            f"ID: {pattern_info.gate_id}",
            f"Category: {pattern_info.category}",
            f"Priority: {pattern_info.priority}",
            f"Weight: {pattern_info.weight}",
            f"Description: {pattern_info.description}",
            f"Patterns: {', '.join(pattern_info.patterns)}"
        ]
        
        return "\n".join(text_parts)
    
    def get_pattern_texts(self) -> List[str]:
        """Get all pattern texts for embedding"""
        return self.pattern_texts.copy()
    
    def get_patterns_by_category(self, category: str) -> List[PatternInfo]:
        """Get patterns by category"""
        return [p for p in self.patterns.values() if p.category.lower() == category.lower()]
    
    def get_patterns_by_priority(self, priority: str) -> List[PatternInfo]:
        """Get patterns by priority"""
        return [p for p in self.patterns.values() if p.priority.lower() == priority.lower()]
    
    def search_patterns(self, query: str) -> List[PatternInfo]:
        """Search patterns by query"""
        query_lower = query.lower()
        results = []
        
        for pattern_info in self.patterns.values():
            # Search in display name, description, and patterns
            if (query_lower in pattern_info.display_name.lower() or
                query_lower in pattern_info.description.lower() or
                any(query_lower in pattern.lower() for pattern in pattern_info.patterns)):
                results.append(pattern_info)
        
        return results
    
    def get_relevant_patterns_for_query(self, query: str, max_patterns: int = 5) -> List[str]:
        """Get relevant pattern texts for a given query"""
        # Simple keyword-based matching
        query_lower = query.lower()
        relevant_patterns = []
        
        for pattern_info in self.patterns.values():
            relevance_score = 0
            
            # Check if query keywords match pattern info
            if query_lower in pattern_info.display_name.lower():
                relevance_score += 3
            if query_lower in pattern_info.description.lower():
                relevance_score += 2
            if query_lower in pattern_info.category.lower():
                relevance_score += 1
            
            # Check if query keywords match any patterns
            for pattern in pattern_info.patterns:
                if query_lower in pattern.lower():
                    relevance_score += 2
            
            if relevance_score > 0:
                pattern_text = self._create_pattern_text(pattern_info)
                relevant_patterns.append((relevance_score, pattern_text))
        
        # Sort by relevance score and return top patterns
        relevant_patterns.sort(key=lambda x: x[0], reverse=True)
        return [pattern_text for _, pattern_text in relevant_patterns[:max_patterns]]
    
    def get_all_pattern_summary(self) -> str:
        """Get a summary of all patterns"""
        summary_parts = ["Enhanced Pattern Library Summary:"]
        
        # Group by category
        categories = {}
        for pattern_info in self.patterns.values():
            if pattern_info.category not in categories:
                categories[pattern_info.category] = []
            categories[pattern_info.category].append(pattern_info)
        
        for category, patterns in categories.items():
            summary_parts.append(f"\n{category} ({len(patterns)} gates):")
            for pattern_info in patterns:
                summary_parts.append(f"  - {pattern_info.display_name} ({pattern_info.priority})")
        
        return "\n".join(summary_parts)
