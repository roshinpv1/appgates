import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Represents a pattern match result"""
    file: str
    pattern: str
    weight: float
    type: str = "pattern"
    line_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class ConditionResult:
    """Represents a condition evaluation result"""
    condition_name: str
    type: str
    operator: str
    passed: bool
    weight: float
    matches: List[PatternMatch]
    max_possible_matches: int = 1


@dataclass
class CriteriaResult:
    """Represents a criteria evaluation result"""
    passed: bool
    condition_results: List[ConditionResult]
    matches: List[PatternMatch]
    total_weight: float
    max_possible_matches: int = 1


class CriteriaEvaluator:
    """Evaluates criteria-based pattern configurations with AND/OR/NOT logic"""
    
    def __init__(self, codebase_files: List[str], file_contents: Dict[str, str] = None):
        self.codebase_files = codebase_files
        self.file_contents = file_contents or {}
        
    def evaluate_criteria(self, criteria: Dict[str, Any]) -> CriteriaResult:
        """Evaluate criteria with AND/OR/NOT logic"""
        
        operator = criteria.get("operator", "AND")
        conditions = criteria.get("conditions", [])
        
        if not conditions:
            return CriteriaResult(
                passed=False,
                condition_results=[],
                matches=[],
                total_weight=0.0,
                max_possible_matches=0
            )
        
        print(f"   🔍 Evaluating {len(conditions)} conditions with {operator} logic...")
        
        # Evaluate each condition
        condition_results = []
        all_matches = []
        total_weight = 0.0
        max_possible_matches = 0
        
        for i, condition in enumerate(conditions):
            print(f"   📋 Evaluating condition {i+1}/{len(conditions)}: {condition.get('name', 'unknown')}")
            condition_result = self._evaluate_condition(condition)
            condition_results.append(condition_result)
            all_matches.extend(condition_result.matches)
            total_weight += condition_result.weight
            max_possible_matches += condition_result.max_possible_matches
            
            print(f"   ✅ Condition {i+1} result: {'PASS' if condition_result.passed else 'FAIL'} ({len(condition_result.matches)} matches)")
        
        # Apply logic operator
        passed = self._apply_logic_operator(operator, condition_results)
        
        print(f"   🎯 Overall criteria result: {'PASS' if passed else 'FAIL'} ({len(all_matches)} total matches)")
        
        return CriteriaResult(
            passed=passed,
            condition_results=condition_results,
            matches=all_matches,
            total_weight=total_weight,
            max_possible_matches=max_possible_matches
        )
    
    def _evaluate_condition(self, condition: Dict[str, Any]) -> ConditionResult:
        """Evaluate a single condition"""
        
        condition_name = condition.get("name", "unknown")
        condition_type = condition.get("type", "pattern")
        operator = condition.get("operator", "OR")
        weight = condition.get("weight", 1.0)
        
        if condition_type == "pattern":
            return self._evaluate_pattern_condition(condition_name, operator, weight, condition)
        elif condition_type == "file_pattern":
            return self._evaluate_file_pattern_condition(condition_name, operator, weight, condition)
        elif condition_type == "criteria":
            return self._evaluate_nested_criteria_condition(condition_name, operator, weight, condition)
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")
    
    def _evaluate_pattern_condition(self, name: str, operator: str, weight: float, condition: Dict) -> ConditionResult:
        """Evaluate a pattern condition"""
        
        patterns = condition.get("patterns", [])
        file_context = condition.get("file_context")
        technology = condition.get("technology")
        
        matches = []
        
        for pattern_config in patterns:
            pattern = pattern_config["pattern"]
            pattern_weight = pattern_config.get("weight", 1.0)
            pattern_technology = pattern_config.get("technology")
            pattern_file_context = pattern_config.get("file_context")
            
            # Find pattern matches
            pattern_matches = self._find_pattern_matches(
                pattern, 
                pattern_weight, 
                file_context or pattern_file_context,
                technology or pattern_technology
            )
            matches.extend(pattern_matches)
        
        # Determine if condition passed based on operator
        passed = self._apply_logic_operator(operator, matches)
        
        return ConditionResult(
            condition_name=name,
            type="pattern",
            operator=operator,
            passed=passed,
            weight=weight,
            matches=matches,
            max_possible_matches=len(self.codebase_files)
        )
    
    def _evaluate_file_pattern_condition(self, name: str, operator: str, weight: float, condition: Dict) -> ConditionResult:
        """Evaluate a file pattern condition"""
        
        file_patterns = condition.get("file_patterns", [])
        matches = []
        
        for file_pattern_config in file_patterns:
            pattern = file_pattern_config["pattern"]
            pattern_weight = file_pattern_config.get("weight", 1.0)
            exclude_dirs = file_pattern_config.get("exclude", [])
            
            # Find files that match the pattern
            matching_files = []
            for file_path in self.codebase_files:
                # Check if file should be excluded
                if any(exclude_dir in file_path for exclude_dir in exclude_dirs):
                    continue
                
                file_name = os.path.basename(file_path)
                if re.match(pattern, file_name):
                    matching_files.append(file_path)
            
            # Add matches
            for file_path in matching_files:
                matches.append(PatternMatch(
                    file=file_path,
                    pattern=pattern,
                    weight=pattern_weight,
                    type="file_pattern"
                ))
        
        # Determine if condition passed based on operator
        passed = self._apply_logic_operator(operator, matches)
        
        return ConditionResult(
            condition_name=name,
            type="file_pattern",
            operator=operator,
            passed=passed,
            weight=weight,
            matches=matches,
            max_possible_matches=len(self.codebase_files)
        )
    
    def _evaluate_nested_criteria_condition(self, name: str, operator: str, weight: float, condition: Dict) -> ConditionResult:
        """Evaluate a nested criteria condition"""
        
        nested_criteria = condition.get("criteria", {})
        
        # Recursively evaluate nested criteria
        nested_result = self.evaluate_criteria(nested_criteria)
        
        return ConditionResult(
            condition_name=name,
            type="criteria",
            operator=operator,
            passed=nested_result.passed,
            weight=weight,
            matches=nested_result.matches,
            max_possible_matches=nested_result.max_possible_matches
        )
    
    def _find_pattern_matches(self, pattern: str, weight: float, file_context: str = None, technology: str = None) -> List[PatternMatch]:
        """Find pattern matches in files"""
        
        matches = []
        processed_files = 0
        max_files_to_process = 1000  # Limit to prevent hanging
        
        for file_path in self.codebase_files:
            # Limit processing to prevent hanging
            if processed_files >= max_files_to_process:
                print(f"   ⚠️ Reached file limit ({max_files_to_process}), stopping pattern search")
                break
            
            # Apply file context filter
            if file_context and not self._matches_file_context(file_path, file_context):
                continue
            
            # Apply technology filter
            if technology and not self._matches_technology(file_path, technology):
                continue
            
            # Search for pattern in file content
            file_content = self.file_contents.get(file_path, "")
            if not file_content:
                continue
            
            try:
                # Find all matches in the file
                pattern_matches = re.finditer(pattern, file_content, re.MULTILINE)
                
                for match in pattern_matches:
                    line_number = file_content[:match.start()].count('\n') + 1
                    context = self._extract_context(file_content, match.start(), match.end())
                    
                    matches.append(PatternMatch(
                        file=file_path,
                        pattern=pattern,
                        weight=weight,
                        type="pattern",
                        line_number=line_number,
                        context=context
                    ))
                    
                    # Limit matches per file to prevent excessive results
                    if len(matches) >= 100:
                        print(f"   ⚠️ Reached match limit (100) for pattern '{pattern}', stopping")
                        break
                
                processed_files += 1
                
                # Progress logging every 100 files
                if processed_files % 100 == 0:
                    print(f"   📊 Processed {processed_files} files, found {len(matches)} matches")
                    
            except re.error as e:
                print(f"   ⚠️ Invalid regex pattern '{pattern}': {e}")
                continue
            except Exception as e:
                print(f"   ⚠️ Error processing file {file_path}: {e}")
                continue
        
        print(f"   ✅ Pattern '{pattern}' evaluation complete: {len(matches)} matches in {processed_files} files")
        return matches
    
    def _matches_file_context(self, file_path: str, file_context: str) -> bool:
        """Check if file matches the specified file context"""
        
        if file_context == "test_files":
            # Check if file is a test file
            test_patterns = [
                r".*Test\.java$",
                r".*_test\.py$",
                r".*\.spec\.js$",
                r".*\.test\.js$",
                r".*Test\.cs$",
                r".*_test\.go$"
            ]
            return any(re.match(pattern, os.path.basename(file_path)) for pattern in test_patterns)
        
        elif file_context == "config_files":
            # Check if file is a config file
            config_patterns = [
                r".*\.yml$",
                r".*\.yaml$",
                r".*\.json$",
                r".*\.properties$",
                r".*\.conf$",
                r".*\.ini$"
            ]
            return any(re.match(pattern, os.path.basename(file_path)) for pattern in config_patterns)
        
        elif file_context == "source_files":
            # Check if file is a source file
            source_patterns = [
                r".*\.java$",
                r".*\.py$",
                r".*\.js$",
                r".*\.ts$",
                r".*\.cs$",
                r".*\.go$"
            ]
            return any(re.match(pattern, os.path.basename(file_path)) for pattern in source_patterns)
        
        return True  # Default to matching if context is not recognized
    
    def _matches_technology(self, file_path: str, technology: str) -> bool:
        """Check if file matches the specified technology"""
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        technology_extensions = {
            "java": [".java"],
            "python": [".py", ".pyc"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "csharp": [".cs"],
            "go": [".go"],
            "rust": [".rs"],
            "php": [".php"],
            "ruby": [".rb"],
            "scala": [".scala"],
            "kotlin": [".kt"],
            "swift": [".swift"]
        }
        
        if technology in technology_extensions:
            return file_extension in technology_extensions[technology]
        
        return True  # Default to matching if technology is not recognized
    
    def _extract_context(self, content: str, start: int, end: int, context_lines: int = 2) -> str:
        """Extract context around a pattern match"""
        
        lines = content.split('\n')
        line_number = content[:start].count('\n')
        
        start_line = max(0, line_number - context_lines)
        end_line = min(len(lines), line_number + context_lines + 1)
        
        context_lines = lines[start_line:end_line]
        return '\n'.join(context_lines)
    
    def _apply_logic_operator(self, operator: str, items: List) -> bool:
        """Apply AND/OR/NOT logic to a list of items"""
        
        if not items:
            return False
        
        if operator == "AND":
            # All items must be truthy
            return all(bool(item) for item in items)
        
        elif operator == "OR":
            # At least one item must be truthy
            return any(bool(item) for item in items)
        
        elif operator == "NOT":
            # No items should be truthy (inverse logic)
            return not any(bool(item) for item in items)
        
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def _apply_logic_operator_to_conditions(self, operator: str, condition_results: List[ConditionResult]) -> bool:
        """Apply AND/OR/NOT logic to condition results"""
        
        if not condition_results:
            return False
        
        if operator == "AND":
            # All conditions must pass
            return all(condition.passed for condition in condition_results)
        
        elif operator == "OR":
            # At least one condition must pass
            return any(condition.passed for condition in condition_results)
        
        elif operator == "NOT":
            # No conditions should pass (inverse logic)
            return not any(condition.passed for condition in condition_results)
        
        else:
            raise ValueError(f"Unknown operator: {operator}")


class EnhancedGateEvaluator:
    """Enhanced gate evaluator that integrates criteria evaluation"""
    
    def __init__(self, codebase_files: List[str], file_contents: Dict[str, str] = None):
        self.codebase_files = codebase_files
        self.file_contents = file_contents or {}
        self.criteria_evaluator = CriteriaEvaluator(codebase_files, file_contents)
    
    def evaluate_gate(self, gate_name: str, gate_config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a gate using criteria-based configuration"""
        
        # Check if gate has criteria configuration
        if "criteria" not in gate_config:
            # Fall back to legacy pattern evaluation
            return self._evaluate_legacy_gate(gate_name, gate_config)
        
        # Evaluate criteria
        criteria_result = self.criteria_evaluator.evaluate_criteria(gate_config["criteria"])
        
        # Calculate score
        score_result = self._calculate_criteria_score(criteria_result, gate_config)
        
        return {
            "gate_name": gate_name,
            "display_name": gate_config.get("display_name", gate_name),
            "category": gate_config.get("category", "Unknown"),
            "weight": gate_config.get("weight", 1.0),
            "score": score_result["score"],
            "status": score_result["status"],
            "criteria_score": score_result.get("criteria_score", 0.0),
            "coverage_score": score_result.get("coverage_score", 0.0),
            "condition_results": criteria_result.condition_results,
            "matches": criteria_result.matches,
            "total_weight": criteria_result.total_weight
        }
    
    def _calculate_criteria_score(self, criteria_result: CriteriaResult, gate_config: Dict) -> Dict[str, Any]:
        """Calculate score based on criteria evaluation results"""
        
        # Check if criteria passed
        if not criteria_result.passed:
            return {
                "score": 0.0,
                "status": "FAIL",
                "reason": "Criteria not met"
            }
        
        # Get scoring configuration
        scoring_config = gate_config.get("scoring", {})
        pass_threshold = scoring_config.get("pass_threshold", 20.0)
        criteria_weight = scoring_config.get("criteria_weight", 0.8)
        coverage_weight = scoring_config.get("coverage_weight", 0.2)
        
        # Calculate criteria score
        criteria_score = self._calculate_criteria_component_score(criteria_result, scoring_config)
        
        # Calculate coverage score
        coverage_score = self._calculate_coverage_component_score(criteria_result, gate_config)
        
        # Combine scores
        final_score = (criteria_score * criteria_weight) + (coverage_score * coverage_weight)
        
        # Determine status
        status = "PASS" if final_score >= pass_threshold else "FAIL"
        
        return {
            "score": final_score,
            "status": status,
            "criteria_score": criteria_score,
            "coverage_score": coverage_score
        }
    
    def _calculate_criteria_component_score(self, criteria_result: CriteriaResult, scoring_config: Dict) -> float:
        """Calculate score based on criteria evaluation"""
        
        condition_results = criteria_result.condition_results
        logic_multipliers = scoring_config.get("logic_multipliers", {
            "AND": 1.0,
            "OR": 0.8,
            "NOT": 1.2
        })
        condition_weights = scoring_config.get("condition_weights", {
            "pattern": 1.0,
            "file_pattern": 0.7,
            "criteria": 1.2
        })
        
        total_score = 0.0
        total_weight = 0.0
        
        for condition_result in condition_results:
            condition_type = condition_result.type
            operator = condition_result.operator
            passed = condition_result.passed
            weight = condition_result.weight
            
            # Apply multipliers
            logic_multiplier = logic_multipliers.get(operator, 1.0)
            type_weight = condition_weights.get(condition_type, 1.0)
            
            # Calculate condition score
            condition_score = 100.0 if passed else 0.0
            
            # Apply weights
            weighted_score = condition_score * logic_multiplier * type_weight * weight
            total_score += weighted_score
            total_weight += weight * logic_multiplier * type_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_coverage_component_score(self, criteria_result: CriteriaResult, gate_config: Dict) -> float:
        """Calculate score based on coverage ratio"""
        
        expected_coverage = gate_config.get("expected_coverage", {})
        expected_percentage = expected_coverage.get("percentage", 25) / 100.0
        
        total_matches = len(criteria_result.matches)
        total_files = len(self.codebase_files)
        
        if total_files == 0 or expected_percentage == 0:
            return 0.0
        
        actual_coverage = total_matches / total_files
        coverage_ratio = actual_coverage / expected_percentage
        
        return self._calculate_simple_score_from_ratio(coverage_ratio)
    
    def _calculate_simple_score_from_ratio(self, coverage_ratio: float) -> float:
        """Calculate score from coverage ratio using simplified logic"""
        
        if coverage_ratio >= 1.0:
            # Perfect or exceeding expectations
            return 100.0
        elif coverage_ratio >= 0.8:
            # Excellent (80%+ of expected)
            return 80.0 + (coverage_ratio - 0.8) * 100.0
        elif coverage_ratio >= 0.5:
            # Good (50-80% of expected)
            return 50.0 + (coverage_ratio - 0.5) * 100.0
        elif coverage_ratio >= 0.2:
            # Adequate (20-50% of expected)
            return 20.0 + (coverage_ratio - 0.2) * 100.0
        else:
            # Poor (< 20% of expected)
            return coverage_ratio * 100.0
    
    def _evaluate_legacy_gate(self, gate_name: str, gate_config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate legacy gate configuration (fallback)"""
        
        # This would implement the existing pattern evaluation logic
        # For now, return a basic result
        return {
            "gate_name": gate_name,
            "display_name": gate_config.get("display_name", gate_name),
            "category": gate_config.get("category", "Unknown"),
            "weight": gate_config.get("weight", 1.0),
            "score": 0.0,
            "status": "FAIL",
            "reason": "Legacy gate evaluation not implemented"
        }


def migrate_legacy_gate(legacy_gate: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy gate configuration to criteria-based format"""
    
    gate_name = list(legacy_gate.keys())[0]
    gate_config = legacy_gate[gate_name]
    
    # Extract legacy patterns
    legacy_patterns = gate_config.get("patterns", [])
    
    # Create criteria-based structure
    criteria = {
        "operator": "OR",
        "conditions": [
            {
                "name": "legacy_patterns",
                "type": "pattern",
                "operator": "OR",
                "weight": gate_config.get("weight", 1.0),
                "patterns": [
                    {"pattern": pattern, "weight": 1.0}
                    for pattern in legacy_patterns
                ]
            }
        ]
    }
    
    # Create scoring configuration
    category = gate_config.get("category", "Quality")
    if category == "Security":
        scoring = {
            "pass_threshold": 100.0,
            "perfect_threshold": 100.0,
            "criteria_weight": 1.0,
            "coverage_weight": 0.0,
            "logic_multipliers": {
                "AND": 1.0,
                "OR": 0.8,
                "NOT": 1.2
            }
        }
    else:
        scoring = {
            "pass_threshold": 20.0,
            "perfect_threshold": 70.0,
            "criteria_weight": 0.8,
            "coverage_weight": 0.2,
            "logic_multipliers": {
                "AND": 1.0,
                "OR": 0.8,
                "NOT": 1.2
            },
            "condition_weights": {
                "pattern": 1.0,
                "file_pattern": 0.7,
                "criteria": 1.2
            }
        }
    
    # Update gate configuration
    gate_config["criteria"] = criteria
    gate_config["scoring"] = scoring
    
    return {gate_name: gate_config} 