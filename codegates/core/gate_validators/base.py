"""
Base Gate Validator - Abstract base class for all gate validators
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor
import json

from ...models import Language, FileAnalysis
from pydantic import BaseModel


class GateValidationResult(BaseModel):
    """Result of gate validation"""
    expected: int
    found: int
    quality_score: float
    details: List[str] = []
    recommendations: List[str] = []
    technologies: Dict[str, List[str]] = {}  # New field for detected technologies
    matches: List[Dict[str, Any]] = []  # Code matches found during validation


class BaseGateValidator(ABC):
    """Abstract base class for gate validators"""
    
    def __init__(self, language: Language):
        self.language = language
        self.patterns = self._get_language_patterns()
        self.config_patterns = self._get_config_patterns()
        self.technology_patterns = self._get_technology_patterns()
    
    @abstractmethod
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate gate implementation"""
        pass
    
    @abstractmethod
    def _get_language_patterns(self) -> Dict[str, List[str]]:
        """Get language-specific patterns for validation"""
        pass
    
    @abstractmethod
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get configuration file patterns"""
        pass
    
    def _get_technology_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Get technology detection patterns by category"""
        
        if self.language == Language.PYTHON:
            return {
                'logging': {
                    'loguru': [r'from loguru import', r'import loguru', r'loguru\.'],
                    'structlog': [r'import structlog', r'structlog\.'],
                    'python-json-logger': [r'pythonjsonlogger', r'JsonFormatter'],
                    'logging': [r'import logging', r'logging\.'],
                },
                'web_frameworks': {
                    'fastapi': [r'from fastapi import', r'FastAPI\(', r'@app\.'],
                    'flask': [r'from flask import', r'Flask\(', r'@app\.route'],
                    'django': [r'from django', r'django\.', r'urls\.py'],
                    'starlette': [r'from starlette', r'Starlette\('],
                },
                'async': {
                    'asyncio': [r'import asyncio', r'async def', r'await '],
                    'aiohttp': [r'import aiohttp', r'aiohttp\.'],
                    'aiofiles': [r'import aiofiles', r'aiofiles\.'],
                },
                'testing': {
                    'pytest': [r'import pytest', r'@pytest\.', r'def test_'],
                    'unittest': [r'import unittest', r'unittest\.TestCase'],
                    'mock': [r'from unittest.mock', r'@mock\.'],
                },
                'database': {
                    'sqlalchemy': [r'from sqlalchemy', r'sqlalchemy\.'],
                    'django-orm': [r'from django.db', r'models\.Model'],
                    'pymongo': [r'import pymongo', r'pymongo\.'],
                    'redis': [r'import redis', r'redis\.'],
                },
                'monitoring': {
                    'sentry': [r'import sentry_sdk', r'sentry_sdk\.'],
                    'prometheus': [r'prometheus_client', r'prometheus\.'],
                    'datadog': [r'datadog', r'ddtrace'],
                },
            }
        elif self.language == Language.JAVA:
            return {
                'logging': {
                    'logback': [r'logback\.xml', r'ch\.qos\.logback'],
                    'log4j': [r'log4j', r'org\.apache\.log4j'],
                    'slf4j': [r'org\.slf4j', r'import.*slf4j'],
                },
                'web_frameworks': {
                    'spring-boot': [r'@SpringBootApplication', r'@RestController', r'@RequestMapping'],
                    'spring-mvc': [r'@Controller', r'@RequestMapping'],
                    'jersey': [r'@Path', r'@GET', r'@POST'],
                    'servlet': [r'HttpServlet', r'@WebServlet'],
                },
                'testing': {
                    'junit': [r'@Test', r'import.*junit', r'org\.junit'],
                    'mockito': [r'import.*mockito', r'@Mock'],
                    'testng': [r'import.*testng', r'@Test'],
                },
                'database': {
                    'hibernate': [r'@Entity', r'@Table', r'hibernate'],
                    'jpa': [r'@Entity', r'javax\.persistence'],
                    'jdbc': [r'java\.sql', r'DriverManager'],
                },
                'monitoring': {
                    'micrometer': [r'micrometer', r'@Timed'],
                    'actuator': [r'spring-boot-actuator', r'@Endpoint'],
                },
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'logging': {
                    'winston': [r'require\(["\']winston', r'import.*winston', r'winston\.'],
                    'bunyan': [r'require\(["\']bunyan', r'bunyan\.'],
                    'pino': [r'require\(["\']pino', r'pino\('],
                    'console': [r'console\.log', r'console\.error'],
                },
                'web_frameworks': {
                    'express': [r'require\(["\']express', r'express\(', r'app\.get'],
                    'koa': [r'require\(["\']koa', r'new Koa'],
                    'fastify': [r'require\(["\']fastify', r'fastify\('],
                    'nestjs': [r'@nestjs', r'@Controller', r'@Injectable'],
                },
                'frontend': {
                    'react': [r'import.*react', r'from ["\']react', r'React\.'],
                    'vue': [r'import.*vue', r'Vue\.', r'@Component'],
                    'angular': [r'@angular', r'@Component', r'@Injectable'],
                },
                'testing': {
                    'jest': [r'describe\(', r'it\(', r'test\(', r'expect\('],
                    'mocha': [r'require\(["\']mocha', r'describe\(', r'it\('],
                    'cypress': [r'cy\.', r'cypress'],
                },
                'monitoring': {
                    'sentry': [r'@sentry', r'Sentry\.'],
                    'datadog': [r'dd-trace', r'datadog'],
                },
            }
        elif self.language == Language.CSHARP:
            return {
                'logging': {
                    'serilog': [r'using Serilog', r'Log\.', r'Serilog\.'],
                    'nlog': [r'using NLog', r'NLog\.'],
                    'ilogger': [r'ILogger<', r'_logger\.Log'],
                },
                'web_frameworks': {
                    'asp.net-core': [r'Microsoft\.AspNetCore', r'\[ApiController\]', r'\[Route'],
                    'mvc': [r'Controller', r'ActionResult'],
                    'web-api': [r'\[ApiController\]', r'\[HttpGet\]'],
                },
                'testing': {
                    'xunit': [r'using Xunit', r'\[Fact\]', r'\[Theory\]'],
                    'nunit': [r'using NUnit', r'\[Test\]'],
                    'mstest': [r'Microsoft\.VisualStudio\.TestTools', r'\[TestMethod\]'],
                },
                'database': {
                    'entity-framework': [r'using.*EntityFramework', r'DbContext'],
                    'dapper': [r'using Dapper', r'Dapper\.'],
                },
                'monitoring': {
                    'application-insights': [r'Microsoft\.ApplicationInsights', r'TelemetryClient'],
                },
            }
        else:
            return {}
    
    def _detect_technologies(self, target_path: Path, file_analyses: List[FileAnalysis]) -> Dict[str, List[str]]:
        """Detect technologies used in the codebase"""
        
        detected_technologies = {}
        
        # Get relevant files for this language
        relevant_files = [f for f in file_analyses if f.language == self.language]
        
        for category, tech_patterns in self.technology_patterns.items():
            detected_technologies[category] = []
            
            for tech_name, patterns in tech_patterns.items():
                found = False
                
                # Check in code files
                for file_analysis in relevant_files:
                    try:
                        file_path = target_path / file_analysis.file_path
                        if file_path.exists() and file_path.is_file():
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                                    found = True
                                    break
                            
                            if found:
                                break
                    except Exception:
                        continue
                
                # Check in config files
                if not found:
                    config_files = [
                        'package.json', 'requirements.txt', 'pom.xml', 'build.gradle',
                        'Gemfile', 'composer.json', 'project.json', '*.csproj'
                    ]
                    
                    for config_file in config_files:
                        try:
                            config_path = target_path / config_file
                            if config_path.exists():
                                content = config_path.read_text(encoding='utf-8', errors='ignore')
                                
                                for pattern in patterns:
                                    if re.search(pattern, content, re.IGNORECASE):
                                        found = True
                                        break
                                
                                if found:
                                    break
                        except Exception:
                            continue
                
                if found:
                    detected_technologies[category].append(tech_name)
        
        # Remove empty categories
        return {k: v for k, v in detected_technologies.items() if v}
    
    @abstractmethod
    def _calculate_expected_count(self, total_loc: int, file_count: int,
                                lang_files: List[FileAnalysis]) -> int:
        """Calculate expected count for this gate"""
        pass
    
    @abstractmethod
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess implementation quality"""
        pass
    
    @abstractmethod
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Get recommendations when no implementation found"""
        pass
    
    @abstractmethod
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Get recommendations for partial implementation"""
        pass
    
    @abstractmethod
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Get recommendations for quality improvement"""
        pass
    
    def _get_file_extensions(self) -> List[str]:
        """Get file extensions for the current language"""
        
        if self.language == Language.PYTHON:
            return ['*.py']
        elif self.language == Language.JAVA:
            return ['*.java']
        elif self.language == Language.JAVASCRIPT:
            return ['*.js', '*.mjs']
        elif self.language == Language.TYPESCRIPT:
            return ['*.ts', '*.tsx']
        elif self.language == Language.CSHARP:
            return ['*.cs']
        else:
            return ['*.*']
    
    def _search_files_for_patterns(self, target_path: Path, extensions: List[str], 
                                 patterns: List[str]) -> List[Dict[str, Any]]:
        """Search files for patterns with comprehensive metadata extraction"""
        matches = []
        attempted_patterns = set()  # Track all patterns that were attempted
        
        for ext in extensions:
            files = target_path.rglob(f"*{ext}")
            for file_path in files:
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            for pattern in patterns:
                                attempted_patterns.add(pattern)  # Record that this pattern was tried
                                match_obj = re.search(pattern, line, re.IGNORECASE)
                                if match_obj:
                                    # Extract surrounding context (3 lines before and after)
                                    context_start = max(0, line_num - 4)
                                    context_end = min(len(lines), line_num + 3)
                                    context_lines = lines[context_start:context_end]
                                    
                                    # Get the matched text and position
                                    matched_text = match_obj.group(0)
                                    match_start = match_obj.start()
                                    match_end = match_obj.end()
                                    
                                    # Determine the function/method context
                                    function_context = self._extract_function_context(lines, line_num)
                                    
                                    # Determine severity based on pattern type
                                    severity = self._determine_pattern_severity(pattern, matched_text)
                                    
                                    match_data = {
                                        # Core Match Information
                                        'file_path': str(file_path.relative_to(target_path)),
                                        'line_number': line_num,
                                        'pattern': pattern,
                                        'matched_text': matched_text.strip(),
                                        'match_start': match_start,
                                        'match_end': match_end,
                                        'full_line': line.strip(),
                                        
                                        # Context Information
                                        'context': [line.strip() for line in context_lines],
                                        'function_context': function_context,
                                        
                                        # Classification
                                        'severity': severity,
                                        'language': self.language.value,
                                        'file_extension': file_path.suffix,
                                        'gate_type': self.__class__.__name__.replace('Validator', ''),
                                        
                                        # Additional Metadata
                                        'line_length': len(line),
                                        'indentation_level': len(line) - len(line.lstrip()),
                                        'is_comment': line.strip().startswith(('#', '//', '/*', '*')),
                                        'is_string_literal': self._is_in_string_literal(line, match_start),
                                        
                                        # Remediation Information
                                        'suggested_fix': self._suggest_fix_for_pattern(pattern, matched_text, line),
                                        'documentation_link': self._get_documentation_link(pattern),
                                        'priority': self._calculate_priority(severity, function_context),
                                    }
                                    
                                    matches.append(match_data)
                                    
                    except Exception as e:
                        # Log the error but continue processing
                        print(f"⚠️ Error processing file {file_path}: {e}")
                        continue
        
        # Add patterns that were attempted but found no matches
        successful_patterns = set(match['pattern'] for match in matches)
        failed_patterns = attempted_patterns - successful_patterns
        
        # Record patterns that didn't find matches for better debugging
        for failed_pattern in failed_patterns:
            pattern_attempt_record = {
                'file_path': 'N/A - No matches found',
                'line_number': 0,
                'pattern': failed_pattern,
                'matched_text': '',
                'match_start': 0,
                'match_end': 0,
                'full_line': '',
                'context': [],
                'function_context': '',
                'severity': 'info',
                'language': self.language.value,
                'file_extension': '',
                'gate_type': self.__class__.__name__.replace('Validator', ''),
                'line_length': 0,
                'indentation_level': 0,
                'is_comment': False,
                'is_string_literal': False,
                'suggested_fix': f'Implement patterns matching: {failed_pattern}',
                'documentation_link': self._get_documentation_link(failed_pattern),
                'priority': 'medium',
                'status': 'pattern_not_found',  # Special status for unsuccessful patterns
                'files_searched': len([f for ext in extensions for f in target_path.rglob(f"*{ext}") if f.is_file()]),
                'total_lines_searched': 'N/A'  # Simplified to avoid complex calculation
            }
            matches.append(pattern_attempt_record)
        
        return matches
    
    def _extract_function_context(self, lines: List[str], current_line: int) -> Dict[str, Any]:
        """Extract function/method context information"""
        
        function_patterns = {
            Language.PYTHON: [r'^\s*def\s+(\w+)', r'^\s*class\s+(\w+)', r'^\s*async\s+def\s+(\w+)'],
            Language.JAVA: [r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)*(\w+)\s*\(', r'^\s*(?:public|private|protected)?\s*class\s+(\w+)'],
            Language.JAVASCRIPT: [r'^\s*function\s+(\w+)', r'^\s*const\s+(\w+)\s*=', r'^\s*(\w+)\s*:\s*function'],
            Language.TYPESCRIPT: [r'^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)', r'^\s*(?:export\s+)?class\s+(\w+)'],
            Language.CSHARP: [r'^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:\w+\s+)*(\w+)\s*\(', r'^\s*(?:public|private|protected|internal)?\s*class\s+(\w+)']
        }
        
        patterns = function_patterns.get(self.language, [])
        
        # Search backwards from current line to find function definition
        for i in range(current_line - 1, max(0, current_line - 50), -1):
            line = lines[i].strip()
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    return {
                        'function_name': match.group(1),
                        'function_line': i + 1,
                        'function_signature': line,
                        'distance_from_function': current_line - (i + 1)
                    }
        
        return {
            'function_name': 'unknown',
            'function_line': 0,
            'function_signature': '',
            'distance_from_function': 0
        }
    
    def _determine_pattern_severity(self, pattern: str, matched_text: str) -> str:
        """Determine severity level of the pattern match"""
        
        # High severity patterns (security/critical issues)
        high_severity_keywords = ['password', 'secret', 'token', 'key', 'auth', 'credential', 'sql injection', 'xss']
        
        # Medium severity patterns (important but not critical)
        medium_severity_keywords = ['error', 'exception', 'warning', 'deprecated', 'todo', 'fixme']
        
        # Low severity patterns (informational)
        low_severity_keywords = ['log', 'debug', 'info', 'trace']
        
        pattern_lower = pattern.lower()
        matched_lower = matched_text.lower()
        
        for keyword in high_severity_keywords:
            if keyword in pattern_lower or keyword in matched_lower:
                return 'HIGH'
        
        for keyword in medium_severity_keywords:
            if keyword in pattern_lower or keyword in matched_lower:
                return 'MEDIUM'
        
        for keyword in low_severity_keywords:
            if keyword in pattern_lower or keyword in matched_lower:
                return 'LOW'
        
        return 'MEDIUM'  # Default severity
    
    def _classify_pattern_type(self, pattern: str) -> str:
        """Classify the type of pattern for better categorization"""
        
        pattern_types = {
            'logging': ['log', 'logger', 'console', 'print', 'debug'],
            'error_handling': ['try', 'catch', 'except', 'error', 'exception'],
            'security': ['password', 'token', 'secret', 'auth', 'credential'],
            'database': ['sql', 'query', 'select', 'insert', 'update', 'delete'],
            'api': ['http', 'rest', 'api', 'endpoint', 'request', 'response'],
            'testing': ['test', 'assert', 'mock', 'spec', 'should'],
            'configuration': ['config', 'setting', 'property', 'env'],
            'monitoring': ['metric', 'trace', 'span', 'monitor', 'alert']
        }
        
        pattern_lower = pattern.lower()
        
        for category, keywords in pattern_types.items():
            if any(keyword in pattern_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _categorize_match(self, pattern: str, matched_text: str) -> str:
        """Categorize the match for better organization"""
        
        # Use pattern type as base category
        base_category = self._classify_pattern_type(pattern)
        
        # Add specific subcategories based on matched text
        if 'structured' in matched_text.lower():
            return f"{base_category}_structured"
        elif 'async' in matched_text.lower():
            return f"{base_category}_async"
        elif 'error' in matched_text.lower():
            return f"{base_category}_error"
        
        return base_category
    
    def _is_in_string_literal(self, line: str, position: int) -> bool:
        """Check if the match is inside a string literal"""
        
        # Simple check for common string delimiters
        before_match = line[:position]
        
        # Count quotes before the match
        single_quotes = before_match.count("'") - before_match.count("\\'")
        double_quotes = before_match.count('"') - before_match.count('\\"')
        
        # If odd number of quotes, we're inside a string
        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)
    
    def _suggest_fix_for_pattern(self, pattern: str, matched_text: str, full_line: str) -> str:
        """Suggest a fix for the detected pattern"""
        
        pattern_lower = pattern.lower()
        
        if 'password' in pattern_lower or 'secret' in pattern_lower:
            return "Remove sensitive data from logs. Use placeholder values or hash sensitive information."
        elif 'log' in pattern_lower and 'error' not in pattern_lower:
            return "Consider using structured logging with appropriate log levels."
        elif 'try' in pattern_lower or 'catch' in pattern_lower:
            return "Ensure proper error handling with specific exception types and logging."
        elif 'todo' in pattern_lower or 'fixme' in pattern_lower:
            return "Address this TODO/FIXME item before production deployment."
        else:
            return "Review this code pattern for compliance with best practices."
    
    def _get_documentation_link(self, pattern: str) -> str:
        """Get relevant documentation link for the pattern"""
        
        # This could be expanded to return actual documentation links
        # For now, return a placeholder that could be configured
        pattern_type = self._classify_pattern_type(pattern)
        
        doc_links = {
            'logging': 'https://docs.example.com/logging-best-practices',
            'error_handling': 'https://docs.example.com/error-handling',
            'security': 'https://docs.example.com/security-guidelines',
            'testing': 'https://docs.example.com/testing-standards',
            'api': 'https://docs.example.com/api-design',
        }
        
        return doc_links.get(pattern_type, 'https://docs.example.com/coding-standards')
    
    def _calculate_priority(self, severity: str, function_context: Dict[str, Any]) -> int:
        """Calculate priority score (1-10, 10 being highest priority)"""
        
        base_priority = {
            'HIGH': 8,
            'MEDIUM': 5,
            'LOW': 2
        }.get(severity, 5)
        
        # Increase priority if in main/public functions
        function_name = function_context.get('function_name', '').lower()
        if any(keyword in function_name for keyword in ['main', 'public', 'api', 'controller']):
            base_priority += 2
        
        # Decrease priority if in test files
        if any(keyword in function_name for keyword in ['test', 'spec', 'mock']):
            base_priority -= 1
        
        return max(1, min(10, base_priority))
    
    def _estimate_expected_count(self, file_analyses: List[FileAnalysis]) -> int:
        """Estimate expected count based on file analyses"""
        
        # Filter files for current language
        lang_files = [f for f in file_analyses if f.language == self.language]
        
        if not lang_files:
            return 0
        
        total_loc = sum(f.lines_of_code for f in lang_files)
        file_count = len(lang_files)
        
        return self._calculate_expected_count(total_loc, file_count, lang_files)
    
    def _calculate_quality_score(self, matches: List[Dict[str, Any]], expected: int) -> float:
        """Calculate quality score based on matches found vs expected"""
        if expected == 0:
            return 100.0 if len(matches) == 0 else 50.0
        
        coverage = min(len(matches) / expected, 1.0) * 100
        
        # Assess quality based on implementation patterns found
        quality_assessment = self._assess_implementation_quality(matches)
        quality_bonus = sum(quality_assessment.values()) if quality_assessment else 0
        
        # Calculate final score (coverage + quality bonus, capped at 100)
        final_score = min(coverage + quality_bonus, 100.0)
        
        return final_score
    
    def _generate_llm_recommendations(self, gate_name: str, matches: List[Dict[str, Any]], 
                                    expected: int, detected_technologies: Dict[str, List[str]],
                                    llm_manager=None) -> List[str]:
        """Generate intelligent recommendations using LLM analysis"""
        
        if not llm_manager or not llm_manager.is_enabled():
            # Fallback to static recommendations
            return self._get_static_recommendations(matches, expected)
        
        try:
            # Prepare context for LLM analysis
            context = self._prepare_llm_context(gate_name, matches, expected, detected_technologies)
            
            # Generate LLM prompt
            prompt = self._create_recommendation_prompt(context)
            
            # Get LLM response
            llm_response = llm_manager.analyze_code_with_context(
                prompt=prompt,
                context=context,
                analysis_type="recommendations"
            )
            
            if llm_response and llm_response.get('recommendations'):
                recommendations = llm_response['recommendations']
                
                # Validate and format recommendations
                if isinstance(recommendations, list):
                    return [str(rec).strip() for rec in recommendations if rec and str(rec).strip()]
                elif isinstance(recommendations, str):
                    # Split string recommendations by newlines or bullets
                    lines = recommendations.split('\n')
                    formatted_recs = []
                    for line in lines:
                        line = line.strip()
                        # Remove bullet points and numbering
                        line = re.sub(r'^[-*•]\s*', '', line)
                        line = re.sub(r'^\d+\.\s*', '', line)
                        if line and len(line) > 10:  # Filter out very short lines
                            formatted_recs.append(line)
                    return formatted_recs[:5]  # Limit to 5 recommendations
                
        except Exception as e:
            print(f"⚠️ LLM recommendation generation failed: {e}")
        
        # Fallback to static recommendations
        return self._get_static_recommendations(matches, expected)
    
    def _prepare_llm_context(self, gate_name: str, matches: List[Dict[str, Any]], 
                           expected: int, detected_technologies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Prepare context for LLM analysis"""
        
        # Extract key information from matches
        files_analyzed = list(set(match.get('relative_path', match.get('file', 'unknown')) for match in matches))
        languages = list(set(match.get('language', 'unknown') for match in matches))
        severity_counts = {}
        pattern_types = {}
        
        for match in matches:
            severity = match.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            pattern_type = match.get('pattern_type', 'unknown')
            pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
        
        # Get sample matches for analysis (limit to avoid token overflow)
        sample_matches = matches[:10] if len(matches) > 10 else matches
        
        # Simplify matches for LLM (remove verbose fields)
        simplified_matches = []
        for match in sample_matches:
            simplified_match = {
                'file': match.get('file_name', 'unknown'),
                'line': match.get('line_number', 0),
                'code': match.get('matched_text', match.get('match', '')),
                'context': match.get('full_line', ''),
                'severity': match.get('severity', 'UNKNOWN'),
                'category': match.get('category', 'unknown'),
                'function': match.get('function_context', {}).get('function_name', 'unknown') if match.get('function_context') else 'unknown'
            }
            simplified_matches.append(simplified_match)
        
        context = {
            'gate_name': gate_name,
            'language': self.language.value if self.language else 'unknown',
            'expected_count': expected,
            'found_count': len(matches),
            'files_analyzed': files_analyzed[:5],  # Limit files for context
            'languages_detected': languages,
            'severity_distribution': severity_counts,
            'pattern_types': pattern_types,
            'detected_technologies': detected_technologies,
            'sample_matches': simplified_matches,
            'total_files': len(files_analyzed),
            'coverage_percentage': round((len(matches) / expected * 100) if expected > 0 else 0, 1)
        }
        
        return context
    
    def _create_recommendation_prompt(self, context: Dict[str, Any]) -> str:
        """Create LLM prompt for generating recommendations"""
        
        gate_name = context['gate_name']
        language = context['language']
        found_count = context['found_count']
        expected_count = context['expected_count']
        coverage = context['coverage_percentage']
        technologies = context['detected_technologies']
        sample_matches = context['sample_matches']
        severity_dist = context['severity_distribution']
        
        # Create technology context
        tech_context = ""
        if technologies:
            tech_list = []
            for category, techs in technologies.items():
                if techs:
                    tech_list.append(f"{category}: {', '.join(techs)}")
            if tech_list:
                tech_context = f"\n\nDetected Technologies:\n" + "\n".join(tech_list)
        
        # Create matches context
        matches_context = ""
        if sample_matches:
            matches_context = f"\n\nSample Code Patterns Found:\n"
            for i, match in enumerate(sample_matches[:5], 1):
                matches_context += f"{i}. File: {match['file']}, Line: {match['line']}\n"
                matches_context += f"   Code: {match['code']}\n"
                matches_context += f"   Severity: {match['severity']}, Function: {match['function']}\n"
        
        # Create severity context
        severity_context = ""
        if severity_dist:
            severity_context = f"\n\nSeverity Distribution:\n"
            for severity, count in severity_dist.items():
                severity_context += f"- {severity}: {count} issues\n"
        
        prompt = f"""
You are a senior software architect and code quality expert. Analyze the following code quality gate results and provide specific, actionable recommendations.

## Gate Analysis: {gate_name}
- **Language**: {language}
- **Coverage**: {found_count}/{expected_count} patterns found ({coverage}% coverage)
- **Status**: {'PASS' if coverage >= 80 else 'FAIL' if coverage < 60 else 'WARNING'}

{tech_context}
{severity_context}
{matches_context}

## Task
Based on this analysis, provide 3-5 specific, actionable recommendations to improve the {gate_name} implementation. Consider:

1. **Immediate Actions**: What should be fixed right away (especially HIGH severity issues)?
2. **Technology-Specific**: Recommendations based on the detected technologies
3. **Best Practices**: Industry standards for {gate_name} in {language}
4. **Implementation Strategy**: How to systematically improve coverage
5. **Monitoring & Maintenance**: Long-term quality assurance

## Requirements
- Be specific and actionable (not generic advice)
- Reference the actual technologies and patterns found
- Prioritize recommendations by impact and urgency
- Include concrete examples when possible
- Focus on practical implementation steps

Provide your response as a JSON object with this structure:
{{
    "recommendations": [
        "Specific recommendation 1 with concrete actions",
        "Specific recommendation 2 with implementation details",
        "Specific recommendation 3 with technology-specific guidance",
        "Specific recommendation 4 with monitoring suggestions",
        "Specific recommendation 5 with best practices"
    ]
}}
"""
        
        return prompt.strip()
    
    def _get_static_recommendations(self, matches: List[Dict[str, Any]], expected: int) -> List[str]:
        """Get static recommendations as fallback when LLM is unavailable"""
        
        if len(matches) == 0:
            return self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            return self._get_partial_implementation_recommendations()
        else:
            return self._get_quality_improvement_recommendations() 