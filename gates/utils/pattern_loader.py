"""
Pattern Loader for Externalized JSON Pattern Library
Loads patterns from JSON file and implements weighted scoring system
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re
from base import Node


class PatternLoader:
    """Loads and manages externalized patterns from JSON file with weighted scoring"""
    
    def __init__(self, pattern_file_path: str = None):
        """Initialize pattern loader with JSON file path"""
        if pattern_file_path is None:
            # Default to patterns directory
            current_dir = Path(__file__).parent
            pattern_file_path = current_dir.parent / "patterns" / "pattern_library.json"
        
        self.pattern_file_path = Path(pattern_file_path)
        self.pattern_library = self._load_pattern_library()
        self.total_weight = self._calculate_total_weight()
    
    def _load_pattern_library(self) -> Dict[str, Any]:
        """Load pattern library from JSON file"""
        try:
            if not self.pattern_file_path.exists():
                raise FileNotFoundError(f"Pattern library file not found: {self.pattern_file_path}")
            
            with open(self.pattern_file_path, 'r', encoding='utf-8') as f:
                library = json.load(f)
            
            print(f"📚 Loaded pattern library: {library['metadata']['total_gates']} gates, {library['metadata']['total_patterns']} patterns")
            return library
        except Exception as e:
            print(f"❌ Error loading pattern library: {e}")
            return {}
    
    def _calculate_total_weight(self) -> float:
        """Calculate total weight of all gates"""
        total_weight = 0.0
        for gate_name, gate_data in self.pattern_library.get("gates", {}).items():
            total_weight += gate_data.get("weight", 0.0)
        return total_weight
    
    def get_gate_info(self, gate_name: str) -> Optional[Dict[str, Any]]:
        """Get complete gate information including patterns and scoring"""
        return self.pattern_library.get("gates", {}).get(gate_name)
    
    def get_gate_weight(self, gate_name: str) -> float:
        """Get weight for a specific gate"""
        gate_info = self.get_gate_info(gate_name)
        return gate_info.get("weight", 0.0) if gate_info else 0.0
    
    def get_gate_patterns(self, gate_name: str, technologies: List[str]) -> List[Dict[str, Any]]:
        """Get patterns for a gate and technology stack with weights"""
        gate_info = self.get_gate_info(gate_name)
        if not gate_info:
            return []
        
        patterns = gate_info.get("patterns", {})
        all_patterns = []
        
        # Normalize technology names
        normalized_technologies = [tech.lower() for tech in technologies]
        
        # Technology mapping for better coverage
        tech_mapping = {
            'java': ['java', 'spring', 'kotlin', 'scala'],
            'python': ['python', 'django', 'flask', 'fastapi'],
            'javascript': ['javascript', 'js', 'node', 'nodejs', 'react', 'angular', 'vue'],
            'typescript': ['typescript', 'ts', 'angular', 'nest', 'nestjs'],
            'csharp': ['csharp', 'c#', 'dotnet', '.net', 'aspnet'],
            'go': ['go', 'golang'],
            'rust': ['rust'],
            'php': ['php', 'laravel', 'symfony'],
            'ruby': ['ruby', 'rails'],
            'swift': ['swift', 'ios'],
            'kotlin': ['kotlin', 'android']
        }
        
        # Find matching technologies
        matched_technologies = set()
        for tech in normalized_technologies:
            for pattern_tech, variations in tech_mapping.items():
                if tech in variations or any(var in tech for var in variations):
                    matched_technologies.add(pattern_tech)
        
        # Include patterns for matched technologies
        for tech in matched_technologies:
            if tech in patterns:
                tech_patterns = patterns[tech]
                all_patterns.extend(tech_patterns)
                print(f"   📋 Added {len(tech_patterns)} {tech} patterns for {gate_name}")
        
        # Always include all_languages patterns
        if 'all_languages' in patterns:
            all_lang_patterns = patterns['all_languages']
            all_patterns.extend(all_lang_patterns)
            print(f"   📋 Added {len(all_lang_patterns)} all_languages patterns for {gate_name}")
        
        return all_patterns
    
    def get_pattern_strings(self, gate_name: str, technologies: List[str]) -> List[str]:
        """Get pattern strings for a gate (for backward compatibility)"""
        patterns = self.get_gate_patterns(gate_name, technologies)
        return [p["pattern"] for p in patterns]
    
    def calculate_weighted_score(self, gate_name: str, matches: List[Dict[str, Any]], 
                               metadata: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate weighted score for a gate based on matches and pattern weights"""
        gate_info = self.get_gate_info(gate_name)
        if not gate_info:
            return 0.0, {}
        
        scoring_config = gate_info.get("scoring", {})
        expected_coverage = gate_info.get("expected_coverage", {})
        
        # Special handling for security gates (AVOID_LOGGING_SECRETS)
        if gate_name == "AVOID_LOGGING_SECRETS":
            return self._calculate_security_gate_score(matches, scoring_config)
        
        # Calculate weighted match score
        weighted_score = self._calculate_weighted_match_score(gate_name, matches, metadata, expected_coverage)
        
        # Apply scoring configuration
        final_score = self._apply_scoring_config(weighted_score, scoring_config)
        
        # Calculate detailed scoring info
        scoring_details = {
            "gate_weight": gate_info.get("weight", 0.0),
            "weighted_score": weighted_score,
            "final_score": final_score,
            "matches_count": len(matches),
            "expected_coverage": expected_coverage,
            "scoring_config": scoring_config
        }
        
        return final_score, scoring_details
    
    def _calculate_security_gate_score(self, matches: List[Dict[str, Any]], 
                                     scoring_config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate score for security gates (fewer matches = better score)"""
        base_score = scoring_config.get("base_score", 100)
        violation_penalty = scoring_config.get("violation_penalty", 20)
        max_penalty = scoring_config.get("max_penalty", 100)
        bonus_for_clean = scoring_config.get("bonus_for_clean", 10)
        
        if len(matches) == 0:
            # No violations found - perfect score with bonus
            final_score = min(base_score + bonus_for_clean, 100.0)
        else:
            # Penalize based on number of violations
            penalty = min(len(matches) * violation_penalty, max_penalty)
            final_score = max(0.0, base_score - penalty)
        
        # Create scoring details
        scoring_details = {
            "gate_weight": 0.0,  # Will be set by caller
            "weighted_score": final_score,
            "final_score": final_score,
            "matches_count": len(matches),
            "expected_coverage": {"percentage": 0, "reasoning": "No secrets should be logged - this is a security gate where 0 violations is the goal", "confidence": "high"},
            "scoring_config": scoring_config,
            "security_violations": len(matches),
            "penalty_applied": min(len(matches) * violation_penalty, max_penalty) if matches else 0,
            "is_security_gate": True
        }
        
        return final_score, scoring_details
    
    def _calculate_weighted_match_score(self, gate_name: str, matches: List[Dict[str, Any]], 
                                      metadata: Dict[str, Any], expected_coverage: Dict[str, Any]) -> float:
        """Calculate weighted score based on pattern matches and their weights"""
        if not matches:
            return 0.0
        
        # Get patterns for this gate
        technologies = self._get_primary_technologies(metadata)
        patterns = self.get_gate_patterns(gate_name, technologies)
        
        # Create pattern weight mapping
        pattern_weights = {p["pattern"]: p["weight"] for p in patterns}
        
        # Calculate weighted match score
        total_weighted_score = 0.0
        total_possible_weight = 0.0
        
        # Group matches by file to avoid over-counting
        files_with_matches = set()
        file_match_weights = {}
        
        for match in matches:
            file_path = match["file"]
            pattern = match["pattern"]
            pattern_weight = pattern_weights.get(pattern, 1.0)  # Default weight of 1.0
            
            files_with_matches.add(file_path)
            
            # Track highest weight pattern per file
            if file_path not in file_match_weights:
                file_match_weights[file_path] = pattern_weight
            else:
                file_match_weights[file_path] = max(file_match_weights[file_path], pattern_weight)
        
        # Calculate weighted score based on files with matches
        for file_path, weight in file_match_weights.items():
            total_weighted_score += weight
        
        # Calculate total possible weight (all patterns)
        for pattern in patterns:
            total_possible_weight += pattern["weight"]
        
        # Calculate coverage ratio
        if total_possible_weight > 0:
            coverage_ratio = total_weighted_score / total_possible_weight
        else:
            coverage_ratio = 0.0
        
        # Apply expected coverage adjustment
        expected_percentage = expected_coverage.get("percentage", 10) / 100.0
        adjusted_score = coverage_ratio * 100.0
        
        # Bonus for exceeding expectations
        if coverage_ratio > expected_percentage:
            excess_ratio = min((coverage_ratio - expected_percentage) / expected_percentage, 0.2)
            bonus = excess_ratio * 20.0
            adjusted_score = min(adjusted_score + bonus, 100.0)
        
        return adjusted_score
    
    def _apply_scoring_config(self, base_score: float, scoring_config: Dict[str, Any]) -> float:
        """Apply scoring configuration (bonus/penalty thresholds)"""
        bonus_threshold = scoring_config.get("bonus_threshold", 0.8)
        bonus_multiplier = scoring_config.get("bonus_multiplier", 1.1)
        penalty_threshold = scoring_config.get("penalty_threshold", 0.3)
        penalty_multiplier = scoring_config.get("penalty_multiplier", 0.8)
        
        score_ratio = base_score / 100.0
        
        if score_ratio >= bonus_threshold:
            # Apply bonus
            final_score = base_score * bonus_multiplier
        elif score_ratio <= penalty_threshold:
            # Apply penalty
            final_score = base_score * penalty_multiplier
        else:
            # No adjustment
            final_score = base_score
        
        return min(final_score, 100.0)
    
    def _get_primary_technologies(self, metadata: Dict[str, Any]) -> List[str]:
        """Determine primary technologies from metadata"""
        language_stats = metadata.get("language_stats", {})
        
        if not language_stats:
            return []
        
        # Calculate total files
        total_files = sum(stats.get("files", 0) for stats in language_stats.values())
        
        if total_files == 0:
            return []
        
        # Define technology relevance mapping
        primary_languages = {
            "Java", "Python", "JavaScript", "TypeScript", "C#", "C++", "C", 
            "Go", "Rust", "Kotlin", "Scala", "Swift", "PHP", "Ruby"
        }
        
        primary_technologies = []
        
        # Find languages that make up significant portion of the codebase
        for language, stats in language_stats.items():
            file_count = stats.get("files", 0)
            percentage = (file_count / total_files) * 100
            
            if language in primary_languages and percentage >= 20.0:
                primary_technologies.append(language)
        
        # If no primary technology found, take the most dominant
        if not primary_technologies:
            dominant_primary = None
            max_percentage = 0
            
            for language, stats in language_stats.items():
                if language in primary_languages:
                    file_count = stats.get("files", 0)
                    percentage = (file_count / total_files) * 100
                    if percentage > max_percentage and percentage >= 10.0:
                        max_percentage = percentage
                        dominant_primary = language
            
            if dominant_primary:
                primary_technologies.append(dominant_primary)
        
        return primary_technologies
    
    def calculate_overall_weighted_score(self, gate_results: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """Calculate overall weighted score from all gate results"""
        if not gate_results:
            return 0.0, {}
        
        total_weighted_score = 0.0
        total_weight = 0.0
        gate_scores = {}
        
        for result in gate_results:
            gate_name = result["gate"]
            gate_weight = self.get_gate_weight(gate_name)
            gate_score = result.get("score", 0.0)
            
            if gate_weight > 0:
                weighted_gate_score = gate_score * gate_weight
                total_weighted_score += weighted_gate_score
                total_weight += gate_weight
                
                gate_scores[gate_name] = {
                    "score": gate_score,
                    "weight": gate_weight,
                    "weighted_score": weighted_gate_score
                }
        
        overall_score = (total_weighted_score / total_weight) if total_weight > 0 else 0.0
        
        scoring_summary = {
            "overall_score": overall_score,
            "total_weight": total_weight,
            "gate_scores": gate_scores,
            "applicable_gates": len([r for r in gate_results if r.get("status") != "NOT_APPLICABLE"])
        }
        
        return overall_score, scoring_summary
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about the pattern library"""
        gates = self.pattern_library.get("gates", {})
        
        total_patterns = 0
        total_gates = len(gates)
        technology_coverage = {}
        
        for gate_name, gate_data in gates.items():
            patterns = gate_data.get("patterns", {})
            for tech, tech_patterns in patterns.items():
                if tech not in technology_coverage:
                    technology_coverage[tech] = 0
                technology_coverage[tech] += len(tech_patterns)
                total_patterns += len(tech_patterns)
        
        return {
            "total_gates": total_gates,
            "total_patterns": total_patterns,
            "total_weight": self.total_weight,
            "technology_coverage": technology_coverage,
            "supported_technologies": list(technology_coverage.keys())
        }


# Global pattern loader instance
_pattern_loader = None

def get_pattern_loader() -> PatternLoader:
    """Get global pattern loader instance"""
    global _pattern_loader
    if _pattern_loader is None:
        _pattern_loader = PatternLoader()
    return _pattern_loader

def get_weighted_patterns_for_gate(gate_name: str, technologies: List[str]) -> List[Dict[str, Any]]:
    """Get weighted patterns for a gate (for backward compatibility)"""
    loader = get_pattern_loader()
    return loader.get_gate_patterns(gate_name, technologies)

def get_pattern_strings_for_gate(gate_name: str, technologies: List[str]) -> List[str]:
    """Get pattern strings for a gate (for backward compatibility)"""
    loader = get_pattern_loader()
    return loader.get_pattern_strings(gate_name, technologies)

def calculate_weighted_gate_score(gate_name: str, matches: List[Dict[str, Any]], 
                                metadata: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """Calculate weighted score for a gate"""
    loader = get_pattern_loader()
    return loader.calculate_weighted_score(gate_name, matches, metadata)

def calculate_overall_weighted_score(gate_results: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
    """Calculate overall weighted score from gate results"""
    loader = get_pattern_loader()
    return loader.calculate_overall_weighted_score(gate_results)

def get_pattern_statistics() -> Dict[str, Any]:
    """Get pattern library statistics"""
    loader = get_pattern_loader()
    return loader.get_pattern_statistics() 