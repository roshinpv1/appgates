"""
Testing Gate Validators - Validators for testing-related quality gates
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from ...models import Language, FileAnalysis, GateType
from .base import BaseGateValidator, GateValidationResult


class AutomatedTestsValidator(BaseGateValidator):
    """Validates automated test coverage and quality"""
    
    def __init__(self, language: Language, gate_type: GateType = GateType.AUTOMATED_TESTS):
        """Initialize with gate type for pattern loading"""
        super().__init__(language, gate_type)
    
    def validate(self, target_path: Path, 
                file_analyses: List[FileAnalysis]) -> GateValidationResult:
        """Validate automated test implementation"""
        
        # Get all patterns from loaded configuration
        all_patterns = []
        for category_patterns in self.patterns.values():
            if isinstance(category_patterns, list):
                all_patterns.extend(category_patterns)
        
        if not all_patterns:
            # Fallback to hardcoded patterns
            all_patterns = self._get_hardcoded_patterns().get('test_patterns', [])
        
        # Search for patterns
        matches = self._search_files_for_patterns(
            target_path, 
            self._get_file_extensions(), 
            all_patterns
        )
        
        # For test gates, we want to include test files
        # No need to filter them out
        
        # Calculate expected count based on source files
        source_files = [f for f in file_analyses if not self._is_test_file(f.file_path)]
        expected = self._estimate_expected_count(source_files)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(matches, expected)
        
        # Generate details and recommendations
        details = self._generate_details(matches)
        recommendations = self._generate_recommendations_from_matches(matches, expected)
        
        return GateValidationResult(
            expected=expected,
            found=len(matches),
            quality_score=quality_score,
            details=details,
            recommendations=recommendations,
            matches=matches
        )
    
    def _get_hardcoded_patterns(self) -> Dict[str, List[str]]:
        """Get hardcoded automated test patterns for each language as fallback"""
        
        if self.language == Language.PYTHON:
            return {
                'test_patterns': [
                    r'def test_\w+\s*\(',
                    r'class Test\w+\s*\(',
                    r'@pytest\.',
                    r'@patch\s*\(',
                    r'@mock\.',
                    r'assert\s+',
                    r'assertEqual\s*\(',
                    r'assertTrue\s*\(',
                    r'assertFalse\s*\(',
                    r'assertRaises\s*\(',
                    r'unittest\.',
                    r'pytest\.',
                    r'nose\.',
                    r'mock\.',
                    r'MagicMock\s*\(',
                    r'Mock\s*\(',
                ]
            }
        elif self.language == Language.JAVA:
            return {
                'test_patterns': [
                    r'@Test\s*',
                    r'@Before\s*',
                    r'@After\s*',
                    r'@BeforeEach\s*',
                    r'@AfterEach\s*',
                    r'@BeforeAll\s*',
                    r'@AfterAll\s*',
                    r'@Mock\s*',
                    r'@Spy\s*',
                    r'@InjectMocks\s*',
                    r'Assert\.',
                    r'assertEquals\s*\(',
                    r'assertTrue\s*\(',
                    r'assertFalse\s*\(',
                    r'assertThrows\s*\(',
                    r'Mockito\.',
                    r'when\s*\(',
                    r'verify\s*\(',
                    r'JUnit',
                    r'TestNG',
                ]
            }
        elif self.language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            return {
                'test_patterns': [
                    r'describe\s*\(',
                    r'it\s*\(',
                    r'test\s*\(',
                    r'expect\s*\(',
                    r'beforeEach\s*\(',
                    r'afterEach\s*\(',
                    r'beforeAll\s*\(',
                    r'afterAll\s*\(',
                    r'jest\.',
                    r'sinon\.',
                    r'chai\.',
                    r'assert\.',
                    r'should\.',
                    r'\.toBe\s*\(',
                    r'\.toEqual\s*\(',
                    r'\.toHaveBeenCalled',
                    r'\.toThrow\s*\(',
                    r'mount\s*\(',
                    r'shallow\s*\(',
                    r'render\s*\(',
                    r'fireEvent\.',
                    r'screen\.',
                ]
            }
        elif self.language == Language.CSHARP:
            return {
                'test_patterns': [
                    r'\[Test\]',
                    r'\[TestMethod\]',
                    r'\[Fact\]',
                    r'\[Theory\]',
                    r'\[SetUp\]',
                    r'\[TearDown\]',
                    r'\[TestInitialize\]',
                    r'\[TestCleanup\]',
                    r'Assert\.',
                    r'Should\.',
                    r'Expect\.',
                    r'Mock\.',
                    r'Verify\s*\(',
                    r'Setup\s*\(',
                    r'Returns\s*\(',
                    r'TestContext\s+',
                    r'TestFixture',
                    r'NUnit\.',
                    r'MSTest\.',
                    r'xUnit\.',
                ]
            }
        else:
            return {'test_patterns': []}
    
    def _get_config_patterns(self) -> Dict[str, List[str]]:
        """Get test configuration patterns"""
        return {
            'test_config': [
                'pytest.ini', 'tox.ini', 'jest.config.js', 'karma.conf.js',
                'test.config.js', 'mocha.opts', 'jasmine.json', 
                'phpunit.xml', 'TestConfiguration.cs', 'app.config'
            ]
        }
    
    def _calculate_expected_count(self, lang_files: List[FileAnalysis]) -> int:
        """Calculate expected test instances"""
        
        # For test gates, we want to calculate expected count based on source files
        source_files = len([f for f in lang_files 
                          if not self._is_test_file(f.file_path)])
        
        # Estimate test methods needed:
        # - At least 2 tests per source file
        # - Additional tests based on LOC (1 test per 50 LOC)
        base_tests = source_files * 2
        loc_based_tests = sum(f.lines_of_code for f in lang_files) // 50
        
        return max(base_tests + loc_based_tests, 10)  # At least 10 tests minimum
    
    def _assess_implementation_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """Assess test implementation quality"""
        
        quality_scores = {}
        
        # Check for test framework usage
        framework_patterns = ['@test', 'describe', 'it(', 'def test_', 'assert']
        framework_matches = len([match for match in matches 
                               if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                     for pattern in framework_patterns)])
        
        if framework_matches > 0:
            quality_scores['test_framework'] = min(framework_matches * 2, 15)
        
        # Check for mocking/stubbing
        mock_patterns = ['mock', 'stub', 'spy', 'fake', '@mock', 'mockito']
        mock_matches = len([match for match in matches 
                          if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                for pattern in mock_patterns)])
        
        if mock_matches > 0:
            quality_scores['mocking'] = min(mock_matches * 2, 15)
        
        # Check for test organization (describe/context blocks)
        org_patterns = ['describe', 'context', 'suite', 'testcase']
        org_matches = len([match for match in matches 
                         if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                               for pattern in org_patterns)])
        
        if org_matches > 0:
            quality_scores['organization'] = min(org_matches * 2, 15)
        
        # Check for assertions
        assertion_patterns = ['assert', 'expect', 'should', 'verify']
        assertion_matches = len([match for match in matches 
                               if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                     for pattern in assertion_patterns)])
        
        if assertion_matches > 0:
            quality_scores['assertions'] = min(assertion_matches * 2, 15)
        
        # Check for setup/teardown
        setup_patterns = ['setup', 'before', 'after', 'fixture']
        setup_matches = len([match for match in matches 
                           if any(pattern in match.get('matched_text', match.get('match', '')).lower() 
                                 for pattern in setup_patterns)])
        
        if setup_matches > 0:
            quality_scores['test_lifecycle'] = min(setup_matches * 2, 15)
        
        return quality_scores
    
    def _get_zero_implementation_recommendations(self) -> List[str]:
        """Recommendations when no tests found"""
        
        return [
            "Implement automated tests for your codebase",
            "Choose appropriate testing framework (pytest, JUnit, Jest, etc.)",
            "Start with unit tests for core business logic",
            "Add integration tests for API endpoints",
            "Implement test coverage reporting",
            "Set up continuous integration with automated testing"
        ]
    
    def _get_partial_implementation_recommendations(self) -> List[str]:
        """Recommendations for partial test implementation"""
        
        return [
            "Increase test coverage for untested modules",
            "Add more edge case testing scenarios",
            "Implement integration and end-to-end tests",
            "Add performance and load testing",
            "Implement test data factories and fixtures"
        ]
    
    def _get_quality_improvement_recommendations(self) -> List[str]:
        """Recommendations for improving test quality"""
        
        return [
            "Add more assertions and edge case testing",
            "Implement property-based testing",
            "Add mutation testing to verify test quality",
            "Implement test performance monitoring",
            "Add visual regression testing for UI components"
        ]
    
    def _generate_details(self, matches: List[Dict[str, Any]]) -> List[str]:
        """Generate test implementation details"""
        
        if not matches:
            return super()._generate_details([])
        
        # Add to details set for uniqueness
        self._details_set.add(f"Found {len(matches)} test implementations")
        
        # Group by file
        files_with_tests = len(set(match.get('file_path', match.get('file', 'unknown')) for match in matches))
        self._details_set.add(f"Tests present in {files_with_tests} files")
        
        # Check for different types of tests
        types = set()  # Use set for unique types
        if any('unit' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Unit tests')
        if any('integration' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('Integration tests')
        if any('e2e' in match.get('matched_text', match.get('match', '')).lower() for match in matches):
            types.add('End-to-end tests')
        
        if types:
            self._details_set.add(f"Test types: {', '.join(sorted(types))}")
        
        # Add detailed match information using the standardized method
        if matches:
            self._details_set.add("")  # Add spacing
            
            # Define categories for tests
            category_keywords = {
                'Test Frameworks': ['@test', 'describe', 'it(', 'test_', 'fact'],
                'Assertions': ['assert', 'expect', 'should', 'verify'],
                'Mocking': ['mock', 'stub', 'spy', 'fake'],
                'Setup/Teardown': ['before', 'after', 'setup', 'teardown'],
                'Test Utilities': ['fixture', 'helper', 'factory', 'builder']
            }
            
            detailed_matches = self._generate_detailed_match_info(
                matches, 
                max_items=15,
                show_categories=True,
                category_keywords=category_keywords
            )
            self._details_set.update(detailed_matches)
        
        return list(self._details_set)

    def _generate_recommendations_from_matches(self, matches: List[Dict[str, Any]], 
                                             expected: int) -> List[str]:
        """Generate recommendations based on test findings"""
        
        if len(matches) == 0:
            recommendations = self._get_zero_implementation_recommendations()
        elif len(matches) < expected:
            recommendations = self._get_partial_implementation_recommendations()
        else:
            recommendations = self._get_quality_improvement_recommendations()
            
        # Add recommendations to set for uniqueness
        self._recommendations_set.update(recommendations)
        return list(self._recommendations_set) 